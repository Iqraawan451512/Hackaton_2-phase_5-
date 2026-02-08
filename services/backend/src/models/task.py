# [Task]: T014 — Task model with all fields and validation rules
"""Task model for the Todo Chatbot Backend Service."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class TaskStatus(str, Enum):
    """Valid task statuses."""
    PENDING = "pending"
    COMPLETED = "completed"
    DELETED = "deleted"


class TaskPriority(str, Enum):
    """Valid task priorities."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RecurrencePattern(str, Enum):
    """Valid recurrence patterns."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class Task(BaseModel):
    """Primary entity representing a user's to-do item."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)
    due_date: Optional[datetime] = None
    tags: list[str] = Field(default_factory=list)
    recurrence_pattern: Optional[RecurrencePattern] = None
    recurrence_parent_id: Optional[str] = None
    created_by: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator("title")
    @classmethod
    def title_not_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Title must not be empty or whitespace-only")
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        if len(v) > 20:
            raise ValueError("Maximum 20 tags per task")
        for tag in v:
            if not tag or not tag.strip():
                raise ValueError("Tag must be a non-empty string")
            if len(tag) > 50:
                raise ValueError("Tag must be at most 50 characters")
        return v


class TaskCreate(BaseModel):
    """Request schema for creating a task."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)
    due_date: Optional[datetime] = None
    tags: list[str] = Field(default_factory=list)
    recurrence_pattern: Optional[RecurrencePattern] = None

    @field_validator("title")
    @classmethod
    def title_not_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Title must not be empty or whitespace-only")
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        if len(v) > 20:
            raise ValueError("Maximum 20 tags per task")
        for tag in v:
            if not tag or not tag.strip():
                raise ValueError("Tag must be a non-empty string")
            if len(tag) > 50:
                raise ValueError("Tag must be at most 50 characters")
        return v


class TaskUpdate(BaseModel):
    """Request schema for updating a task."""
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None
    tags: Optional[list[str]] = None

    @field_validator("title")
    @classmethod
    def title_not_whitespace(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Title must not be empty or whitespace-only")
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is None:
            return v
        if len(v) > 20:
            raise ValueError("Maximum 20 tags per task")
        for tag in v:
            if not tag or not tag.strip():
                raise ValueError("Tag must be a non-empty string")
            if len(tag) > 50:
                raise ValueError("Tag must be at most 50 characters")
        return v
