# [Task]: T051 — Notification Service Dapr subscription to reminders topic
"""Handler for reminder events from the reminders topic."""

from src.config import get_logger
from src.services.notification_service import NotificationService

logger = get_logger("reminders_handler")

_service: NotificationService | None = None


def get_notification_service() -> NotificationService:
    """Get or create the NotificationService singleton."""
    global _service
    if _service is None:
        _service = NotificationService()
    return _service


async def handle_reminder(event_data: dict) -> None:
    """Process a reminder event from the reminders topic.

    Called by Dapr when a message arrives on the reminders topic.
    Delivers a push notification to the task owner.
    """
    reminder_id = event_data.get("reminder_id", "")
    task_id = event_data.get("task_id", "")
    user_id = event_data.get("user_id", "")

    if not reminder_id or not task_id:
        logger.warning(
            "invalid_reminder_event",
            reminder_id=reminder_id,
            task_id=task_id,
        )
        return

    message = f"Reminder: Your task {task_id} is due soon!"

    service = get_notification_service()
    service.deliver(
        reminder_id=reminder_id,
        task_id=task_id,
        user_id=user_id,
        message=message,
    )

    logger.info(
        "reminder_processed",
        reminder_id=reminder_id,
        task_id=task_id,
    )
