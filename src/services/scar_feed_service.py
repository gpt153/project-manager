"""
Service to aggregate SCAR activity logs and format for streaming.
"""

import asyncio
import logging
from datetime import datetime
from typing import AsyncGenerator, Dict, List
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import ScarCommandExecution

logger = logging.getLogger(__name__)


async def get_recent_scar_activity(
    session: AsyncSession, project_id: UUID, limit: int = 50, verbosity_level: int = 2
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
        .where(ScarCommandExecution.project_id == project_id)
        .order_by(desc(ScarCommandExecution.started_at))
        .limit(limit)
    )

    result = await session.execute(query)
    activities = result.scalars().all()

    activity_list = [
        {
            "id": str(activity.id),
            "timestamp": (
                activity.started_at.isoformat()
                if activity.started_at
                else (
                    activity.completed_at.isoformat()
                    if activity.completed_at
                    else datetime.utcnow().isoformat()
                )
            ),
            "source": activity.source,  # Uses @property
            "message": (
                f"{activity.command_type.value}: {activity.status.value}"
                if activity.status
                else activity.command_type.value
            ),
            "phase": activity.phase.name if activity.phase else None,
        }
        for activity in reversed(activities)  # Reverse to get chronological order
    ]

    logger.debug(f"Retrieved {len(activity_list)} SCAR activities for project {project_id}")
    return activity_list


async def stream_scar_activity(
    session: AsyncSession, project_id: UUID, verbosity_level: int = 2
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

    # Track the last activity timestamp we've seen
    last_timestamp = None

    # Get initial activities
    activities = await get_recent_scar_activity(
        session, project_id, limit=10, verbosity_level=verbosity_level
    )
    if activities:
        last_timestamp = activities[-1]["timestamp"]
        for activity in activities:
            yield activity

    # Poll for new activities
    while True:
        await asyncio.sleep(2)  # Poll every 2 seconds

        # Query for activities newer than last_timestamp
        # Note: verbosity filtering done in Python (line 54) since it's a @property
        if last_timestamp:
            # Convert ISO timestamp string to datetime for comparison
            last_dt = datetime.fromisoformat(last_timestamp)
            query = (
                select(ScarCommandExecution)
                .where(
                    ScarCommandExecution.project_id == project_id,
                    ScarCommandExecution.started_at > last_dt,
                )
                .order_by(ScarCommandExecution.started_at.asc())
            )
        else:
            query = (
                select(ScarCommandExecution)
                .where(ScarCommandExecution.project_id == project_id)
                .order_by(desc(ScarCommandExecution.started_at))
                .limit(1)
            )

        result = await session.execute(query)
        new_activities = result.scalars().all()

        for activity in new_activities:
            activity_dict = {
                "id": str(activity.id),
                "timestamp": (
                    activity.started_at.isoformat()
                    if activity.started_at
                    else datetime.utcnow().isoformat()
                ),
                "source": activity.source,
                "message": (
                    f"{activity.command_type.value}: {activity.status.value}"
                    if activity.status
                    else activity.command_type.value
                ),
                "phase": activity.phase.name if activity.phase else None,
            }
            last_timestamp = activity_dict["timestamp"]
            yield activity_dict


# Note: add_scar_activity removed - use the proper SCAR executor service
# from src.services.scar_executor instead
