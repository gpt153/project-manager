"""
Project Manager PydanticAI Agent.

This module implements the conversational AI agent that orchestrates
software development workflows for non-technical users.
"""

from uuid import UUID

from pydantic_ai import Agent, RunContext

from src.agent.prompts import ORCHESTRATOR_SYSTEM_PROMPT
from src.agent.tools import (
    AgentDependencies,
    get_conversation_history,
    get_project,
    save_conversation_message,
    update_project_status,
    update_project_vision,
)
from src.database.models import MessageRole, ProjectStatus
from src.services.scar_executor import (
    ScarCommand,
    execute_scar_command,
    get_command_history,
)
from src.services.workflow_orchestrator import advance_workflow, get_workflow_state


# Dynamic system prompt that injects project context
async def build_system_prompt(ctx: RunContext[AgentDependencies]) -> str:
    """
    Build system prompt with current project context injected.

    This allows PM to be context-aware of the current project.
    """
    # Get project context
    project = None
    if ctx.deps.project_id:
        project = await get_project(ctx.deps.session, ctx.deps.project_id)

    # Build context variables
    context_vars = {
        "project_name": project.name if project else "No project selected",
        "github_repo_url": (
            project.github_repo_url if project and project.github_repo_url else "Not configured"
        ),
        "project_status": project.status.value if project else "Unknown",
        "project_description": (
            project.description if project and project.description else "No description"
        ),
    }

    # Format system prompt with context
    return ORCHESTRATOR_SYSTEM_PROMPT.format(**context_vars)


# Initialize the PydanticAI agent
# Note: Uses ANTHROPIC_API_KEY environment variable
orchestrator_agent = Agent(
    model="anthropic:claude-sonnet-4-20250514",
    deps_type=AgentDependencies,
    system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,  # Will format dynamically in run_orchestrator
    retries=2,
)


@orchestrator_agent.tool
async def save_message(ctx: RunContext[AgentDependencies], role: str, content: str) -> str:
    """
    Save a conversation message to the database.

    Args:
        ctx: Agent context with dependencies
        role: Message role (user, assistant, system)
        content: Message content

    Returns:
        str: Confirmation message
    """
    if not ctx.deps.project_id:
        return "Error: No active project"

    # Convert role string to enum
    role_enum = MessageRole[role.upper()]

    await save_conversation_message(ctx.deps.session, ctx.deps.project_id, role_enum, content)

    return f"Message saved as {role}"


@orchestrator_agent.tool
async def get_project_context(ctx: RunContext[AgentDependencies]) -> dict:
    """
    Retrieve current project context.

    Args:
        ctx: Agent context with dependencies

    Returns:
        dict: Project information
    """
    if not ctx.deps.project_id:
        return {"error": "No active project"}

    project = await get_project(ctx.deps.session, ctx.deps.project_id)

    if not project:
        return {"error": "Project not found"}

    return {
        "id": str(project.id),
        "name": project.name,
        "description": project.description,
        "status": project.status.value,
        "github_repo_url": project.github_repo_url,
        "telegram_chat_id": project.telegram_chat_id,
        "has_vision_document": project.vision_document is not None,
        "created_at": project.created_at.isoformat(),
        "updated_at": project.updated_at.isoformat(),
    }


@orchestrator_agent.tool
async def get_conversation(ctx: RunContext[AgentDependencies], limit: int = 20) -> list[dict]:
    """
    Retrieve conversation history.

    Args:
        ctx: Agent context with dependencies
        limit: Maximum number of messages

    Returns:
        list[dict]: List of messages
    """
    if not ctx.deps.project_id:
        return [{"error": "No active project"}]

    messages = await get_conversation_history(ctx.deps.session, ctx.deps.project_id, limit)

    return [
        {
            "role": msg.role.value,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat(),
        }
        for msg in messages
    ]


@orchestrator_agent.tool
async def update_status(ctx: RunContext[AgentDependencies], new_status: str) -> str:
    """
    Update project status.

    Args:
        ctx: Agent context with dependencies
        new_status: New status (BRAINSTORMING, VISION_REVIEW, etc.)

    Returns:
        str: Confirmation message
    """
    if not ctx.deps.project_id:
        return "Error: No active project"

    try:
        status_enum = ProjectStatus[new_status.upper()]
        await update_project_status(ctx.deps.session, ctx.deps.project_id, status_enum)
        return f"Project status updated to {new_status}"
    except KeyError:
        return f"Error: Invalid status '{new_status}'"


@orchestrator_agent.tool
async def save_vision_document(ctx: RunContext[AgentDependencies], vision_doc: dict) -> str:
    """
    Save vision document to project.

    Args:
        ctx: Agent context with dependencies
        vision_doc: Vision document as dictionary

    Returns:
        str: Confirmation message
    """
    if not ctx.deps.project_id:
        return "Error: No active project"

    await update_project_vision(ctx.deps.session, ctx.deps.project_id, vision_doc)

    return "Vision document saved successfully"


