"""
Service layer for project data aggregation and business logic.
"""

import logging
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import (
    ConversationMessage,
    PhaseStatus,
    Project,
    ProjectStatus,
    WorkflowPhase,
)

logger = logging.getLogger(__name__)


class ProjectCreate(BaseModel):
    """Schema for creating a new project."""

    name: str
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    """Schema for project response."""

    id: str
    name: str
    description: Optional[str]
    status: str
    github_repo_url: Optional[str]
    telegram_chat_id: Optional[int]
    created_at: str
    updated_at: str
    open_issues_count: int = 0
    closed_issues_count: int = 0

    model_config = {"from_attributes": True}


async def get_all_projects(session: AsyncSession) -> List[Dict]:
    """
    Get all projects with issue counts and stats.

    Args:
        session: Database session

    Returns:
        List of project dictionaries with metadata
    """
    query = select(Project).order_by(Project.created_at.desc())
    result = await session.execute(query)
    projects = result.scalars().all()

    project_list = []
    for project in projects:
        # Count messages for activity metric
        msg_query = select(func.count(ConversationMessage.id)).where(
            ConversationMessage.project_id == project.id
        )
        msg_result = await session.execute(msg_query)
        message_count = msg_result.scalar() or 0

        # Count workflow phases
        phase_query = select(func.count(WorkflowPhase.id)).where(
            WorkflowPhase.project_id == project.id,
            WorkflowPhase.status == PhaseStatus.COMPLETED,
        )
        phase_result = await session.execute(phase_query)
        completed_phases = phase_result.scalar() or 0

        project_dict = {
            "id": str(project.id),
            "name": project.name,
            "description": project.description,
            "status": project.status.value,
            "github_repo_url": project.github_repo_url,
            "telegram_chat_id": project.telegram_chat_id,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat(),
            "message_count": message_count,
            "completed_phases": completed_phases,
            # Placeholders for GitHub issues (to be integrated later)
            "open_issues_count": 0,
            "closed_issues_count": 0,
        }
        project_list.append(project_dict)

    logger.info(f"Retrieved {len(project_list)} projects")
    return project_list


async def get_project_with_stats(session: AsyncSession, project_id: UUID) -> Optional[Dict]:
    """
    Get a single project with detailed statistics.

    Args:
        session: Database session
        project_id: Project UUID

    Returns:
        Project dictionary with stats or None if not found
    """
    query = select(Project).where(Project.id == project_id)
    result = await session.execute(query)
    project = result.scalar_one_or_none()

    if not project:
        logger.warning(f"Project {project_id} not found")
        return None

    # Get message count
    msg_query = select(func.count(ConversationMessage.id)).where(
        ConversationMessage.project_id == project.id
    )
    msg_result = await session.execute(msg_query)
    message_count = msg_result.scalar() or 0

    # Get phases
    phase_query = (
        select(WorkflowPhase)
        .where(WorkflowPhase.project_id == project.id)
        .order_by(WorkflowPhase.phase_number)
    )
    phase_result = await session.execute(phase_query)
    phases = phase_result.scalars().all()

    project_dict = {
        "id": str(project.id),
        "name": project.name,
        "description": project.description,
        "status": project.status.value,
        "github_repo_url": project.github_repo_url,
        "telegram_chat_id": project.telegram_chat_id,
        "vision_document": project.vision_document,
        "created_at": project.created_at.isoformat(),
        "updated_at": project.updated_at.isoformat(),
        "message_count": message_count,
        "phases": [
            {
                "id": str(phase.id),
                "name": phase.name,
                "description": phase.description,
                "order": phase.order,
                "is_completed": phase.is_completed,
                "is_current": phase.is_current,
            }
            for phase in phases
        ],
    }

    logger.info(f"Retrieved project {project_id} with stats")
    return project_dict


async def create_project(
    session: AsyncSession, name: str, description: Optional[str] = None
) -> Project:
    """
    Create a new project.

    Args:
        session: Database session
        name: Project name
        description: Optional project description

    Returns:
        Created Project instance
    """
    project = Project(
        name=name,
        description=description,
        status=ProjectStatus.BRAINSTORMING,
    )

    session.add(project)
    await session.flush()  # Flush to get ID
    await session.refresh(project)

    logger.info(f"Created project {project.id}: {name}")
    return project


async def get_conversation_history(
    session: AsyncSession, project_id: UUID, limit: int = 100
) -> List[Dict]:
    """
    Get conversation history for a project.

    Args:
        session: Database session
        project_id: Project UUID
        limit: Maximum number of messages to return

    Returns:
        List of message dictionaries
    """
    query = (
        select(ConversationMessage)
        .where(ConversationMessage.project_id == project_id)
        .order_by(ConversationMessage.timestamp.asc())
        .limit(limit)
    )

    result = await session.execute(query)
    messages = result.scalars().all()

    return [
        {
            "id": str(msg.id),
            "role": msg.role.value,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat(),
            "metadata": msg.message_metadata,
        }
        for msg in messages
    ]


async def add_message(
    session: AsyncSession,
    project_id: UUID,
    role: str,
    content: str,
    metadata: Optional[Dict] = None,
) -> ConversationMessage:
    """
    Add a message to the conversation history.

    Args:
        session: Database session
        project_id: Project UUID
        role: Message role ('user', 'assistant', 'system')
        content: Message content
        metadata: Optional metadata dictionary

    Returns:
        Created ConversationMessage instance
    """
    from src.database.models import MessageRole

    message = ConversationMessage(
        project_id=project_id,
        role=MessageRole(role),
        content=content,
        message_metadata=metadata,
    )

    session.add(message)
    await session.flush()
    await session.refresh(message)

    logger.info(f"Added {role} message to project {project_id}")
    return message
