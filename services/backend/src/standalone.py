"""Standalone in-memory adapters for deployment without Dapr.

Used when STANDALONE_MODE=true (e.g., Hugging Face Spaces).
Replaces Dapr StateStore, EventPublisher, and ReminderScheduler
with in-memory implementations that have the same interface.
"""

import json
from typing import Any, Optional

from src.config import get_logger

logger = get_logger("standalone")


class MemoryStateStore:
    """In-memory state store — same interface as Dapr StateStore."""

    def __init__(self) -> None:
        self._data: dict[str, str] = {}

    def save(self, key: str, value: Any) -> None:
        self._data[key] = json.dumps(value)

    def get(self, key: str) -> Optional[dict]:
        raw = self._data.get(key)
        if raw:
            return json.loads(raw)
        return None

    def delete(self, key: str) -> None:
        self._data.pop(key, None)

    def bulk_get(self, keys: list[str]) -> dict[str, Any]:
        result = {}
        for key in keys:
            raw = self._data.get(key)
            if raw:
                result[key] = json.loads(raw)
        return result


class MemoryEventPublisher:
    """In-memory event publisher — logs events instead of Kafka."""

    def publish(self, topic: str, data: dict[str, Any]) -> None:
        logger.info(
            "event_published_memory",
            topic=topic,
            event_type=data.get("event_type", "unknown"),
        )

    def publish_task_event(self, event: Any) -> None:
        self.publish("task-events", event.model_dump(mode="json"))

    def publish_task_update(
        self, event_type: str, task_id: str, task_data: dict[str, Any]
    ) -> None:
        self.publish("task-updates", {
            "event_type": event_type,
            "task_id": task_id,
            "task": task_data,
        })


class MemoryReminderScheduler:
    """In-memory reminder scheduler — no Dapr Jobs dependency."""

    def __init__(self, state_store: Optional[MemoryStateStore] = None):
        self.store = state_store or MemoryStateStore()

    def schedule(self, task_id: str, due_date: Any) -> None:
        logger.info("reminder_scheduled_memory", task_id=task_id)

    def cancel(self, task_id: str) -> bool:
        logger.info("reminder_cancelled_memory", task_id=task_id)
        return True

    def get_reminder_for_task(self, task_id: str) -> None:
        return None

    def mark_sent(self, reminder_id: str) -> None:
        return None
