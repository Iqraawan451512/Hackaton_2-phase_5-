# [Task]: T070 — Unit tests for WebSocket relay logic
"""Tests for the WebSocket ConnectionManager."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.api.websocket import ConnectionManager


@pytest.fixture
def manager():
    return ConnectionManager()


@pytest.fixture
def mock_websocket():
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    return ws


class TestConnectionManager:
    """Tests for the ConnectionManager class."""

    @pytest.mark.asyncio
    async def test_connect_adds_client(self, manager, mock_websocket):
        await manager.connect(mock_websocket)
        assert mock_websocket in manager.active_connections
        assert len(manager.active_connections) == 1

    @pytest.mark.asyncio
    async def test_connect_calls_accept(self, manager, mock_websocket):
        await manager.connect(mock_websocket)
        mock_websocket.accept.assert_called_once()

    def test_disconnect_removes_client(self, manager, mock_websocket):
        manager.active_connections.append(mock_websocket)
        manager.disconnect(mock_websocket)
        assert mock_websocket not in manager.active_connections

    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all(self, manager):
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        manager.active_connections = [ws1, ws2]

        await manager.broadcast({"event": "test"})

        ws1.send_text.assert_called_once()
        ws2.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_removes_stale_connections(self, manager):
        ws_good = AsyncMock()
        ws_bad = AsyncMock()
        ws_bad.send_text.side_effect = Exception("Connection lost")
        manager.active_connections = [ws_good, ws_bad]

        await manager.broadcast({"event": "test"})

        assert ws_good in manager.active_connections
        assert ws_bad not in manager.active_connections

    @pytest.mark.asyncio
    async def test_broadcast_empty_connections(self, manager):
        # Should not raise
        await manager.broadcast({"event": "test"})

    @pytest.mark.asyncio
    async def test_multiple_connect_disconnect(self, manager):
        ws1 = AsyncMock()
        ws2 = AsyncMock()

        await manager.connect(ws1)
        await manager.connect(ws2)
        assert len(manager.active_connections) == 2

        manager.disconnect(ws1)
        assert len(manager.active_connections) == 1
        assert ws2 in manager.active_connections
