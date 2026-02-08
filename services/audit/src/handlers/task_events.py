# [Task]: T033 — Audit Service Dapr subscription to task-events topic
"""Handler for task-events Pub/Sub subscription."""

from datetime import datetime, timezone

from src.config import get_logger
from src.services.audit_service import AuditLogService

logger = get_logger("task_events_handler")

_service: AuditLogService | None = None


def get_audit_service() -> AuditLogService:
    """Get or create the AuditLogService singleton."""
    global _service
    if _service is None:
        _service = AuditLogService()
    return _service


async def handle_task_event(event_data: dict) -> None:
    """Process a task event from the task-events topic.

    Called by Dapr when a message arrives on the task-events topic.
    Persists the event as an AuditLogEntry.
    """
    service = get_audit_service()

    event_id = event_data.get("event_id", "")
    event_type = event_data.get("event_type", "")
    task_id = event_data.get("task_id", "")
    payload = event_data.get("payload", {})
    user_id = event_data.get("user_id", "")
    timestamp_str = event_data.get("timestamp")

    # Idempotency check: skip duplicate events
    if service.is_duplicate(event_id):
        logger.info(
            "duplicate_event_skipped",
            event_id=event_id,
            event_type=event_type,
        )
        return

    event_timestamp = (
        datetime.fromisoformat(timestamp_str)
        if timestamp_str
        else datetime.now(timezone.utc)
    )

    service.persist_event(
        event_id=event_id,
        event_type=event_type,
        task_id=task_id,
        payload=payload,
        user_id=user_id,
        event_timestamp=event_timestamp,
    )

    logger.info(
        "task_event_processed",
        event_id=event_id,
        event_type=event_type,
        task_id=task_id,
    )
