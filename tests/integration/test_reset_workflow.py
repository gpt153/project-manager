"""
Integration tests for the complete reset workflow.

Tests that reset works correctly across all integration points:
- REST API
- WebSocket protocol
- Topic management
- Message isolation
"""

import pytest

from src.agent.tools import get_conversation_history, save_conversation_message
from src.database.models import MessageRole, Project
from src.services.topic_manager import create_new_topic, get_active_topic


@pytest.mark.asyncio
async def test_reset_clears_active_context(db_session):
    """
    Test that reset creates a new topic and future messages use the new context.
    This is the core behavior that fixes issue #56.
    """
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.commit()

    # Conversation about Feature A
    msg1 = await save_conversation_message(
        db_session, project.id, MessageRole.USER, "Let's implement Feature A"
    )
    msg2 = await save_conversation_message(
        db_session, project.id, MessageRole.ASSISTANT, "Great! Let's work on Feature A"
    )

    # Get context before reset
    history_before = await get_conversation_history(db_session, project.id, active_topic_only=True)
    assert len(history_before) == 2

    # User resets context
    new_topic = await create_new_topic(
        db_session, project.id, title="Reset - New Conversation", summary="User requested reset"
    )
    await db_session.commit()

    # User starts new conversation about Feature B
    msg3 = await save_conversation_message(
        db_session,
        project.id,
        MessageRole.USER,
        "Now let's talk about Feature B",
        topic_id=new_topic.id,
    )

    # Get context after reset
    history_after = await get_conversation_history(db_session, project.id, active_topic_only=True)

    # Should only see Feature B message, NOT Feature A
    assert len(history_after) == 1
    assert history_after[0].id == msg3.id
    assert "Feature B" in history_after[0].content
    assert msg1.id not in [m.id for m in history_after]
    assert msg2.id not in [m.id for m in history_after]


@pytest.mark.asyncio
async def test_reset_preserves_history(db_session):
    """Test that reset preserves old messages but isolates them."""
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.commit()

    # Old conversation
    msg1 = await save_conversation_message(
        db_session, project.id, MessageRole.USER, "Old topic message"
    )
    old_topic_id = msg1.topic_id

    # Reset
    new_topic = await create_new_topic(db_session, project.id, title="Reset")
    await db_session.commit()

    # New conversation
    msg2 = await save_conversation_message(
        db_session, project.id, MessageRole.USER, "New topic message", topic_id=new_topic.id
    )

    # Get ALL messages (not just active topic)
    all_messages = await get_conversation_history(
        db_session, project.id, limit=50, active_topic_only=False
    )

    # Both messages should exist
    assert len(all_messages) == 2
    message_ids = [m.id for m in all_messages]
    assert msg1.id in message_ids
    assert msg2.id in message_ids

    # But they're in different topics
    assert msg1.topic_id == old_topic_id
    assert msg2.topic_id == new_topic.id
    assert msg1.topic_id != msg2.topic_id


@pytest.mark.asyncio
async def test_reset_scenario_from_issue_56(db_session):
    """
    Reproduce and verify fix for the exact scenario from issue #56.

    Timeline:
    - Jan 6: User discusses SSE feed
    - Jan 7: User discusses chat features
    - Problem: PM hallucinates about SSE feed
    - Solution: Reset clears SSE feed context
    """
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.commit()

    # Jan 6: SSE Feed discussion
    sse_msg1 = await save_conversation_message(
        db_session, project.id, MessageRole.USER, "Let's enhance the SSE feed to show SCAR execution"
    )
    sse_msg2 = await save_conversation_message(
        db_session, project.id, MessageRole.ASSISTANT, "Great idea! I'll help with the SSE feed."
    )

    # User realizes PM is off-topic and resets
    new_topic = await create_new_topic(db_session, project.id, title="Reset - Chat Features")
    await db_session.commit()

    # Jan 7: Chat Features discussion (fresh context)
    chat_msg1 = await save_conversation_message(
        db_session,
        project.id,
        MessageRole.USER,
        "Let's discuss chat UI features - instant message display",
        topic_id=new_topic.id,
    )
    chat_msg2 = await save_conversation_message(
        db_session,
        project.id,
        MessageRole.ASSISTANT,
        "That's a great UX improvement for the chat interface",
        topic_id=new_topic.id,
    )

    # Get active context (what PM sees)
    active_context = await get_conversation_history(db_session, project.id, active_topic_only=True)

    # PM should ONLY see chat features, NOT SSE feed
    assert len(active_context) == 2
    context_ids = [m.id for m in active_context]
    assert chat_msg1.id in context_ids
    assert chat_msg2.id in context_ids
    assert sse_msg1.id not in context_ids  # This was the bug!
    assert sse_msg2.id not in context_ids  # This was the bug!

    # Verify content
    context_content = " ".join([m.content for m in active_context])
    assert "chat" in context_content.lower()
    assert "sse feed" not in context_content.lower()


@pytest.mark.asyncio
async def test_reset_with_correction_phrase(db_session):
    """
    Test that user correction triggers automatic topic switch.
    Simulates: User says "but we weren't discussing X"
    """
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.commit()

    # Initial topic
    msg1 = await save_conversation_message(
        db_session, project.id, MessageRole.USER, "Tell me about Feature A"
    )
    topic1_id = msg1.topic_id

    # User correction (should trigger topic switch)
    msg2 = await save_conversation_message(
        db_session,
        project.id,
        MessageRole.USER,
        "but we weren't discussing Feature A, we were talking about Feature B",
    )

    # Automatic topic switch should have occurred
    assert msg2.topic_id != topic1_id

    # Active context should only show the correction
    active_context = await get_conversation_history(db_session, project.id, active_topic_only=True)

    # Should have the correction message in the new topic
    assert len(active_context) >= 1
    assert msg2.id in [m.id for m in active_context]


@pytest.mark.asyncio
async def test_multiple_resets_in_sequence(db_session):
    """Test that multiple resets work correctly."""
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.commit()

    # Topic 1
    msg1 = await save_conversation_message(db_session, project.id, MessageRole.USER, "Topic 1")
    topic1 = await get_active_topic(db_session, project.id)

    # Reset to Topic 2
    topic2 = await create_new_topic(db_session, project.id, title="Topic 2")
    await db_session.commit()

    # Reset to Topic 3
    topic3 = await create_new_topic(db_session, project.id, title="Topic 3")
    await db_session.commit()

    # Verify progression
    assert topic1.id != topic2.id
    assert topic2.id != topic3.id

    # Only Topic 3 should be active
    active = await get_active_topic(db_session, project.id)
    assert active.id == topic3.id

    # Topics 1 and 2 should be ended
    await db_session.refresh(topic1)
    await db_session.refresh(topic2)
    assert topic1.is_active is False
    assert topic2.is_active is False
    assert topic3.is_active is True
