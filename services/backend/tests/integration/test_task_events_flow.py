# [Task]: T039 — Integration test: task CRUD → event → Audit Service
"""Integration test for the task event publishing flow.

Tests that task CRUD operations publish the correct events
and that the Audit Service handler correctly processes them.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from src.models.task import TaskCreate, TaskPriority, TaskUpdate
from src.services.task_service import TaskService


@pytest.fixture
def captured_events():
    """Capture events published by the EventPublisher."""
    return []


@pytest.fixture
def mock_store():
    """Create a mock StateStore backed by a dict."""
    store = MagicMock()
    data = {}

    def save(key, value):
        data[key] = value

    def get(key):
        return data.get(key)

    def delete(key):
        data.pop(key, None)

    def bulk_get(keys):
        return {k: data[k] for k in keys if k in data}

    store.save.side_effect = save
    store.get.side_effect = get
    store.delete.side_effect = delete
    store.bulk_get.side_effect = bulk_get
    store._data = data
    return store


@pytest.fixture
def mock_publisher(captured_events):
    """Create a mock publisher that captures events."""
    pub = MagicMock()

    def capture_publish(topic, data):
        captured_events.append({"topic": topic, "data": data})

    pub.publish.side_effect = capture_publish
    return pub


@pytest.fixture
def service(mock_store, mock_publisher):
    """Create a TaskService with mock dependencies."""
    return TaskService(
        state_store=mock_store, publisher=mock_publisher
    )


class TestTaskEventFlow:
    """Integration tests for the full task event flow."""

    def test_create_publishes_created_event(
        self, service, captured_events
    ):
        """Creating a task should publish a task.created event."""
        task = service.create(
            TaskCreate(title="Integration test task"), "user-1"
        )

        assert len(captured_events) == 1
        event = captured_events[0]
        assert event["topic"] == "task-events"
        assert event["data"]["event_type"] == "task.created"
        assert event["data"]["task_id"] == task.id
        assert event["data"]["user_id"] == "user-1"
        payload = event["data"]["payload"]
        assert payload["task"]["title"] == "Integration test task"

    def test_update_publishes_updated_event(
        self, service, captured_events
    ):
        """Updating a task should publish a task.updated event."""
        task = service.create(
            TaskCreate(title="Before update"), "user-1"
        )
        captured_events.clear()

        service.update(
            task.id,
            TaskUpdate(title="After update"),
            "user-1",
        )

        assert len(captured_events) == 1
        event = captured_events[0]
        assert event["data"]["event_type"] == "task.updated"
        payload = event["data"]["payload"]
        assert "title" in payload["changes"]

    def test_complete_publishes_completed_event(
        self, service, captured_events
    ):
        """Completing a task should publish a task.completed event."""
        task = service.create(
            TaskCreate(title="Complete me"), "user-1"
        )
        captured_events.clear()

        service.complete(task.id, "user-1")

        assert len(captured_events) == 1
        event = captured_events[0]
        assert event["data"]["event_type"] == "task.completed"
        payload = event["data"]["payload"]
        assert payload["task_id"] == task.id
        assert "completed_at" in payload

    def test_delete_publishes_deleted_event(
        self, service, captured_events
    ):
        """Deleting a task should publish a task.deleted event."""
        task = service.create(
            TaskCreate(title="Delete me"), "user-1"
        )
        captured_events.clear()

        service.delete(task.id, "user-1")

        assert len(captured_events) == 1
        event = captured_events[0]
        assert event["data"]["event_type"] == "task.deleted"
        payload = event["data"]["payload"]
        assert payload["task_id"] == task.id

    def test_full_lifecycle_events(self, service, captured_events):
        """Full lifecycle should produce exactly 4 events."""
        task = service.create(
            TaskCreate(
                title="Lifecycle",
                priority=TaskPriority.HIGH,
            ),
            "user-1",
        )
        service.update(
            task.id,
            TaskUpdate(title="Updated lifecycle"),
            "user-1",
        )
        service.complete(task.id, "user-1")
        service.delete(task.id, "user-1")

        assert len(captured_events) == 4
        event_types = [e["data"]["event_type"] for e in captured_events]
        assert event_types == [
            "task.created",
            "task.updated",
            "task.completed",
            "task.deleted",
        ]

    def test_audit_handler_processes_created_event(
        self, service, captured_events
    ):
        """Verify the Audit Service handler can process a created event."""
        import asyncio
        from services.audit.src.handlers.task_events import (
            handle_task_event,
        )
        from services.audit.src.services.audit_service import (
            AuditLogService,
        )

        # Create audit service with its own mock store
        audit_store = MagicMock()
        audit_data = {}
        audit_store.save.side_effect = lambda k, v: audit_data.__setitem__(k, v)
        audit_store.get.side_effect = lambda k: audit_data.get(k)
        audit_svc = AuditLogService(state_store=audit_store)

        # Create a task to generate an event
        task = service.create(
            TaskCreate(title="Audit test"), "user-1"
        )
        event_data = captured_events[0]["data"]

        # Process the event through audit handler
        import services.audit.src.handlers.task_events as handler_module
        handler_module._service = audit_svc

        asyncio.get_event_loop().run_until_complete(
            handle_task_event(event_data)
        )

        # Verify audit log was created
        assert audit_store.save.called
        assert not audit_svc.is_duplicate("nonexistent")
        assert audit_svc.is_duplicate(event_data["event_id"])
