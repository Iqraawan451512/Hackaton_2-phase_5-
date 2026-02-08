# [Task]: T055 — Unit tests for NotificationService
"""Tests for NotificationService with mocked state store."""

from unittest.mock import MagicMock

import pytest

from src.models.notification import (
    DeliveryStatus,
    NotificationChannel,
)
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
def service(mock_store):
    """Create a NotificationService with mock state store."""
    return NotificationService(state_store=mock_store)


class TestDeliver:
    """Tests for NotificationService.deliver()."""

    def test_deliver_creates_notification(self, service):
        n = service.deliver(
            reminder_id="rem-1",
            task_id="task-1",
            user_id="user-1",
            message="Your task is due!",
        )

        assert n.reminder_id == "rem-1"
        assert n.user_id == "user-1"
        assert n.message == "Your task is due!"
        assert n.delivery_status == DeliveryStatus.DELIVERED
        assert n.sent_at is not None

    def test_deliver_default_channel_is_push(self, service):
        n = service.deliver(
            reminder_id="rem-2",
            task_id="task-2",
            user_id="user-1",
            message="Due soon",
        )
        assert n.channel == NotificationChannel.PUSH

    def test_deliver_email_channel(self, service):
        n = service.deliver(
            reminder_id="rem-3",
            task_id="task-3",
            user_id="user-1",
            message="Due soon",
            channel=NotificationChannel.EMAIL,
        )
        assert n.channel == NotificationChannel.EMAIL

    def test_deliver_persists_to_store(self, service, mock_store):
        service.deliver(
            reminder_id="rem-4",
            task_id="task-4",
            user_id="user-1",
            message="Due soon",
        )
        mock_store.save.assert_called_once()


class TestGet:
    """Tests for NotificationService.get()."""

    def test_get_existing(self, service):
        n = service.deliver(
            reminder_id="rem-5",
            task_id="task-5",
            user_id="user-1",
            message="Due!",
        )
        result = service.get(n.notification_id)

        assert result is not None
        assert result.notification_id == n.notification_id

    def test_get_nonexistent(self, service):
        result = service.get("nonexistent")
        assert result is None
