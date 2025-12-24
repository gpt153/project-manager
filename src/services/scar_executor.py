"""
SCAR Command Execution Service.

This service handles execution of SCAR commands (prime, plan-feature-github,
execute-github, validate) and manages the workflow automation.
"""

import asyncio
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import (
    CommandType,
    ExecutionStatus,
    Project,
    ScarCommandExecution,
)


class ScarCommand(str, Enum):
    """SCAR commands that can be executed"""

    PRIME = "prime"
    PLAN_FEATURE_GITHUB = "plan-feature-github"
    EXECUTE_GITHUB = "execute-github"
    VALIDATE = "validate"


class CommandResult(BaseModel):
    """Result of a SCAR command execution"""

    success: bool
    output: str
    error: Optional[str] = None
    duration_seconds: float


async def execute_scar_command(
    session: AsyncSession,
    project_id: UUID,
    command: ScarCommand,
    args: Optional[list[str]] = None,
    phase_id: Optional[UUID] = None,
) -> CommandResult:
    """
    Execute a SCAR command and track execution in database.

    Args:
        session: Database session
        project_id: Project UUID
        command: SCAR command to execute
        args: Optional command arguments
        phase_id: Optional workflow phase ID

    Returns:
        CommandResult: Execution result with output and status
    """
    # Get project to find repo path
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project or not project.github_repo_url:
        return CommandResult(
            success=False,
            output="",
            error="Project not found or no GitHub repo configured",
            duration_seconds=0.0,
        )

    # Create execution record
    # Build command args string
    args_str = " ".join(args) if args else ""

    execution = ScarCommandExecution(
        project_id=project_id,
        phase_id=phase_id,
        command_type=_command_to_type(command),
        command_args=args_str,
        status=ExecutionStatus.QUEUED,
        started_at=datetime.utcnow(),
    )
    session.add(execution)
    await session.commit()
    await session.refresh(execution)

    # Execute command
    start_time = datetime.utcnow()
    try:
        # Update status to running
        execution.status = ExecutionStatus.RUNNING
        await session.commit()

        # Build command
        cmd_parts = ["/command-invoke", command.value]
        if args:
            cmd_parts.extend(args)

        # Execute (this is a placeholder - real implementation would use SCAR API)
        # For now, we'll simulate execution
        output, error = await _simulate_scar_execution(command, args)

        # Calculate duration
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Update execution record
        execution.status = ExecutionStatus.COMPLETED if not error else ExecutionStatus.FAILED
        execution.completed_at = end_time
        execution.output = output
        if error:
            execution.error = error

        await session.commit()

        return CommandResult(
            success=not bool(error),
            output=output,
            error=error,
            duration_seconds=duration,
        )

    except Exception as e:
        # Mark as failed
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        execution.status = ExecutionStatus.FAILED
        execution.completed_at = end_time
        execution.error = str(e)
        await session.commit()

        return CommandResult(
            success=False,
            output="",
            error=str(e),
            duration_seconds=duration,
        )


async def _simulate_scar_execution(
    command: ScarCommand, args: Optional[list[str]] = None
) -> tuple[str, Optional[str]]:
    """
    Simulate SCAR command execution.

    In production, this would call the actual SCAR API or Claude Code integration.
    For now, we simulate with realistic responses.

    Args:
        command: SCAR command to simulate
        args: Optional command arguments

    Returns:
        tuple: (output, error) - error is None if successful
    """
    # Simulate execution time
    await asyncio.sleep(0.5)

    if command == ScarCommand.PRIME:
        return (
            "Primed project context successfully.\n"
            "Analyzed 127 files, loaded key dependencies and patterns.\n"
            "Ready for feature planning and implementation.",
            None,
        )

    elif command == ScarCommand.PLAN_FEATURE_GITHUB:
        feature_name = args[0] if args else "Feature"
        return (
            f"Created implementation plan for: {feature_name}\n"
            f"Plan includes 5 steps across 8 files.\n"
            f"Branch: feature/{feature_name.lower().replace(' ', '-')}\n"
            "Plan document saved to .agents/plans/",
            None,
        )

    elif command == ScarCommand.EXECUTE_GITHUB:
        return (
            "Executed implementation plan successfully.\n"
            "Modified 8 files, created 3 new files.\n"
            "All tests passing.\n"
            "Pull request created: #123",
            None,
        )

    elif command == ScarCommand.VALIDATE:
        return (
            "Validation complete.\n"
            "✓ All tests passing (127/127)\n"
            "✓ Code quality checks passed\n"
            "✓ No security issues found\n"
            "Ready for review and merge.",
            None,
        )

    return ("Unknown command", "Command not recognized")


def _command_to_type(command: ScarCommand) -> CommandType:
    """Convert ScarCommand enum to CommandType enum"""
    mapping = {
        ScarCommand.PRIME: CommandType.PRIME,
        ScarCommand.PLAN_FEATURE_GITHUB: CommandType.PLAN_FEATURE_GITHUB,
        ScarCommand.EXECUTE_GITHUB: CommandType.EXECUTE_GITHUB,
        ScarCommand.VALIDATE: CommandType.VALIDATE,
    }
    return mapping[command]


async def get_command_history(
    session: AsyncSession, project_id: UUID, limit: int = 10
) -> list[ScarCommandExecution]:
    """
    Get command execution history for a project.

    Args:
        session: Database session
        project_id: Project UUID
        limit: Maximum number of executions to return

    Returns:
        list[ScarCommandExecution]: Recent command executions
    """
    result = await session.execute(
        select(ScarCommandExecution)
        .where(ScarCommandExecution.project_id == project_id)
        .order_by(ScarCommandExecution.started_at.desc())
        .limit(limit)
    )

    return list(result.scalars().all())


async def get_last_successful_command(
    session: AsyncSession, project_id: UUID, command_type: CommandType
) -> Optional[ScarCommandExecution]:
    """
    Get the last successful execution of a specific command type.

    Args:
        session: Database session
        project_id: Project UUID
        command_type: Type of command to find

    Returns:
        Optional[ScarCommandExecution]: Last successful execution or None
    """
    result = await session.execute(
        select(ScarCommandExecution)
        .where(ScarCommandExecution.project_id == project_id)
        .where(ScarCommandExecution.command_type == command_type)
        .where(ScarCommandExecution.status == ExecutionStatus.COMPLETED)
        .order_by(ScarCommandExecution.completed_at.desc())
        .limit(1)
    )

    return result.scalar_one_or_none()
