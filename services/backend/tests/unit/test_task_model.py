# [Task]: T024 — Unit tests for Task model validation rules
"""Tests for Task model validation."""

import pytest
from pydantic import ValidationError

from src.models.task import (
    Task,
    TaskCreate,
    TaskPriority,
    TaskStatus,
    RecurrencePattern,
)


class TestTaskModel:
    """Tests for the Task model."""

    def test_create_valid_task(self):
        task = Task(title="Buy groceries", created_by="user-1")
        assert task.title == "Buy groceries"
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.MEDIUM
        assert task.tags == []
        assert task.recurrence_pattern is None
        assert task.id is not None
        assert task.created_at is not None

    def test_title_required(self):
        with pytest.raises(ValidationError):
            Task(created_by="user-1")

    def test_title_not_empty(self):
        with pytest.raises(ValidationError):
            Task(title="", created_by="user-1")

    def test_title_not_whitespace(self):
        with pytest.raises(ValidationError):
            Task(title="   ", created_by="user-1")

    def test_title_max_length(self):
        with pytest.raises(ValidationError):
            Task(title="x" * 256, created_by="user-1")

    def test_valid_priorities(self):
        for p in TaskPriority:
            task = Task(title="Test", created_by="u", priority=p)
            assert task.priority == p

    def test_invalid_priority(self):
        with pytest.raises(ValidationError):
            Task(title="Test", created_by="u", priority="urgent")

    def test_valid_status(self):
        for s in TaskStatus:
            task = Task(title="Test", created_by="u", status=s)
            assert task.status == s

    def test_valid_recurrence(self):
        for r in RecurrencePattern:
            task = Task(
                title="Test", created_by="u",
                recurrence_pattern=r,
            )
            assert task.recurrence_pattern == r

    def test_tags_max_count(self):
        with pytest.raises(ValidationError):
            Task(
                title="Test", created_by="u",
                tags=["tag"] * 21,
            )

    def test_tag_max_length(self):
        with pytest.raises(ValidationError):
            Task(
                title="Test", created_by="u",
                tags=["x" * 51],
            )

    def test_tag_not_empty(self):
        with pytest.raises(ValidationError):
            Task(title="Test", created_by="u", tags=[""])

    def test_description_max_length(self):
        with pytest.raises(ValidationError):
            Task(
                title="Test", created_by="u",
                description="x" * 2001,
            )


class TestTaskCreate:
    """Tests for the TaskCreate request schema."""

    def test_minimal_create(self):
        tc = TaskCreate(title="New task")
        assert tc.title == "New task"
        assert tc.priority == TaskPriority.MEDIUM
        assert tc.tags == []

    def test_full_create(self):
        tc = TaskCreate(
            title="Full task",
            description="A description",
            priority=TaskPriority.HIGH,
            tags=["work", "urgent"],
            recurrence_pattern=RecurrencePattern.DAILY,
        )
        assert tc.recurrence_pattern == RecurrencePattern.DAILY
        assert len(tc.tags) == 2
