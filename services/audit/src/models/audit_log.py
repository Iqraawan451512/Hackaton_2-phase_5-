# [Task]: T018 — AuditLogEntry model
"""Audit log entry model for persisting task events."""

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class AuditLogEntry(BaseModel):
    """Persisted record consumed by the Audit Service from
    the task-events Kafka topic."""
    log_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_id: str
    event_type: str
    task_id: str
    payload: dict[str, Any]
    user_id: str
    event_timestamp: datetime
    received_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
