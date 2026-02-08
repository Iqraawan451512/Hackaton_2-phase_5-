# [Task]: T036 — Unit tests for TaskService CRUD operations
"""Tests for TaskService CRUD operations with mocked Dapr dependencies."""

from unittest.mock import MagicMock, patch

import pytest

from src.models.task import (
    Task,
    TaskCreate,
    TaskPriority,
    TaskStatus,
    TaskUpdate,
    RecurrencePattern,
)
from src.services.task_service import TaskService, _task_key, _user_index_key


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
def mock_publisher():
    """Create a mock EventPublisher."""
    return MagicMock()


@pytest.fixture
def service(mock_store, mock_publisher):
    """Create a TaskService with mock dependencies."""
    return TaskService(
        state_store=mock_store, publisher=mock_publisher
    )


class TestCreateTask:
    """Tests for TaskService.create()."""

    def test_create_minimal_task(self, service, mock_publisher):
        data = TaskCreate(title="Buy groceries")
        task = service.create(data, "user-1")

        assert task.title == "Buy groceries"
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.MEDIUM
        assert task.created_by == "user-1"
        assert task.id is not None
        mock_publisher.publish.assert_called_once()

    def test_create_full_task(self, service, mock_publisher):
        data = TaskCreate(
            title="Full task",
            description="A description",
            priority=TaskPriority.HIGH,
            tags=["work", "urgent"],
            recurrence_pattern=RecurrencePattern.DAILY,
        )
        task = service.create(data, "user-1")

        assert task.priority == TaskPriority.HIGH
        assert task.tags == ["work", "urgent"]
        assert task.recurrence_pattern == RecurrencePattern.DAILY
        mock_publisher.publish.assert_called_once()

    def test_create_publishes_created_event(
        self, service, mock_publisher
    ):
        data = TaskCreate(title="Test")
        service.create(data, "user-1")

        call_args = mock_publisher.publish.call_args
        assert call_args[0][0] == "task-events"
        event_data = call_args[0][1]
        assert event_data["event_type"] == "task.created"

    def test_create_saves_to_store(self, service, mock_store):
        data = TaskCreate(title="Store test")
        task = service.create(data, "user-1")

        mock_store.save.assert_any_call(
            _task_key(task.id),
            task.model_dump(mode="json"),
        )

    def test_create_updates_user_index(self, service, mock_store):
        data = TaskCreate(title="Index test")
        task = service.create(data, "user-1")

        mock_store.save.assert_any_call(
            _user_index_key("user-1"),
            {"task_ids": [task.id]},
        )


class TestGetTask:
    """Tests for TaskService.get()."""

    def test_get_existing_task(self, service):
        data = TaskCreate(title="Get me")
        created = service.create(data, "user-1")
        result = service.get(created.id)

        assert result is not None
        assert result.title == "Get me"
        assert result.id == created.id

    def test_get_nonexistent_task(self, service):
        result = service.get("nonexistent-id")
        assert result is None


class TestListTasks:
    """Tests for TaskService.list_by_user()."""

    def test_list_empty(self, service):
        result = service.list_by_user("user-no-tasks")
        assert result == []

    def test_list_user_tasks(self, service):
        service.create(TaskCreate(title="Task 1"), "user-1")
        service.create(TaskCreate(title="Task 2"), "user-1")
        result = service.list_by_user("user-1")

        assert len(result) == 2
        titles = {t.title for t in result}
        assert titles == {"Task 1", "Task 2"}

    def test_list_excludes_deleted(self, service):
        task = service.create(TaskCreate(title="Delete me"), "user-1")
        service.delete(task.id, "user-1")
        result = service.list_by_user("user-1")

        assert len(result) == 0


class TestUpdateTask:
    """Tests for TaskService.update()."""

    def test_update_title(self, service, mock_publisher):
        task = service.create(TaskCreate(title="Old"), "user-1")
        mock_publisher.reset_mock()

        updated = service.update(
            task.id, TaskUpdate(title="New"), "user-1"
        )
        assert updated.title == "New"
        mock_publisher.publish.assert_called_once()

    def test_update_nonexistent(self, service):
        result = service.update(
            "no-id", TaskUpdate(title="X"), "user-1"
        )
        assert result is None

    def test_update_no_changes(self, service, mock_publisher):
        task = service.create(TaskCreate(title="Same"), "user-1")
        mock_publisher.reset_mock()

        result = service.update(
            task.id, TaskUpdate(title="Same"), "user-1"
        )
        assert result.title == "Same"
        mock_publisher.publish.assert_not_called()

    def test_update_publishes_updated_event(
        self, service, mock_publisher
    ):
        task = service.create(TaskCreate(title="Before"), "user-1")
        mock_publisher.reset_mock()

        service.update(
            task.id, TaskUpdate(title="After"), "user-1"
        )
        call_args = mock_publisher.publish.call_args
        event_data = call_args[0][1]
        assert event_data["event_type"] == "task.updated"


class TestDeleteTask:
    """Tests for TaskService.delete()."""

    def test_delete_existing(self, service, mock_publisher):
        task = service.create(TaskCreate(title="Delete me"), "user-1")
        mock_publisher.reset_mock()

        result = service.delete(task.id, "user-1")
        assert result is True
        mock_publisher.publish.assert_called_once()

    def test_delete_nonexistent(self, service):
        result = service.delete("no-id", "user-1")
        assert result is False

    def test_delete_sets_status(self, service):
        task = service.create(TaskCreate(title="Soft del"), "user-1")
        service.delete(task.id, "user-1")

        deleted_task = service.get(task.id)
        assert deleted_task.status == TaskStatus.DELETED

    def test_delete_publishes_deleted_event(
        self, service, mock_publisher
    ):
        task = service.create(TaskCreate(title="Del evt"), "user-1")
        mock_publisher.reset_mock()

        service.delete(task.id, "user-1")
        call_args = mock_publisher.publish.call_args
        event_data = call_args[0][1]
        assert event_data["event_type"] == "task.deleted"


class TestCompleteTask:
    """Tests for TaskService.complete()."""

    def test_complete_existing(self, service, mock_publisher):
        task = service.create(TaskCreate(title="Complete me"), "user-1")
        mock_publisher.reset_mock()

        result = service.complete(task.id, "user-1")
        assert result.status == TaskStatus.COMPLETED
        mock_publisher.publish.assert_called_once()

    def test_complete_nonexistent(self, service):
        result = service.complete("no-id", "user-1")
        assert result is None

    def test_complete_publishes_completed_event(
        self, service, mock_publisher
    ):
        task = service.create(TaskCreate(title="Done"), "user-1")
        mock_publisher.reset_mock()

        service.complete(task.id, "user-1")
        call_args = mock_publisher.publish.call_args
        event_data = call_args[0][1]
        assert event_data["event_type"] == "task.completed"

    def test_complete_with_recurrence(self, service, mock_publisher):
        task = service.create(
            TaskCreate(
                title="Recurring",
                recurrence_pattern=RecurrencePattern.DAILY,
            ),
            "user-1",
        )
        mock_publisher.reset_mock()

        service.complete(task.id, "user-1")
        call_args = mock_publisher.publish.call_args
        event_data = call_args[0][1]
        payload = event_data["payload"]
        assert payload["recurrence_pattern"] == "daily"
