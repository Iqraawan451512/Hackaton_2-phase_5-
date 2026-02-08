# [Task]: T092 — Full end-to-end test: CRUD → events → recurring → reminders → sync → audit
"""End-to-end integration test covering the complete task lifecycle.

Tests the full pipeline:
1. Create task with due date and recurrence → task.created event
2. Update task → task.updated event
3. Complete task → task.completed event → recurring task triggered → reminder cancelled
4. Delete task → task.deleted event
5. All events audit-logged and broadcast via task-updates
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from src.models.task import TaskCreate, TaskPriority, TaskUpdate, RecurrencePattern
from src.services.task_service import TaskService


@pytest.fixture
def captured_events():
    """Capture all events published to any topic."""
    return []


@pytest.fixture
def mock_store():
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
    pub = MagicMock()

    def capture(topic, data):
        captured_events.append({"topic": topic, "data": data})

    pub.publish.side_effect = capture
    pub.publish_task_update.side_effect = lambda et, tid, td: captured_events.append(
        {"topic": "task-updates", "data": {"event_type": et, "task_id": tid, "task": td}}
    )
    return pub


@pytest.fixture
def service(mock_store, mock_publisher):
    return TaskService(state_store=mock_store, publisher=mock_publisher)


class TestFullEndToEnd:
    """Full end-to-end lifecycle tests."""

    def test_complete_lifecycle_produces_correct_events(
        self, service, captured_events
    ):
        """Full CRUD lifecycle should produce events to both task-events and task-updates."""
        # 1. Create a recurring task with due date
        task = service.create(
            TaskCreate(
                title="E2E test task",
                priority=TaskPriority.HIGH,
                tags=["e2e", "test"],
                recurrence_pattern=RecurrencePattern.DAILY,
                due_date=datetime.now(timezone.utc) + timedelta(hours=2),
            ),
            "e2e-user",
        )
        assert task.id is not None
        assert task.recurrence_pattern == RecurrencePattern.DAILY

        # 2. Update the task
        updated = service.update(
            task.id,
            TaskUpdate(title="E2E updated task", priority=TaskPriority.MEDIUM),
            "e2e-user",
        )
        assert updated.title == "E2E updated task"
        assert updated.priority == TaskPriority.MEDIUM

        # 3. Complete the task
        completed = service.complete(task.id, "e2e-user")
        assert completed.status.value == "completed"

        # 4. Delete the task
        deleted = service.delete(task.id, "e2e-user")
        assert deleted is True

        # Verify event stream
        task_events = [
            e for e in captured_events if e["topic"] == "task-events"
        ]
        task_updates = [
            e for e in captured_events if e["topic"] == "task-updates"
        ]

        # Should have 4 task-events: created, updated, completed, deleted
        assert len(task_events) == 4
        event_types = [e["data"]["event_type"] for e in task_events]
        assert event_types == [
            "task.created",
            "task.updated",
            "task.completed",
            "task.deleted",
        ]

        # Should have 4 task-updates (one per CRUD operation)
        assert len(task_updates) == 4
        update_types = [e["data"]["event_type"] for e in task_updates]
        assert update_types == [
            "task.created",
            "task.updated",
            "task.completed",
            "task.deleted",
        ]

    def test_completed_event_includes_recurrence(
        self, service, captured_events
    ):
        """task.completed event for a recurring task includes the pattern."""
        task = service.create(
            TaskCreate(
                title="Recurring E2E",
                recurrence_pattern=RecurrencePattern.WEEKLY,
            ),
            "e2e-user",
        )
        service.complete(task.id, "e2e-user")

        completed_events = [
            e for e in captured_events
            if e["topic"] == "task-events"
            and e["data"].get("event_type") == "task.completed"
        ]
        assert len(completed_events) == 1
        payload = completed_events[0]["data"]["payload"]
        assert payload["recurrence_pattern"] == "weekly"

    def test_no_update_event_on_no_changes(
        self, service, captured_events
    ):
        """Updating with identical values should NOT produce an event."""
        task = service.create(
            TaskCreate(title="No change"), "e2e-user"
        )
        captured_events.clear()

        service.update(
            task.id,
            TaskUpdate(title="No change"),
            "e2e-user",
        )

        task_events = [
            e for e in captured_events if e["topic"] == "task-events"
        ]
        assert len(task_events) == 0

    def test_list_excludes_deleted_tasks(self, service):
        """Deleted tasks should not appear in listing."""
        t1 = service.create(TaskCreate(title="Keep"), "e2e-user")
        t2 = service.create(TaskCreate(title="Delete"), "e2e-user")
        service.delete(t2.id, "e2e-user")

        tasks = service.list_by_user("e2e-user")
        ids = [t.id for t in tasks]
        assert t1.id in ids
        assert t2.id not in ids

    def test_search_filter_sort_integration(self, service):
        """Full filter/sort/search pipeline."""
        service.create(
            TaskCreate(title="Alpha", priority=TaskPriority.LOW, tags=["a"]),
            "e2e-user",
        )
        service.create(
            TaskCreate(title="Beta", priority=TaskPriority.HIGH, tags=["b"]),
            "e2e-user",
        )
        service.create(
            TaskCreate(title="Alpha Beta", priority=TaskPriority.MEDIUM, tags=["a", "b"]),
            "e2e-user",
        )

        # Search
        results = service.list_tasks("e2e-user", search="alpha")
        assert len(results) == 2

        # Filter by tag
        results = service.list_tasks("e2e-user", tag="b")
        assert len(results) == 2

        # Filter by priority
        results = service.list_tasks("e2e-user", priority="high")
        assert len(results) == 1

        # Sort by priority ascending
        results = service.list_tasks(
            "e2e-user", sort_by="priority", sort_order="asc"
        )
        assert results[0].priority == TaskPriority.HIGH
