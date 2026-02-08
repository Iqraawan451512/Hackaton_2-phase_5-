# [Task]: T015 — TaskEvent model per contracts/task-events.json schema
"""Task event model for publishing to the task-events Kafka topic."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class TaskEventType(str, Enum):
    """Valid task event types."""
    CREATED = "task.created"
    UPDATED = "task.updated"
    COMPLETED = "task.completed"
    DELETED = "task.deleted"


class TaskEvent(BaseModel):
    """Immutable event record for task lifecycle actions.

    Published to task-events Kafka topic via Dapr Pub/Sub.
    Consumed by Audit Service and Recurring Task Service.
    """
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: TaskEventType
    task_id: str
    payload: dict[str, Any]
    user_id: str
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class TaskCreatedPayload(BaseModel):
    """Payload for task.created events."""
    task: dict[str, Any]


class TaskUpdatedPayload(BaseModel):
    """Payload for task.updated events."""
    task_id: str
    changes: dict[str, dict[str, Any]]


class TaskCompletedPayload(BaseModel):
    """Payload for task.completed events."""
    task_id: str
    completed_at: datetime
    recurrence_pattern: Optional[str] = None


class TaskDeletedPayload(BaseModel):
    """Payload for task.deleted events."""
    task_id: str
    deleted_at: datetime
