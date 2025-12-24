"""
Workflow Orchestration Service.

This service manages the complete PIV loop workflow:
Prime → Investigate/Plan → Validate

It coordinates SCAR commands, approval gates, and phase transitions.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import (
    GateStatus,
    GateType,
    PhaseStatus,
    Project,
    ProjectStatus,
    WorkflowPhase,
)
from src.services.approval_gate import ApprovalRequest, create_approval_gate
from src.services.scar_executor import (
    ScarCommand,
    execute_scar_command,
)


class WorkflowState(BaseModel):
    """Current state of the workflow"""

    current_phase: str
    next_action: str
    awaiting_approval: bool = False
    pending_approval_id: Optional[UUID] = None


class PhaseConfig(BaseModel):
    """Configuration for a workflow phase"""

    number: int
    name: str
    description: str
    scar_command: Optional[ScarCommand] = None
    requires_approval: bool = False
    approval_gate_type: Optional[GateType] = None


# Define the standard PIV workflow phases
WORKFLOW_PHASES = [
    PhaseConfig(
        number=1,
        name="Vision Document Review",
        description="Review and approve the generated vision document",
        scar_command=None,
        requires_approval=True,
        approval_gate_type=GateType.VISION_DOC,
    ),
    PhaseConfig(
        number=2,
        name="Prime Context",
        description="Load complete project context into SCAR",
        scar_command=ScarCommand.PRIME,
        requires_approval=False,
    ),
    PhaseConfig(
        number=3,
        name="Plan Feature",
        description="Create detailed implementation plan",
        scar_command=ScarCommand.PLAN_FEATURE_GITHUB,
        requires_approval=True,
        approval_gate_type=GateType.PHASE_START,
    ),
    PhaseConfig(
        number=4,
        name="Execute Implementation",
        description="Implement the planned feature",
        scar_command=ScarCommand.EXECUTE_GITHUB,
        requires_approval=False,
    ),
    PhaseConfig(
        number=5,
        name="Validate & Test",
        description="Run tests and validate implementation",
        scar_command=ScarCommand.VALIDATE,
        requires_approval=True,
        approval_gate_type=GateType.PHASE_COMPLETE,
    ),
]


async def get_workflow_state(session: AsyncSession, project_id: UUID) -> WorkflowState:
    """
    Get the current workflow state for a project.

    Args:
        session: Database session
        project_id: Project UUID

    Returns:
        WorkflowState: Current workflow state and next action
    """
    # Get project
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise ValueError(f"Project {project_id} not found")

    # Get current phase
    phase_result = await session.execute(
        select(WorkflowPhase)
        .where(WorkflowPhase.project_id == project_id)
        .order_by(WorkflowPhase.phase_number.desc())
        .limit(1)
    )
    current_phase = phase_result.scalar_one_or_none()

    # Determine state based on project status
    if project.status == ProjectStatus.BRAINSTORMING:
        return WorkflowState(
            current_phase="Brainstorming",
            next_action="Continue conversation to gather requirements",
            awaiting_approval=False,
        )

    elif project.status == ProjectStatus.VISION_REVIEW:
        return WorkflowState(
            current_phase="Vision Document Review",
            next_action="Awaiting user approval of vision document",
            awaiting_approval=True,
        )

    elif project.status == ProjectStatus.PLANNING:
        if not current_phase:
            return WorkflowState(
                current_phase="Planning",
                next_action="Execute PRIME command to load context",
                awaiting_approval=False,
            )
        elif current_phase.phase_number == 2 and current_phase.status == PhaseStatus.COMPLETED:
            return WorkflowState(
                current_phase="Planning",
                next_action="Execute PLAN-FEATURE-GITHUB command",
                awaiting_approval=False,
            )
        else:
            return WorkflowState(
                current_phase="Planning",
                next_action="Awaiting plan approval",
                awaiting_approval=True,
            )

    elif project.status == ProjectStatus.IN_PROGRESS:
        if current_phase and current_phase.phase_number == 4:
            return WorkflowState(
                current_phase="Implementation",
                next_action="Execute VALIDATE command",
                awaiting_approval=False,
            )
        else:
            return WorkflowState(
                current_phase="Implementation",
                next_action="Execute EXECUTE-GITHUB command",
                awaiting_approval=False,
            )

    elif project.status == ProjectStatus.COMPLETED:
        return WorkflowState(
            current_phase="Completed",
            next_action="Project implementation complete!",
            awaiting_approval=False,
        )

    # Default fallback
    return WorkflowState(
        current_phase=project.status.value,
        next_action="Determine next workflow step",
        awaiting_approval=False,
    )


async def advance_workflow(session: AsyncSession, project_id: UUID) -> tuple[bool, str]:
    """
    Advance the workflow to the next phase.

    This automatically determines the next action and executes it.

    Args:
        session: Database session
        project_id: Project UUID

    Returns:
        tuple: (success, message) - success flag and status message
    """
    # Get current state
    await get_workflow_state(session, project_id)

    # Get project
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        return False, "Project not found"

    # Get current phase number
    phase_result = await session.execute(
        select(WorkflowPhase)
        .where(WorkflowPhase.project_id == project_id)
        .order_by(WorkflowPhase.phase_number.desc())
        .limit(1)
    )
    current_phase = phase_result.scalar_one_or_none()
    next_phase_number = (current_phase.phase_number + 1) if current_phase else 1

    # Find next phase configuration
    next_phase_config = next((p for p in WORKFLOW_PHASES if p.number == next_phase_number), None)

    if not next_phase_config:
        # Workflow complete
        project.status = ProjectStatus.COMPLETED
        await session.commit()
        return True, "Workflow completed successfully!"

    # Create workflow phase record
    workflow_phase = WorkflowPhase(
        project_id=project_id,
        phase_number=next_phase_config.number,
        name=next_phase_config.name,
        description=next_phase_config.description,
        scar_command=(
            next_phase_config.scar_command.value if next_phase_config.scar_command else None
        ),
        status=PhaseStatus.PENDING,
    )
    session.add(workflow_phase)
    await session.commit()
    await session.refresh(workflow_phase)

    # If phase requires approval, create approval gate
    if next_phase_config.requires_approval:
        approval_request = ApprovalRequest(
            gate_type=next_phase_config.approval_gate_type,
            title=f"Approve: {next_phase_config.name}",
            summary=next_phase_config.description,
        )

        await create_approval_gate(
            session, project_id, next_phase_config.approval_gate_type, approval_request
        )

        workflow_phase.status = PhaseStatus.BLOCKED
        await session.commit()

        return True, f"Created approval gate for: {next_phase_config.name}"

    # If phase has a SCAR command, execute it
    if next_phase_config.scar_command:
        workflow_phase.status = PhaseStatus.IN_PROGRESS
        workflow_phase.started_at = datetime.utcnow()
        await session.commit()

        # Prepare command arguments
        args = []
        if next_phase_config.scar_command == ScarCommand.PLAN_FEATURE_GITHUB:
            # Use project name as feature name
            args = [project.name]

        # Execute command
        result = await execute_scar_command(
            session,
            project_id,
            next_phase_config.scar_command,
            args,
            workflow_phase.id,
        )

        if result.success:
            workflow_phase.status = PhaseStatus.COMPLETED
            workflow_phase.completed_at = datetime.utcnow()
            await session.commit()

            return True, f"Completed phase: {next_phase_config.name}\n{result.output}"
        else:
            workflow_phase.status = PhaseStatus.FAILED
            workflow_phase.error_message = result.error
            await session.commit()

            return False, f"Phase failed: {result.error}"

    return True, f"Advanced to phase: {next_phase_config.name}"


async def handle_approval_response(
    session: AsyncSession, gate_id: UUID, approved: bool, notes: Optional[str] = None
) -> tuple[bool, str]:
    """
    Handle user response to an approval gate and continue workflow.

    Args:
        session: Database session
        gate_id: Approval gate UUID
        approved: Whether the gate was approved
        notes: Optional notes from user

    Returns:
        tuple: (success, message) - success flag and status message
    """
    # Get the approval gate to find project
    from src.database.models import ApprovalGate
    from src.services.approval_gate import approve_gate, reject_gate

    result = await session.execute(select(ApprovalGate).where(ApprovalGate.id == gate_id))
    gate = result.scalar_one_or_none()

    if not gate:
        return False, "Approval gate not found"

    if gate.status != GateStatus.PENDING:
        return False, f"Gate already {gate.status.value}"

    project_id = gate.project_id

    # Approve or reject
    if approved:
        await approve_gate(session, gate_id, notes)
        message = "Approval granted. Continuing workflow..."

        # Continue to next phase
        success, phase_message = await advance_workflow(session, project_id)
        return success, f"{message}\n{phase_message}"
    else:
        await reject_gate(session, gate_id, notes or "User rejected")
        return False, "Approval rejected. Workflow paused."


async def reset_workflow(session: AsyncSession, project_id: UUID) -> bool:
    """
    Reset the workflow to the beginning.

    Args:
        session: Database session
        project_id: Project UUID

    Returns:
        bool: Success flag
    """
    # Update project status
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        return False

    project.status = ProjectStatus.BRAINSTORMING
    await session.commit()

    return True
