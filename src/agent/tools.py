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
    session: AsyncSession,
    project_id: UUID,
    role: MessageRole,
    content: str,
    topic_id: Optional[UUID] = None
) -> ConversationMessage:
    """
    Save a conversation message to the database.

    Args:
        session: Database session
        project_id: Project UUID
        role: Message role (USER, ASSISTANT, SYSTEM)
        content: Message content
        topic_id: Optional topic ID (will auto-detect if not provided)

    Returns:
        ConversationMessage: Saved message object
    """
    from src.services.topic_manager import (
        get_active_topic,
        create_new_topic,
        should_create_new_topic
    )

    # Auto-detect topic if not provided
    if topic_id is None:
        # Check if we should create new topic (only for user messages)
        if role == MessageRole.USER:
            should_create = await should_create_new_topic(session, project_id, content)
            if should_create:
                new_topic = await create_new_topic(session, project_id)
                topic_id = new_topic.id
            else:
                # Use active topic or create one if none exists
                active_topic = await get_active_topic(session, project_id)
                if active_topic:
                    topic_id = active_topic.id
                else:
                    # No active topic - create first one
                    new_topic = await create_new_topic(session, project_id, title="Initial Conversation")
                    topic_id = new_topic.id
        else:
            # Assistant messages - always use active topic
            active_topic = await get_active_topic(session, project_id)
            if active_topic:
                topic_id = active_topic.id

    # Create message
    message = ConversationMessage(
        project_id=project_id,
        topic_id=topic_id,
        role=role,
        content=content,
        timestamp=datetime.utcnow()
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
    session: AsyncSession,
    project_id: UUID,
    limit: int = 50,
    topic_id: Optional[UUID] = None,
    active_topic_only: bool = False
) -> list[ConversationMessage]:
    """
    Retrieve conversation history for a project.

    Args:
        session: Database session
        project_id: Project UUID
        limit: Maximum number of messages to retrieve
        topic_id: Optional specific topic ID to filter by
        active_topic_only: If True, only return messages from active topic

    Returns:
        list[ConversationMessage]: List of messages ordered by timestamp
    """
    from src.services.topic_manager import get_active_topic

    # Build query
    query = select(ConversationMessage).where(ConversationMessage.project_id == project_id)

    # Filter by topic if requested
    if topic_id:
        query = query.where(ConversationMessage.topic_id == topic_id)
    elif active_topic_only:
        active_topic = await get_active_topic(session, project_id)
        if active_topic:
            query = query.where(ConversationMessage.topic_id == active_topic.id)
        else:
            # No active topic - return empty
            return []

    # Order and limit
    query = query.order_by(ConversationMessage.timestamp.asc()).limit(limit)

    result = await session.execute(query)
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
