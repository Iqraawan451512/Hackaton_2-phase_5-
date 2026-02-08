# [Task]: T054 — Unit tests for ReminderScheduler
"""Tests for ReminderScheduler with mocked Dapr dependencies."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.models.reminder import ReminderStatus
from src.services.reminder_scheduler import (
    REMINDER_OFFSET_MINUTES,
    ReminderScheduler,
)


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

    store.save.side_effect = save
    store.get.side_effect = get
    store.delete.side_effect = delete
    store._data = data
    return store


@pytest.fixture
def scheduler(mock_store):
    """Create a ReminderScheduler with mock state store."""
    with patch(
        "src.services.reminder_scheduler.DaprClient"
    ) as mock_dapr_cls:
        mock_client = MagicMock()
        mock_dapr_cls.return_value.__enter__ = MagicMock(
            return_value=mock_client
        )
        mock_dapr_cls.return_value.__exit__ = MagicMock(
            return_value=False
        )
        sched = ReminderScheduler(state_store=mock_store)
        yield sched


class TestSchedule:
    """Tests for ReminderScheduler.schedule()."""

    def test_schedule_creates_reminder(self, scheduler):
        due = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc)
        reminder = scheduler.schedule("task-1", due)

        assert reminder.task_id == "task-1"
        assert reminder.status == ReminderStatus.PENDING
        assert reminder.reminder_id is not None

    def test_schedule_time_is_before_due(self, scheduler):
        due = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc)
        reminder = scheduler.schedule("task-1", due)

        expected_time = due - timedelta(minutes=REMINDER_OFFSET_MINUTES)
        assert reminder.scheduled_time == expected_time

    def test_schedule_persists_to_store(self, scheduler, mock_store):
        due = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc)
        reminder = scheduler.schedule("task-1", due)

        # Should save the reminder and the task index
        assert mock_store.save.call_count >= 2

    def test_reschedule_cancels_previous(self, scheduler):
        due1 = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc)
        due2 = datetime(2026, 4, 1, 12, 0, tzinfo=timezone.utc)

        r1 = scheduler.schedule("task-1", due1)
        r2 = scheduler.schedule("task-1", due2)

        # Should be a new reminder
        assert r2.reminder_id != r1.reminder_id
        assert r2.scheduled_time == due2 - timedelta(
            minutes=REMINDER_OFFSET_MINUTES
        )


class TestCancel:
    """Tests for ReminderScheduler.cancel()."""

    def test_cancel_existing(self, scheduler):
        due = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc)
        scheduler.schedule("task-1", due)
        result = scheduler.cancel("task-1")
        assert result is True

    def test_cancel_nonexistent(self, scheduler):
        result = scheduler.cancel("no-task")
        assert result is False

    def test_cancel_marks_cancelled(self, scheduler):
        due = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc)
        scheduler.schedule("task-1", due)
        scheduler.cancel("task-1")

        reminder = scheduler.get_reminder_for_task("task-1")
        assert reminder.status == ReminderStatus.CANCELLED


class TestGetReminderForTask:
    """Tests for ReminderScheduler.get_reminder_for_task()."""

    def test_get_existing(self, scheduler):
        due = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc)
        scheduled = scheduler.schedule("task-1", due)
        found = scheduler.get_reminder_for_task("task-1")

        assert found is not None
        assert found.reminder_id == scheduled.reminder_id

    def test_get_nonexistent(self, scheduler):
        result = scheduler.get_reminder_for_task("no-task")
        assert result is None


class TestMarkSent:
    """Tests for ReminderScheduler.mark_sent()."""

    def test_mark_sent(self, scheduler):
        due = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc)
        reminder = scheduler.schedule("task-1", due)
        result = scheduler.mark_sent(reminder.reminder_id)

        assert result is not None
        assert result.status == ReminderStatus.SENT

    def test_mark_sent_nonexistent(self, scheduler):
        result = scheduler.mark_sent("no-reminder")
        assert result is None
