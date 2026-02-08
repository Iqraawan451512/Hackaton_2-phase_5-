# [Task]: T040 — Recurring Task Service Dapr subscription handler
"""Handler for task.completed events from the task-events topic."""

from src.config import get_logger
from src.services.recurring_service import RecurringTaskService

logger = get_logger("task_events_handler")

_service: RecurringTaskService | None = None


def get_recurring_service() -> RecurringTaskService:
    """Get or create the RecurringTaskService singleton."""
    global _service
    if _service is None:
        _service = RecurringTaskService()
    return _service


async def handle_task_event(event_data: dict) -> None:
    """Process a task event — only acts on task.completed events
    where the task has a recurrence_pattern.

    Called by Dapr when a message arrives on the task-events topic.
    """
    event_type = event_data.get("event_type", "")

    # Only process completed events
    if event_type != "task.completed":
        logger.debug(
            "event_skipped",
            event_type=event_type,
            reason="not_completed_event",
        )
        return

    payload = event_data.get("payload", {})
    recurrence_pattern = payload.get("recurrence_pattern")

    if not recurrence_pattern:
        logger.debug(
            "event_skipped",
            event_type=event_type,
            reason="no_recurrence_pattern",
        )
        return

    task_id = payload.get("task_id", "")
    user_id = event_data.get("user_id", "")

    logger.info(
        "recurring_task_triggered",
        task_id=task_id,
        recurrence_pattern=recurrence_pattern,
    )

    service = get_recurring_service()
    await service.create_next_instance(
        task_id=task_id,
        recurrence_pattern=recurrence_pattern,
        user_id=user_id,
    )
