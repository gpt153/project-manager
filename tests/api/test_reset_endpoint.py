"""
Tests for the /reset endpoint.
"""

from uuid import uuid4

import pytest
from fastapi import status

from src.database.models import Project, ProjectStatus
from src.services.topic_manager import create_new_topic, get_active_topic


@pytest.mark.asyncio
async def test_reset_endpoint_success(client, db_session):
    """Test that reset endpoint creates a new topic."""
    # Create a project
    project = Project(name="Test Project", status=ProjectStatus.BRAINSTORMING)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Create initial topic
    initial_topic = await create_new_topic(db_session, project.id, title="Initial Topic")
    await db_session.commit()

    # Call reset endpoint
    response = await client.post(f"/api/projects/{project.id}/reset")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["success"] is True
    assert "new_topic_id" in data
    assert data["previous_messages_preserved"] is True
    assert "reset successfully" in data["message"].lower()

    # Verify new topic was created and old one ended
    active_topic = await get_active_topic(db_session, project.id)
    assert active_topic is not None
    assert str(active_topic.id) == data["new_topic_id"]
    assert active_topic.id != initial_topic.id

    # Verify initial topic is no longer active
    await db_session.refresh(initial_topic)
    assert initial_topic.is_active is False
    assert initial_topic.ended_at is not None


@pytest.mark.asyncio
async def test_reset_endpoint_project_not_found(client, db_session):
    """Test that reset endpoint returns 404 for non-existent project."""
    non_existent_id = uuid4()

    response = await client.post(f"/api/projects/{non_existent_id}/reset")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_reset_endpoint_creates_topic_with_correct_title(client, db_session):
    """Test that reset endpoint creates topic with appropriate title."""
    # Create a project
    project = Project(name="Test Project", status=ProjectStatus.BRAINSTORMING)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Call reset endpoint
    response = await client.post(f"/api/projects/{project.id}/reset")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Verify the new topic has the correct title
    active_topic = await get_active_topic(db_session, project.id)
    assert active_topic is not None
    assert "Reset" in active_topic.topic_title
    assert "New Conversation" in active_topic.topic_title


@pytest.mark.asyncio
async def test_reset_endpoint_multiple_resets(client, db_session):
    """Test that multiple resets work correctly."""
    # Create a project
    project = Project(name="Test Project", status=ProjectStatus.BRAINSTORMING)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # First reset
    response1 = await client.post(f"/api/projects/{project.id}/reset")
    assert response1.status_code == status.HTTP_200_OK
    topic_id_1 = response1.json()["new_topic_id"]

    # Second reset
    response2 = await client.post(f"/api/projects/{project.id}/reset")
    assert response2.status_code == status.HTTP_200_OK
    topic_id_2 = response2.json()["new_topic_id"]

    # Verify different topics were created
    assert topic_id_1 != topic_id_2

    # Verify only the last topic is active
    active_topic = await get_active_topic(db_session, project.id)
    assert active_topic is not None
    assert str(active_topic.id) == topic_id_2
