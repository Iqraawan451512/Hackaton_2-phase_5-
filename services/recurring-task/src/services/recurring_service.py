# [Task]: T041, T044 — RecurringTaskService with date computation and logging
"""Recurring task service: computes next due date and creates next task instance."""

import json
from datetime import datetime, timedelta, timezone

from dapr.clients import DaprClient

from src.config import BACKEND_APP_ID, get_logger

logger = get_logger("recurring_service")


def compute_next_due_date(
    recurrence_pattern: str,
    from_date: datetime | None = None,
) -> datetime:
    """Compute the next due date based on recurrence pattern.

    Args:
        recurrence_pattern: One of 'daily', 'weekly', 'monthly'.
        from_date: Base date to compute from (defaults to now UTC).

    Returns:
        The next due date as a UTC datetime.
    """
    base = from_date or datetime.now(timezone.utc)

    if recurrence_pattern == "daily":
        return base + timedelta(days=1)
    elif recurrence_pattern == "weekly":
        return base + timedelta(weeks=1)
    elif recurrence_pattern == "monthly":
        # Add roughly 30 days; handle month boundaries
        month = base.month + 1
        year = base.year
        if month > 12:
            month = 1
            year += 1
        day = min(base.day, 28)  # Safe for all months
        return base.replace(year=year, month=month, day=day)
    else:
        raise ValueError(
            f"Unknown recurrence pattern: {recurrence_pattern}"
        )


class RecurringTaskService:
    """Creates next task instances for recurring tasks via Dapr Service Invocation."""

    async def create_next_instance(
        self,
        task_id: str,
        recurrence_pattern: str,
        user_id: str,
    ) -> dict | None:
        """Create the next instance of a recurring task.

        1. Fetch the original task from Backend Service.
        2. Compute the next due date.
        3. Create a new task via Backend Service with the
           recurrence_parent_id pointing to the original.
        """
        # Fetch the original task via Dapr Service Invocation
        original_task = await self._get_task(task_id)
        if original_task is None:
            logger.warning(
                "original_task_not_found",
                task_id=task_id,
            )
            return None

        next_due = compute_next_due_date(
            recurrence_pattern,
            from_date=datetime.now(timezone.utc),
        )

        new_task_data = {
            "title": original_task.get("title", "Recurring task"),
            "description": original_task.get("description"),
            "priority": original_task.get("priority", "medium"),
            "tags": original_task.get("tags", []),
            "recurrence_pattern": recurrence_pattern,
            "due_date": next_due.isoformat(),
        }

        created = await self._create_task(new_task_data, user_id)

        logger.info(
            "recurring_task_created",
            original_task_id=task_id,
            new_task_id=created.get("id") if created else None,
            recurrence_pattern=recurrence_pattern,
            next_due=next_due.isoformat(),
        )
        return created

    async def _get_task(self, task_id: str) -> dict | None:
        """Fetch a task from the Backend Service via Dapr."""
        with DaprClient() as client:
            resp = client.invoke_method(
                app_id=BACKEND_APP_ID,
                method_name=f"api/tasks/{task_id}",
                http_verb="GET",
            )
            if resp.status_code == 200:
                return json.loads(resp.data)
            return None

    async def _create_task(
        self, task_data: dict, user_id: str
    ) -> dict | None:
        """Create a task via the Backend Service using Dapr."""
        with DaprClient() as client:
            resp = client.invoke_method(
                app_id=BACKEND_APP_ID,
                method_name="api/tasks",
                http_verb="POST",
                data=json.dumps(task_data),
                content_type="application/json",
                http_querystring={"user_id": user_id},
            )
            if resp.status_code in (200, 201):
                return json.loads(resp.data)
            logger.error(
                "task_creation_failed",
                status_code=resp.status_code,
            )
            return None
