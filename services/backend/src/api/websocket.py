# [Task]: T065 — WebSocket endpoint for real-time client sync
"""WebSocket endpoint for broadcasting task updates to connected clients."""

import asyncio
import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.config import get_logger

logger = get_logger("websocket")

router = APIRouter()


class ConnectionManager:
    """Manages active WebSocket connections and broadcasts messages."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(
            "client_connected",
            total_connections=len(self.active_connections),
        )

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.remove(websocket)
        logger.info(
            "client_disconnected",
            total_connections=len(self.active_connections),
        )

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Send a message to all connected clients."""
        disconnected = []
        data = json.dumps(message)
        for connection in self.active_connections:
            try:
                await connection.send_text(data)
            except Exception:
                disconnected.append(connection)

        for conn in disconnected:
            self.active_connections.remove(conn)

        if disconnected:
            logger.info(
                "stale_connections_removed",
                count=len(disconnected),
            )


# Singleton connection manager
manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time task updates.

    Clients connect here to receive broadcast task-update events.
    The connection stays open until the client disconnects.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive; wait for client messages (e.g., ping)
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
