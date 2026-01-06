# Feature: Enhance SSE Feed to Show Detailed SCAR Execution Output Like Claude Code CLI

The following plan should be complete, but it's important that you validate documentation and codebase patterns and task sanity before you start implementing.

Pay special attention to naming of existing utils types and models. Import from the right files etc.

## Feature Description

Transform the SSE (Server-Sent Events) activity feed to display detailed, real-time SCAR execution output similar to Claude Code CLI's verbose mode. Instead of showing only high-level command status (e.g., "PRIME: COMPLETED"), the feed should stream granular execution details including:

- Individual bash commands executed with parameters
- File read operations with file paths and content snippets
- Glob pattern searches and matching files
- Grep operations with search patterns and results
- Edit operations showing modified files
- Tool invocation sequences with parameters
- Subagent spawning and completion events
- Progress indicators during long-running operations

This provides users with full transparency into what SCAR is doing, matching the detailed output experience of Claude Code CLI.

## User Story

As a Project Manager WebUI user
I want to see detailed, step-by-step SCAR execution output in the right panel SSE feed
So that I can understand exactly what operations SCAR is performing (bash commands, file reads, searches, etc.) and monitor progress in real-time like Claude Code CLI shows

## Problem Statement

**Current State**:
- SSE feed shows only coarse-grained activity: "PRIME: RUNNING" → "PRIME: COMPLETED"
- No visibility into individual operations (bash, file reads, tool calls)
- Users cannot see what SCAR is actually doing during execution
- Lacks the detailed transparency that Claude Code CLI provides
- No progress indicators during long operations

**Desired State**:
- SSE feed shows every tool invocation (Bash, Read, Grep, Glob, Edit, etc.)
- Real-time streaming of command execution and output
- File operations visible with paths and snippets
- Search operations show patterns and match counts
- Subagent activities tracked and displayed
- Users get Claude Code CLI-level transparency

**Technical Constraint**:
SCAR does NOT provide native streaming. It uses an HTTP polling-based API (`GET /test/messages/:id`) that returns accumulated messages after completion. Therefore, we must:
1. Poll SCAR more frequently during execution (reduce from 2s to 0.5s)
2. Parse accumulated message content to extract individual operations
3. Stream parsed operations incrementally to SSE feed
4. Infer operation types from message text patterns

## Solution Statement

Implement a **message parsing and streaming architecture** that:

1. **Enhanced SCAR Polling**: Increase polling frequency from 2s to 0.5s to capture messages more quickly
2. **Message Parsing Service**: Parse SCAR message text to extract individual tool invocations
3. **Activity Event Model**: Create detailed activity event types (BashActivity, FileReadActivity, etc.)
4. **Real-time Streaming**: Stream parsed activities to SSE feed as they're detected
5. **Database Persistence**: Store detailed activities for historical view
6. **Frontend Enhancement**: Display activities with appropriate icons and formatting

**Architecture Approach**:
- **Polling Layer** (`ScarClient`): Reduce poll interval, detect new messages incrementally
- **Parsing Layer** (`ScarMessageParser`): Extract tool calls from message text using regex patterns
- **Activity Storage** (`ScarActivity` model): Store granular activities with type, parameters, output
- **SSE Streaming** (`ScarFeedService`): Stream activities as they're parsed
- **Frontend Display**: Render activities with operation-specific formatting

## Feature Metadata

**Feature Type**: Enhancement
**Estimated Complexity**: High
**Primary Systems Affected**:
- SCAR client polling (`src/scar/client.py`)
- SCAR message parsing (NEW: `src/scar/message_parser.py`)
- Database models (`src/database/models.py`)
- SSE feed service (`src/services/scar_feed_service.py`)
- SSE API endpoint (`src/api/sse.py`)
- Frontend SSE hook and components

**Dependencies**:
- `sse-starlette==2.1.0` (existing)
- `sqlalchemy[asyncio]>=2.0.36` (existing)
- `pydantic>=2.10.0` (existing)

---

## CONTEXT REFERENCES

### Relevant Codebase Files IMPORTANT: YOU MUST READ THESE FILES BEFORE IMPLEMENTING!

**SCAR Integration Layer:**
- `src/scar/client.py` (lines 213-289) - **Why**: Polling logic for message retrieval, currently 2s interval
- `src/scar/types.py` (complete) - **Why**: Message type definitions, need to understand ScarMessage structure
- `src/services/scar_executor.py` (lines 98-156) - **Why**: Command execution flow, where polling happens

**SSE Streaming Layer:**
- `src/services/scar_feed_service.py` (lines 71-149) - **Why**: Current polling-based streaming implementation
- `src/api/sse.py` (lines 22-104) - **Why**: SSE endpoint configuration, event format

**Database Layer:**
- `src/database/models.py` (lines 248-301) - **Why**: ScarCommandExecution model, need to add ScarActivity model
- `src/database/connection.py` (lines 32-62) - **Why**: Session configuration

**Frontend Layer:**
- `frontend/src/hooks/useScarFeed.ts` - **Why**: EventSource client, need to handle new event types
- `frontend/src/components/RightPanel/ScarActivityFeed.tsx` - **Why**: UI rendering, need activity type-specific display

### New Files to Create

- `src/scar/message_parser.py` - Message parsing service to extract tool invocations from SCAR text
- `src/database/migrations/versions/XXX_add_scar_activity_table.py` - Alembic migration for new table
- `tests/scar/test_message_parser.py` - Unit tests for message parser
- `tests/services/test_scar_feed_enhanced.py` - Integration tests for enhanced feed

