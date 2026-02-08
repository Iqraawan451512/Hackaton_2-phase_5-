# [Task]: T071 — Integration test: task update → task-updates → WebSocket → client
"""Integration test for the real-time sync flow."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.api.websocket import ConnectionManager
from src.events.task_updates_handler import handle_task_update


@pytest.fixture
def manager():
    """Create a fresh ConnectionManager."""
    return ConnectionManager()


@pytest.fixture
def mock_client():
    """Create a mock WebSocket client."""
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    return ws


class TestRealtimeSyncFlow:
    """Integration tests for the real-time sync pipeline."""

    @pytest.mark.asyncio
    async def test_task_update_relayed_to_websocket_client(
        self, manager, mock_client
    ):
        """A task-update event should be broadcast to connected clients."""
        import src.api.websocket as ws_module
        original_manager = ws_module.manager
        ws_module.manager = manager

        import src.events.task_updates_handler as handler_module
        # Reload to pick up new manager reference
        handler_module.manager = manager

        await manager.connect(mock_client)

        event_data = {
            "event_type": "task.created",
            "task_id": "task-1",
            "task": {
                "id": "task-1",
                "title": "Real-time test",
                "status": "pending",
            },
        }

        await handle_task_update(event_data)

        mock_client.send_text.assert_called_once()
        sent_data = json.loads(mock_client.send_text.call_args[0][0])
        assert sent_data["event_type"] == "task.created"
        assert sent_data["task_id"] == "task-1"

        # Restore
        ws_module.manager = original_manager

    @pytest.mark.asyncio
    async def test_multiple_clients_receive_update(
        self, manager
    ):
        """All connected clients should receive the broadcast."""
        import src.api.websocket as ws_module
        original_manager = ws_module.manager
        ws_module.manager = manager

        import src.events.task_updates_handler as handler_module
        handler_module.manager = manager

        client1 = AsyncMock()
        client1.accept = AsyncMock()
        client1.send_text = AsyncMock()
        client2 = AsyncMock()
        client2.accept = AsyncMock()
        client2.send_text = AsyncMock()

        await manager.connect(client1)
        await manager.connect(client2)

        await handle_task_update({
            "event_type": "task.updated",
            "task_id": "task-2",
            "task": {"id": "task-2", "title": "Updated"},
        })

        client1.send_text.assert_called_once()
        client2.send_text.assert_called_once()

        ws_module.manager = original_manager

    @pytest.mark.asyncio
    async def test_disconnected_client_does_not_block(
        self, manager
    ):
        """A disconnected client should be cleaned up without blocking."""
        import src.api.websocket as ws_module
        original_manager = ws_module.manager
        ws_module.manager = manager

        import src.events.task_updates_handler as handler_module
        handler_module.manager = manager

        good_client = AsyncMock()
        good_client.accept = AsyncMock()
        good_client.send_text = AsyncMock()
        bad_client = AsyncMock()
        bad_client.accept = AsyncMock()
        bad_client.send_text = AsyncMock(
            side_effect=Exception("Disconnected")
        )

        await manager.connect(good_client)
        await manager.connect(bad_client)

        await handle_task_update({
            "event_type": "task.deleted",
            "task_id": "task-3",
            "task": {"id": "task-3"},
        })

        good_client.send_text.assert_called_once()
        assert bad_client not in manager.active_connections

        ws_module.manager = original_manager
