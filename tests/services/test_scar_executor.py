"""
Tests for SCAR command execution service.
"""

import pytest

from src.database.models import ExecutionStatus, Project, ProjectStatus
from src.services.scar_executor import (
    ScarCommand,
    execute_scar_command,
    get_command_history,
    get_last_successful_command,
)


@pytest.mark.asyncio
async def test_execute_prime_command(db_session):
    """Test executing PRIME command"""
    # Create a test project with repo URL
    project = Project(
        name="Test Project",
        status=ProjectStatus.PLANNING,
        github_repo_url="https://github.com/test/repo",
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Execute PRIME command
    result = await execute_scar_command(
        db_session, project.id, ScarCommand.PRIME
    )

    assert result.success is True
    assert "Primed project context" in result.output
    assert result.error is None
    assert result.duration_seconds > 0


@pytest.mark.asyncio
async def test_execute_plan_command(db_session):
    """Test executing PLAN-FEATURE-GITHUB command"""
    # Create a test project
    project = Project(
        name="Test Feature",
        status=ProjectStatus.PLANNING,
        github_repo_url="https://github.com/test/repo",
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Execute PLAN command
    result = await execute_scar_command(
        db_session, project.id, ScarCommand.PLAN_FEATURE_GITHUB, args=["Test Feature"]
    )

    assert result.success is True
    assert "implementation plan" in result.output
    assert result.error is None


@pytest.mark.asyncio
async def test_execute_without_repo_url(db_session):
    """Test executing command on project without GitHub repo"""
    # Create project without repo URL
    project = Project(
        name="Test Project",
        status=ProjectStatus.BRAINSTORMING,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Execute command
    result = await execute_scar_command(
        db_session, project.id, ScarCommand.PRIME
    )

    assert result.success is False
    assert result.error is not None
    assert "github repo" in result.error.lower()


@pytest.mark.asyncio
async def test_get_command_history(db_session):
    """Test retrieving command execution history"""
    # Create a test project
    project = Project(
        name="Test Project",
        status=ProjectStatus.PLANNING,
        github_repo_url="https://github.com/test/repo",
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Execute multiple commands
    await execute_scar_command(db_session, project.id, ScarCommand.PRIME)
    await execute_scar_command(
        db_session, project.id, ScarCommand.PLAN_FEATURE_GITHUB, args=["Feature"]
    )

    # Get history
    history = await get_command_history(db_session, project.id, limit=10)

    assert len(history) == 2
    assert history[0].command_type.value in ["PRIME", "PLAN_FEATURE_GITHUB"]
    assert history[0].status == ExecutionStatus.COMPLETED


@pytest.mark.asyncio
async def test_get_last_successful_command(db_session):
    """Test getting last successful command of a specific type"""
    # Create a test project
    project = Project(
        name="Test Project",
        status=ProjectStatus.PLANNING,
        github_repo_url="https://github.com/test/repo",
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Execute command
    await execute_scar_command(db_session, project.id, ScarCommand.PRIME)

    # Get last successful PRIME
    from src.database.models import CommandType

    last_prime = await get_last_successful_command(
        db_session, project.id, CommandType.PRIME
    )

    assert last_prime is not None
    assert last_prime.command_type == CommandType.PRIME
    assert last_prime.status == ExecutionStatus.COMPLETED


@pytest.mark.asyncio
async def test_command_execution_tracking(db_session):
    """Test that command execution is properly tracked in database"""
    # Create a test project
    project = Project(
        name="Test Project",
        status=ProjectStatus.PLANNING,
        github_repo_url="https://github.com/test/repo",
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Execute command
    await execute_scar_command(db_session, project.id, ScarCommand.VALIDATE)

    # Check execution record was created
    history = await get_command_history(db_session, project.id, limit=1)

    assert len(history) == 1
    exec_record = history[0]
    assert exec_record.project_id == project.id
    assert exec_record.command_type.value == "VALIDATE"
    assert exec_record.started_at is not None
    assert exec_record.completed_at is not None
    assert exec_record.output is not None
