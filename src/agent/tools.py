"""
PydanticAI agent tools for database and state management.

These tools allow the agent to interact with the database and manage
project state during conversations.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import (
    ConversationMessage,
    MessageRole,
    Project,
    ProjectStatus,
)


class AgentDependencies(BaseModel):
    """Dependencies injected into the agent for tool execution"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    session: AsyncSession
    project_id: Optional[UUID] = None


async def save_conversation_message(
    session: AsyncSession, project_id: UUID, role: MessageRole, content: str
) -> ConversationMessage:
    """
    Save a conversation message to the database.

    Args:
        session: Database session
        project_id: Project UUID
        role: Message role (USER, ASSISTANT, SYSTEM)
        content: Message content

    Returns:
        ConversationMessage: Saved message object
    """
    message = ConversationMessage(
        project_id=project_id,
        role=role,
        content=content,
        timestamp=datetime.utcnow(),
    )
    session.add(message)
    await session.commit()
    await session.refresh(message)
    return message


async def get_project(session: AsyncSession, project_id: UUID) -> Optional[Project]:
    """
    Retrieve a project by ID.

    Args:
        session: Database session
        project_id: Project UUID

    Returns:
        Project: Project object or None if not found
    """
    result = await session.execute(select(Project).where(Project.id == project_id))
    return result.scalar_one_or_none()


async def update_project_status(
    session: AsyncSession, project_id: UUID, status: ProjectStatus
) -> Project:
    """
    Update project status.

    Args:
        session: Database session
        project_id: Project UUID
        status: New status

    Returns:
        Project: Updated project object
    """
    project = await get_project(session, project_id)
    if project:
        project.status = status
        project.updated_at = datetime.utcnow()
        await session.commit()
        await session.refresh(project)
    return project


async def get_conversation_history(
    session: AsyncSession, project_id: UUID, limit: int = 50
) -> list[ConversationMessage]:
    """
    Retrieve conversation history for a project.

    Args:
        session: Database session
        project_id: Project UUID
        limit: Maximum number of messages to retrieve

    Returns:
        list[ConversationMessage]: List of messages ordered by timestamp
    """
    result = await session.execute(
        select(ConversationMessage)
        .where(ConversationMessage.project_id == project_id)
        .order_by(ConversationMessage.timestamp.asc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def update_project_vision(
    session: AsyncSession, project_id: UUID, vision_document: dict
) -> Project:
    """
    Update project vision document.

    Args:
        session: Database session
        project_id: Project UUID
        vision_document: Vision document as dict

    Returns:
        Project: Updated project object
    """
    project = await get_project(session, project_id)
    if project:
        project.vision_document = vision_document
        project.updated_at = datetime.utcnow()
        await session.commit()
        await session.refresh(project)
    return project
