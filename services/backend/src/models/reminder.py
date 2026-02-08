# [Task]: T016 — Reminder model
"""Reminder model for scheduling task due-date notifications."""

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class ReminderStatus(str, Enum):
    """Valid reminder statuses."""
    PENDING = "pending"
    SENT = "sent"
    CANCELLED = "cancelled"


class Reminder(BaseModel):
    """Scheduled notification trigger managed via Dapr Jobs API."""
    reminder_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    scheduled_time: datetime
    status: ReminderStatus = Field(default=ReminderStatus.PENDING)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
