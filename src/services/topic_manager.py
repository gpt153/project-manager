"""
Conversation Topic Management Service.

Handles automatic topic segmentation based on conversation flow.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import ConversationMessage, ConversationTopic, MessageRole

logger = logging.getLogger(__name__)


async def get_active_topic(session: AsyncSession, project_id: UUID) -> Optional[ConversationTopic]:
    """
    Get the currently active topic for a project.

    Args:
        session: Database session
        project_id: Project UUID

    Returns:
        Active ConversationTopic or None
    """
    stmt = (
        select(ConversationTopic)
        .where(
            and_(
                ConversationTopic.project_id == project_id,
                ConversationTopic.is_active
            )
        )
        .order_by(desc(ConversationTopic.started_at))
        .limit(1)
    )

    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_new_topic(
    session: AsyncSession,
    project_id: UUID,
    title: Optional[str] = None,
    summary: Optional[str] = None
) -> ConversationTopic:
    """
    Create a new conversation topic.

    Args:
        session: Database session
        project_id: Project UUID
        title: Optional topic title
        summary: Optional topic summary

    Returns:
        New ConversationTopic
    """
    # End previous active topic
    active_topic = await get_active_topic(session, project_id)
    if active_topic:
        active_topic.is_active = False
        active_topic.ended_at = datetime.utcnow()
        logger.info(f"Ended topic {active_topic.id}: {active_topic.topic_title}")

    # Create new topic
    new_topic = ConversationTopic(
        project_id=project_id,
        topic_title=title or f"Topic {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
        topic_summary=summary,
        started_at=datetime.utcnow(),
        is_active=True
    )
    session.add(new_topic)
    await session.flush()  # Get ID

    logger.info(f"Created new topic {new_topic.id}: {new_topic.topic_title}")
    return new_topic


async def should_create_new_topic(
    session: AsyncSession,
    project_id: UUID,
    user_message: str
) -> bool:
    """
    Determine if a new topic should be created based on conversation signals.

    Args:
        session: Database session
        project_id: Project UUID
        user_message: Current user message

    Returns:
        True if new topic should be created
    """
    # Check for explicit topic switch phrases
    topic_switch_phrases = [
        "new topic",
        "different topic",
        "let's discuss",
        "lets discuss",
        "switching to",
        "moving on to",
        "but we weren't discussing",
        "but we werent discussing",
        "we were talking about",
    ]

    user_lower = user_message.lower()
    for phrase in topic_switch_phrases:
        if phrase in user_lower:
            logger.info(f"Topic switch detected: '{phrase}' in message")
            return True

    # Check for time gap since last message
    active_topic = await get_active_topic(session, project_id)
    if active_topic:
        # Get last message in topic
        stmt = (
            select(ConversationMessage)
            .where(ConversationMessage.topic_id == active_topic.id)
            .order_by(desc(ConversationMessage.timestamp))
            .limit(1)
        )
        result = await session.execute(stmt)
        last_message = result.scalar_one_or_none()

        if last_message:
            # Ensure timezone-aware comparison
            if last_message.timestamp.tzinfo is None:
                last_time = last_message.timestamp.replace(tzinfo=timezone.utc)
            else:
                last_time = last_message.timestamp

            now = datetime.now(timezone.utc)
            time_gap = (now - last_time).total_seconds()

            # Create new topic if >1 hour gap
            if time_gap > 3600:
                logger.info(f"Time gap detected: {time_gap/60:.1f} minutes since last message")
                return True

    return False


async def generate_topic_title(
    session: AsyncSession,
    topic_id: UUID
) -> str:
    """
    Generate a descriptive title for a topic based on its messages.

    This is a simplified version - could be enhanced with LLM summarization.

    Args:
        session: Database session
        topic_id: Topic UUID

    Returns:
        Generated topic title
    """
    # Get first few messages
    stmt = (
        select(ConversationMessage)
        .where(ConversationMessage.topic_id == topic_id)
        .order_by(ConversationMessage.timestamp)
        .limit(3)
    )

    result = await session.execute(stmt)
    messages = result.scalars().all()

    if not messages:
        return "Untitled Topic"

    # Extract keywords from first user message
    first_user_msg = None
    for msg in messages:
        if msg.role == MessageRole.USER:
            first_user_msg = msg
            break

    if not first_user_msg:
        return "Untitled Topic"

    # Simple title generation: first 5 words
    words = first_user_msg.content.split()[:5]
    title = " ".join(words)
    if len(words) == 5:
        title += "..."

    return title
