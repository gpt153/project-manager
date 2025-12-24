"""
Tests for project service layer.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import ProjectStatus
from src.services.project_service import (
    add_message,
    create_project,
    get_all_projects,
    get_conversation_history,
    get_project_with_stats,
)


@pytest.mark.asyncio
async def test_create_project(test_session: AsyncSession):
    """Test creating a new project."""
    project = await create_project(test_session, name="Test Project", description="A test project")

    assert project.name == "Test Project"
    assert project.description == "A test project"
    assert project.status == ProjectStatus.BRAINSTORMING
    assert project.id is not None


@pytest.mark.asyncio
async def test_get_all_projects(test_session: AsyncSession):
    """Test retrieving all projects."""
    # Create test projects
    await create_project(test_session, name="Project 1")
    await create_project(test_session, name="Project 2")
    await test_session.commit()

    # Get all projects
    projects = await get_all_projects(test_session)

    assert len(projects) == 2
    assert projects[0]["name"] == "Project 2"  # Ordered by created_at desc
    assert projects[1]["name"] == "Project 1"


@pytest.mark.asyncio
async def test_get_project_with_stats(test_session: AsyncSession):
    """Test retrieving a project with statistics."""
    # Create a project
    project = await create_project(test_session, name="Test Project")
    await test_session.commit()

    # Get project with stats
    project_dict = await get_project_with_stats(test_session, project.id)

    assert project_dict is not None
    assert project_dict["name"] == "Test Project"
    assert project_dict["message_count"] == 0
    assert "phases" in project_dict


@pytest.mark.asyncio
async def test_add_message(test_session: AsyncSession):
    """Test adding a message to conversation history."""
    # Create a project
    project = await create_project(test_session, name="Test Project")
    await test_session.commit()

    # Add a message
    message = await add_message(
        test_session, project_id=project.id, role="USER", content="Hello, world!"
    )
    await test_session.commit()

    assert message.content == "Hello, world!"
    assert message.role.value == "USER"
    assert message.project_id == project.id


@pytest.mark.asyncio
async def test_get_conversation_history(test_session: AsyncSession):
    """Test retrieving conversation history."""
    # Create a project
    project = await create_project(test_session, name="Test Project")
    await test_session.commit()

    # Add messages
    await add_message(test_session, project.id, "USER", "Message 1")
    await add_message(test_session, project.id, "ASSISTANT", "Message 2")
    await test_session.commit()

    # Get conversation history
    messages = await get_conversation_history(test_session, project.id)

    assert len(messages) == 2
    assert messages[0]["content"] == "Message 1"
    assert messages[1]["content"] == "Message 2"
