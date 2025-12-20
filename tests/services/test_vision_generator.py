"""
Tests for vision document generation service.
"""

import pytest
from unittest.mock import AsyncMock, patch

from src.database.models import MessageRole, Project, ProjectStatus
from src.services.vision_generator import (
    Feature,
    VisionDocument,
    check_conversation_completeness,
    extract_features,
    generate_vision_document,
    vision_document_to_dict,
    vision_document_to_markdown,
)
from src.agent.tools import save_conversation_message


@pytest.mark.asyncio
async def test_check_conversation_completeness_empty(db_session):
    """Test completeness check with no messages"""
    # Create a test project
    project = Project(
        name="Test Project",
        status=ProjectStatus.BRAINSTORMING,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Check completeness with empty conversation
    result = await check_conversation_completeness(db_session, project.id)

    assert result.is_ready is False
    assert result.next_question is not None
    assert "project" in result.next_question.lower()


@pytest.mark.asyncio
async def test_check_conversation_completeness_with_messages(db_session):
    """Test completeness check with conversation"""
    # Create a test project
    project = Project(
        name="Test Project",
        status=ProjectStatus.BRAINSTORMING,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Add conversation messages
    messages = [
        ("I want to build a task manager app", MessageRole.USER),
        ("Great! Who will use this app?", MessageRole.ASSISTANT),
        ("Busy professionals and students", MessageRole.USER),
        ("What features do you want?", MessageRole.ASSISTANT),
        ("Task creation, reminders, and prioritization", MessageRole.USER),
    ]

    for content, role in messages:
        await save_conversation_message(db_session, project.id, role, content)

    # Mock the agent response
    with patch("src.services.vision_generator.completeness_agent.run") as mock_run:
        mock_result = AsyncMock()
        mock_result.data.is_ready = False
        mock_result.data.next_question = "What problem does this solve?"
        mock_run.return_value = mock_result

        result = await check_conversation_completeness(db_session, project.id)

        assert mock_run.called


@pytest.mark.asyncio
async def test_extract_features(db_session):
    """Test feature extraction from conversation"""
    # Create a test project
    project = Project(
        name="Test Project",
        status=ProjectStatus.BRAINSTORMING,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Add conversation with features
    messages = [
        ("I need task creation and editing", MessageRole.USER),
        ("Also email reminders would be great", MessageRole.USER),
        ("And a dashboard to see everything", MessageRole.USER),
    ]

    for content, role in messages:
        await save_conversation_message(db_session, project.id, role, content)

    # Mock the agent response
    mock_features = [
        Feature(name="Task Management", description="Create and edit tasks", priority="HIGH"),
        Feature(name="Email Reminders", description="Send reminder emails", priority="MEDIUM"),
        Feature(name="Dashboard", description="Overview of all tasks", priority="HIGH"),
    ]

    with patch("src.services.vision_generator.feature_extraction_agent.run") as mock_run:
        mock_result = AsyncMock()
        mock_result.data = mock_features
        mock_run.return_value = mock_result

        features = await extract_features(db_session, project.id)

        assert len(features) == 3
        assert features[0].name == "Task Management"
        assert features[0].priority == "HIGH"


@pytest.mark.asyncio
async def test_generate_vision_document_not_ready(db_session):
    """Test vision generation fails when conversation not ready"""
    # Create a test project
    project = Project(
        name="Test Project",
        status=ProjectStatus.BRAINSTORMING,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Mock completeness check to return not ready
    with patch("src.services.vision_generator.completeness_agent.run") as mock_check:
        mock_result = AsyncMock()
        mock_result.data.is_ready = False
        mock_result.data.next_question = "What problem does this solve?"
        mock_check.return_value = mock_result

        with pytest.raises(ValueError, match="not ready"):
            await generate_vision_document(db_session, project.id)


@pytest.mark.asyncio
async def test_generate_vision_document_success(db_session):
    """Test successful vision document generation"""
    # Create a test project
    project = Project(
        name="Test Project",
        status=ProjectStatus.BRAINSTORMING,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Add conversation
    await save_conversation_message(
        db_session, project.id, MessageRole.USER, "I want to build a task manager"
    )

    # Mock completeness check to return ready
    with patch("src.services.vision_generator.completeness_agent.run") as mock_check:
        mock_check_result = AsyncMock()
        mock_check_result.data.is_ready = True
        mock_check.return_value = mock_check_result

        # Mock vision generation
        mock_vision = VisionDocument(
            what_it_is="A simple task management application",
            who_its_for=["Busy professionals", "Students"],
            problem_statement="People struggle to organize their tasks",
            solution_overview="A streamlined task manager with reminders",
            key_features=[
                Feature(name="Task Creation", description="Create tasks easily", priority="HIGH"),
            ],
            user_journey="User signs up, creates tasks, gets reminders",
            success_metrics=["100 active users in first month"],
            out_of_scope=["Mobile app", "Team collaboration"],
        )

        with patch("src.services.vision_generator.vision_generation_agent.run") as mock_gen:
            mock_gen_result = AsyncMock()
            mock_gen_result.data = mock_vision
            mock_gen.return_value = mock_gen_result

            vision = await generate_vision_document(db_session, project.id)

            assert vision.what_it_is == "A simple task management application"
            assert len(vision.who_its_for) == 2
            assert len(vision.key_features) == 1


def test_vision_document_to_markdown():
    """Test markdown conversion"""
    vision = VisionDocument(
        what_it_is="A task manager",
        who_its_for=["Professionals"],
        problem_statement="Too many tasks",
        solution_overview="Organize them better",
        key_features=[
            Feature(name="Tasks", description="Create tasks", priority="HIGH"),
        ],
        user_journey="User creates tasks",
        success_metrics=["100 users"],
        out_of_scope=["Mobile app"],
    )

    markdown = vision_document_to_markdown(vision)

    assert "# Project Vision Document" in markdown
    assert "## What It Is" in markdown
    assert "A task manager" in markdown
    assert "### Tasks (HIGH Priority)" in markdown
    assert "## Out of Scope" in markdown


def test_vision_document_to_dict():
    """Test dictionary conversion"""
    vision = VisionDocument(
        what_it_is="A task manager",
        who_its_for=["Professionals"],
        problem_statement="Too many tasks",
        solution_overview="Organize them better",
        key_features=[
            Feature(name="Tasks", description="Create tasks", priority="HIGH"),
        ],
        user_journey="User creates tasks",
        success_metrics=["100 users"],
        out_of_scope=["Mobile app"],
    )

    doc_dict = vision_document_to_dict(vision)

    assert doc_dict["what_it_is"] == "A task manager"
    assert len(doc_dict["key_features"]) == 1
    assert doc_dict["key_features"][0]["name"] == "Tasks"
    assert doc_dict["key_features"][0]["priority"] == "HIGH"
