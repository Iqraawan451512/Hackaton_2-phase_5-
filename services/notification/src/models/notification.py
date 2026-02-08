# [Task]: T017 — Notification model
"""Notification model for messages delivered to users."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class NotificationChannel(str, Enum):
    """Delivery channel for notifications."""
    PUSH = "push"
    EMAIL = "email"


class DeliveryStatus(str, Enum):
    """Delivery status of a notification."""
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"


class Notification(BaseModel):
    """A message delivered to a user via push or email."""
    notification_id: str = Field(
        default_factory=lambda: str(uuid.uuid4())
    )
    reminder_id: str
    user_id: str
    channel: NotificationChannel = Field(
        default=NotificationChannel.PUSH
    )
    delivery_status: DeliveryStatus = Field(
        default=DeliveryStatus.PENDING
    )
    message: str
    sent_at: Optional[datetime] = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
