"""
Unit tests for the Topic Manager service.
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import select

from src.database.models import ConversationMessage, ConversationTopic, MessageRole, Project
from src.services.topic_manager import (
    create_new_topic,
    generate_topic_title,
    get_active_topic,
    should_create_new_topic,
)


@pytest.mark.asyncio
async def test_get_active_topic_no_topics(db_session):
    """Test getting active topic when none exists."""
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.commit()

    active_topic = await get_active_topic(db_session, project.id)
    assert active_topic is None


@pytest.mark.asyncio
async def test_get_active_topic_returns_active(db_session):
    """Test getting active topic when one exists."""
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.flush()

    topic = ConversationTopic(
        project_id=project.id,
        topic_title="Active Topic",
        is_active=True
    )
    db_session.add(topic)
    await db_session.commit()

    active_topic = await get_active_topic(db_session, project.id)
    assert active_topic is not None
    assert active_topic.id == topic.id
    assert active_topic.is_active is True


@pytest.mark.asyncio
async def test_get_active_topic_ignores_inactive(db_session):
    """Test that inactive topics are ignored."""
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.flush()

    # Create inactive topic
    inactive_topic = ConversationTopic(
        project_id=project.id,
        topic_title="Inactive Topic",
        is_active=False
    )
    db_session.add(inactive_topic)
    await db_session.commit()

    active_topic = await get_active_topic(db_session, project.id)
    assert active_topic is None


@pytest.mark.asyncio
async def test_create_new_topic_first_topic(db_session):
    """Test creating the first topic for a project."""
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.commit()

    new_topic = await create_new_topic(
        db_session,
        project.id,
        title="First Topic",
        summary="This is the first topic"
    )

    assert new_topic is not None
    assert new_topic.topic_title == "First Topic"
    assert new_topic.topic_summary == "This is the first topic"
    assert new_topic.is_active is True
    assert new_topic.project_id == project.id


@pytest.mark.asyncio
async def test_create_new_topic_ends_previous(db_session):
    """Test that creating a new topic ends the previous active topic."""
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.flush()

    # Create first topic
    first_topic = await create_new_topic(db_session, project.id, title="First Topic")
    await db_session.commit()

    assert first_topic.is_active is True

    # Create second topic
    second_topic = await create_new_topic(db_session, project.id, title="Second Topic")
    await db_session.commit()

    # Refresh first topic from database
    await db_session.refresh(first_topic)

    assert first_topic.is_active is False
    assert first_topic.ended_at is not None
    assert second_topic.is_active is True


@pytest.mark.asyncio
async def test_should_create_new_topic_with_phrase(db_session):
    """Test topic detection with explicit phrase."""
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.commit()

    user_message = "let's discuss a new feature"
    should_create = await should_create_new_topic(db_session, project.id, user_message)

    assert should_create is True


@pytest.mark.asyncio
async def test_should_create_new_topic_with_correction(db_session):
    """Test topic detection with user correction."""
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.commit()

    user_message = "but we weren't discussing that feature"
    should_create = await should_create_new_topic(db_session, project.id, user_message)

    assert should_create is True


@pytest.mark.asyncio
async def test_should_create_new_topic_time_gap(db_session):
    """Test topic detection with time gap."""
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.flush()

    # Create topic with old message
    topic = await create_new_topic(db_session, project.id, title="Old Topic")
    await db_session.flush()

    old_message = ConversationMessage(
        project_id=project.id,
        topic_id=topic.id,
        role=MessageRole.USER,
        content="Old message",
        timestamp=datetime.utcnow() - timedelta(hours=2)  # 2 hours ago
    )
    db_session.add(old_message)
    await db_session.commit()

    # Check if new topic should be created
    should_create = await should_create_new_topic(
        db_session,
        project.id,
        "New message after time gap"
    )

    assert should_create is True


@pytest.mark.asyncio
async def test_should_create_new_topic_no_gap(db_session):
    """Test topic detection without time gap."""
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.flush()

    # Create topic with recent message
    topic = await create_new_topic(db_session, project.id, title="Recent Topic")
    await db_session.flush()

    recent_message = ConversationMessage(
        project_id=project.id,
        topic_id=topic.id,
        role=MessageRole.USER,
        content="Recent message",
        timestamp=datetime.utcnow() - timedelta(minutes=5)  # 5 minutes ago
    )
    db_session.add(recent_message)
    await db_session.commit()

    # Check if new topic should be created
    should_create = await should_create_new_topic(
        db_session,
        project.id,
        "Continuing the conversation"
    )

    assert should_create is False


@pytest.mark.asyncio
async def test_generate_topic_title(db_session):
    """Test topic title generation from messages."""
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.flush()

    topic = await create_new_topic(db_session, project.id)
    await db_session.flush()

    # Add messages to topic
    message = ConversationMessage(
        project_id=project.id,
        topic_id=topic.id,
        role=MessageRole.USER,
        content="I want to add a dark mode toggle to the app"
    )
    db_session.add(message)
    await db_session.commit()

    # Generate title
    title = await generate_topic_title(db_session, topic.id)

    assert title is not None
    assert len(title) > 0
    assert "I want to add" in title or "I want to" in title


@pytest.mark.asyncio
async def test_generate_topic_title_no_messages(db_session):
    """Test topic title generation with no messages."""
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.flush()

    topic = await create_new_topic(db_session, project.id)
    await db_session.commit()

    # Generate title with no messages
    title = await generate_topic_title(db_session, topic.id)

    assert title == "Untitled Topic"


@pytest.mark.asyncio
async def test_multiple_active_topics_returns_latest(db_session):
    """Test that with multiple active topics, the latest is returned."""
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.flush()

    # Create two topics manually (simulating a bug scenario)
    topic1 = ConversationTopic(
        project_id=project.id,
        topic_title="Topic 1",
        started_at=datetime.utcnow() - timedelta(hours=1),
        is_active=True
    )
    topic2 = ConversationTopic(
        project_id=project.id,
        topic_title="Topic 2",
        started_at=datetime.utcnow(),
        is_active=True
    )
    db_session.add(topic1)
    db_session.add(topic2)
    await db_session.commit()

    active_topic = await get_active_topic(db_session, project.id)

    # Should return the most recent one
    assert active_topic.id == topic2.id
