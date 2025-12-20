"""
Tests for approval gate service.
"""

import pytest

from src.database.models import GateStatus, Project, ProjectStatus
from src.services.approval_gate import (
    ApprovalRequest,
    GateType,
    approve_gate,
    create_approval_gate,
    get_gate_history,
    get_pending_gates,
    reject_gate,
)


@pytest.mark.asyncio
async def test_create_approval_gate(db_session):
    """Test creating an approval gate"""
    # Create a test project
    project = Project(
        name="Test Project",
        status=ProjectStatus.BRAINSTORMING,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Create approval request
    request = ApprovalRequest(
        gate_type=GateType.VISION_DOC,
        title="Review Vision Document",
        summary="Please review the generated vision document",
        details={"doc_version": "1.0"},
        considerations="This will guide the entire project",
    )

    # Create gate
    gate = await create_approval_gate(
        db_session, project.id, GateType.VISION_DOC, request
    )

    assert gate.project_id == project.id
    assert gate.gate_type == "VISION_DOC"
    assert gate.status == GateStatus.PENDING
    assert gate.context["title"] == "Review Vision Document"
    assert gate.created_at is not None


@pytest.mark.asyncio
async def test_approve_gate(db_session):
    """Test approving a gate"""
    # Create project and gate
    project = Project(name="Test Project", status=ProjectStatus.BRAINSTORMING)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    request = ApprovalRequest(
        gate_type=GateType.VISION_DOC,
        title="Review",
        summary="Please review",
    )

    gate = await create_approval_gate(
        db_session, project.id, GateType.VISION_DOC, request
    )

    # Approve the gate
    approved = await approve_gate(db_session, gate.id, "Looks good!")

    assert approved.status == GateStatus.APPROVED
    assert approved.approver_notes == "Looks good!"
    assert approved.approved_at is not None


@pytest.mark.asyncio
async def test_reject_gate(db_session):
    """Test rejecting a gate"""
    # Create project and gate
    project = Project(name="Test Project", status=ProjectStatus.BRAINSTORMING)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    request = ApprovalRequest(
        gate_type=GateType.VISION_DOC,
        title="Review",
        summary="Please review",
    )

    gate = await create_approval_gate(
        db_session, project.id, GateType.VISION_DOC, request
    )

    # Reject the gate
    rejected = await reject_gate(db_session, gate.id, "Needs more detail")

    assert rejected.status == GateStatus.REJECTED
    assert rejected.approver_notes == "Needs more detail"
    assert rejected.approved_at is not None


@pytest.mark.asyncio
async def test_approve_already_approved_gate(db_session):
    """Test that approving an already approved gate raises error"""
    # Create project and gate
    project = Project(name="Test Project", status=ProjectStatus.BRAINSTORMING)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    request = ApprovalRequest(
        gate_type=GateType.VISION_DOC,
        title="Review",
        summary="Please review",
    )

    gate = await create_approval_gate(
        db_session, project.id, GateType.VISION_DOC, request
    )

    # Approve once
    await approve_gate(db_session, gate.id)

    # Try to approve again
    with pytest.raises(ValueError, match="already"):
        await approve_gate(db_session, gate.id)


@pytest.mark.asyncio
async def test_get_pending_gates(db_session):
    """Test retrieving pending gates"""
    # Create project
    project = Project(name="Test Project", status=ProjectStatus.BRAINSTORMING)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Create multiple gates
    request1 = ApprovalRequest(
        gate_type=GateType.VISION_DOC,
        title="Vision Review",
        summary="Review vision",
    )

    request2 = ApprovalRequest(
        gate_type=GateType.PHASE_START,
        title="Plan Review",
        summary="Review plan",
    )

    gate1 = await create_approval_gate(
        db_session, project.id, GateType.VISION_DOC, request1
    )

    gate2 = await create_approval_gate(
        db_session, project.id, GateType.PHASE_START, request2
    )

    # Approve one gate
    await approve_gate(db_session, gate1.id)

    # Get pending gates
    pending = await get_pending_gates(db_session, project.id)

    assert len(pending) == 1
    assert pending[0].id == gate2.id
    assert pending[0].status == GateStatus.PENDING


@pytest.mark.asyncio
async def test_get_gate_history(db_session):
    """Test retrieving gate history"""
    # Create project
    project = Project(name="Test Project", status=ProjectStatus.BRAINSTORMING)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Create gates with different statuses
    request1 = ApprovalRequest(
        gate_type=GateType.VISION_DOC,
        title="Vision",
        summary="Review",
    )

    request2 = ApprovalRequest(
        gate_type=GateType.PHASE_START,
        title="Plan",
        summary="Review",
    )

    gate1 = await create_approval_gate(
        db_session, project.id, GateType.VISION_DOC, request1
    )

    gate2 = await create_approval_gate(
        db_session, project.id, GateType.PHASE_START, request2
    )

    # Approve one, reject another
    await approve_gate(db_session, gate1.id)
    await reject_gate(db_session, gate2.id, "Not ready")

    # Get all history
    history = await get_gate_history(db_session, project.id)

    assert len(history) == 2
    assert history[0].status in [GateStatus.APPROVED, GateStatus.REJECTED]
    assert history[1].status in [GateStatus.APPROVED, GateStatus.REJECTED]
