# [Task]: T025 — Unit tests for TaskEvent model
"""Tests for TaskEvent model."""

from datetime import datetime, timezone

from src.events.task_event import (
    TaskCompletedPayload,
    TaskCreatedPayload,
    TaskDeletedPayload,
    TaskEvent,
    TaskEventType,
    TaskUpdatedPayload,
)


class TestTaskEvent:
    """Tests for the TaskEvent model."""

    def test_create_event(self):
        event = TaskEvent(
            event_type=TaskEventType.CREATED,
            task_id="task-123",
            payload={"task": {"title": "Test"}},
            user_id="user-1",
        )
        assert event.event_type == TaskEventType.CREATED
        assert event.task_id == "task-123"
        assert event.event_id is not None
        assert event.timestamp is not None

    def test_all_event_types(self):
        for et in TaskEventType:
            event = TaskEvent(
                event_type=et,
                task_id="t-1",
                payload={},
                user_id="u-1",
            )
            assert event.event_type == et


class TestPayloads:
    """Tests for event payload schemas."""

    def test_created_payload(self):
        p = TaskCreatedPayload(
            task={"id": "t-1", "title": "Test"}
        )
        assert p.task["id"] == "t-1"

    def test_updated_payload(self):
        p = TaskUpdatedPayload(
            task_id="t-1",
            changes={
                "title": {"old": "Old", "new": "New"}
            },
        )
        assert p.changes["title"]["new"] == "New"

    def test_completed_payload(self):
        p = TaskCompletedPayload(
            task_id="t-1",
            completed_at=datetime.now(timezone.utc),
            recurrence_pattern="daily",
        )
        assert p.recurrence_pattern == "daily"

    def test_completed_payload_no_recurrence(self):
        p = TaskCompletedPayload(
            task_id="t-1",
            completed_at=datetime.now(timezone.utc),
        )
        assert p.recurrence_pattern is None

    def test_deleted_payload(self):
        p = TaskDeletedPayload(
            task_id="t-1",
            deleted_at=datetime.now(timezone.utc),
        )
        assert p.task_id == "t-1"
