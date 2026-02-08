# [Task]: T056 — Integration test: due date → Dapr Job → reminder → notification
"""Integration test for the reminder and notification flow."""

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.handlers.reminders import handle_reminder
from src.models.notification import DeliveryStatus, NotificationChannel
from src.services.notification_service import NotificationService


@pytest.fixture
def mock_store():
    """Create a mock StateStore backed by a dict."""
    store = MagicMock()
    data = {}

    def save(key, value):
        data[key] = value

    def get(key):
        return data.get(key)

    store.save.side_effect = save
    store.get.side_effect = get
    store._data = data
    return store


@pytest.fixture
def notification_service(mock_store):
    """Create a NotificationService with mock state store."""
    return NotificationService(state_store=mock_store)


class TestReminderFlow:
    """Integration tests for the reminder → notification flow."""

    def test_reminder_event_triggers_notification(
        self, notification_service
    ):
        """A reminder event should create and deliver a notification."""
        import src.handlers.reminders as handler_module
        handler_module._service = notification_service

        event_data = {
            "reminder_id": "rem-1",
            "task_id": "task-1",
            "user_id": "user-1",
            "scheduled_time": datetime.now(timezone.utc).isoformat(),
            "status": "sent",
        }

        asyncio.get_event_loop().run_until_complete(
            handle_reminder(event_data)
        )

        # Verify notification was created
        # The handler creates a notification via the service
        assert notification_service.store.save.called

    def test_reminder_event_without_task_id_is_skipped(
        self, notification_service
    ):
        """A reminder event without task_id should be skipped."""
        import src.handlers.reminders as handler_module
        handler_module._service = notification_service

        event_data = {
            "reminder_id": "rem-2",
            "task_id": "",
            "user_id": "user-1",
        }

        asyncio.get_event_loop().run_until_complete(
            handle_reminder(event_data)
        )

        # No notification should be created
        notification_service.store.save.assert_not_called()

    def test_full_reminder_to_notification_flow(
        self, notification_service
    ):
        """Full flow: reminder event → NotificationService.deliver()."""
        import src.handlers.reminders as handler_module
        handler_module._service = notification_service

        event_data = {
            "reminder_id": "rem-3",
            "task_id": "task-3",
            "user_id": "user-3",
            "scheduled_time": datetime.now(timezone.utc).isoformat(),
            "status": "sent",
        }

        asyncio.get_event_loop().run_until_complete(
            handle_reminder(event_data)
        )

        # Check the saved notification data
        save_calls = notification_service.store.save.call_args_list
        assert len(save_calls) == 1
        saved_data = save_calls[0][0][1]  # second positional arg
        assert saved_data["reminder_id"] == "rem-3"
        assert saved_data["user_id"] == "user-3"
        assert saved_data["delivery_status"] == "delivered"
