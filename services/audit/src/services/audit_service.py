# [Task]: T034 — AuditLogService to persist audit log entries
"""Audit log service for persisting task events."""

from datetime import datetime, timezone
from typing import Optional

from src.config import StateStore, get_logger
from src.models.audit_log import AuditLogEntry

logger = get_logger("audit_service")

KEY_PREFIX = "audit-log"


def _audit_key(log_id: str) -> str:
    return f"{KEY_PREFIX}||{log_id}"


def _event_index_key(event_id: str) -> str:
    return f"audit-event||{event_id}"


class AuditLogService:
    """Persists AuditLogEntry records to Dapr state store."""

    def __init__(self, state_store: Optional[StateStore] = None):
        self.store = state_store or StateStore()

    def persist_event(
        self,
        event_id: str,
        event_type: str,
        task_id: str,
        payload: dict,
        user_id: str,
        event_timestamp: datetime,
    ) -> AuditLogEntry:
        """Create and persist an audit log entry from a task event."""
        entry = AuditLogEntry(
            event_id=event_id,
            event_type=event_type,
            task_id=task_id,
            payload=payload,
            user_id=user_id,
            event_timestamp=event_timestamp,
        )
        self.store.save(
            _audit_key(entry.log_id),
            entry.model_dump(mode="json"),
        )
        # Index by event_id for deduplication lookups
        self.store.save(
            _event_index_key(event_id),
            {"log_id": entry.log_id},
        )

        logger.info(
            "audit_log_persisted",
            log_id=entry.log_id,
            event_id=event_id,
            event_type=event_type,
            task_id=task_id,
        )
        return entry

    def get_by_log_id(self, log_id: str) -> Optional[AuditLogEntry]:
        """Retrieve an audit log entry by its log ID."""
        data = self.store.get(_audit_key(log_id))
        if data is None:
            return None
        return AuditLogEntry(**data)

    def is_duplicate(self, event_id: str) -> bool:
        """Check if an event has already been processed (idempotency)."""
        return self.store.get(_event_index_key(event_id)) is not None
