# [Task]: T046 — Integration test: complete recurring task → next instance created
"""Integration test for the recurring task flow.

Tests that completing a recurring task triggers creation of the next
instance with the correct due date and recurrence pattern.
"""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.handlers.task_events import handle_task_event
from src.services.recurring_service import (
    RecurringTaskService,
    compute_next_due_date,
)


@pytest.fixture
def mock_recurring_service():
    """Create a mock RecurringTaskService."""
    svc = MagicMock(spec=RecurringTaskService)
    svc.create_next_instance = AsyncMock(
        return_value={"id": "new-task-1", "title": "Recurring"}
    )
    return svc


class TestRecurringFlow:
    """Integration tests for the recurring task flow."""

    def test_completed_event_with_recurrence_triggers_creation(
        self, mock_recurring_service
    ):
        """A task.completed event with recurrence_pattern should
        trigger creation of the next instance."""
        import src.handlers.task_events as handler_module
        handler_module._service = mock_recurring_service

        event_data = {
            "event_id": "evt-1",
            "event_type": "task.completed",
            "task_id": "task-1",
            "user_id": "user-1",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": {
                "task_id": "task-1",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "recurrence_pattern": "daily",
            },
        }

        asyncio.get_event_loop().run_until_complete(
            handle_task_event(event_data)
        )

        mock_recurring_service.create_next_instance.assert_called_once_with(
            task_id="task-1",
            recurrence_pattern="daily",
            user_id="user-1",
        )

    def test_completed_event_without_recurrence_is_skipped(
        self, mock_recurring_service
    ):
        """A task.completed event without recurrence should be ignored."""
        import src.handlers.task_events as handler_module
        handler_module._service = mock_recurring_service

        event_data = {
            "event_id": "evt-2",
            "event_type": "task.completed",
            "task_id": "task-2",
            "user_id": "user-1",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": {
                "task_id": "task-2",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "recurrence_pattern": None,
            },
        }

        asyncio.get_event_loop().run_until_complete(
            handle_task_event(event_data)
        )

        mock_recurring_service.create_next_instance.assert_not_called()

    def test_non_completed_event_is_skipped(
        self, mock_recurring_service
    ):
        """Non-completed events should be ignored."""
        import src.handlers.task_events as handler_module
        handler_module._service = mock_recurring_service

        event_data = {
            "event_id": "evt-3",
            "event_type": "task.created",
            "task_id": "task-3",
            "user_id": "user-1",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": {"task": {"title": "Test"}},
        }

        asyncio.get_event_loop().run_until_complete(
            handle_task_event(event_data)
        )

        mock_recurring_service.create_next_instance.assert_not_called()

    def test_weekly_recurrence_date_computation(self):
        """Verify weekly date computation integrates correctly."""
        base = datetime(2026, 2, 8, tzinfo=timezone.utc)
        next_due = compute_next_due_date("weekly", from_date=base)
        assert next_due.day == 15
        assert next_due.month == 2

    def test_monthly_recurrence_date_computation(self):
        """Verify monthly date computation integrates correctly."""
        base = datetime(2026, 2, 8, tzinfo=timezone.utc)
        next_due = compute_next_due_date("monthly", from_date=base)
        assert next_due.month == 3
        assert next_due.day == 8
