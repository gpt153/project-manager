"""
SCAR Command Execution Service.

This service handles execution of SCAR commands (prime, plan-feature-github,
execute-github, validate) and manages the workflow automation.
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

import httpx
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.database.models import (
    CommandType,
    ExecutionStatus,
    Project,
    ScarCommandExecution,
)
from src.scar.client import ScarClient

logger = logging.getLogger(__name__)


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

        # Initialize SCAR client
        client = ScarClient(settings)

        # Send command to SCAR
        logger.info(
            f"Executing SCAR command: {command.value}",
            extra={"project_id": str(project_id), "command": command.value, "command_args": args},
        )

        conversation_id = await client.send_command(
            project_id, command.value, args, github_repo_url=project.github_repo_url
        )

        # Wait for completion
        logger.info(
            "Polling SCAR for command completion",
            extra={"conversation_id": conversation_id, "timeout": settings.scar_timeout_seconds},
        )

        messages = await client.wait_for_completion(
            conversation_id, timeout=settings.scar_timeout_seconds
        )

        # Aggregate output from all messages
        output = "\n".join(msg.message for msg in messages)

        # Calculate duration
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Update execution record
        execution.status = ExecutionStatus.COMPLETED
        execution.completed_at = end_time
        execution.output = output

        await session.commit()

        logger.info(
            "SCAR command completed successfully",
            extra={
                "project_id": str(project_id),
                "command": command.value,
                "duration": duration,
                "message_count": len(messages),
            },
        )

        return CommandResult(
            success=True,
            output=output,
            error=None,
            duration_seconds=duration,
        )

    except httpx.ConnectError as e:
        # SCAR not running
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        error_msg = f"SCAR is not available. Ensure SCAR is running at {settings.scar_base_url}"

        logger.error(
            f"SCAR connection failed: {error_msg}",
            extra={"project_id": str(project_id), "command": command.value, "error": str(e)},
        )

        execution.status = ExecutionStatus.FAILED
        execution.completed_at = end_time
        execution.error = error_msg
        await session.commit()

        return CommandResult(
            success=False,
            output="",
            error=error_msg,
            duration_seconds=duration,
        )

    except TimeoutError as e:
        # Command timed out
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        error_msg = f"SCAR command timed out after {duration:.1f}s: {str(e)}"

        logger.error(
            "SCAR command timeout",
            extra={"project_id": str(project_id), "command": command.value, "duration": duration},
        )

        execution.status = ExecutionStatus.FAILED
        execution.completed_at = end_time
        execution.error = error_msg
        await session.commit()

        return CommandResult(
            success=False,
            output="",
            error=error_msg,
            duration_seconds=duration,
        )

    except Exception as e:
        # Generic error
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        error_msg = f"SCAR command failed: {str(e)}"

        logger.error(
            "SCAR command failed with exception",
            extra={
                "project_id": str(project_id),
                "command": command.value,
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )

        execution.status = ExecutionStatus.FAILED
        execution.completed_at = end_time
        execution.error = error_msg
        await session.commit()

        return CommandResult(
            success=False,
            output="",
            error=error_msg,
            duration_seconds=duration,
        )


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
