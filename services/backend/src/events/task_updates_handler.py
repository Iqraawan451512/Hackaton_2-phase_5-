# [Task]: T066 — Dapr subscription handler for task-updates topic
"""Handler for task-updates Pub/Sub — relays events to WebSocket clients."""

import asyncio

from src.api.websocket import manager
from src.config import get_logger

logger = get_logger("task_updates_handler")


async def handle_task_update(event_data: dict) -> None:
    """Relay a task-update event to all connected WebSocket clients.

    Called by Dapr when a message arrives on the task-updates topic.
    """
    logger.info(
        "task_update_received",
        event_type=event_data.get("event_type", "unknown"),
        task_id=event_data.get("task_id", "unknown"),
    )
    await manager.broadcast(event_data)