@orchestrator_agent.tool
async def get_workflow_status(ctx: RunContext[AgentDependencies]) -> dict:
    """
    Get current workflow status and next action.

    Args:
        ctx: Agent context with dependencies

    Returns:
        dict: Workflow state information
    """
    if not ctx.deps.project_id:
        return {"error": "No active project"}

    state = await get_workflow_state(ctx.deps.session, ctx.deps.project_id)

    return {
        "current_phase": state.current_phase,
        "next_action": state.next_action,
        "awaiting_approval": state.awaiting_approval,
    }


@orchestrator_agent.tool
async def continue_workflow(ctx: RunContext[AgentDependencies]) -> str:
    """
    Advance the workflow to the next phase.

    This automatically executes the next SCAR command or creates an approval gate.

    Args:
        ctx: Agent context with dependencies

    Returns:
        str: Status message about what was done
    """
    if not ctx.deps.project_id:
        return "Error: No active project"

    success, message = await advance_workflow(ctx.deps.session, ctx.deps.project_id)

    return message if success else f"Error: {message}"


@orchestrator_agent.tool
async def get_scar_history(
    ctx: RunContext[AgentDependencies], limit: int = 5, only_recent: bool = True
) -> list[dict]:
    """
    Get SCAR command execution history.

    ⚠️ IMPORTANT: Only call this when:
    - User explicitly asks about SCAR status
    - User asks "what has SCAR done?"
    - You need to check if a command completed

    DO NOT call this automatically for context. It may contain old, irrelevant information.

    Args:
        ctx: Agent context with dependencies
        limit: Maximum number of executions to return
        only_recent: Only return executions from last 30 minutes (default: True)

    Returns:
        list[dict]: Recent command executions
    """
    if not ctx.deps.project_id:
        return [{"error": "No active project"}]

    history = await get_command_history(ctx.deps.session, ctx.deps.project_id, limit)

    # Filter by recency if requested
    if only_recent:
        from datetime import datetime, timedelta, timezone

        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=30)

        history = [
            exec
            for exec in history
            if exec.started_at and exec.started_at.replace(tzinfo=timezone.utc) > cutoff_time
        ]

    return [
        {
            "command_type": exec.command_type.value,
            "command_args": exec.command_args,
            "status": exec.status.value,
            "started_at": exec.started_at.isoformat() if exec.started_at else None,
            "completed_at": exec.completed_at.isoformat() if exec.completed_at else None,
            "output": exec.output[:200] if exec.output else None,  # Truncate for readability
            "error": exec.error,
        }
        for exec in history
    ]


@orchestrator_agent.tool
async def execute_scar(
    ctx: RunContext[AgentDependencies], command: str, args: list[str] | None = None
) -> dict:
    """
    Execute a SCAR command directly.

    This tool allows you to run SCAR commands to perform development workflows:
    - prime: Load codebase understanding
    - plan-feature-github: Create implementation plan
    - execute-github: Implement from plan
    - validate: Run tests and validation

    Args:
        ctx: Agent context with dependencies
        command: SCAR command name (prime, plan-feature-github, execute-github, validate)
        args: Optional command arguments (e.g., feature description for planning)

    Returns:
        dict: Execution result with success, output, error, and duration
    """
    if not ctx.deps.project_id:
        return {"success": False, "error": "No active project"}

    # Map string commands to ScarCommand enum
    command_map = {
        "prime": ScarCommand.PRIME,
        "plan-feature-github": ScarCommand.PLAN_FEATURE_GITHUB,
        "execute-github": ScarCommand.EXECUTE_GITHUB,
        "validate": ScarCommand.VALIDATE,
    }

    scar_cmd = command_map.get(command.lower())
    if not scar_cmd:
        return {
            "success": False,
            "error": f"Invalid command: {command}. Valid commands: {list(command_map.keys())}",
        }

    # Execute via scar_executor
    result = await execute_scar_command(ctx.deps.session, ctx.deps.project_id, scar_cmd, args or [])

    return {
        "success": result.success,
        "output": result.output,
        "error": result.error,
        "duration_seconds": result.duration_seconds,
    }


