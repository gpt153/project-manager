"""
Tests for the orchestrator agent.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agent.orchestrator_agent import orchestrator_agent, run_orchestrator
from src.agent.tools import AgentDependencies
from src.database.models import Project, ProjectStatus


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