### Relevant Documentation YOU SHOULD READ THESE BEFORE IMPLEMENTING!

- [Claude Code CLI Reference](https://code.claude.com/docs/en/cli-reference)
  - Section: Verbose output and streaming
  - **Why**: Understand what detailed output looks like in Claude Code CLI
- [Claude Bash Tool Documentation](https://docs.claude.com/en/docs/agents-and-tools/tool-use/bash-tool)
  - Section: Tool invocation format
  - **Why**: Understand how bash commands are structured in messages
- [Server-Sent Events API](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)
  - Section: Event stream format
  - **Why**: Required for proper SSE event structuring
- [sse-starlette Documentation](https://github.com/sysid/sse-starlette)
  - Section: Event formatting and streaming
  - **Why**: Library-specific streaming patterns

### Patterns to Follow

**Error Handling Pattern** (from `src/services/scar_executor.py`):
```python
try:
    # Execute operation
    result = await operation()
except httpx.ConnectError as e:
    # Handle connection errors
    logger.error(f"SCAR connection failed: {e}")
    execution.status = ExecutionStatus.FAILED
    await session.commit()
except TimeoutError as e:
    # Handle timeouts
    logger.error(f"Operation timed out: {e}")
except Exception as e:
    # Generic error handling
    logger.error(f"Unexpected error: {e}", extra={"error_type": type(e).__name__})
```

**Logging Pattern** (from `src/services/scar_executor.py` lines 108-111):
```python
logger.info(
    "Executing SCAR command: {command.value}",
    extra={"project_id": str(project_id), "command": command.value, "command_args": args}
)
```

**Database Timestamp Pattern** (from `src/services/scar_feed_service.py` lines 110-119):
```python
# Convert ISO timestamp string to datetime for comparison
last_dt = datetime.fromisoformat(last_timestamp)
query = (
    select(ScarCommandExecution)
    .where(
        ScarCommandExecution.project_id == project_id,
        ScarCommandExecution.started_at > last_dt,
    )
    .order_by(ScarCommandExecution.started_at.asc())
)
```

**SSE Event Format Pattern** (from `src/api/sse.py` lines 68-80):
```python
# Send activity event
yield {
    "event": "activity",
    "data": json.dumps(activity)
}

# Send heartbeat event
yield {
    "event": "heartbeat",
    "data": json.dumps({"status": "alive", "timestamp": datetime.utcnow().isoformat()})
}
```

**Naming Conventions**:
- **Functions**: `snake_case` (e.g., `parse_message`, `extract_tool_calls`)
- **Classes**: `PascalCase` (e.g., `ScarMessageParser`, `ActivityEvent`)
- **Enums**: `UPPER_SNAKE_CASE` values (e.g., `ActivityType.BASH_COMMAND`)
- **Database Models**: `PascalCase` (e.g., `ScarActivity`)

**Testing Pattern** (from `tests/services/test_scar_executor.py`):
```python
@pytest.mark.asyncio
async def test_execute_command(db_session):
    """Test command execution with database session"""
    # Setup
    project = Project(name="Test", github_repo_url="https://github.com/test/repo")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Execute
    result = await execute_command(db_session, project.id, args)

    # Assert
    assert result.success is True
    assert "expected output" in result.output
```

---

## IMPLEMENTATION PLAN

### Phase 1: Foundation - Message Parsing Service

Create the core message parsing infrastructure to extract tool invocations from SCAR message text.

**Tasks:**

- Design `ActivityType` enum for different operation types
- Create `ScarActivity` database model for storing detailed activities
- Implement `ScarMessageParser` to extract tool calls from text
- Write comprehensive unit tests for parser

### Phase 2: Enhanced SCAR Polling

Modify SCAR client to poll more frequently and detect new messages incrementally.

**Tasks:**

- Reduce `ScarClient.wait_for_completion()` poll interval from 2s to 0.5s
- Add `get_new_messages()` method to retrieve only messages since last poll
- Implement incremental message streaming during execution
- Test polling behavior with mock SCAR responses

### Phase 3: Activity Storage and Streaming

Integrate message parsing with database storage and SSE streaming.

**Tasks:**

- Create `ScarActivity` table via Alembic migration
- Update `ScarFeedService` to parse and stream activities
- Modify `execute_scar_command()` to parse messages and store activities
- Stream activities to SSE feed in real-time

### Phase 4: Frontend Enhancement

Update frontend to display detailed activities with appropriate formatting.

**Tasks:**

- Extend `useScarFeed` hook to handle new activity event types
- Create activity type-specific renderers (Bash, Read, Grep, etc.)
- Add icons and styling for different operation types
- Implement collapsible output for verbose activities

---

## STEP-BY-STEP TASKS

IMPORTANT: Execute every task in order, top to bottom. Each task is atomic and independently testable.

### CREATE `src/scar/message_parser.py`

- **IMPLEMENT**: Activity type enum and parsing logic
- **PATTERN**: Enum pattern from `src/database/models.py` (lines 77-95)
- **IMPORTS**:
  ```python
  import re
  from enum import Enum
  from typing import List, Optional
  from pydantic import BaseModel, Field
  ```
- **GOTCHA**: SCAR messages are unstructured text, not JSON. Parser must use regex patterns to extract tool invocations
- **VALIDATE**: `uv run python -c "from src.scar.message_parser import ScarMessageParser; print('✓ Parser imports valid')"`

**Implementation Details**:

```python
class ActivityType(str, Enum):
    """Types of SCAR activities that can be extracted from messages"""
    BASH_COMMAND = "bash_command"
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_EDIT = "file_edit"
    GREP_SEARCH = "grep_search"
    GLOB_PATTERN = "glob_pattern"
    AGENT_THINKING = "agent_thinking"
    AGENT_RESPONSE = "agent_response"
    SUBAGENT_SPAWN = "subagent_spawn"
    TOOL_INVOCATION = "tool_invocation"
    ERROR = "error"
    PROGRESS = "progress"

class ActivityEvent(BaseModel):
    """Parsed activity event from SCAR message"""
    type: ActivityType
    timestamp: str  # ISO 8601
    description: str  # Human-readable description
    details: dict  # Operation-specific details
    output: Optional[str] = None  # Command output or result

class ScarMessageParser:
    """Parses SCAR message text to extract individual tool invocations and activities"""

    # Regex patterns for different tool types
    BASH_PATTERN = re.compile(r'(?:Running command|Executing|Bash):\s*`([^`]+)`')
    READ_PATTERN = re.compile(r'(?:Reading file|Read):\s*`([^`]+)`')
    GREP_PATTERN = re.compile(r'(?:Searching|Grep):\s*pattern\s*["\']([^"\']+)["\'].*in\s*`([^`]+)`')
    GLOB_PATTERN = re.compile(r'(?:Finding files|Glob):\s*pattern\s*["\']([^"\']+)["\']')
    EDIT_PATTERN = re.compile(r'(?:Editing|Edit):\s*`([^`]+)`')

    @staticmethod
    def parse_message(message: str, timestamp: str) -> List[ActivityEvent]:
        """
        Parse a SCAR message to extract individual activities.

        Args:
            message: Raw message text from SCAR
            timestamp: Message timestamp (ISO 8601)

        Returns:
            List of extracted activity events
        """
        activities = []

        # Extract bash commands
        for match in ScarMessageParser.BASH_PATTERN.finditer(message):
            activities.append(ActivityEvent(
                type=ActivityType.BASH_COMMAND,
                timestamp=timestamp,
                description=f"Executing bash command",
                details={"command": match.group(1)},
                output=None  # Output extracted separately if present
            ))

        # Extract file reads
        for match in ScarMessageParser.READ_PATTERN.finditer(message):
            activities.append(ActivityEvent(
                type=ActivityType.FILE_READ,
                timestamp=timestamp,
                description=f"Reading file",
                details={"file_path": match.group(1)},
                output=None
            ))

        # Extract grep searches
        for match in ScarMessageParser.GREP_PATTERN.finditer(message):
            activities.append(ActivityEvent(
                type=ActivityType.GREP_SEARCH,
                timestamp=timestamp,
                description=f"Searching for pattern",
                details={
                    "pattern": match.group(1),
                    "target": match.group(2)
                },
                output=None
            ))

        # Extract glob patterns
        for match in ScarMessageParser.GLOB_PATTERN.finditer(message):
            activities.append(ActivityEvent(
                type=ActivityType.GLOB_PATTERN,
                timestamp=timestamp,
                description=f"Finding files with pattern",
                details={"pattern": match.group(1)},
                output=None
            ))

        # Extract file edits
        for match in ScarMessageParser.EDIT_PATTERN.finditer(message):
            activities.append(ActivityEvent(
                type=ActivityType.FILE_EDIT,
                timestamp=timestamp,
                description=f"Editing file",
                details={"file_path": match.group(1)},
                output=None
            ))

        # If no specific patterns matched, create generic activity
        if not activities and message.strip():
            activities.append(ActivityEvent(
                type=ActivityType.AGENT_RESPONSE,
                timestamp=timestamp,
                description="Agent response",
                details={},
                output=message[:200] + ("..." if len(message) > 200 else "")
            ))

        return activities
```

---

### UPDATE `src/database/models.py`

- **ADD**: ScarActivity model after ScarCommandExecution (after line 301)
- **PATTERN**: Mirror ScarCommandExecution structure (lines 248-301)
- **IMPORTS**: No new imports needed
- **GOTCHA**: Use `JSONB` for `details` field to store flexible activity-specific data
- **VALIDATE**: `uv run python -c "from src.database.models import ScarActivity; print('✓ ScarActivity model valid')"`

**Implementation Details**:

```python
class ScarActivity(Base):
    """Tracks individual SCAR activities (tool calls, operations)"""

    __tablename__ = "scar_activities"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    execution_id = Column(PGUUID(as_uuid=True), ForeignKey("scar_executions.id"), nullable=False)
    project_id = Column(PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    activity_type = Column(String(50), nullable=False)  # bash_command, file_read, etc.
    description = Column(Text, nullable=False)  # Human-readable description
    details = Column(JSONB, nullable=True)  # Activity-specific data (command, file_path, etc.)
    output = Column(Text, nullable=True)  # Command output or result
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    execution = relationship("ScarCommandExecution", back_populates="activities")
    project = relationship("Project")

    @property
    def source(self):
        """Activity source is always SCAR"""
        return "scar"

    @property
    def verbosity_level(self):
        """Activities are high verbosity (level 3)"""
        return 3

    def __repr__(self) -> str:
        return f"<ScarActivity(id={self.id}, type={self.activity_type}, timestamp={self.timestamp})>"

# Update ScarCommandExecution to add relationship
# Add this inside ScarCommandExecution class (around line 267):
    activities = relationship(
        "ScarActivity", back_populates="execution", cascade="all, delete-orphan"
    )
```

---

### CREATE `src/database/migrations/versions/XXX_add_scar_activity_table.py`

- **IMPLEMENT**: Alembic migration to create `scar_activities` table
- **PATTERN**: Follow existing migration structure in `src/database/migrations/versions/`
- **IMPORTS**:
  ```python
  from alembic import op
  import sqlalchemy as sa
  from sqlalchemy.dialects.postgresql import UUID, JSONB
  ```
- **GOTCHA**: Use `PGUUID(as_uuid=True)` for UUID columns, not `sa.String`
- **VALIDATE**: `uv run alembic upgrade head` (should apply migration successfully)

**Implementation Details**:

```python
"""add_scar_activity_table

Revision ID: <generated>
Revises: <previous_revision>
Create Date: 2026-01-06

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision = '<generated>'
down_revision = '<previous_revision>'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'scar_activities',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('execution_id', UUID(as_uuid=True), sa.ForeignKey('scar_executions.id'), nullable=False),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('activity_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('details', JSONB(), nullable=True),
        sa.Column('output', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Add index on execution_id for faster queries
    op.create_index('idx_scar_activities_execution_id', 'scar_activities', ['execution_id'])

    # Add index on project_id + timestamp for SSE feed queries
    op.create_index('idx_scar_activities_project_timestamp', 'scar_activities', ['project_id', 'timestamp'])

def downgrade() -> None:
    op.drop_index('idx_scar_activities_project_timestamp')
    op.drop_index('idx_scar_activities_execution_id')
    op.drop_table('scar_activities')
```

---

### UPDATE `src/scar/client.py`

- **REFACTOR**: Reduce poll interval from 2.0s to 0.5s (line 214)
- **ADD**: `get_new_messages_incremental()` method to retrieve only new messages
- **PATTERN**: Follow existing async/await pattern from `wait_for_completion()`
- **IMPORTS**: No new imports needed
- **GOTCHA**: Must track `last_message_count` to avoid re-processing messages
- **VALIDATE**: `uv run python -m pytest tests/scar/test_client.py -v`

**Implementation Details**:

```python
# Line 214: Change poll_interval default
async def wait_for_completion(
    self, conversation_id: str, timeout: Optional[float] = None, poll_interval: float = 0.5  # CHANGED: 2.0 → 0.5
) -> list[ScarMessage]:

# Add new method after wait_for_completion (around line 290):
async def stream_messages_incremental(
    self,
    conversation_id: str,
    timeout: Optional[float] = None,
    poll_interval: float = 0.5,
) -> AsyncGenerator[ScarMessage, None]:
    """
    Stream SCAR messages incrementally as they arrive.

    Unlike wait_for_completion which returns all messages at the end,
    this yields new messages as they're detected during polling.

    Args:
        conversation_id: Conversation ID to poll
        timeout: Max wait time in seconds (defaults to self.timeout_seconds)
        poll_interval: Seconds between polls (default: 0.5)

    Yields:
        ScarMessage: New messages as they arrive

    Raises:
        TimeoutError: If no completion detected within timeout
        httpx.HTTPError: If request fails
    """
    if timeout is None:
        timeout = float(self.timeout_seconds)

    logger.info(
        "Starting incremental message stream",
        extra={
            "conversation_id": conversation_id,
            "timeout": timeout,
            "poll_interval": poll_interval,
        },
    )

    start_time = asyncio.get_event_loop().time()
    previous_message_count = 0
    stable_count = 0

    while True:
        # Check timeout
        elapsed = asyncio.get_event_loop().time() - start_time
        if elapsed >= timeout:
            raise TimeoutError(
                f"Message stream timed out after {elapsed:.1f}s "
                f"(timeout: {timeout}s, conversation: {conversation_id})"
            )

        # Get current messages
        messages = await self.get_messages(conversation_id)
        current_count = len(messages)

        # Yield only NEW messages
        if current_count > previous_message_count:
            new_messages = messages[previous_message_count:]
            for msg in new_messages:
                yield msg

            previous_message_count = current_count
            stable_count = 0
        else:
            stable_count += 1

        # Check for completion (2 stable polls)
        if stable_count >= 2:
            logger.info(
                "Message stream completed",
                extra={
                    "conversation_id": conversation_id,
                    "message_count": current_count,
                    "duration": elapsed,
                },
            )
            return

        # Wait before next poll
        await asyncio.sleep(poll_interval)
```

---

### UPDATE `src/scar/types.py`

- **ADD**: Import statement for AsyncGenerator
- **PATTERN**: Follow existing Pydantic model patterns
- **IMPORTS**:
  ```python
  from typing import AsyncGenerator  # Add to existing imports
  ```
- **GOTCHA**: None
- **VALIDATE**: `uv run python -c "from src.scar.types import ScarMessage; print('✓ Types valid')"`

---

### UPDATE `src/services/scar_executor.py`

- **REFACTOR**: Modify `execute_scar_command()` to parse messages and store activities
- **ADD**: Import `ScarMessageParser` and `ScarActivity`
- **PATTERN**: Follow existing error handling and logging patterns
- **IMPORTS**:
  ```python
  from src.scar.message_parser import ScarMessageParser, ActivityEvent
  from src.database.models import ScarActivity
  ```
- **GOTCHA**: Must use `stream_messages_incremental()` instead of `wait_for_completion()`
- **VALIDATE**: `uv run python -m pytest tests/services/test_scar_executor.py::test_execute_prime_command -v`

**Implementation Details**:

Replace the message retrieval and parsing section (lines 113-128) with:

```python
# OLD CODE (lines 113-128):
#     messages = await client.wait_for_completion(
#         conversation_id, timeout=settings.scar_timeout_seconds
#     )
#     output = "\n".join(msg.message for msg in messages)

# NEW CODE:
        # Stream messages incrementally and parse activities
        all_messages = []
        async for msg in client.stream_messages_incremental(
            conversation_id, timeout=settings.scar_timeout_seconds
        ):
            all_messages.append(msg)

            # Parse message for activities
            activities = ScarMessageParser.parse_message(
                msg.message,
                msg.timestamp.isoformat()
            )

            # Store each activity in database
            for activity_event in activities:
                activity = ScarActivity(
                    execution_id=execution.id,
                    project_id=project_id,
                    activity_type=activity_event.type.value,
                    description=activity_event.description,
                    details=activity_event.details,
                    output=activity_event.output,
                    timestamp=datetime.fromisoformat(activity_event.timestamp),
                )
                session.add(activity)

            # Commit activities immediately for SSE feed to pick up
            await session.commit()

        # Aggregate output from all messages
        output = "\n".join(msg.message for msg in all_messages)
```

---

### UPDATE `src/services/scar_feed_service.py`

- **REFACTOR**: Add activity streaming alongside execution streaming
- **ADD**: Query for ScarActivity records
- **PATTERN**: Mirror existing `stream_scar_activity()` structure
- **IMPORTS**:
  ```python
  from src.database.models import ScarActivity  # Add to existing imports
  ```
- **GOTCHA**: Activities have `verbosity_level=3` property, filter accordingly
- **VALIDATE**: `uv run python -m pytest tests/services/test_scar_feed_enhanced.py -v`

**Implementation Details**:

Modify `stream_scar_activity()` function (lines 71-149):

```python
async def stream_scar_activity(
    session: AsyncSession, project_id: UUID, verbosity_level: int = 2
) -> AsyncGenerator[Dict, None]:
    """
    Stream SCAR activity updates in real-time.

    Streams both:
    - ScarCommandExecution records (verbosity 1-2)
    - ScarActivity records (verbosity 3 - detailed operations)

    Args:
        session: Database session
        project_id: Project UUID
        verbosity_level: Minimum verbosity level to include (1=low, 2=medium, 3=high)

    Yields:
        Activity dictionaries as they occur
    """
    logger.info(f"Starting SCAR activity stream for project {project_id} (verbosity: {verbosity_level})")

    last_execution_timestamp = None
    last_activity_timestamp = None

    # Get initial command executions (verbosity 1-2)
    executions = await get_recent_scar_activity(
        session, project_id, limit=10, verbosity_level=verbosity_level
    )
    if executions:
        last_execution_timestamp = executions[-1]["timestamp"]
        for execution in executions:
            yield execution

    # Get initial detailed activities (verbosity 3)
    if verbosity_level >= 3:
        query = (
            select(ScarActivity)
            .where(ScarActivity.project_id == project_id)
            .order_by(ScarActivity.timestamp.desc())
            .limit(20)
        )
        result = await session.execute(query)
        activities = list(reversed(result.scalars().all()))

        if activities:
            last_activity_timestamp = activities[-1].timestamp.isoformat()
            for activity in activities:
                yield {
                    "id": str(activity.id),
                    "timestamp": activity.timestamp.isoformat(),
                    "source": "scar",
                    "message": activity.description,
                    "type": activity.activity_type,
                    "details": activity.details,
                    "output": activity.output,
                    "verbosity": 3,
                }

    # Poll for new activities
    while True:
        await asyncio.sleep(0.5)  # CHANGED: 2s → 0.5s to match SCAR polling

        # Query for new command executions
        if last_execution_timestamp and verbosity_level <= 2:
            last_dt = datetime.fromisoformat(last_execution_timestamp)
            query = (
                select(ScarCommandExecution)
                .where(
                    ScarCommandExecution.project_id == project_id,
                    ScarCommandExecution.started_at > last_dt,
                )
                .order_by(ScarCommandExecution.started_at.asc())
            )

            result = await session.execute(query)
            new_executions = result.scalars().all()

            for execution in new_executions:
                execution_dict = {
                    "id": str(execution.id),
                    "timestamp": execution.started_at.isoformat(),
                    "source": "scar",
                    "message": f"{execution.command_type.value}: {execution.status.value}",
                    "phase": execution.phase.name if execution.phase else None,
                    "verbosity": 2,
                }
                last_execution_timestamp = execution_dict["timestamp"]
                yield execution_dict

        # Query for new detailed activities (verbosity 3)
        if verbosity_level >= 3:
            if last_activity_timestamp:
                last_dt = datetime.fromisoformat(last_activity_timestamp)
            else:
                last_dt = datetime.utcnow()

            query = (
                select(ScarActivity)
                .where(
                    ScarActivity.project_id == project_id,
                    ScarActivity.timestamp > last_dt,
                )
                .order_by(ScarActivity.timestamp.asc())
            )

            result = await session.execute(query)
            new_activities = result.scalars().all()

            for activity in new_activities:
                activity_dict = {
                    "id": str(activity.id),
                    "timestamp": activity.timestamp.isoformat(),
                    "source": "scar",
                    "message": activity.description,
                    "type": activity.activity_type,
                    "details": activity.details,
                    "output": activity.output,
                    "verbosity": 3,
                }
                last_activity_timestamp = activity_dict["timestamp"]
                yield activity_dict
```

---

### CREATE `tests/scar/test_message_parser.py`

- **IMPLEMENT**: Comprehensive unit tests for ScarMessageParser
- **PATTERN**: Follow existing pytest patterns from `tests/services/`
- **IMPORTS**:
  ```python
  import pytest
  from src.scar.message_parser import ScarMessageParser, ActivityType, ActivityEvent
  ```
- **GOTCHA**: Test both positive cases (patterns match) and negative cases (no patterns)
- **VALIDATE**: `uv run python -m pytest tests/scar/test_message_parser.py -v`

**Implementation Details**:

```python
"""
Tests for SCAR message parser.
"""
import pytest
from src.scar.message_parser import ScarMessageParser, ActivityType, ActivityEvent

def test_parse_bash_command():
    """Test parsing bash command from message"""
    message = "Running command: `git status`"
    timestamp = "2026-01-06T10:00:00Z"

    activities = ScarMessageParser.parse_message(message, timestamp)

    assert len(activities) == 1
    assert activities[0].type == ActivityType.BASH_COMMAND
    assert activities[0].details["command"] == "git status"
    assert activities[0].timestamp == timestamp

def test_parse_file_read():
    """Test parsing file read operation"""
    message = "Reading file: `src/main.py`"
    timestamp = "2026-01-06T10:01:00Z"

    activities = ScarMessageParser.parse_message(message, timestamp)

    assert len(activities) == 1
    assert activities[0].type == ActivityType.FILE_READ
    assert activities[0].details["file_path"] == "src/main.py"

def test_parse_grep_search():
    """Test parsing grep search operation"""
    message = 'Searching: pattern "class Project" in `src/database/models.py`'
    timestamp = "2026-01-06T10:02:00Z"

    activities = ScarMessageParser.parse_message(message, timestamp)

    assert len(activities) == 1
    assert activities[0].type == ActivityType.GREP_SEARCH
    assert activities[0].details["pattern"] == "class Project"
    assert activities[0].details["target"] == "src/database/models.py"

def test_parse_glob_pattern():
    """Test parsing glob pattern operation"""
    message = 'Finding files: pattern "**/*.py"'
    timestamp = "2026-01-06T10:03:00Z"

    activities = ScarMessageParser.parse_message(message, timestamp)

    assert len(activities) == 1
    assert activities[0].type == ActivityType.GLOB_PATTERN
    assert activities[0].details["pattern"] == "**/*.py"

def test_parse_multiple_operations():
    """Test parsing message with multiple operations"""
    message = """
    Reading file: `src/config.py`
    Running command: `ls -la`
    Editing: `src/main.py`
    """
    timestamp = "2026-01-06T10:04:00Z"

    activities = ScarMessageParser.parse_message(message, timestamp)

    assert len(activities) == 3
    types = [a.type for a in activities]
    assert ActivityType.FILE_READ in types
    assert ActivityType.BASH_COMMAND in types
    assert ActivityType.FILE_EDIT in types

def test_parse_no_patterns():
    """Test parsing message with no recognizable patterns"""
    message = "This is a generic response from the agent."
    timestamp = "2026-01-06T10:05:00Z"

    activities = ScarMessageParser.parse_message(message, timestamp)

    assert len(activities) == 1
    assert activities[0].type == ActivityType.AGENT_RESPONSE
    assert "generic response" in activities[0].output

def test_parse_empty_message():
    """Test parsing empty message"""
    message = ""
    timestamp = "2026-01-06T10:06:00Z"

    activities = ScarMessageParser.parse_message(message, timestamp)

    assert len(activities) == 0
```

---

### UPDATE `frontend/src/hooks/useScarFeed.ts`

- **ADD**: Handle new activity event types with `verbosity` field
- **REFACTOR**: Add activity type filtering
- **PATTERN**: Follow existing EventSource pattern
- **IMPORTS**:
  ```typescript
  // No new imports needed
  ```
- **GOTCHA**: Activities with `verbosity: 3` should only show when verbosity >= 3
- **VALIDATE**: Manual testing with frontend dev server

**Implementation Details**:

```typescript
// Update ScarActivity interface
export interface ScarActivity {
  id: string;
  timestamp: string;
  source: 'po' | 'scar' | 'claude';
  message: string;
  phase?: string;

  // NEW FIELDS for detailed activities
  type?: string;  // bash_command, file_read, etc.
  details?: Record<string, any>;  // Activity-specific data
  output?: string;  // Command output
  verbosity?: number;  // 1-3
}

// Update event listener to filter by verbosity
eventSource.addEventListener('activity', (event) => {
  const activity: ScarActivity = JSON.parse(event.data);

  // Filter by verbosity level
  const activityVerbosity = activity.verbosity ?? 2;  // Default to medium
  if (activityVerbosity <= verbosity) {
    setActivities((prev) => [...prev, activity]);
  }
});
```

---

### UPDATE `frontend/src/components/RightPanel/ScarActivityFeed.tsx`

- **ADD**: Activity type-specific rendering with icons
- **ADD**: Collapsible output sections for verbose activities
- **PATTERN**: Follow existing component structure
- **IMPORTS**:
  ```typescript
  import { ChevronDown, ChevronRight, Terminal, FileText, Search, Code } from 'lucide-react';
  ```
- **GOTCHA**: Long output should be truncated with "Show more" button
- **VALIDATE**: Manual testing in browser

**Implementation Details**:

```typescript
// Add activity icon mapping
const getActivityIcon = (type?: string) => {
  switch (type) {
    case 'bash_command':
      return <Terminal className="w-4 h-4 text-blue-500" />;
    case 'file_read':
    case 'file_write':
    case 'file_edit':
      return <FileText className="w-4 h-4 text-green-500" />;
    case 'grep_search':
    case 'glob_pattern':
      return <Search className="w-4 h-4 text-purple-500" />;
    default:
      return <Code className="w-4 h-4 text-gray-500" />;
  }
};

// Add activity details renderer
const ActivityDetails = ({ activity }: { activity: ScarActivity }) => {
  const [expanded, setExpanded] = React.useState(false);

  if (!activity.details && !activity.output) return null;

  return (
    <div className="ml-6 mt-1 text-sm">
      {/* Details (command, file_path, etc.) */}
      {activity.details && (
        <div className="text-gray-600 font-mono text-xs">
          {Object.entries(activity.details).map(([key, value]) => (
            <div key={key}>
              <span className="text-gray-500">{key}:</span> {value}
            </div>
          ))}
        </div>
      )}

      {/* Output (collapsible) */}
      {activity.output && (
        <div className="mt-1">
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1 text-gray-500 hover:text-gray-700"
          >
            {expanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
            <span className="text-xs">Output</span>
          </button>
          {expanded && (
            <pre className="mt-1 p-2 bg-gray-50 rounded text-xs overflow-x-auto">
              {activity.output}
            </pre>
          )}
        </div>
      )}
    </div>
  );
};

// Update activity rendering
<div className="flex items-start gap-2">
  {getActivityIcon(activity.type)}
  <div className="flex-1">
    <div className="text-sm">{activity.message}</div>
    <ActivityDetails activity={activity} />
  </div>
  <div className="text-xs text-gray-400">
    {new Date(activity.timestamp).toLocaleTimeString()}
  </div>
</div>
```

---

## TESTING STRATEGY

### Unit Tests

**Coverage Target**: 85%+ for new code

**Test Files**:
- `tests/scar/test_message_parser.py` - Parser logic with various message formats
- `tests/scar/test_client.py` - Incremental streaming behavior
- `tests/services/test_scar_feed_enhanced.py` - Activity streaming logic

**Key Test Scenarios**:
- Message parsing with all activity types
- Message parsing with multiple operations in one message
- Message parsing with no recognizable patterns
- Incremental message streaming with new messages arriving
- Activity storage and retrieval from database
- SSE feed filtering by verbosity level

### Integration Tests

**Test Files**:
- `tests/services/test_scar_executor.py` - End-to-end command execution with activity parsing

**Test Scenarios**:
- Execute SCAR command and verify activities are created
- Verify activities are committed immediately for SSE feed
- Test timeout behavior with incremental streaming
- Test connection error handling during streaming

### Manual Testing

**Test Scenarios**:
1. **Low Verbosity (1)**: Only major events (command start/complete)
2. **Medium Verbosity (2)**: Command executions with status
3. **High Verbosity (3)**: All detailed activities (bash, file reads, etc.)

**Test Steps**:
1. Start Project Manager backend: `uv run uvicorn src.main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Open browser to `http://localhost:3002`
4. Create project or select existing one
5. Send message requesting codebase analysis
6. Observe right panel SSE feed:
   - Verbosity 1: Should show "PRIME: RUNNING" → "PRIME: COMPLETED"
   - Verbosity 2: Should show execution status updates
   - Verbosity 3: Should show individual bash commands, file reads, etc.
7. Verify timestamps are recent (within seconds)
8. Verify activities appear in real-time (not all at once after completion)

---

## VALIDATION COMMANDS

Execute every command to ensure zero regressions and 100% feature correctness.

### Level 1: Import Validation (CRITICAL)

**Verify all imports resolve before running tests:**

```bash
uv run python -c "from src.main import app; print('✓ All imports valid')"
```

**Expected**: "✓ All imports valid" (no ModuleNotFoundError or ImportError)

**Why**: Catches incorrect imports immediately. If this fails, fix imports before proceeding.

### Level 2: Database Migration

**Apply new migration:**

```bash
uv run alembic upgrade head
```

**Expected**: Migration applies successfully, `scar_activities` table created

**Verify table creation:**

```bash
uv run python -c "from src.database.models import ScarActivity; from src.database.connection import engine; import asyncio; asyncio.run(engine.dispose()); print('✓ ScarActivity table exists')"
```

### Level 3: Unit Tests

**Run message parser tests:**

```bash
uv run python -m pytest tests/scar/test_message_parser.py -v
```

**Expected**: All tests pass (100% coverage for parser)

**Run SCAR client tests:**

```bash
uv run python -m pytest tests/scar/test_client.py -v
```

**Expected**: All tests pass, incremental streaming works

**Run SSE feed tests:**

```bash
uv run python -m pytest tests/services/test_scar_feed_enhanced.py -v
```

**Expected**: All tests pass, activities stream correctly

### Level 4: Integration Tests

**Run full SCAR executor tests:**

```bash
uv run python -m pytest tests/services/test_scar_executor.py -v
```

**Expected**: All tests pass, activities created during execution

### Level 5: Type Checking

**Run mypy type checking:**

```bash
uv run mypy src/scar/message_parser.py src/services/scar_feed_service.py
```

**Expected**: No type errors

### Level 6: Linting

**Run ruff linting:**

```bash
uv run ruff check src/scar/message_parser.py src/services/scar_feed_service.py
```

**Expected**: No linting errors

**Auto-fix issues:**

```bash
uv run ruff check --fix src/
```

### Level 7: Manual End-to-End Testing

**Start backend:**

```bash
uv run uvicorn src.main:app --reload
```

**Start frontend (separate terminal):**

```bash
cd frontend && npm run dev
```

**Test Steps**:
1. Navigate to `http://localhost:3002`
2. Select project with GitHub repo configured
3. Send message: "Analyze the codebase structure"
4. Observe SSE feed in right panel
5. Verify activities appear in real-time
6. Test all 3 verbosity levels (1, 2, 3)
7. Verify detailed activities show for verbosity 3

**Expected Behavior**:
- Verbosity 1: Only "PRIME: RUNNING" → "PRIME: COMPLETED"
- Verbosity 2: Command executions with status updates
- Verbosity 3: Individual operations (bash, file reads) with details

### Level 8: Performance Testing

**Verify poll interval reduction doesn't overload database:**

```bash
# Monitor database connection pool
uv run python -c "from src.database.connection import engine; import asyncio; async def check(): print(f'Pool size: {engine.pool.size()}'); print(f'Checked out: {engine.pool.checkedout()}'); asyncio.run(check())"
```

**Expected**: Pool size stable, no connection exhaustion

---

## ACCEPTANCE CRITERIA

- [ ] Feature implements detailed SCAR activity streaming (bash, file reads, etc.)
- [ ] All validation commands pass with zero errors
- [ ] Unit test coverage ≥85% for new code
- [ ] Integration tests verify end-to-end workflow
- [ ] Code follows project conventions and patterns (snake_case, PascalCase)
- [ ] No regressions in existing functionality
- [ ] Database migration applies successfully
- [ ] SSE feed streams activities in real-time (<1s latency)
- [ ] Frontend displays activities with appropriate icons and formatting
- [ ] Verbosity filtering works correctly (1=low, 2=medium, 3=high)
- [ ] Long output is collapsible with "Show more" UI
- [ ] Performance is acceptable (poll interval 0.5s doesn't overload DB)
- [ ] Manual testing confirms Claude Code CLI-like transparency

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order (top to bottom)
- [ ] Each task validation passed immediately after implementation
- [ ] All validation commands executed successfully
- [ ] Full test suite passes (unit + integration)
- [ ] No linting or type checking errors
- [ ] Manual testing confirms feature works across all verbosity levels
- [ ] Acceptance criteria all met
- [ ] Code reviewed for quality and maintainability
- [ ] Database migration tested on clean database
- [ ] SSE feed performance verified under load (multiple concurrent connections)

---

## NOTES

### Design Trade-offs

**Polling vs. True Streaming**:
- **Constraint**: SCAR Test Adapter API does NOT support true streaming (WebSocket/SSE)
- **Solution**: Enhanced polling with 0.5s interval and incremental message processing
- **Trade-off**: Minimum 0.5s latency vs. instant streaming (acceptable for MVP)

**Message Parsing Approach**:
- **Constraint**: SCAR messages are unstructured text, not structured JSON
- **Solution**: Regex-based parsing to extract tool invocations
- **Limitation**: May miss operations if message format changes
- **Mitigation**: Comprehensive test coverage, fallback to generic "agent_response" type

**Database Storage**:
- **Decision**: Store all activities in `scar_activities` table
- **Benefit**: Historical view, replay capabilities, verbosity filtering
- **Cost**: Increased database storage (~100 activities per command)
- **Optimization**: Add retention policy later if needed (e.g., delete activities >30 days)

**Frontend Performance**:
- **Concern**: Rendering hundreds of activities could slow down UI
- **Mitigation**: Virtual scrolling (future enhancement), collapsible sections
- **Note**: Test with long-running commands (validate phase) to ensure UI remains responsive

### Future Enhancements

**Real Streaming** (if SCAR adds WebSocket support):
- Replace polling with WebSocket subscription
- Eliminate 0.5s latency
- Reduce database load (no repeated queries)

**Advanced Filtering**:
- Filter by activity type (show only bash commands, hide file reads)
- Search/filter activities by keyword
- Highlight errors and warnings

**Activity Replay**:
- Replay SCAR execution step-by-step
- "Time travel" debugging through past executions
- Export execution trace for sharing

**Performance Optimizations**:
- Virtual scrolling for large activity lists
- Activity aggregation (combine related operations)
- Lazy loading of output (fetch on expand)

### Breaking Changes

**None** - This is a pure enhancement. Existing low/medium verbosity levels continue to work as before.

### Migration Notes

**Database Migration Required**: Run `uv run alembic upgrade head` before deploying

**Backward Compatibility**: Existing `ScarCommandExecution` records continue to work. New `ScarActivity` table is additive.

**Rollback Plan**: If issues occur, run `uv run alembic downgrade -1` to remove `scar_activities` table

---

## RESEARCH REFERENCES

**Claude Code CLI Documentation**:
- [CLI Reference](https://code.claude.com/docs/en/cli-reference) - Verbose output and streaming modes
- [Bash Tool Documentation](https://docs.claude.com/en/docs/agents-and-tools/tool-use/bash-tool) - Tool invocation format

**Server-Sent Events (SSE)**:
- [MDN: Using Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events) - SSE API specification
- [sse-starlette Documentation](https://github.com/sysid/sse-starlette) - Library-specific patterns

**LangWatch Scenario Testing**:
- [Testing Remote Agents with SSE](https://langwatch.ai/scenario/examples/testing-remote-agents/sse/) - SSE test adapter pattern

**Project-Specific Context**:
- `.agents/plans/fix-sse-feed-complete.md` - Previous SSE debugging and fixes (PR #46, PR #48)
- `.agents/reference/scar-workflow-guide.md` - SCAR workflow patterns and commands

---

## REVISION HISTORY

- **2026-01-06**: Initial plan created based on feature request
- **Target Completion**: 2026-01-07
- **Estimated Effort**: 6-8 hours (1 developer)