def detect_topic_change(messages: list, current_message: str) -> bool:
    """
    Detect if conversation topic has changed based on explicit signals.

    Args:
        messages: Recent conversation history
        current_message: Current user message to analyze

    Returns:
        True if topic change detected, False otherwise
    """
    # Check for explicit topic corrections
    correction_phrases = [
        "but we weren't discussing",
        "but we werent discussing",
        "we were talking about",
        "not about that",
        "different topic",
        "let's discuss",
        "lets discuss",
        "switching topics",
        "new topic",
        "back to",
    ]

    current_lower = current_message.lower()
    for phrase in correction_phrases:
        if phrase in current_lower:
            return True

    # Check for time gaps (>1 hour between messages)
    if len(messages) >= 2:
        from datetime import timezone

        last_msg = messages[-1]
        prev_msg = messages[-2]

        # Ensure timestamps are timezone-aware
        if last_msg.timestamp.tzinfo is None:
            last_time = last_msg.timestamp.replace(tzinfo=timezone.utc)
        else:
            last_time = last_msg.timestamp

        if prev_msg.timestamp.tzinfo is None:
            prev_time = prev_msg.timestamp.replace(tzinfo=timezone.utc)
        else:
            prev_time = prev_msg.timestamp

        time_gap = (last_time - prev_time).total_seconds()
        if time_gap > 3600:  # 1 hour
            return True

    return False


# Convenience function for running the agent
async def run_orchestrator(
    project_id: UUID,
    user_message: str,
    session,
) -> str:
    """
    Run the orchestrator agent with a user message.

    Now includes conversation history for context continuity, making PM
    remember previous discussion across messages.

    Args:
        project_id: Project UUID
        user_message: User's message
        session: Database session

    Returns:
        str: Agent's response
    """
    deps = AgentDependencies(session=session, project_id=project_id)

    # Save user message first (this handles topic detection)
    await save_conversation_message(session, project_id, MessageRole.USER, user_message)

    # Get conversation history - ONLY from active topic
    # This ensures we don't bleed context from old topics
    history_messages = await get_conversation_history(
        session, project_id, limit=50, active_topic_only=True  # Only get current topic
    )

    # Build conversation context from history
    # We'll try using PydanticAI's message_history parameter, with a fallback
    # to embedding history in the user message if that doesn't work
    # Disabled message_history feature due to PydanticAI compatibility issues
    # Using fallback method that embeds history in the user message instead
    if False:  # Temporarily disabled
        try:
            # Try using PydanticAI's message_history parameter (if supported)
            from pydantic_ai.messages import ModelRequest, ModelResponse

            message_history = []
            for msg in history_messages[:-1]:  # Exclude the user message we just added
                if msg.role == MessageRole.USER:
                    message_history.append(ModelRequest(parts=[msg.content]))
                elif msg.role == MessageRole.ASSISTANT:
                    message_history.append(ModelResponse(parts=[msg.content]))

            # Run agent with conversation history
            result = await orchestrator_agent.run(
                user_message, message_history=message_history, deps=deps
            )
        except TypeError:
            pass

    if True:  # Use fallback method
        # Fallback: If message_history parameter doesn't exist, embed history in message
        # This ensures conversation context even if PydanticAI API differs

        # Detect topic change
        topic_changed = detect_topic_change(history_messages, user_message)

        # Build conversation context with recency weighting
        history_context = ""
        if len(history_messages) > 1:  # More than just the current message
            if topic_changed:
                # Topic changed - only use recent messages, add warning
                history_context = (
                    "\n\n⚠️ **IMPORTANT: The user has switched topics or corrected you.**\n\n"
                )
                history_context += "## CURRENT TOPIC (Focus on this):\n\n"
                # Only last 4 messages (2 turns)
                for msg in history_messages[-5:-1][-4:]:
                    role_name = "User" if msg.role == MessageRole.USER else "You (PM)"
                    history_context += f"**{role_name}**: {msg.content}\n\n"
            else:
                # Normal flow - use weighted context
                recent_messages = history_messages[-7:-1]  # Last 6 messages (3 turns)
                older_messages = history_messages[-21:-7] if len(history_messages) > 7 else []

                history_context = "\n\n## CURRENT CONVERSATION (Most Important):\n\n"
                for msg in recent_messages:
                    role_name = "User" if msg.role == MessageRole.USER else "You (PM)"
                    history_context += f"**{role_name}**: {msg.content}\n\n"

                if older_messages:
                    history_context += "\n\n## Earlier Context (Only If Relevant):\n\n"
                    for msg in older_messages[-5:]:  # Max 5 older messages
                        role_name = "User" if msg.role == MessageRole.USER else "You (PM)"
                        history_context += f"**{role_name}**: {msg.content}\n\n"

            # Add current message
            history_context += f"\n---\n\n**Current User Message**: {user_message}\n\n"
            history_context += "Please respond considering the conversation context above."

        # Run agent with history embedded in message
        result = await orchestrator_agent.run(
            history_context if history_context else user_message, deps=deps
        )

    # Save assistant response
    await save_conversation_message(session, project_id, MessageRole.ASSISTANT, result.output)

    return result.output
