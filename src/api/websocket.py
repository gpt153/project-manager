"""
WebSocket endpoint for bidirectional chat communication.
"""

import json
import logging
from uuid import UUID, uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.agent.orchestrator_agent import run_orchestrator
from src.database.connection import async_session_maker
from src.services.project_service import add_message
from src.services.websocket_manager import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/chat/{project_id}")
async def websocket_chat_endpoint(websocket: WebSocket, project_id: UUID):
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
        await ws_manager.send_status_update(
            connection_id, "connected", "Connected to Project Orchestrator"
        )

        # Listen for messages
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            logger.debug(f"Received message on connection {connection_id}: {data[:100]}")

            try:
                message_data = json.loads(data)
                user_content = message_data.get("content", "").strip()

                if not user_content:
                    await ws_manager.send_error(
                        connection_id, "EMPTY_MESSAGE", "Message content cannot be empty"
                    )
                    continue

                # Process message with orchestrator agent
                async with async_session_maker() as session:
                    try:
                        # Run orchestrator agent to generate response
                        # Note: run_orchestrator saves both user and assistant messages
                        logger.info(f"Running orchestrator agent for project {project_id}")

                        try:
                            # Get last two messages (user + assistant) to send back
                            from sqlalchemy import desc, select

                            from src.database.models import ConversationMessage, MessageRole

                            # Run orchestrator (saves both user and assistant messages)
                            await run_orchestrator(
                                project_id=project_id, user_message=user_content, session=session
                            )
                            await session.commit()

                            # Get the last 2 messages (user + assistant) to send to client
                            stmt = (
                                select(ConversationMessage)
                                .where(ConversationMessage.project_id == project_id)
                                .order_by(desc(ConversationMessage.timestamp))
                                .limit(2)
                            )

                            result = await session.execute(stmt)
                            recent_messages = result.scalars().all()

                            # Send both messages to client
                            for msg in reversed(
                                recent_messages
                            ):  # Reverse to get chronological order
                                await ws_manager.send_personal_message(
                                    {
                                        "type": "chat",
                                        "data": {
                                            "id": str(msg.id),
                                            "role": msg.role.value,
                                            "content": msg.content,
                                            "timestamp": msg.timestamp.isoformat(),
                                        },
                                    },
                                    connection_id,
                                )

                        except Exception as agent_error:
                            logger.error(f"Orchestrator agent error: {agent_error}")
                            # Fallback to simple response on agent failure
                            fallback_response = (
                                "I'm having trouble processing that right now. Please try again."
                            )
                            agent_msg = await add_message(
                                session,
                                project_id=project_id,
                                role=MessageRole.ASSISTANT,
                                content=fallback_response,
                            )
                            await session.commit()

                            await ws_manager.send_personal_message(
                                {
                                    "type": "chat",
                                    "data": {
                                        "id": str(agent_msg.id),
                                        "role": MessageRole.ASSISTANT.value,
                                        "content": fallback_response,
                                        "timestamp": agent_msg.created_at.isoformat(),
                                    },
                                },
                                connection_id,
                            )

                    except Exception as db_error:
                        logger.error(f"Database error: {db_error}")
                        await session.rollback()
                        await ws_manager.send_error(
                            connection_id, "DATABASE_ERROR", "Failed to process message"
                        )

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received on connection {connection_id}")
                await ws_manager.send_error(
                    connection_id, "INVALID_JSON", "Message must be valid JSON"
                )
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
