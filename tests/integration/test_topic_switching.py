"""
Integration tests for conversation topic switching.

These tests verify that the topic segmentation system works correctly
in real-world scenarios.
"""

from datetime import datetime, timedelta

import pytest

from src.agent.tools import get_conversation_history, save_conversation_message
from src.database.models import MessageRole, Project
from src.services.topic_manager import get_active_topic


@pytest.mark.asyncio
async def test_first_message_creates_topic(db_session):
    """Test that the first message creates an initial topic."""
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.commit()

    # Save first message
    message = await save_conversation_message(
        db_session,
        project.id,
        MessageRole.USER,
        "Hello, I want to build a feature"
    )

    # Verify topic was created
    active_topic = await get_active_topic(db_session, project.id)
    assert active_topic is not None
    assert active_topic.topic_title == "Initial Conversation"
    assert message.topic_id == active_topic.id


@pytest.mark.asyncio
async def test_continuing_conversation_same_topic(db_session):
    """Test that continuing a conversation stays in the same topic."""
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.commit()

    # First message
    msg1 = await save_conversation_message(
        db_session,
        project.id,
        MessageRole.USER,
        "I want to add dark mode"
    )

    # Second message (continuation)
    msg2 = await save_conversation_message(
        db_session,
        project.id,
        MessageRole.USER,
        "It should toggle between light and dark"
    )

    # Both messages should be in the same topic
    assert msg1.topic_id == msg2.topic_id


@pytest.mark.asyncio
async def test_explicit_topic_switch(db_session):
    """Test that explicit topic switch creates new topic."""
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.commit()

    # First conversation
    msg1 = await save_conversation_message(
        db_session,
        project.id,
        MessageRole.USER,
        "I want to add dark mode"
    )

    # Explicit topic switch
    msg2 = await save_conversation_message(
        db_session,
        project.id,
        MessageRole.USER,
        "let's discuss a different feature - user authentication"
    )

    # Should be in different topics
    assert msg1.topic_id != msg2.topic_id

    # Verify first topic is ended
    first_topic = await db_session.get(type(msg1.topic), msg1.topic_id)
    assert first_topic.is_active is False
    assert first_topic.ended_at is not None


@pytest.mark.asyncio
async def test_user_correction_creates_new_topic(db_session):
    """Test that user correction creates a new topic."""
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.commit()

    # First message
    msg1 = await save_conversation_message(
        db_session,
        project.id,
        MessageRole.USER,
        "Tell me about the SSE feed"
    )

    # User correction
    msg2 = await save_conversation_message(
        db_session,
        project.id,
        MessageRole.USER,
        "but we weren't discussing the SSE feed, we were talking about chat features"
    )

    # Should create new topic
    assert msg1.topic_id != msg2.topic_id


@pytest.mark.asyncio
async def test_conversation_history_filters_by_topic(db_session):
    """Test that conversation history respects topic boundaries."""
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.commit()

    # Topic 1 messages
    msg1 = await save_conversation_message(
        db_session,
        project.id,
        MessageRole.USER,
        "Let's discuss Feature A"
    )
    msg2 = await save_conversation_message(
        db_session,
        project.id,
        MessageRole.ASSISTANT,
        "Great! Let's talk about Feature A"
    )

    # Topic 2 messages (switch)
    msg3 = await save_conversation_message(
        db_session,
        project.id,
        MessageRole.USER,
        "let's discuss Feature B instead"
    )
    msg4 = await save_conversation_message(
        db_session,
        project.id,
        MessageRole.ASSISTANT,
        "Sure, let's talk about Feature B"
    )

    # Get history for active topic only
    history = await get_conversation_history(
        db_session,
        project.id,
        limit=50,
        active_topic_only=True
    )

    # Should only include Topic 2 messages
    assert len(history) == 2
    assert history[0].id == msg3.id
    assert history[1].id == msg4.id


@pytest.mark.asyncio
async def test_assistant_messages_use_active_topic(db_session):
    """Test that assistant messages always use the active topic."""
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.commit()

    # User message creates topic
    user_msg = await save_conversation_message(
        db_session,
        project.id,
        MessageRole.USER,
        "Hello"
    )

    # Assistant response should use same topic
    assistant_msg = await save_conversation_message(
        db_session,
        project.id,
        MessageRole.ASSISTANT,
        "Hi! How can I help?"
    )

    assert user_msg.topic_id == assistant_msg.topic_id


@pytest.mark.asyncio
async def test_multiple_topic_switches(db_session):
    """Test multiple topic switches in sequence."""
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.commit()

    # Topic 1
    msg1 = await save_conversation_message(
        db_session,
        project.id,
        MessageRole.USER,
        "Let's talk about Feature A"
    )

    # Topic 2
    msg2 = await save_conversation_message(
        db_session,
        project.id,
        MessageRole.USER,
        "new topic - Feature B"
    )

    # Topic 3
    msg3 = await save_conversation_message(
        db_session,
        project.id,
        MessageRole.USER,
        "switching to Feature C"
    )

    # All three should have different topics
    assert msg1.topic_id != msg2.topic_id
    assert msg2.topic_id != msg3.topic_id
    assert msg1.topic_id != msg3.topic_id

    # Only the last topic should be active
    active_topic = await get_active_topic(db_session, project.id)
    assert active_topic.id == msg3.topic_id


@pytest.mark.asyncio
async def test_get_history_with_specific_topic_id(db_session):
    """Test retrieving history for a specific topic."""
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.commit()

    # Topic 1
    msg1 = await save_conversation_message(
        db_session,
        project.id,
        MessageRole.USER,
        "Topic 1 message"
    )
    topic1_id = msg1.topic_id

    # Topic 2
    msg2 = await save_conversation_message(
        db_session,
        project.id,
        MessageRole.USER,
        "let's discuss something else"
    )

    # Get history for topic 1 specifically
    history = await get_conversation_history(
        db_session,
        project.id,
        topic_id=topic1_id
    )

    # Should only include topic 1 messages
    assert len(history) == 1
    assert history[0].id == msg1.id


@pytest.mark.asyncio
async def test_context_isolation_prevents_bleeding(db_session):
    """
    Test that context from old topics doesn't bleed into new topics.
    This is the core issue that Phase 2 aims to fix.
    """
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.commit()

    # Simulate the scenario from issue #56
    # Jan 6: Discussion about SSE feed (Topic 1)
    sse_msg1 = await save_conversation_message(
        db_session,
        project.id,
        MessageRole.USER,
        "Let's enhance the SSE feed to show detailed SCAR execution"
    )
    sse_msg2 = await save_conversation_message(
        db_session,
        project.id,
        MessageRole.ASSISTANT,
        "Great idea! I'll help you enhance the SSE feed."
    )

    # Jan 7: Discussion about chat features (Topic 2)
    chat_msg1 = await save_conversation_message(
        db_session,
        project.id,
        MessageRole.USER,
        "let's discuss a change in the webui for instant message display"
    )
    chat_msg2 = await save_conversation_message(
        db_session,
        project.id,
        MessageRole.ASSISTANT,
        "That's a great UX improvement for the chat interface"
    )

    # Get active topic history
    active_history = await get_conversation_history(
        db_session,
        project.id,
        limit=50,
        active_topic_only=True
    )

    # Should only contain chat messages, NOT SSE messages
    message_ids = [msg.id for msg in active_history]
    assert sse_msg1.id not in message_ids
    assert sse_msg2.id not in message_ids
    assert chat_msg1.id in message_ids
    assert chat_msg2.id in message_ids

    # Verify we're in a different topic
    assert chat_msg1.topic_id != sse_msg1.topic_id
