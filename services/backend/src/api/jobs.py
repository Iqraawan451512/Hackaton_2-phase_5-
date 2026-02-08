# [Task]: T048 — Dapr Jobs trigger callback endpoint
"""Jobs callback endpoint for handling Dapr Jobs firing."""

from fastapi import APIRouter, Request

from src.config import get_logger
from src.events.publisher import EventPublisher, TOPIC_REMINDERS
from src.services.reminder_scheduler import ReminderScheduler

logger = get_logger("jobs_api")

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

_scheduler: ReminderScheduler | None = None
_publisher: EventPublisher | None = None


def get_scheduler() -> ReminderScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = ReminderScheduler()
    return _scheduler


def get_publisher() -> EventPublisher:
    global _publisher
    if _publisher is None:
        _publisher = EventPublisher()
    return _publisher


@router.post("/trigger")
async def trigger_job(request: Request) -> dict:
    """Handle a Dapr Job firing.

    When a scheduled reminder fires, this endpoint:
    1. Marks the reminder as sent.
    2. Publishes a reminder event to the reminders topic.
    """
    body = await request.json()
    data = body.get("data", body)

    reminder_id = data.get("job_id", "")
    task_id = data.get("task_id", "")

    scheduler = get_scheduler()
    reminder = scheduler.mark_sent(reminder_id)

    if reminder is None:
        logger.warning(
            "reminder_not_found",
            reminder_id=reminder_id,
        )
        return {"status": "SKIPPED", "reason": "reminder_not_found"}

    publisher = get_publisher()
    publisher.publish(TOPIC_REMINDERS, {
        "reminder_id": reminder.reminder_id,
        "task_id": task_id,
        "scheduled_time": reminder.scheduled_time.isoformat(),
        "status": reminder.status.value,
    })

    logger.info(
        "reminder_triggered",
        reminder_id=reminder_id,
        task_id=task_id,
    )
    return {"status": "SUCCESS"}
