# [Task]: T052, T053 — NotificationService with push delivery and logging
"""Notification service for delivering reminder notifications."""

from datetime import datetime, timezone
from typing import Optional

from src.config import StateStore, get_logger
from src.models.notification import (
    DeliveryStatus,
    Notification,
    NotificationChannel,
)

logger = get_logger("notification_service")

KEY_PREFIX = "notification"


def _notification_key(notification_id: str) -> str:
    return f"{KEY_PREFIX}||{notification_id}"


class NotificationService:
    """Delivers notifications to users when reminders fire."""

    def __init__(self, state_store: Optional[StateStore] = None):
        self.store = state_store or StateStore()

    def deliver(
        self,
        reminder_id: str,
        task_id: str,
        user_id: str,
        message: str,
        channel: NotificationChannel = NotificationChannel.PUSH,
    ) -> Notification:
        """Create and deliver a notification to a user.

        In this implementation, 'delivery' persists the notification
        record to state store and logs the action. A real implementation
        would integrate with push notification services.
        """
        notification = Notification(
            reminder_id=reminder_id,
            user_id=user_id,
            channel=channel,
            message=message,
            delivery_status=DeliveryStatus.DELIVERED,
            sent_at=datetime.now(timezone.utc),
        )

        self.store.save(
            _notification_key(notification.notification_id),
            notification.model_dump(mode="json"),
        )

        logger.info(
            "notification_delivered",
            notification_id=notification.notification_id,
            reminder_id=reminder_id,
            task_id=task_id,
            user_id=user_id,
            channel=channel.value,
        )
        return notification

    def get(self, notification_id: str) -> Optional[Notification]:
        """Retrieve a notification by ID."""
        data = self.store.get(_notification_key(notification_id))
        if data is None:
            return None
        return Notification(**data)
