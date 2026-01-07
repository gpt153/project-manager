"""
Tests for the orchestrator agent.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agent.orchestrator_agent import (
    detect_topic_change,
    orchestrator_agent,
    run_orchestrator,
)
from src.agent.tools import AgentDependencies
from src.database.models import MessageRole, Project, ProjectStatus


@pytest.mark.asyncio
async def test_agent_initialization():
    """Test that the agent is properly initialized"""
    assert orchestrator_agent is not None
    assert orchestrator_agent.model is not None
    assert orchestrator_agent.deps_type == AgentDependencies


@pytest.mark.asyncio
async def test_save_message_tool(db_session):
    """Test the save_message tool"""
    # Create a test project
    project = Project(
        name="Test Project",
        status=ProjectStatus.BRAINSTORMING,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Create dependencies
    deps = AgentDependencies(session=db_session, project_id=project.id)

    # Create mock context
    mock_ctx = MagicMock()
    mock_ctx.deps = deps

    # Import the tool function directly
    from src.agent.orchestrator_agent import save_message

    # Call the tool
    result = await save_message(mock_ctx, "user", "Test message")

    assert "saved" in result.lower()


@pytest.mark.asyncio
async def test_get_project_context_tool(db_session):
    """Test the get_project_context tool"""
    # Create a test project
    project = Project(
        name="Test Project",
        description="Test description",
        status=ProjectStatus.BRAINSTORMING,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Create dependencies
    deps = AgentDependencies(session=db_session, project_id=project.id)

    # Create mock context
    mock_ctx = MagicMock()
    mock_ctx.deps = deps

    # Import the tool function
    from src.agent.orchestrator_agent import get_project_context

    # Call the tool
    result = await get_project_context(mock_ctx)

    assert result["name"] == "Test Project"
    assert result["description"] == "Test description"
    assert result["status"] == "BRAINSTORMING"


@pytest.mark.asyncio
async def test_update_status_tool(db_session):
    """Test the update_status tool"""
    # Create a test project
    project = Project(
        name="Test Project",
        status=ProjectStatus.BRAINSTORMING,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Create dependencies
    deps = AgentDependencies(session=db_session, project_id=project.id)

    # Create mock context
    mock_ctx = MagicMock()
    mock_ctx.deps = deps

    # Import the tool function
    from src.agent.orchestrator_agent import update_status

    # Call the tool
    result = await update_status(mock_ctx, "PLANNING")

    assert "updated" in result.lower()
    assert "PLANNING" in result


@pytest.mark.asyncio
async def test_run_orchestrator_saves_messages(db_session):
    """Test that run_orchestrator saves user and assistant messages"""
    # Create a test project
    project = Project(
        name="Test Project",
        status=ProjectStatus.BRAINSTORMING,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Mock the agent run method to return a simple response
    with patch.object(orchestrator_agent, "run", new_callable=AsyncMock) as mock_run:
        mock_result = MagicMock()
        mock_result.data = "Hello! I'd be happy to help you build your project."
        mock_run.return_value = mock_result

        # Run the orchestrator
        response = await run_orchestrator(project.id, "I want to build an app", db_session)

        # Verify response
        assert response == "Hello! I'd be happy to help you build your project."

        # Verify messages were saved
        from src.agent.tools import get_conversation_history

        history = await get_conversation_history(db_session, project.id)

        assert len(history) == 2
        assert history[0].content == "I want to build an app"
        assert history[0].role.value == "USER"
        assert history[1].role.value == "ASSISTANT"


# Phase 1 Tests: Context Management


def test_detect_topic_change_with_correction_phrase():
    """Test that detect_topic_change identifies explicit user corrections"""
    # Create mock messages
    now = datetime.now(timezone.utc)
    messages = [
        MagicMock(
            content="Let's discuss the SSE feed",
            timestamp=now - timedelta(minutes=5),
            role=MessageRole.USER,
        ),
        MagicMock(
            content="Sure, the SSE feed needs...",
            timestamp=now - timedelta(minutes=4),
            role=MessageRole.ASSISTANT,
        ),
        MagicMock(
            content="but we weren't discussing the SSE feed",
            timestamp=now,
            role=MessageRole.USER,
        ),
    ]

    # Test with correction phrase
    assert detect_topic_change(messages, "but we weren't discussing the SSE feed") is True


def test_detect_topic_change_with_new_topic_phrase():
    """Test that detect_topic_change identifies 'let's discuss' phrases"""
    now = datetime.now(timezone.utc)
    messages = [
        MagicMock(content="Previous topic", timestamp=now - timedelta(minutes=5), role=MessageRole.USER),
        MagicMock(content="Response", timestamp=now - timedelta(minutes=4), role=MessageRole.ASSISTANT),
        MagicMock(content="lets discuss something else", timestamp=now, role=MessageRole.USER),
    ]

    assert detect_topic_change(messages, "lets discuss something else") is True


