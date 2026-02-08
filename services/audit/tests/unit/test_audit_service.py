# [Task]: T038 — Unit tests for AuditLogService
"""Tests for AuditLogService with mocked state store."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from src.models.audit_log import AuditLogEntry
from src.services.audit_service import (
    AuditLogService,
    _audit_key,
    _event_index_key,
)


@pytest.fixture
def mock_store():
    """Create a mock StateStore backed by a dict."""
    store = MagicMock()
    data = {}

    def save(key, value):
        data[key] = value

    def get(key):
        return data.get(key)

    store.save.side_effect = save
    store.get.side_effect = get
    store._data = data
    return store


@pytest.fixture
def service(mock_store):
    """Create an AuditLogService with mock state store."""
    return AuditLogService(state_store=mock_store)


class TestPersistEvent:
    """Tests for AuditLogService.persist_event()."""

    def test_persist_creates_entry(self, service):
        now = datetime.now(timezone.utc)
        entry = service.persist_event(
            event_id="evt-1",
            event_type="task.created",
            task_id="task-1",
            payload={"task": {"title": "Test"}},
            user_id="user-1",
            event_timestamp=now,
        )

        assert entry.event_id == "evt-1"
        assert entry.event_type == "task.created"
        assert entry.task_id == "task-1"
        assert entry.user_id == "user-1"
        assert entry.log_id is not None

    def test_persist_saves_to_store(self, service, mock_store):
        now = datetime.now(timezone.utc)
        entry = service.persist_event(
            event_id="evt-2",
            event_type="task.updated",
            task_id="task-2",
            payload={"changes": {}},
            user_id="user-1",
            event_timestamp=now,
        )

        mock_store.save.assert_any_call(
            _audit_key(entry.log_id),
            entry.model_dump(mode="json"),
        )

    def test_persist_creates_event_index(self, service, mock_store):
        now = datetime.now(timezone.utc)
        entry = service.persist_event(
            event_id="evt-3",
            event_type="task.deleted",
            task_id="task-3",
            payload={},
            user_id="user-1",
            event_timestamp=now,
        )

        mock_store.save.assert_any_call(
            _event_index_key("evt-3"),
            {"log_id": entry.log_id},
        )


class TestGetByLogId:
    """Tests for AuditLogService.get_by_log_id()."""

    def test_get_existing(self, service):
        now = datetime.now(timezone.utc)
        entry = service.persist_event(
            event_id="evt-4",
            event_type="task.completed",
            task_id="task-4",
            payload={},
            user_id="user-1",
            event_timestamp=now,
        )
        result = service.get_by_log_id(entry.log_id)

        assert result is not None
        assert result.log_id == entry.log_id

    def test_get_nonexistent(self, service):
        result = service.get_by_log_id("nonexistent")
        assert result is None


class TestIsDuplicate:
    """Tests for AuditLogService.is_duplicate()."""

    def test_not_duplicate(self, service):
        assert service.is_duplicate("new-event") is False

    def test_is_duplicate_after_persist(self, service):
        now = datetime.now(timezone.utc)
        service.persist_event(
            event_id="dup-evt",
            event_type="task.created",
            task_id="task-5",
            payload={},
            user_id="user-1",
            event_timestamp=now,
        )
        assert service.is_duplicate("dup-evt") is True
