# [Task]: T026, T035 — TaskService with CRUD operations and structured logging
"""Task service for CRUD operations using Dapr state store."""

from datetime import datetime, timezone
from typing import Optional

from src.config import StateStore, get_logger
from src.events.publisher import EventPublisher, TOPIC_TASK_EVENTS
from src.events.task_event import (
    TaskCompletedPayload,
    TaskCreatedPayload,
    TaskDeletedPayload,
    TaskEvent,
    TaskEventType,
    TaskUpdatedPayload,
)
from src.models.task import Task, TaskCreate, TaskStatus, TaskUpdate

logger = get_logger("task_service")

# Dapr state store key prefix (per data-model.md)
KEY_PREFIX = "task"


def _task_key(task_id: str) -> str:
    return f"{KEY_PREFIX}||{task_id}"


def _user_index_key(user_id: str) -> str:
    return f"user-tasks||{user_id}"


class TaskService:
    """Manages task lifecycle with event publishing."""

    def __init__(
        self,
        state_store: Optional[StateStore] = None,
        publisher: Optional[EventPublisher] = None,
    ):
        self.store = state_store or StateStore()
        self.publisher = publisher or EventPublisher()

    def create(self, data: TaskCreate, user_id: str) -> Task:
        """Create a new task and publish task.created event."""
        task = Task(
            title=data.title,
            description=data.description,
            priority=data.priority,
            due_date=data.due_date,
            tags=data.tags,
            recurrence_pattern=data.recurrence_pattern,
            created_by=user_id,
        )
        self.store.save(_task_key(task.id), task.model_dump(mode="json"))
        self._add_to_user_index(user_id, task.id)

        logger.info(
            "task_created",
            task_id=task.id,
            user_id=user_id,
            title=task.title,
        )

        payload = TaskCreatedPayload(
            task=task.model_dump(mode="json")
        )
        event = TaskEvent(
            event_type=TaskEventType.CREATED,
            task_id=task.id,
            payload=payload.model_dump(mode="json"),
            user_id=user_id,
        )
        self.publisher.publish(
            TOPIC_TASK_EVENTS, event.model_dump(mode="json")
        )
        self.publisher.publish_task_update(
            "task.created", task.id, task.model_dump(mode="json")
        )
        return task

    def get(self, task_id: str) -> Optional[Task]:
        """Retrieve a task by ID."""
        data = self.store.get(_task_key(task_id))
        if data is None:
            return None
        return Task(**data)

    def list_by_user(self, user_id: str) -> list[Task]:
        """List all tasks for a user."""
        index = self.store.get(_user_index_key(user_id))
        if not index:
            return []
        task_ids = index.get("task_ids", [])
        if not task_ids:
            return []
        keys = [_task_key(tid) for tid in task_ids]
        bulk = self.store.bulk_get(keys)
        tasks = []
        for tid in task_ids:
            data = bulk.get(_task_key(tid))
            if data and data.get("status") != TaskStatus.DELETED.value:
                tasks.append(Task(**data))
        return tasks

    def list_tasks(
        self,
        user_id: str,
        search: Optional[str] = None,
        priority: Optional[str] = None,
        tag: Optional[str] = None,
        status: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> list[Task]:
        """List tasks with filtering, sorting, and search.

        Args:
            user_id: User ID to filter by.
            search: Case-insensitive title search.
            priority: Filter by priority (high/medium/low).
            tag: Filter by tag name.
            status: Filter by status (pending/completed/deleted).
            sort_by: Field to sort by (created_at, priority, due_date, title).
            sort_order: Sort direction (asc or desc).
        """
        tasks = self.list_by_user(user_id)

        # Filter by status
        if status:
            tasks = [t for t in tasks if t.status.value == status]

        # Filter by priority
        if priority:
            tasks = [t for t in tasks if t.priority.value == priority]

        # Filter by tag
        if tag:
            tasks = [t for t in tasks if tag in t.tags]

        # Search by title
        if search:
            search_lower = search.lower()
            tasks = [
                t for t in tasks
                if search_lower in t.title.lower()
            ]

        # Sort
        priority_order = {"high": 0, "medium": 1, "low": 2}
        reverse = sort_order == "desc"

        if sort_by == "priority":
            tasks.sort(
                key=lambda t: priority_order.get(
                    t.priority.value, 1
                ),
                reverse=reverse,
            )
        elif sort_by == "due_date":
            tasks.sort(
                key=lambda t: t.due_date or datetime.max.replace(
                    tzinfo=timezone.utc
                ),
                reverse=reverse,
            )
        elif sort_by == "title":
            tasks.sort(
                key=lambda t: t.title.lower(),
                reverse=reverse,
            )
        else:  # default: created_at
            tasks.sort(
                key=lambda t: t.created_at,
                reverse=reverse,
            )

        return tasks

    def update(
        self, task_id: str, data: TaskUpdate, user_id: str
    ) -> Optional[Task]:
        """Update a task and publish task.updated event."""
        task = self.get(task_id)
        if task is None:
            return None

        changes = {}
        update_data = data.model_dump(exclude_unset=True)
        for field, new_val in update_data.items():
            old_val = getattr(task, field)
            if old_val != new_val:
                changes[field] = {"old": old_val, "new": new_val}
                setattr(task, field, new_val)

        if not changes:
            return task

        task.updated_at = datetime.now(timezone.utc)
        self.store.save(
            _task_key(task.id), task.model_dump(mode="json")
        )

        logger.info(
            "task_updated",
            task_id=task.id,
            user_id=user_id,
            fields=list(changes.keys()),
        )

        payload = TaskUpdatedPayload(
            task_id=task.id,
            changes={
                k: {
                    "old": str(v["old"]),
                    "new": str(v["new"]),
                }
                for k, v in changes.items()
            },
        )
        event = TaskEvent(
            event_type=TaskEventType.UPDATED,
            task_id=task.id,
            payload=payload.model_dump(mode="json"),
            user_id=user_id,
        )
        self.publisher.publish(
            TOPIC_TASK_EVENTS, event.model_dump(mode="json")
        )
        self.publisher.publish_task_update(
            "task.updated", task.id, task.model_dump(mode="json")
        )
        return task

    def delete(self, task_id: str, user_id: str) -> bool:
        """Soft-delete a task and publish task.deleted event."""
        task = self.get(task_id)
        if task is None:
            return False

        task.status = TaskStatus.DELETED
        task.updated_at = datetime.now(timezone.utc)
        self.store.save(
            _task_key(task.id), task.model_dump(mode="json")
        )

        logger.info(
            "task_deleted",
            task_id=task.id,
            user_id=user_id,
        )

        payload = TaskDeletedPayload(
            task_id=task.id,
            deleted_at=task.updated_at,
        )
        event = TaskEvent(
            event_type=TaskEventType.DELETED,
            task_id=task.id,
            payload=payload.model_dump(mode="json"),
            user_id=user_id,
        )
        self.publisher.publish(
            TOPIC_TASK_EVENTS, event.model_dump(mode="json")
        )
        self.publisher.publish_task_update(
            "task.deleted", task.id, task.model_dump(mode="json")
        )
        return True

    def complete(self, task_id: str, user_id: str) -> Optional[Task]:
        """Mark a task as completed and publish task.completed event."""
        task = self.get(task_id)
        if task is None:
            return None

        now = datetime.now(timezone.utc)
        task.status = TaskStatus.COMPLETED
        task.updated_at = now
        self.store.save(
            _task_key(task.id), task.model_dump(mode="json")
        )

        logger.info(
            "task_completed",
            task_id=task.id,
            user_id=user_id,
            recurrence=task.recurrence_pattern,
        )

        payload = TaskCompletedPayload(
            task_id=task.id,
            completed_at=now,
            recurrence_pattern=(
                task.recurrence_pattern.value
                if task.recurrence_pattern
                else None
            ),
        )
        event = TaskEvent(
            event_type=TaskEventType.COMPLETED,
            task_id=task.id,
            payload=payload.model_dump(mode="json"),
            user_id=user_id,
        )
        self.publisher.publish(
            TOPIC_TASK_EVENTS, event.model_dump(mode="json")
        )
        self.publisher.publish_task_update(
            "task.completed", task.id, task.model_dump(mode="json")
        )
        return task

    def _add_to_user_index(self, user_id: str, task_id: str) -> None:
        """Add a task ID to the user's task index."""
        key = _user_index_key(user_id)
        index = self.store.get(key)
        if index is None:
            index = {"task_ids": []}
        index["task_ids"].append(task_id)
        self.store.save(key, index)
