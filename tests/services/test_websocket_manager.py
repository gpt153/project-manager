"""
Tests for WebSocket manager.
"""

from unittest.mock import AsyncMock

import pytest

from src.services.websocket_manager import WebSocketManager


@pytest.mark.asyncio
async def test_websocket_manager_connect():
    """Test WebSocket connection."""
    manager = WebSocketManager()
    mock_websocket = AsyncMock()

    await manager.connect("test-1", mock_websocket)

    assert manager.get_connection_count() == 1
    mock_websocket.accept.assert_called_once()


@pytest.mark.asyncio
async def test_websocket_manager_disconnect():
    """Test WebSocket disconnection."""
    manager = WebSocketManager()
    mock_websocket = AsyncMock()

    await manager.connect("test-1", mock_websocket)
    await manager.disconnect("test-1")

    assert manager.get_connection_count() == 0


@pytest.mark.asyncio
async def test_websocket_manager_send_message():
    """Test sending a personal message."""
    manager = WebSocketManager()
    mock_websocket = AsyncMock()

    await manager.connect("test-1", mock_websocket)
    result = await manager.send_personal_message({"type": "test", "data": "hello"}, "test-1")

    assert result is True
    mock_websocket.send_text.assert_called_once()


@pytest.mark.asyncio
async def test_websocket_manager_broadcast():
    """Test broadcasting to multiple connections."""
    manager = WebSocketManager()
    mock_ws1 = AsyncMock()
    mock_ws2 = AsyncMock()

    await manager.connect("test-1", mock_ws1)
    await manager.connect("test-2", mock_ws2)

    sent_count = await manager.broadcast({"type": "test", "data": "hello"})

    assert sent_count == 2
    mock_ws1.send_text.assert_called_once()
    mock_ws2.send_text.assert_called_once()
