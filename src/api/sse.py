"""
Server-Sent Events endpoint for streaming SCAR activity feed.
"""
import asyncio
import json
import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Query
from sse_starlette.sse import EventSourceResponse

from src.database.connection import async_session_maker
from src.services.scar_feed_service import stream_scar_activity

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/sse/scar/{project_id}")
async def sse_scar_activity(
    project_id: UUID,
    verbosity: int = Query(default=2, ge=1, le=3, description="Verbosity level: 1=low, 2=medium, 3=high")
):
    """
    Server-Sent Events endpoint for streaming SCAR activity feed.

    This endpoint streams real-time updates of SCAR activity (Project Orchestrator → SCAR → Claude)
    for a specific project. The stream includes heartbeat pings every 30 seconds to keep the
    connection alive.

    Args:
        project_id: Project UUID
        verbosity: Verbosity level filter (1=low, 2=medium, 3=high)

    Returns:
        EventSourceResponse with streaming SCAR activity

    Protocol:
        Event: activity
        Data: {"id": "...", "timestamp": "...", "source": "po|scar|claude", "message": "...", ...}

        Event: heartbeat
        Data: {"status": "alive", "timestamp": "..."}
    """
    logger.info(f"SSE connection established for project {project_id} (verbosity: {verbosity})")

    async def event_generator():
        """Generate Server-Sent Events for SCAR activity."""
        try:
            # Create a new database session for this connection
            async with async_session_maker() as session:
                # Get the activity stream
                activity_stream = stream_scar_activity(session, project_id, verbosity_level=verbosity)

                # Track when we last sent a heartbeat
                last_heartbeat = asyncio.get_event_loop().time()
                heartbeat_interval = 30  # seconds

                try:
                    async for activity in activity_stream:
                        # Send activity event
                        yield {
                            "event": "activity",
                            "data": json.dumps(activity)
                        }

                        # Send heartbeat if it's been a while
                        current_time = asyncio.get_event_loop().time()
                        if current_time - last_heartbeat >= heartbeat_interval:
                            yield {
                                "event": "heartbeat",
                                "data": json.dumps({
                                    "status": "alive",
                                    "timestamp": datetime.utcnow().isoformat()
                                })
                            }
                            last_heartbeat = current_time

                except asyncio.CancelledError:
                    logger.info(f"SSE stream cancelled for project {project_id}")
                    raise
                except Exception as e:
                    logger.error(f"Error in SSE stream for project {project_id}: {e}")
                    # Send error event
                    yield {
                        "event": "error",
                        "data": json.dumps({
                            "code": "STREAM_ERROR",
                            "message": str(e)
                        })
                    }

        except Exception as e:
            logger.error(f"Fatal error in SSE event generator for project {project_id}: {e}")
            yield {
                "event": "error",
                "data": json.dumps({
                    "code": "FATAL_ERROR",
                    "message": "Stream terminated due to error"
                })
            }
        finally:
            logger.info(f"SSE connection closed for project {project_id}")

    return EventSourceResponse(event_generator())