def test_detect_topic_change_with_time_gap():
    """Test that detect_topic_change identifies time gaps >1 hour"""
    now = datetime.now(timezone.utc)
    messages = [
        MagicMock(
            content="Old message",
            timestamp=now - timedelta(hours=2),
            role=MessageRole.USER,
        ),
        MagicMock(
            content="New message after time gap",
            timestamp=now,
            role=MessageRole.USER,
        ),
    ]

    assert detect_topic_change(messages, "New message after time gap") is True


def test_detect_topic_change_no_change():
    """Test that detect_topic_change returns False for normal conversation"""
    now = datetime.now(timezone.utc)
    messages = [
        MagicMock(
            content="Let's discuss feature X",
            timestamp=now - timedelta(minutes=5),
            role=MessageRole.USER,
        ),
        MagicMock(
            content="Sure, feature X needs...",
            timestamp=now - timedelta(minutes=4),
            role=MessageRole.ASSISTANT,
        ),
        MagicMock(
            content="And also what about Y?",
            timestamp=now,
            role=MessageRole.USER,
        ),
    ]

    assert detect_topic_change(messages, "And also what about Y?") is False


def test_detect_topic_change_handles_naive_timestamps():
    """Test that detect_topic_change handles timezone-naive timestamps"""
    now = datetime.now()  # Naive timestamp
    messages = [
        MagicMock(
            content="Old message",
            timestamp=now - timedelta(hours=2),
            role=MessageRole.USER,
        ),
        MagicMock(
            content="New message",
            timestamp=now,
            role=MessageRole.USER,
        ),
    ]

    # Should not crash with naive timestamps
    result = detect_topic_change(messages, "New message")
    assert result is True  # Time gap >1 hour


@pytest.mark.asyncio
async def test_run_orchestrator_with_topic_change_warning(db_session):
    """Test that run_orchestrator detects topic changes and adds warning to context"""
    # Create a test project
    project = Project(
        name="Test Project",
        status=ProjectStatus.BRAINSTORMING,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Add conversation history with topic switch
    from src.agent.tools import save_conversation_message

    await save_conversation_message(
        db_session, project.id, MessageRole.USER, "Let's discuss the SSE feed"
    )
    await save_conversation_message(
        db_session, project.id, MessageRole.ASSISTANT, "Sure, the SSE feed..."
    )
    await db_session.commit()

    # Mock the agent run method to capture the prompt
    captured_prompt = None

    async def mock_run(prompt, deps):
        nonlocal captured_prompt
        captured_prompt = prompt
        mock_result = MagicMock()
        mock_result.output = "I understand, focusing on chat features now."
        return mock_result

    with patch.object(orchestrator_agent, "run", new_callable=AsyncMock) as mock_agent_run:
        mock_agent_run.side_effect = mock_run

        # Send message with topic correction
        await run_orchestrator(
            project.id,
            "but we weren't discussing the sse feed, we were talking about chat features",
            db_session,
        )

        # Verify the warning was included in the prompt
        assert captured_prompt is not None
        assert "⚠️" in captured_prompt
        assert "IMPORTANT" in captured_prompt
        assert "switched topics or corrected you" in captured_prompt
        assert "CURRENT TOPIC" in captured_prompt


@pytest.mark.asyncio
async def test_run_orchestrator_with_recency_weighting(db_session):
    """Test that run_orchestrator prioritizes recent messages over older ones"""
    # Create a test project
    project = Project(
        name="Test Project",
        status=ProjectStatus.BRAINSTORMING,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Add multiple messages to create history
    from src.agent.tools import save_conversation_message

    # Older messages
    for i in range(10):
        await save_conversation_message(
            db_session, project.id, MessageRole.USER, f"Old message {i}"
        )
        await save_conversation_message(
            db_session, project.id, MessageRole.ASSISTANT, f"Old response {i}"
        )

    await db_session.commit()

    # Capture the prompt
    captured_prompt = None

    async def mock_run(prompt, deps):
        nonlocal captured_prompt
        captured_prompt = prompt
        mock_result = MagicMock()
        mock_result.output = "Response"
        return mock_result

    with patch.object(orchestrator_agent, "run", new_callable=AsyncMock) as mock_agent_run:
        mock_agent_run.side_effect = mock_run

        # Send new message
        await run_orchestrator(project.id, "New current message", db_session)

        # Verify prompt structure
        assert captured_prompt is not None
        assert "CURRENT CONVERSATION (Most Important)" in captured_prompt
        assert "Earlier Context (Only If Relevant)" in captured_prompt
        # Most recent messages should appear before older ones
        assert captured_prompt.index("CURRENT CONVERSATION") < captured_prompt.index("Earlier Context")
