"""
Approval Gate Service.

This service manages approval gates - points in the workflow where
user approval is required before proceeding.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import ApprovalGate, GateStatus, GateType


class ApprovalRequest(BaseModel):
    """Structured approval request for user"""

    gate_type: GateType
    title: str = Field(..., description="Clear title for the approval")
    summary: str = Field(..., description="What will happen if approved")
    details: dict = Field(
        default_factory=dict, description="Additional context or data"
    )
    considerations: Optional[str] = Field(
        None, description="Important considerations or warnings"
    )


async def create_approval_gate(
    session: AsyncSession,
    project_id: UUID,
    gate_type: GateType,
    request: ApprovalRequest,
) -> ApprovalGate:
    """
    Create a new approval gate.

    Args:
        session: Database session
        project_id: Project UUID
        gate_type: Type of approval gate
        request: Approval request details

    Returns:
        ApprovalGate: Created approval gate
    """
    gate = ApprovalGate(
        project_id=project_id,
        gate_type=gate_type.value,
        question=request.title,  # Using title as the question field
        status=GateStatus.PENDING,
        context={
            "title": request.title,
            "summary": request.summary,
            "details": request.details,
            "considerations": request.considerations,
        },
        created_at=datetime.utcnow(),
    )

    session.add(gate)
    await session.commit()
    await session.refresh(gate)

    return gate


async def approve_gate(
    session: AsyncSession, gate_id: UUID, approver_notes: Optional[str] = None
) -> ApprovalGate:
    """
    Approve an approval gate.

    Args:
        session: Database session
        gate_id: Approval gate UUID
        approver_notes: Optional notes from approver

    Returns:
        ApprovalGate: Updated approval gate
    """
    result = await session.execute(
        select(ApprovalGate).where(ApprovalGate.id == gate_id)
    )
    gate = result.scalar_one_or_none()

    if not gate:
        raise ValueError(f"Approval gate {gate_id} not found")

    if gate.status != GateStatus.PENDING:
        raise ValueError(f"Gate already {gate.status.value}")

    gate.status = GateStatus.APPROVED
    gate.approved_at = datetime.utcnow()
    if approver_notes:
        gate.approver_notes = approver_notes

    await session.commit()
    await session.refresh(gate)

    return gate


async def reject_gate(
    session: AsyncSession, gate_id: UUID, reason: str
) -> ApprovalGate:
    """
    Reject an approval gate.

    Args:
        session: Database session
        gate_id: Approval gate UUID
        reason: Reason for rejection

    Returns:
        ApprovalGate: Updated approval gate
    """
    result = await session.execute(
        select(ApprovalGate).where(ApprovalGate.id == gate_id)
    )
    gate = result.scalar_one_or_none()

    if not gate:
        raise ValueError(f"Approval gate {gate_id} not found")

    if gate.status != GateStatus.PENDING:
        raise ValueError(f"Gate already {gate.status.value}")

    gate.status = GateStatus.REJECTED
    gate.approved_at = datetime.utcnow()
    gate.approver_notes = reason

    await session.commit()
    await session.refresh(gate)

    return gate


async def get_pending_gates(
    session: AsyncSession, project_id: UUID
) -> list[ApprovalGate]:
    """
    Get all pending approval gates for a project.

    Args:
        session: Database session
        project_id: Project UUID

    Returns:
        list[ApprovalGate]: List of pending gates
    """
    result = await session.execute(
        select(ApprovalGate)
        .where(ApprovalGate.project_id == project_id)
        .where(ApprovalGate.status == GateStatus.PENDING)
        .order_by(ApprovalGate.created_at.asc())
    )

    return list(result.scalars().all())


async def get_gate_history(
    session: AsyncSession, project_id: UUID
) -> list[ApprovalGate]:
    """
    Get all approval gates for a project (including completed ones).

    Args:
        session: Database session
        project_id: Project UUID

    Returns:
        list[ApprovalGate]: List of all gates
    """
    result = await session.execute(
        select(ApprovalGate)
        .where(ApprovalGate.project_id == project_id)
        .order_by(ApprovalGate.created_at.desc())
    )

    return list(result.scalars().all())
