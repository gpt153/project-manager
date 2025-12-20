"""
Service to aggregate SCAR activity logs and format for streaming.
"""
import logging
import asyncio
from typing import List, Dict, AsyncGenerator
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from src.database.models import ScarCommandExecution, Project

logger = logging.getLogger(__name__)


async def get_recent_scar_activity(
    session: AsyncSession,
    project_id: UUID,
    limit: int = 50,
    verbosity_level: int = 2
) -> List[Dict]:
    """
    Get recent SCAR activity for a project.

    Args:
        session: Database session
        project_id: Project UUID
        limit: Maximum number of activities to return
        verbosity_level: Minimum verbosity level to include (1=low, 2=medium, 3=high)

    Returns:
        List of activity dictionaries
    """
    query = (
        select(ScarCommandExecution)
        .where(
            ScarCommandExecution.project_id == project_id,
            ScarCommandExecution.verbosity_level <= verbosity_level
        )
        .order_by(desc(ScarCommandExecution.created_at))
        .limit(limit)
    )

    result = await session.execute(query)
    activities = result.scalars().all()

    activity_list = [
        {
            "id": str(activity.id),
            "timestamp": activity.created_at.isoformat(),
            "source": activity.source,
            "message": activity.message,
            "command": activity.command,
            "phase": activity.phase,
            "verbosity_level": activity.verbosity_level,
            "metadata": activity.metadata,
        }
        for activity in reversed(activities)  # Reverse to get chronological order
    ]

    logger.debug(f"Retrieved {len(activity_list)} SCAR activities for project {project_id}")
    return activity_list


async def stream_scar_activity(
    session: AsyncSession,
    project_id: UUID,
    verbosity_level: int = 2
) -> AsyncGenerator[Dict, None]:
    """
    Stream SCAR activity updates in real-time.

    This is a generator function that yields activity updates as they occur.
    For MVP, it polls the database periodically. In production, this could
    be replaced with a pub/sub mechanism (Redis, etc.).

    Args:
        session: Database session
        project_id: Project UUID
        verbosity_level: Minimum verbosity level to include

    Yields:
        Activity dictionaries as they occur
    """
    logger.info(f"Starting SCAR activity stream for project {project_id}")

    # Track the last activity ID we've seen
    last_id = None

    # Get initial activities
    activities = await get_recent_scar_activity(session, project_id, limit=10, verbosity_level=verbosity_level)
    if activities:
        last_id = activities[-1]["id"]
        for activity in activities:
            yield activity

    # Poll for new activities
    while True:
        await asyncio.sleep(2)  # Poll every 2 seconds

        # Query for activities newer than last_id
        if last_id:
            query = (
                select(ScarCommandExecution)
                .where(
                    ScarCommandExecution.project_id == project_id,
                    ScarCommandExecution.verbosity_level <= verbosity_level,
                    ScarCommandExecution.id > UUID(last_id)
                )
                .order_by(ScarCommandExecution.created_at.asc())
            )
        else:
            query = (
                select(ScarCommandExecution)
                .where(
                    ScarCommandExecution.project_id == project_id,
                    ScarCommandExecution.verbosity_level <= verbosity_level
                )
                .order_by(desc(ScarCommandExecution.created_at))
                .limit(1)
            )

        result = await session.execute(query)
        new_activities = result.scalars().all()

        for activity in new_activities:
            activity_dict = {
                "id": str(activity.id),
                "timestamp": activity.created_at.isoformat(),
                "source": activity.source,
                "message": activity.message,
                "command": activity.command,
                "phase": activity.phase,
                "verbosity_level": activity.verbosity_level,
                "metadata": activity.metadata,
            }
            last_id = activity_dict["id"]
            yield activity_dict


async def add_scar_activity(
    session: AsyncSession,
    project_id: UUID,
    source: str,
    command: str,
    message: str,
    phase: str | None = None,
    verbosity_level: int = 1,
    metadata: Dict | None = None
) -> ScarCommandExecution:
    """
    Add a SCAR activity log entry.

    Args:
        session: Database session
        project_id: Project UUID
        source: Source of the activity ('po', 'scar', 'claude')
        command: Command being executed
        message: Activity message
        phase: Optional workflow phase
        verbosity_level: Verbosity level (1=low, 2=medium, 3=high)
        metadata: Optional metadata dictionary

    Returns:
        Created ScarCommandExecution instance
    """
    activity = ScarCommandExecution(
        project_id=project_id,
        source=source,
        command=command,
        message=message,
        phase=phase,
        verbosity_level=verbosity_level,
        metadata=metadata,
    )

    session.add(activity)
    await session.flush()
    await session.refresh(activity)

    logger.info(f"Added SCAR activity for project {project_id}: {source} - {message[:50]}")
    return activity
