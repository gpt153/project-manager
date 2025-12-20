"""
Tests for agent tools.
"""

import pytest
from uuid import uuid4

from src.agent.tools import (
    get_conversation_history,
    get_project,
    save_conversation_message,
    update_project_status,
    update_project_vision,
)
from src.database.models import MessageRole, Project, ProjectStatus


@pytest.mark.asyncio
async def test_save_conversation_message(db_session):
    """Test saving a conversation message"""
    # Create a test project
    project = Project(
        name="Test Project",
        status=ProjectStatus.BRAINSTORMING,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Save a message
    message = await save_conversation_message(
        db_session, project.id, MessageRole.USER, "Hello, I want to build an app"
    )

    assert message.project_id == project.id
    assert message.role == MessageRole.USER
    assert message.content == "Hello, I want to build an app"
    assert message.timestamp is not None


@pytest.mark.asyncio
async def test_get_project(db_session):
    """Test retrieving a project"""
    # Create a test project
    project = Project(
        name="Test Project",
        description="A test project",
        status=ProjectStatus.BRAINSTORMING,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Retrieve the project
    retrieved = await get_project(db_session, project.id)

    assert retrieved is not None
    assert retrieved.id == project.id
    assert retrieved.name == "Test Project"
    assert retrieved.description == "A test project"


@pytest.mark.asyncio
async def test_get_project_not_found(db_session):
    """Test retrieving a non-existent project"""
    result = await get_project(db_session, uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_update_project_status(db_session):
    """Test updating project status"""
    # Create a test project
    project = Project(
        name="Test Project",
        status=ProjectStatus.BRAINSTORMING,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Update status
    updated = await update_project_status(db_session, project.id, ProjectStatus.PLANNING)

    assert updated.status == ProjectStatus.PLANNING
    assert updated.updated_at > project.created_at


@pytest.mark.asyncio
async def test_get_conversation_history(db_session):
    """Test retrieving conversation history"""
    # Create a test project
    project = Project(
        name="Test Project",
        status=ProjectStatus.BRAINSTORMING,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Add some messages
    messages_data = [
        ("Hello", MessageRole.USER),
        ("Hi! What would you like to build?", MessageRole.ASSISTANT),
        ("I want to build a task manager", MessageRole.USER),
    ]

    for content, role in messages_data:
        await save_conversation_message(db_session, project.id, role, content)

    # Retrieve history
    history = await get_conversation_history(db_session, project.id)

    assert len(history) == 3
    assert history[0].content == "Hello"
    assert history[1].role == MessageRole.ASSISTANT
    assert history[2].content == "I want to build a task manager"


@pytest.mark.asyncio
async def test_update_project_vision(db_session):
    """Test updating project vision document"""
    # Create a test project
    project = Project(
        name="Test Project",
        status=ProjectStatus.BRAINSTORMING,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Update vision
    vision_doc = {
        "title": "Task Manager App",
        "what_it_is": "A simple task manager for busy people",
        "who_its_for": ["Busy professionals", "Students"],
    }

    updated = await update_project_vision(db_session, project.id, vision_doc)

    assert updated.vision_document == vision_doc
    assert updated.vision_document["title"] == "Task Manager App"
