"""
WebSocket connection manager for tracking active sessions and broadcasting.
"""
import json
import logging
from datetime import datetime
from typing import Dict, Optional

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections for real-time chat communication.

    Attributes:
        active_connections: Dictionary mapping connection_id to WebSocket instances
    """

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, connection_id: str, websocket: WebSocket) -> None:
        """
        Register a new WebSocket connection.

        Args:
            connection_id: Unique identifier for the connection
            websocket: WebSocket instance
        """
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        logger.info(f"WebSocket connected: {connection_id} (total: {len(self.active_connections)})")

    async def disconnect(self, connection_id: str) -> None:
        """
        Remove a WebSocket connection.

        Args:
            connection_id: Connection identifier to remove
        """
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            logger.info(f"WebSocket disconnected: {connection_id} (total: {len(self.active_connections)})")

    async def send_personal_message(self, message: dict, connection_id: str) -> bool:
        """
        Send a message to a specific connection.

        Args:
            message: Message dictionary to send
            connection_id: Target connection identifier

        Returns:
            True if message was sent successfully, False otherwise
        """
        websocket = self.active_connections.get(connection_id)
        if not websocket:
            logger.warning(f"Connection {connection_id} not found")
            return False

        try:
            # Add timestamp if not present
            if "timestamp" not in message:
                message["timestamp"] = datetime.utcnow().isoformat()

            await websocket.send_text(json.dumps(message))
            logger.debug(f"Sent message to {connection_id}: {message.get('type')}")
            return True
        except Exception as e:
            logger.error(f"Error sending message to {connection_id}: {e}")
            # Remove dead connection
            await self.disconnect(connection_id)
            return False

    async def broadcast(self, message: dict, exclude: Optional[str] = None) -> int:
        """
        Broadcast a message to all connected clients.

        Args:
            message: Message dictionary to broadcast
            exclude: Optional connection_id to exclude from broadcast

        Returns:
            Number of clients that received the message
        """
        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()

        sent_count = 0
        dead_connections = []

        for connection_id, websocket in self.active_connections.items():
            if connection_id == exclude:
                continue

            try:
                await websocket.send_text(json.dumps(message))
                sent_count += 1
            except Exception as e:
                logger.error(f"Error broadcasting to {connection_id}: {e}")
                dead_connections.append(connection_id)

        # Clean up dead connections
        for conn_id in dead_connections:
            await self.disconnect(conn_id)

        if sent_count > 0:
            logger.debug(f"Broadcasted message to {sent_count} clients")

        return sent_count

    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)

    async def send_status_update(self, connection_id: str, status: str, message: Optional[str] = None) -> bool:
        """
        Send a status update to a connection.

        Args:
            connection_id: Target connection identifier
            status: Status string ('connected', 'disconnected', 'reconnecting')
            message: Optional status message

        Returns:
            True if message was sent successfully
        """
        status_message = {
            "type": "status",
            "data": {
                "status": status,
                "message": message,
            }
        }
        return await self.send_personal_message(status_message, connection_id)

    async def send_error(self, connection_id: str, code: str, message: str) -> bool:
        """
        Send an error message to a connection.

        Args:
            connection_id: Target connection identifier
            code: Error code
            message: Error message

        Returns:
            True if message was sent successfully
        """
        error_message = {
            "type": "error",
            "data": {
                "code": code,
                "message": message,
            }
        }
        return await self.send_personal_message(error_message, connection_id)


# Global WebSocket manager instance
ws_manager = WebSocketManager()
