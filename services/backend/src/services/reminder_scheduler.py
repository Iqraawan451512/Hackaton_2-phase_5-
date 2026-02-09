# [Task]: T047, T050 — ReminderScheduler: schedule/cancel reminders via Dapr Jobs
"""Reminder scheduler for task due-date notifications."""

import json
from datetime import datetime, timedelta, timezone

from src.config import STANDALONE_MODE, StateStore, get_logger

if not STANDALONE_MODE:
    from dapr.clients import DaprClient
from src.models.reminder import Reminder, ReminderStatus

logger = get_logger("reminder_scheduler")

KEY_PREFIX = "reminder"
REMINDER_OFFSET_MINUTES = 30  # Notify 30 min before due


def _reminder_key(reminder_id: str) -> str:
    return f"{KEY_PREFIX}||{reminder_id}"


def _task_reminder_key(task_id: str) -> str:
    return f"task-reminder||{task_id}"


class ReminderScheduler:
    """Schedules and cancels Dapr Jobs for task reminders."""

    def __init__(self, state_store: StateStore | None = None):
        self.store = state_store or StateStore()

    def schedule(self, task_id: str, due_date: datetime) -> Reminder:
        """Schedule a reminder for a task's due date.

        Fires REMINDER_OFFSET_MINUTES before the due date.
        If a reminder already exists for this task, it is rescheduled.
        """
        # Cancel existing reminder if any
        self.cancel(task_id)

        scheduled_time = due_date - timedelta(
            minutes=REMINDER_OFFSET_MINUTES
        )
        reminder = Reminder(
            task_id=task_id,
            scheduled_time=scheduled_time,
        )

        # Persist reminder
        self.store.save(
            _reminder_key(reminder.reminder_id),
            reminder.model_dump(mode="json"),
        )
        # Index by task_id for lookup/cancellation
        self.store.save(
            _task_reminder_key(task_id),
            {"reminder_id": reminder.reminder_id},
        )

        # Schedule Dapr Job
        self._schedule_dapr_job(reminder)

        logger.info(
            "reminder_scheduled",
            reminder_id=reminder.reminder_id,
            task_id=task_id,
            scheduled_time=scheduled_time.isoformat(),
        )
        return reminder

    def cancel(self, task_id: str) -> bool:
        """Cancel a pending reminder for a task.

        Returns True if a reminder was cancelled, False if none existed.
        """
        index = self.store.get(_task_reminder_key(task_id))
        if index is None:
            return False

        reminder_id = index["reminder_id"]
        data = self.store.get(_reminder_key(reminder_id))
        if data is None:
            return False

        reminder = Reminder(**data)
        if reminder.status != ReminderStatus.PENDING:
            return False

        reminder.status = ReminderStatus.CANCELLED
        self.store.save(
            _reminder_key(reminder.reminder_id),
            reminder.model_dump(mode="json"),
        )

        # Cancel Dapr Job
        self._cancel_dapr_job(reminder.reminder_id)

        logger.info(
            "reminder_cancelled",
            reminder_id=reminder.reminder_id,
            task_id=task_id,
        )
        return True

    def get_reminder_for_task(
        self, task_id: str
    ) -> Reminder | None:
        """Get the current reminder for a task, if any."""
        index = self.store.get(_task_reminder_key(task_id))
        if index is None:
            return None
        data = self.store.get(_reminder_key(index["reminder_id"]))
        if data is None:
            return None
        return Reminder(**data)

    def mark_sent(self, reminder_id: str) -> Reminder | None:
        """Mark a reminder as sent after the job fires."""
        data = self.store.get(_reminder_key(reminder_id))
        if data is None:
            return None
        reminder = Reminder(**data)
        reminder.status = ReminderStatus.SENT
        self.store.save(
            _reminder_key(reminder.reminder_id),
            reminder.model_dump(mode="json"),
        )
        return reminder

    def _schedule_dapr_job(self, reminder: Reminder) -> None:
        """Schedule a Dapr Job to fire at the reminder's scheduled_time."""
        with DaprClient() as client:
            # Use Dapr Jobs API (schedule binding)
            client.invoke_binding(
                binding_name="jobs",
                operation="create",
                data=json.dumps({
                    "job_id": reminder.reminder_id,
                    "task_id": reminder.task_id,
                    "scheduled_time": reminder.scheduled_time.isoformat(),
                }),
                binding_metadata={
                    "schedule": reminder.scheduled_time.isoformat(),
                },
            )

    def _cancel_dapr_job(self, reminder_id: str) -> None:
        """Cancel a scheduled Dapr Job."""
        with DaprClient() as client:
            client.invoke_binding(
                binding_name="jobs",
                operation="delete",
                data=json.dumps({"job_id": reminder_id}),
            )
