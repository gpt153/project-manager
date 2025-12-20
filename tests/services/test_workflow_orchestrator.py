"""
Tests for workflow orchestration service.
"""

import pytest

from src.database.models import GateStatus, PhaseStatus, Project, ProjectStatus
from src.services.approval_gate import ApprovalRequest, create_approval_gate
from src.services.workflow_orchestrator import (
    advance_workflow,
    get_workflow_state,
    handle_approval_response,
    reset_workflow,
)


@pytest.mark.asyncio
async def test_get_workflow_state_brainstorming(db_session):
    """Test workflow state during brainstorming"""
    # Create project in brainstorming
    project = Project(
        name="Test Project",
        status=ProjectStatus.BRAINSTORMING,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Get state
    state = await get_workflow_state(db_session, project.id)

    assert state.current_phase == "Brainstorming"
    assert "requirements" in state.next_action.lower()
    assert state.awaiting_approval is False


@pytest.mark.asyncio
async def test_get_workflow_state_vision_review(db_session):
    """Test workflow state during vision review"""
    # Create project in vision review
    project = Project(
        name="Test Project",
        status=ProjectStatus.VISION_REVIEW,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Get state
    state = await get_workflow_state(db_session, project.id)

    assert state.current_phase == "Vision Document Review"
    assert state.awaiting_approval is True


@pytest.mark.asyncio
async def test_advance_workflow_creates_phase(db_session):
    """Test that advancing workflow creates workflow phases"""
    # Create project with GitHub repo
    project = Project(
        name="Test Project",
        status=ProjectStatus.PLANNING,
        github_repo_url="https://github.com/test/repo",
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Advance workflow
    success, message = await advance_workflow(db_session, project.id)

    assert success is True
    assert "approval gate" in message.lower() or "phase" in message.lower()

    # Check that phase was created
    from sqlalchemy import select
    from src.database.models import WorkflowPhase

    result = await db_session.execute(
        select(WorkflowPhase).where(WorkflowPhase.project_id == project.id)
    )
    phases = list(result.scalars().all())

    assert len(phases) > 0


@pytest.mark.asyncio
async def test_handle_approval_response_approved(db_session):
    """Test handling approval gate approval"""
    # Create project
    project = Project(
        name="Test Project",
        status=ProjectStatus.VISION_REVIEW,
        github_repo_url="https://github.com/test/repo",
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Create approval gate
    from src.database.models import GateType

    request = ApprovalRequest(
        gate_type=GateType.VISION_DOC,
        title="Approve Vision",
        summary="Review vision document",
    )

    gate = await create_approval_gate(
        db_session, project.id, GateType.VISION_DOC, request
    )

    # Handle approval
    success, message = await handle_approval_response(
        db_session, gate.id, approved=True, notes="Looks great!"
    )

    assert success is True
    assert "approval granted" in message.lower() or "continuing" in message.lower()

    # Verify gate was approved
    await db_session.refresh(gate)
    assert gate.status == GateStatus.APPROVED
    assert gate.approver_notes == "Looks great!"


@pytest.mark.asyncio
async def test_handle_approval_response_rejected(db_session):
    """Test handling approval gate rejection"""
    # Create project
    project = Project(
        name="Test Project",
        status=ProjectStatus.VISION_REVIEW,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Create approval gate
    from src.database.models import GateType

    request = ApprovalRequest(
        gate_type=GateType.VISION_DOC,
        title="Approve Vision",
        summary="Review vision document",
    )

    gate = await create_approval_gate(
        db_session, project.id, GateType.VISION_DOC, request
    )

    # Handle rejection
    success, message = await handle_approval_response(
        db_session, gate.id, approved=False, notes="Needs more detail"
    )

    assert success is False
    assert "rejected" in message.lower()

    # Verify gate was rejected
    await db_session.refresh(gate)
    assert gate.status == GateStatus.REJECTED
    assert gate.approver_notes == "Needs more detail"


@pytest.mark.asyncio
async def test_reset_workflow(db_session):
    """Test resetting workflow to brainstorming"""
    # Create project in advanced state
    project = Project(
        name="Test Project",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Reset workflow
    success = await reset_workflow(db_session, project.id)

    assert success is True

    # Verify project is back to brainstorming
    await db_session.refresh(project)
    assert project.status == ProjectStatus.BRAINSTORMING


@pytest.mark.asyncio
async def test_workflow_state_with_phases(db_session):
    """Test workflow state tracking across phases"""
    # Create project with GitHub repo
    project = Project(
        name="Test Project",
        status=ProjectStatus.PLANNING,
        github_repo_url="https://github.com/test/repo",
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Create a completed phase
    from src.database.models import WorkflowPhase

    phase = WorkflowPhase(
        project_id=project.id,
        phase_number=2,
        name="Prime Context",
        description="Load project context",
        scar_command="prime",
        status=PhaseStatus.COMPLETED,
    )
    db_session.add(phase)
    await db_session.commit()

    # Get workflow state
    state = await get_workflow_state(db_session, project.id)

    assert state.current_phase == "Planning"
    # Should suggest next SCAR command
    assert "plan" in state.next_action.lower() or "feature" in state.next_action.lower()
