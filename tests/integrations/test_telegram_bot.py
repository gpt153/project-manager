"""
Tests for Telegram bot integration.

Note: These are unit tests that mock the Telegram API.
Full integration tests would require a real Telegram bot token.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.database.models import Project, ProjectStatus
from src.integrations.telegram_bot import OrchestratorTelegramBot


@pytest.fixture
def mock_telegram_update():
    """Create a mock Telegram update"""
    update = MagicMock()
    update.effective_chat.id = 12345
    update.message.text = "I want to build a task manager"
    update.message.reply_text = AsyncMock()
    update.message.chat.send_action = AsyncMock()
    update.callback_query = None
    return update


@pytest.fixture
def mock_context():
    """Create a mock handler context"""
    context = MagicMock()
    context.chat_data = {}
    return context


@pytest.mark.asyncio
async def test_start_command_creates_project(db_session, mock_telegram_update, mock_context):
    """Test that /start command creates a new project"""
    # Create bot
    bot = OrchestratorTelegramBot(
        token="test_token",
        db_session_maker=lambda: db_session
    )

    # Handle start command
    await bot.start_command(mock_telegram_update, mock_context)

    # Check that reply was sent
    assert mock_telegram_update.message.reply_text.called

    # Check that project ID was stored in context
    assert "project_id" in mock_context.chat_data

    # Verify project was created in database
    from sqlalchemy import select
    result = await db_session.execute(select(Project))
    projects = list(result.scalars().all())

    assert len(projects) == 1
    assert projects[0].status == ProjectStatus.BRAINSTORMING
    assert projects[0].telegram_chat_id == "12345"


@pytest.mark.asyncio
async def test_help_command_sends_instructions(db_session, mock_telegram_update, mock_context):
    """Test that /help command sends help text"""
    bot = OrchestratorTelegramBot(
        token="test_token",
        db_session_maker=lambda: db_session
    )

    await bot.help_command(mock_telegram_update, mock_context)

    # Check that help text was sent
    assert mock_telegram_update.message.reply_text.called
    call_args = mock_telegram_update.message.reply_text.call_args
    help_text = call_args[0][0]

    assert "Help" in help_text
    assert "/start" in help_text
    assert "/status" in help_text


@pytest.mark.asyncio
async def test_status_command_shows_workflow_state(db_session, mock_telegram_update, mock_context):
    """Test that /status command shows current workflow state"""
    # Create a project
    project = Project(
        name="Test Project",
        status=ProjectStatus.BRAINSTORMING,
        telegram_chat_id="12345"
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Set project ID in context
    mock_context.chat_data["project_id"] = str(project.id)

    bot = OrchestratorTelegramBot(
        token="test_token",
        db_session_maker=lambda: db_session
    )

    await bot.status_command(mock_telegram_update, mock_context)

    # Check that status was sent
    assert mock_telegram_update.message.reply_text.called
    call_args = mock_telegram_update.message.reply_text.call_args
    status_text = call_args[0][0]

    assert "Status" in status_text
    assert "Phase" in status_text


@pytest.mark.asyncio
async def test_handle_message_without_project(db_session, mock_telegram_update, mock_context):
    """Test handling message without active project"""
    bot = OrchestratorTelegramBot(
        token="test_token",
        db_session_maker=lambda: db_session
    )

    await bot.handle_message(mock_telegram_update, mock_context)

    # Should prompt to start
    assert mock_telegram_update.message.reply_text.called
    call_args = mock_telegram_update.message.reply_text.call_args
    response = call_args[0][0]

    assert "/start" in response


@pytest.mark.asyncio
async def test_handle_message_with_project(db_session, mock_telegram_update, mock_context):
    """Test handling message with active project"""
    # Create a project
    project = Project(
        name="Test Project",
        status=ProjectStatus.BRAINSTORMING,
        telegram_chat_id="12345"
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Set project ID in context
    mock_context.chat_data["project_id"] = str(project.id)

    bot = OrchestratorTelegramBot(
        token="test_token",
        db_session_maker=lambda: db_session
    )

    # Mock the orchestrator agent
    with patch("src.integrations.telegram_bot.run_orchestrator") as mock_orchestrator:
        mock_orchestrator.return_value = "Great idea! Tell me more about your task manager."

        # Mock completeness check
        with patch("src.integrations.telegram_bot.check_conversation_completeness") as mock_completeness:
            mock_completeness.return_value = AsyncMock(is_ready=False)

            await bot.handle_message(mock_telegram_update, mock_context)

            # Check that orchestrator was called
            assert mock_orchestrator.called

            # Check that response was sent
            assert mock_telegram_update.message.reply_text.called


@pytest.mark.asyncio
async def test_callback_generate_vision(db_session, mock_context):
    """Test vision generation callback"""
    # Create a project with conversation
    project = Project(
        name="Test Project",
        status=ProjectStatus.BRAINSTORMING,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Add some conversation messages
    from src.database.models import MessageRole
    from src.agent.tools import save_conversation_message

    await save_conversation_message(
        db_session, project.id, MessageRole.USER, "I want to build a task manager"
    )
    await save_conversation_message(
        db_session, project.id, MessageRole.ASSISTANT, "Tell me more"
    )

    # Set project ID in context
    mock_context.chat_data["project_id"] = str(project.id)

    # Create mock callback query
    query = AsyncMock()
    query.data = "generate_vision"
    query.message.reply_text = AsyncMock()
    query.edit_message_text = AsyncMock()

    update = MagicMock()
    update.callback_query = query

    bot = OrchestratorTelegramBot(
        token="test_token",
        db_session_maker=lambda: db_session
    )

    # Mock vision generation (since it requires completeness)
    with patch("src.integrations.telegram_bot.generate_vision_document") as mock_gen:
        from src.services.vision_generator import VisionDocument, Feature

        mock_vision = VisionDocument(
            what_it_is="A task manager",
            who_its_for=["Users"],
            problem_statement="Too many tasks",
            solution_overview="Organize them",
            key_features=[Feature(name="Tasks", description="Create tasks", priority="HIGH")],
            user_journey="User creates tasks",
            success_metrics=["100 users"],
            out_of_scope=["Mobile app"],
        )
        mock_gen.return_value = mock_vision

        await bot.handle_callback(update, mock_context)

        # Check that vision was generated
        assert query.edit_message_text.called or query.message.reply_text.called


def test_bot_initialization():
    """Test bot initialization"""
    bot = OrchestratorTelegramBot(
        token="test_token",
        db_session_maker=MagicMock()
    )

    assert bot.application is not None
    assert bot.db_session_maker is not None
