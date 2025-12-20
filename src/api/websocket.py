"""
WebSocket endpoint for bidirectional chat communication.
"""
import logging
import json
from uuid import UUID, uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import async_session_maker
from src.services.websocket_manager import ws_manager
from src.services.project_service import add_message

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/chat/{project_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    project_id: UUID
):
    """
    WebSocket endpoint for real-time chat communication.

    This endpoint handles bidirectional communication between the user and
    the Project Orchestrator agent.

    Args:
        websocket: WebSocket connection
        project_id: Project UUID for the conversation

    Protocol:
        Client -> Server: {"content": "user message"}
        Server -> Client: {"type": "chat", "data": {"id": "...", "role": "assistant", "content": "...", "timestamp": "..."}}
        Server -> Client: {"type": "status", "data": {"status": "connected|disconnected", "message": "..."}}
        Server -> Client: {"type": "error", "data": {"code": "...", "message": "..."}}
    """
    connection_id = str(uuid4())

    try:
        # Accept the WebSocket connection
        await ws_manager.connect(connection_id, websocket)

        # Send connection confirmation
        await ws_manager.send_status_update(connection_id, "connected", "Connected to Project Orchestrator")

        # Listen for messages
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            logger.debug(f"Received message on connection {connection_id}: {data[:100]}")

            try:
                message_data = json.loads(data)
                user_content = message_data.get("content", "").strip()

                if not user_content:
                    await ws_manager.send_error(connection_id, "EMPTY_MESSAGE", "Message content cannot be empty")
                    continue

                # Store user message in database
                async with async_session_maker() as session:
                    try:
                        user_msg = await add_message(
                            session,
                            project_id=project_id,
                            role="user",
                            content=user_content
                        )
                        await session.commit()

                        # Echo user message back to client
                        await ws_manager.send_personal_message(
                            {
                                "type": "chat",
                                "data": {
                                    "id": str(user_msg.id),
                                    "role": "user",
                                    "content": user_content,
                                    "timestamp": user_msg.created_at.isoformat(),
                                }
                            },
                            connection_id
                        )

                        # TODO: Run orchestrator agent to generate response
                        # For MVP, send a simple echo response
                        agent_response = f"Received: {user_content[:50]}... (Agent integration coming soon!)"

                        # Store agent response
                        agent_msg = await add_message(
                            session,
                            project_id=project_id,
                            role="assistant",
                            content=agent_response
                        )
                        await session.commit()

                        # Send agent response to client
                        await ws_manager.send_personal_message(
                            {
                                "type": "chat",
                                "data": {
                                    "id": str(agent_msg.id),
                                    "role": "assistant",
                                    "content": agent_response,
                                    "timestamp": agent_msg.created_at.isoformat(),
                                }
                            },
                            connection_id
                        )

                    except Exception as db_error:
                        logger.error(f"Database error: {db_error}")
                        await session.rollback()
                        await ws_manager.send_error(
                            connection_id,
                            "DATABASE_ERROR",
                            "Failed to process message"
                        )

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received on connection {connection_id}")
                await ws_manager.send_error(connection_id, "INVALID_JSON", "Message must be valid JSON")
            except Exception as e:
                logger.error(f"Error processing message on connection {connection_id}: {e}")
                await ws_manager.send_error(connection_id, "PROCESSING_ERROR", str(e))

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket connection {connection_id}: {e}")
    finally:
        # Clean up connection
        await ws_manager.disconnect(connection_id)
