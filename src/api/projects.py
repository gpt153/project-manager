"""
REST API router for project and issue data endpoints.
"""

import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_session
from src.database.models import Project
from src.services.project_service import (
    ProjectCreate,
    create_project,
    get_all_projects,
    get_conversation_history,
    get_project_with_stats,
)
from src.services.topic_manager import create_new_topic
from sqlalchemy import select

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/projects", response_model=List[dict])
async def list_projects(session: AsyncSession = Depends(get_session)):
    """
    Get all projects with issue counts and stats.

    Returns:
        List of projects with metadata (empty list if no projects exist)
    """
    try:
        projects = await get_all_projects(session)
        return projects
    except Exception as e:
        logger.error(f"Error listing projects: {e}", exc_info=True)
        # Return empty list instead of error to handle empty database gracefully
        return []


@router.get("/projects/{project_id}", response_model=dict)
async def get_project(project_id: UUID, session: AsyncSession = Depends(get_session)):
    """
    Get a single project with detailed statistics.

    Args:
        project_id: Project UUID

    Returns:
        Project with detailed stats

    Raises:
        404: Project not found
    """
    try:
        project = await get_project_with_stats(session, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {project_id} not found"
            )
        return project
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve project"
        )


@router.post("/projects", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_new_project(
    project_data: ProjectCreate, session: AsyncSession = Depends(get_session)
):
    """
    Create a new project.

    Args:
        project_data: Project creation data

    Returns:
        Created project data

    Raises:
        400: Invalid project data
    """
    try:
        project = await create_project(
            session, name=project_data.name, description=project_data.description
        )

        return {
            "id": str(project.id),
            "name": project.name,
            "description": project.description,
            "status": project.status.value,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat(),
        }
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create project"
        )


@router.get("/projects/{project_id}/messages", response_model=List[dict])
async def get_project_messages(
    project_id: UUID, limit: int = 100, session: AsyncSession = Depends(get_session)
):
    """
    Get conversation history for a project.

    Args:
        project_id: Project UUID
        limit: Maximum number of messages to return

    Returns:
        List of conversation messages

    Raises:
        404: Project not found
    """
    try:
        messages = await get_conversation_history(session, project_id, limit=limit)
        return messages
    except Exception as e:
        logger.error(f"Error retrieving messages for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve messages"
        )


@router.post("/projects/{project_id}/reset", response_model=dict)
async def reset_project_conversation(
    project_id: UUID, session: AsyncSession = Depends(get_session)
):
    """
    Reset conversation context for a project.

    This creates a new conversation topic, effectively clearing the context
    while preserving message history.

    Args:
        project_id: Project UUID
        session: Database session

    Returns:
        Success message with new topic ID

    Raises:
        404: Project not found
        500: Failed to reset conversation
    """
    try:
        # Verify project exists
        result = await session.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {project_id} not found"
            )

        # Create new topic (this automatically ends the previous one)
        new_topic = await create_new_topic(
            session, project_id, title="Reset - New Conversation", summary="User requested context reset"
        )

        await session.commit()

        logger.info(f"Reset conversation for project {project_id}, new topic: {new_topic.id}")

        return {
            "success": True,
            "message": "Conversation context reset successfully",
            "new_topic_id": str(new_topic.id),
            "previous_messages_preserved": True,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting conversation for project {project_id}: {e}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset conversation context",
        )
