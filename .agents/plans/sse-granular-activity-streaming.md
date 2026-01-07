# Feature: Transform SSE Feed to Stream Granular SCAR Execution Output

The following plan should be complete, but it's important that you validate documentation and codebase patterns and task sanity before you start implementing.

Pay special attention to naming of existing utils types and models. Import from the right files etc.

## Feature Description

Transform the SSE (Server-Sent Events) activity feed from showing only high-level command status (e.g., "PRIME: COMPLETED") to streaming granular, real-time output from SCAR executions. This provides users with Claude Code CLI-level transparency into what SCAR is doing during command execution, displaying each line of output as it becomes available.

**Key Change**: Instead of waiting for SCAR commands to complete before showing output, stream SCAR's text messages incrementally as they arrive, creating a ScarActivity record for each distinct line or message chunk. This creates a detailed activity log similar to watching Claude Code CLI in verbose mode.

## User Story

As a Project Manager WebUI user
I want to see detailed, real-time SCAR execution output in the right panel SSE feed (line-by-line)
So that I can understand exactly what SCAR is doing during execution and monitor progress transparently, similar to watching Claude Code CLI

## Problem Statement

**Current State**:
- SSE feed shows only coarse-grained activity: "PRIME: RUNNING" → "PRIME: COMPLETED"
- No visibility into intermediate output during execution
- Users cannot see what SCAR is actually doing while command runs
- All output bundled into single execution record, only visible after completion
- Lacks real-time progress transparency

**Desired State**:
- SSE feed shows each line/chunk of SCAR output as it arrives
- Real-time streaming of execution progress during command runs
- Users see output incrementally (not all at once after completion)
- Activity feed updates continuously during execution
- Transparent progress similar to Claude Code CLI verbose mode

**Technical Reality**:
SCAR Test Adapter API (`GET /test/messages/:id`) returns accumulated text messages, not structured tool invocations. Messages contain agent responses, which may include references to operations but are unstructured plain text. We cannot reliably parse "bash commands" or "file reads" from this text.

**Solution**: Stream SCAR's text messages line-by-line, creating a `ScarActivity` record for each line of output. This provides transparency without fragile text parsing.

## Solution Statement

Implement a **line-by-line activity streaming architecture** that:

1. **Incremental Polling**: Poll SCAR at 0.5s intervals (faster than current 2s) to capture new messages quickly
2. **Line-by-Line Parsing**: Split SCAR messages into individual lines, creating an activity for each line
3. **Activity Database Model**: Create `ScarActivity` table to store granular line-level activities
4. **Real-time Streaming**: Commit activities immediately and stream via SSE as execution progresses
5. **Frontend Enhancement**: Display activities with verbosity filtering (levels 1-3)
6. **Backward Compatibility**: Existing verbosity levels 1-2 unchanged; level 3 shows line-level detail

**Architecture Approach**:
- **Polling Layer** (`ScarClient`): Add `stream_messages_incremental()` with 0.5s poll interval
- **Execution Layer** (`scar_executor`): Parse messages line-by-line, create activities during execution
- **Activity Storage** (`ScarActivity` model): Store each line as separate activity with timestamp
- **SSE Streaming** (`ScarFeedService`): Stream activities as they're created (real-time)
- **Frontend Display**: Render line-level activities at verbosity=3

## Feature Metadata

**Feature Type**: Enhancement
**Estimated Complexity**: Medium
**Primary Systems Affected**:
- SCAR client polling (`src/scar/client.py`)
- SCAR executor (`src/services/scar_executor.py`)
- Database models (`src/database/models.py`)
- SSE feed service (`src/services/scar_feed_service.py`)
- SSE API endpoint (`src/api/sse.py`)
- Frontend SSE hook and components

**Dependencies**:
- `sse-starlette==2.1.0` (existing)
- `sqlalchemy[asyncio]>=2.0.36` (existing)
- `pydantic>=2.10.0` (existing)
- No new external dependencies required

---

## CONTEXT REFERENCES

### Relevant Codebase Files IMPORTANT: YOU MUST READ THESE FILES BEFORE IMPLEMENTING!

**SCAR Integration Layer:**
- `src/scar/client.py` (lines 213-290) - **Why**: Polling logic for message retrieval, needs incremental streaming method
- `src/scar/types.py` (complete) - **Why**: Message type definitions, understand ScarMessage structure
- `src/services/scar_executor.py` (lines 98-156) - **Why**: Command execution flow, where to add line-by-line parsing

**SSE Streaming Layer:**
- `src/services/scar_feed_service.py` (lines 98-176) - **Why**: Current streaming implementation, needs activity query support
- `src/api/sse.py` (lines 22-104) - **Why**: SSE endpoint configuration, event format

**Database Layer:**
- `src/database/models.py` (lines 279-332) - **Why**: ScarCommandExecution model, need to add ScarActivity model
- `src/database/connection.py` (lines 14-48) - **Why**: Session configuration and engine setup

**Frontend Layer:**
- `frontend/src/hooks/useScarFeed.ts` - **Why**: EventSource client, may need to handle activity events
- `frontend/src/components/RightPanel/ScarActivityFeed.tsx` (lines 40-76) - **Why**: UI rendering, already has basic message display

**Testing Patterns:**
- `tests/unit/scar/test_client.py` (lines 232-375) - **Why**: Polling test patterns with respx mocking
- `tests/conftest.py` (lines 32-96) - **Why**: Database fixtures and async session patterns
- `tests/services/test_scar_executor.py` - **Why**: Execution service test patterns

### New Files to Create

- `src/database/migrations/versions/YYYYMMDD_HHMM_add_scar_activity_table.py` - Alembic migration for new table
- `tests/unit/scar/test_incremental_streaming.py` - Unit tests for incremental message streaming
- `tests/integration/test_activity_streaming.py` - Integration tests for end-to-end activity streaming

### Relevant Documentation YOU SHOULD READ THESE BEFORE IMPLEMENTING!

- [Server-Sent Events API](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)
  - Section: Event stream format
  - **Why**: Required for proper SSE event structuring
- [sse-starlette Documentation](https://github.com/sysid/sse-starlette)
  - Section: Event formatting and streaming
  - **Why**: Library-specific streaming patterns
- [SQLAlchemy Async ORM](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
  - Section: Async session usage and commit patterns
  - **Why**: Proper async database operations during streaming
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
  - Section: Running tasks after response
  - **Why**: Understanding async execution patterns (not using for this feature)

### Patterns to Follow

**Error Handling Pattern** (from `src/services/scar_executor.py` lines 158-233):
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

**Database Commit Pattern** (from `src/services/scar_executor.py` lines 134-139):
```python
# Update execution record
execution.status = ExecutionStatus.COMPLETED
execution.completed_at = end_time
execution.output = output
await session.commit()
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

**Async Generator Pattern** (from `src/scar/client.py` lines 213-289):
```python
async def wait_for_completion(
    self, conversation_id: str, timeout: Optional[float] = None, poll_interval: float = 2.0
) -> list[ScarMessage]:
    """Poll until completion detected"""
    start_time = asyncio.get_event_loop().time()
    previous_message_count = 0
    stable_count = 0

    while True:
        # Check timeout
        elapsed = asyncio.get_event_loop().time() - start_time
        if elapsed >= timeout:
            raise TimeoutError(...)

        # Get messages
        messages = await self.get_messages(conversation_id)

        # Check for new messages
        if len(messages) > previous_message_count:
            stable_count = 0
            previous_message_count = len(messages)
        else:
            stable_count += 1

        # Check for completion
        if stable_count >= 2:
            return messages

        await asyncio.sleep(poll_interval)
```

**Testing Pattern with respx** (from `tests/unit/scar/test_client.py` lines 270-340):
```python
@pytest.mark.asyncio
@respx.mock
async def test_wait_for_completion_streaming(
    client: ScarClient, project_id, respx_mock: MockRouter
):
    """Test waiting with streaming messages"""
    call_count = 0

    def dynamic_response(request):
        nonlocal call_count
        call_count += 1
        # Return different responses based on call count
        # to simulate message accumulation
        ...
        return httpx.Response(200, json={"conversationId": ..., "messages": messages})

    respx_mock.get(f"http://localhost:3000/test/messages/{conversation_id}").mock(
        side_effect=dynamic_response
    )

    messages = await client.wait_for_completion(conversation_id, poll_interval=0.1)
    assert len(messages) == 3
```

**Naming Conventions**:
- **Functions**: `snake_case` (e.g., `stream_messages_incremental`, `create_activity`)
- **Classes**: `PascalCase` (e.g., `ScarActivity`, `ActivityType`)
- **Database Models**: `PascalCase` with `__tablename__` in `snake_case`
- **Enums**: `UPPER_SNAKE_CASE` values (e.g., `ActivityType.TEXT_LINE`)

---

## IMPLEMENTATION PLAN

### Phase 1: Foundation - Database Model and Migration

Create the database infrastructure to store granular line-level activities.

**Tasks:**
- Design `ScarActivity` database model for storing line-level output
- Create Alembic migration to add `scar_activities` table
- Update `ScarCommandExecution` model to add relationship
- Apply migration and verify table creation

### Phase 2: Incremental Message Streaming

Modify SCAR client to stream messages incrementally as they arrive (0.5s polling).

**Tasks:**
- Add `stream_messages_incremental()` async generator method to `ScarClient`
- Reduce poll interval from 2.0s to 0.5s
- Yield new messages as they're detected during polling
- Test incremental streaming with mock responses

### Phase 3: Line-by-Line Activity Creation

Update SCAR executor to parse messages line-by-line and create activities during execution.

**Tasks:**
- Modify `execute_scar_command()` to use `stream_messages_incremental()`
- Parse each message into lines, create `ScarActivity` for each line
- Commit activities immediately for SSE feed to pick up
- Handle empty lines and whitespace appropriately

### Phase 4: SSE Feed Enhancement

Extend SSE feed service to stream activities in real-time during execution.

**Tasks:**
- Update `stream_scar_activity()` to query `ScarActivity` table
- Stream activities at verbosity level 3
- Maintain backward compatibility (levels 1-2 unchanged)
- Reduce SSE polling interval to 0.5s to match SCAR polling

### Phase 5: Frontend Display (Optional Enhancement)

Improve frontend display of granular activities (already has basic rendering).

**Tasks:**
- Verify frontend handles increased activity volume
- Test scrolling performance with many activities
- Add optional: icons for different message types (if time permits)

---

## STEP-BY-STEP TASKS

IMPORTANT: Execute every task in order, top to bottom. Each task is atomic and independently testable.

### CREATE `src/database/models.py` - Add ScarActivity Model

- **ADD**: ScarActivity model after ScarCommandExecution (after line 332)
- **PATTERN**: Mirror ScarCommandExecution structure (lines 279-332)
- **IMPORTS**: No new imports needed (uuid, Column, ForeignKey, etc. already imported)
- **GOTCHA**: Use `Text` column type for `message` field (not String) to support long lines
- **VALIDATE**: `uv run python -c "from src.database.models import ScarActivity; print('✓ ScarActivity model valid')"`

**Implementation**:

```python
class ScarActivity(Base):
    """Tracks individual lines/chunks of SCAR execution output"""

    __tablename__ = "scar_activities"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    execution_id = Column(PGUUID(as_uuid=True), ForeignKey("scar_executions.id"), nullable=False)
    project_id = Column(PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    message = Column(Text, nullable=False)  # Line of output from SCAR
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    sequence_number = Column(Integer, nullable=False)  # Order within execution

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
        return f"<ScarActivity(id={self.id}, execution_id={self.execution_id}, seq={self.sequence_number})>"
```

**Also ADD relationship to ScarCommandExecution** (insert after line 298):

```python
    # Relationships
    project = relationship("Project", back_populates="scar_executions")
    phase = relationship("WorkflowPhase", back_populates="scar_executions")
    activities = relationship(
        "ScarActivity", back_populates="execution", cascade="all, delete-orphan"
    )  # ADD THIS
```

---

### CREATE Alembic Migration

- **IMPLEMENT**: Alembic migration to create `scar_activities` table
- **PATTERN**: Follow existing migrations in `src/database/migrations/versions/`
- **IMPORTS**: Standard alembic imports
- **GOTCHA**: Use `server_default=sa.func.now()` for timestamp, not Python default
- **VALIDATE**: `uv run alembic upgrade head` (should apply successfully)

**Implementation**:

```bash
# Generate migration file
uv run alembic revision -m "add_scar_activity_table"
```

Then edit the generated file (`src/database/migrations/versions/YYYYMMDD_HHMM_add_scar_activity_table.py`):

```python
"""add_scar_activity_table

Revision ID: <generated>
Revises: <previous_revision>
Create Date: <timestamp>

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic
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
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('sequence_number', sa.Integer(), nullable=False),
    )

    # Add indexes for faster queries
    op.create_index('idx_scar_activities_execution_id', 'scar_activities', ['execution_id'])
    op.create_index('idx_scar_activities_project_timestamp', 'scar_activities', ['project_id', 'timestamp'])


def downgrade() -> None:
    op.drop_index('idx_scar_activities_project_timestamp')
    op.drop_index('idx_scar_activities_execution_id')
    op.drop_table('scar_activities')
```

---

### UPDATE `src/scar/client.py` - Add Incremental Streaming

- **ADD**: `stream_messages_incremental()` async generator method (after line 289)
- **PATTERN**: Similar to `wait_for_completion()` but yields messages instead of returning list
- **IMPORTS**: Add `from typing import AsyncGenerator` if not already imported
- **GOTCHA**: Must track `previous_message_count` to yield only new messages
- **VALIDATE**: `uv run python -m pytest tests/unit/scar/test_incremental_streaming.py -v`

**Implementation** (add after `wait_for_completion()` method):

```python
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

### UPDATE `src/scar/types.py` - Add AsyncGenerator Import

- **ADD**: Import AsyncGenerator type if not already present
- **PATTERN**: Add to existing imports at top of file
- **GOTCHA**: None
- **VALIDATE**: `uv run python -c "from src.scar.types import ScarMessage; print('✓ Types valid')"`

**Implementation**:

```python
# At top of file, update imports
from typing import AsyncGenerator, Literal  # Add AsyncGenerator
```

---

### UPDATE `src/services/scar_executor.py` - Stream and Parse Messages

- **REFACTOR**: Replace `wait_for_completion()` with `stream_messages_incremental()`
- **ADD**: Line-by-line parsing and activity creation during execution
- **IMPORTS**: `from src.database.models import ScarActivity`
- **PATTERN**: Follow existing error handling and logging patterns
- **GOTCHA**: Must commit after each activity batch to make visible to SSE feed
- **VALIDATE**: `uv run python -m pytest tests/services/test_scar_executor.py::test_execute_prime_command -v`

**Implementation** (replace lines 117-128):

```python
# OLD CODE (lines 117-128):
#     messages = await client.wait_for_completion(
#         conversation_id, timeout=settings.scar_timeout_seconds
#     )
#     output = "\n".join(msg.message for msg in messages)

# NEW CODE:
        # Stream messages incrementally and create activities
        all_messages = []
        sequence_number = 0

        async for msg in client.stream_messages_incremental(
            conversation_id, timeout=settings.scar_timeout_seconds
        ):
            all_messages.append(msg)

            # Parse message into lines
            lines = msg.message.split("\n")

            # Create activity for each non-empty line
            for line in lines:
                line = line.strip()
                if not line:  # Skip empty lines
                    continue

                activity = ScarActivity(
                    execution_id=execution.id,
                    project_id=project_id,
                    message=line,
                    timestamp=msg.timestamp,
                    sequence_number=sequence_number,
                )
                session.add(activity)
                sequence_number += 1

            # Commit activities immediately for SSE feed to pick up
            await session.commit()

            logger.debug(
                f"Created {len(lines)} activities from message",
                extra={"execution_id": str(execution.id), "sequence": sequence_number}
            )

        # Aggregate output from all messages
        output = "\n".join(msg.message for msg in all_messages)
```

---

### UPDATE `src/services/scar_feed_service.py` - Stream Activities

- **REFACTOR**: Add query for `ScarActivity` records at verbosity level 3
- **ADD**: Stream activities alongside command executions
- **IMPORTS**: `from src.database.models import ScarActivity`
- **PATTERN**: Mirror existing execution streaming logic
- **GOTCHA**: Must handle both ScarCommandExecution (v1-2) and ScarActivity (v3) in same stream
- **VALIDATE**: `uv run python -m pytest tests/integration/test_activity_streaming.py -v`

**Implementation** (modify `stream_scar_activity()` function lines 98-176):

```python
async def stream_scar_activity(
    session: AsyncSession, project_id: UUID, verbosity_level: int = 2
) -> AsyncGenerator[Dict, None]:
    """
    Stream SCAR activity updates in real-time.

    Streams:
    - ScarCommandExecution records (verbosity 1-2): Command status updates
    - ScarActivity records (verbosity 3): Line-level execution output

    Args:
        session: Database session
        project_id: Project UUID
        verbosity_level: Minimum verbosity level to include (1=low, 2=medium, 3=high)

    Yields:
        Activity dictionaries as they occur
    """
    logger.info(f"Starting SCAR activity stream for project {project_id} (verbosity: {verbosity_level})")

    last_execution_timestamp = None
    last_activity_id = None  # Track by ID instead of timestamp for activities

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
            .order_by(ScarActivity.timestamp.desc(), ScarActivity.sequence_number.desc())
            .limit(50)
        )
        result = await session.execute(query)
        activities = list(reversed(result.scalars().all()))

        if activities:
            last_activity_id = activities[-1].id
            for activity in activities:
                yield {
                    "id": str(activity.id),
                    "timestamp": activity.timestamp.isoformat(),
                    "source": "scar",
                    "message": activity.message,
                    "verbosity": 3,
                }

    # Poll for new activities
    while True:
        await asyncio.sleep(0.5)  # Match SCAR polling interval

        # Query for new command executions (verbosity 1-2)
        if verbosity_level <= 2 and last_execution_timestamp:
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
                    "timestamp": execution.started_at.isoformat() if execution.started_at else datetime.utcnow().isoformat(),
                    "source": "scar",
                    "message": f"{execution.command_type.value}: {execution.status.value}",
                    "phase": execution.phase.name if execution.phase else None,
                    "verbosity": 2,
                }
                last_execution_timestamp = execution_dict["timestamp"]
                yield execution_dict

        # Query for new detailed activities (verbosity 3)
        if verbosity_level >= 3:
            if last_activity_id:
                # Get activities created after last_activity_id
                # Use timestamp + sequence_number for ordering
                last_activity_result = await session.execute(
                    select(ScarActivity).where(ScarActivity.id == last_activity_id)
                )
                last_activity = last_activity_result.scalar_one_or_none()

                if last_activity:
                    query = (
                        select(ScarActivity)
                        .where(
                            ScarActivity.project_id == project_id,
                            ScarActivity.timestamp >= last_activity.timestamp,
                        )
                        .order_by(ScarActivity.timestamp.asc(), ScarActivity.sequence_number.asc())
                    )

                    result = await session.execute(query)
                    all_activities = result.scalars().all()

                    # Filter out activities we've already seen
                    new_activities = [a for a in all_activities if a.id != last_activity_id and a.sequence_number > last_activity.sequence_number or a.timestamp > last_activity.timestamp]
                else:
                    new_activities = []
            else:
                # No previous activity, get most recent
                query = (
                    select(ScarActivity)
                    .where(ScarActivity.project_id == project_id)
                    .order_by(ScarActivity.timestamp.desc(), ScarActivity.sequence_number.desc())
                    .limit(1)
                )
                result = await session.execute(query)
                new_activities = result.scalars().all()

            for activity in new_activities:
                activity_dict = {
                    "id": str(activity.id),
                    "timestamp": activity.timestamp.isoformat(),
                    "source": "scar",
                    "message": activity.message,
                    "verbosity": 3,
                }
                last_activity_id = activity.id
                yield activity_dict
```

---

### CREATE `tests/unit/scar/test_incremental_streaming.py`

- **IMPLEMENT**: Unit tests for `stream_messages_incremental()` method
- **PATTERN**: Follow existing test patterns from `test_client.py`
- **IMPORTS**: pytest, respx, ScarClient from fixtures
- **GOTCHA**: Use `async for` to consume generator, verify only new messages yielded
- **VALIDATE**: `uv run python -m pytest tests/unit/scar/test_incremental_streaming.py -v`

**Implementation**:

```python
"""
Unit tests for SCAR incremental message streaming.
"""

from uuid import uuid4

import httpx
import pytest
import respx
from respx import MockRouter

from src.config import Settings
from src.scar.client import ScarClient


@pytest.fixture
def settings():
    """Test settings with SCAR configuration"""
    return Settings(
        scar_base_url="http://localhost:3000",
        scar_timeout_seconds=300,
        scar_conversation_prefix="pm-project-",
        database_url="postgresql+asyncpg://test:test@localhost:5432/test",
    )


@pytest.fixture
def client(settings):
    """SCAR client instance for testing"""
    return ScarClient(settings)


@pytest.fixture
def project_id():
    """Test project UUID"""
    return uuid4()


class TestStreamMessagesIncremental:
    """Tests for ScarClient.stream_messages_incremental()"""

    @pytest.mark.asyncio
    @respx.mock
    async def test_stream_messages_incremental_basic(
        self, client: ScarClient, project_id, respx_mock: MockRouter
    ):
        """Test basic incremental streaming with accumulating messages"""
        conversation_id = f"pm-project-{project_id}"
        call_count = 0

        def dynamic_response(request):
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                # First poll: 1 message
                messages = [
                    {
                        "message": "Starting...",
                        "timestamp": "2024-01-01T00:00:00Z",
                        "direction": "sent",
                    }
                ]
            elif call_count == 2:
                # Second poll: 2 messages (1 new)
                messages = [
                    {
                        "message": "Starting...",
                        "timestamp": "2024-01-01T00:00:00Z",
                        "direction": "sent",
                    },
                    {
                        "message": "Processing...",
                        "timestamp": "2024-01-01T00:00:01Z",
                        "direction": "sent",
                    },
                ]
            else:
                # Subsequent polls: stable (no new messages)
                messages = [
                    {
                        "message": "Starting...",
                        "timestamp": "2024-01-01T00:00:00Z",
                        "direction": "sent",
                    },
                    {
                        "message": "Processing...",
                        "timestamp": "2024-01-01T00:00:01Z",
                        "direction": "sent",
                    },
                ]

            return httpx.Response(
                200, json={"conversationId": conversation_id, "messages": messages}
            )

        respx_mock.get(f"http://localhost:3000/test/messages/{conversation_id}").mock(
            side_effect=dynamic_response
        )

        # Collect all yielded messages
        collected = []
        async for msg in client.stream_messages_incremental(conversation_id, poll_interval=0.1):
            collected.append(msg)

        # Should yield 2 messages total (incrementally)
        assert len(collected) == 2
        assert collected[0].message == "Starting..."
        assert collected[1].message == "Processing..."

    @pytest.mark.asyncio
    @respx.mock
    async def test_stream_messages_incremental_timeout(
        self, client: ScarClient, project_id, respx_mock: MockRouter
    ):
        """Test timeout when messages never stabilize"""
        conversation_id = f"pm-project-{project_id}"
        call_count = 0

        def never_stable(request):
            nonlocal call_count
            call_count += 1
            # Always add new message to prevent stability
            messages = [
                {
                    "message": f"Message {i}",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "direction": "sent",
                }
                for i in range(call_count)
            ]
            return httpx.Response(
                200, json={"conversationId": conversation_id, "messages": messages}
            )

        respx_mock.get(f"http://localhost:3000/test/messages/{conversation_id}").mock(
            side_effect=never_stable
        )

        with pytest.raises(TimeoutError, match="Message stream timed out"):
            collected = []
            async for msg in client.stream_messages_incremental(
                conversation_id, timeout=0.5, poll_interval=0.1
            ):
                collected.append(msg)

    @pytest.mark.asyncio
    @respx.mock
    async def test_stream_messages_incremental_empty_start(
        self, client: ScarClient, project_id, respx_mock: MockRouter
    ):
        """Test streaming when conversation starts empty"""
        conversation_id = f"pm-project-{project_id}"
        call_count = 0

        def dynamic_response(request):
            nonlocal call_count
            call_count += 1

            if call_count <= 2:
                # First 2 polls: no messages
                messages = []
            elif call_count == 3:
                # Third poll: message appears
                messages = [
                    {
                        "message": "Hello",
                        "timestamp": "2024-01-01T00:00:00Z",
                        "direction": "sent",
                    }
                ]
            else:
                # Subsequent: stable
                messages = [
                    {
                        "message": "Hello",
                        "timestamp": "2024-01-01T00:00:00Z",
                        "direction": "sent",
                    }
                ]

            return httpx.Response(
                200, json={"conversationId": conversation_id, "messages": messages}
            )

        respx_mock.get(f"http://localhost:3000/test/messages/{conversation_id}").mock(
            side_effect=dynamic_response
        )

        collected = []
        async for msg in client.stream_messages_incremental(conversation_id, poll_interval=0.1):
            collected.append(msg)

        # Should yield 1 message
        assert len(collected) == 1
        assert collected[0].message == "Hello"
```

---

### CREATE `tests/integration/test_activity_streaming.py`

- **IMPLEMENT**: Integration test for end-to-end activity streaming
- **PATTERN**: Follow integration test patterns from `tests/integration/`
- **IMPORTS**: pytest, db_session fixture, ScarActivity model
- **GOTCHA**: Must create execution first, then activities, then query via SSE service
- **VALIDATE**: `uv run python -m pytest tests/integration/test_activity_streaming.py -v`

**Implementation**:

```python
"""
Integration tests for SCAR activity streaming via SSE feed.
"""

import pytest
from datetime import datetime
from uuid import uuid4

from src.database.models import Project, ScarCommandExecution, ScarActivity, CommandType, ExecutionStatus
from src.services.scar_feed_service import stream_scar_activity


@pytest.mark.asyncio
async def test_stream_activities_verbosity_3(db_session):
    """Test streaming ScarActivity records at verbosity level 3"""
    # Create project
    project = Project(
        name="Test Project",
        github_repo_url="https://github.com/test/repo"
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Create execution
    execution = ScarCommandExecution(
        project_id=project.id,
        command_type=CommandType.PRIME,
        command_args="",
        status=ExecutionStatus.RUNNING,
        started_at=datetime.utcnow(),
    )
    db_session.add(execution)
    await db_session.commit()
    await db_session.refresh(execution)

    # Create activities
    activities = [
        ScarActivity(
            execution_id=execution.id,
            project_id=project.id,
            message="Starting PRIME command",
            sequence_number=0,
            timestamp=datetime.utcnow(),
        ),
        ScarActivity(
            execution_id=execution.id,
            project_id=project.id,
            message="Reading project structure",
            sequence_number=1,
            timestamp=datetime.utcnow(),
        ),
        ScarActivity(
            execution_id=execution.id,
            project_id=project.id,
            message="Analysis complete",
            sequence_number=2,
            timestamp=datetime.utcnow(),
        ),
    ]
    for activity in activities:
        db_session.add(activity)
    await db_session.commit()

    # Stream activities at verbosity 3
    activity_stream = stream_scar_activity(db_session, project.id, verbosity_level=3)

    collected = []
    async for activity_dict in activity_stream:
        collected.append(activity_dict)
        # Break after collecting initial activities (don't wait for polling loop)
        if len(collected) >= 3:
            break

    # Verify we got all 3 activities
    assert len(collected) == 3
    assert collected[0]["message"] == "Starting PRIME command"
    assert collected[1]["message"] == "Reading project structure"
    assert collected[2]["message"] == "Analysis complete"
    assert all(a["verbosity"] == 3 for a in collected)


@pytest.mark.asyncio
async def test_stream_activities_verbosity_2_no_details(db_session):
    """Test that verbosity 2 does not include ScarActivity records"""
    # Create project
    project = Project(
        name="Test Project",
        github_repo_url="https://github.com/test/repo"
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Create execution
    execution = ScarCommandExecution(
        project_id=project.id,
        command_type=CommandType.PRIME,
        command_args="",
        status=ExecutionStatus.COMPLETED,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
    )
    db_session.add(execution)
    await db_session.commit()
    await db_session.refresh(execution)

    # Create activities (should NOT appear at verbosity 2)
    activity = ScarActivity(
        execution_id=execution.id,
        project_id=project.id,
        message="Detailed line",
        sequence_number=0,
        timestamp=datetime.utcnow(),
    )
    db_session.add(activity)
    await db_session.commit()

    # Stream at verbosity 2
    activity_stream = stream_scar_activity(db_session, project.id, verbosity_level=2)

    collected = []
    async for activity_dict in activity_stream:
        collected.append(activity_dict)
        # Break after collecting initial activities
        if len(collected) >= 1:
            break

    # Should only get command execution, not the detailed activity
    assert len(collected) == 1
    assert "PRIME: COMPLETED" in collected[0]["message"]
    assert collected[0]["verbosity"] == 2
```

---

### OPTIONAL: Update Frontend (Already Has Basic Support)

The frontend already displays activities line-by-line. This task is optional and only needed if there are rendering issues with increased volume.

- **TEST**: Manually verify frontend handles increased activity volume
- **PATTERN**: Existing `ScarActivityFeed.tsx` already renders messages line-by-line
- **GOTCHA**: Lots of activities might cause performance issues (test with long commands)
- **VALIDATE**: Manual testing in browser

**No code changes needed** - frontend already supports this via existing `ScarActivity` interface and mapping.

---

## TESTING STRATEGY

### Unit Tests

**Coverage Target**: 80%+ for new code

**Test Files**:
- `tests/unit/scar/test_incremental_streaming.py` - Incremental streaming with respx mocks
- Existing: `tests/unit/scar/test_client.py` - Verify no regressions

**Key Test Scenarios**:
- Incremental streaming yields only new messages
- Timeout when messages never stabilize
- Empty conversation that later gets messages
- Multiple messages arriving in batches

### Integration Tests

**Test Files**:
- `tests/integration/test_activity_streaming.py` - End-to-end activity streaming
- Existing: `tests/services/test_scar_executor.py` - Verify execution creates activities

**Test Scenarios**:
- Execute command and verify activities are created with sequence numbers
- Activities are committed immediately (visible during execution)
- SSE feed streams activities at verbosity 3
- Verbosity 1-2 unchanged (no activities, only command status)

### Manual Testing

**Test Scenarios**:
1. **Verbosity 1**: Only "PRIME: RUNNING" → "PRIME: COMPLETED"
2. **Verbosity 2**: Command status updates (existing behavior)
3. **Verbosity 3**: Line-by-line SCAR output streaming in real-time

**Test Steps**:
1. Start backend: `uv run uvicorn src.main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Open browser to `http://localhost:3002`
4. Select/create project with GitHub repo
5. Send message that triggers SCAR command (e.g., "analyze codebase")
6. Set verbosity to "High" (3) in right panel
7. Observe activities appear line-by-line in real-time
8. Verify activities have timestamps close to "now" (within seconds)
9. Test with verbosity 1 and 2 to ensure backward compatibility

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
uv run python -c "from src.database.models import ScarActivity; print('✓ ScarActivity table exists')"
```

### Level 3: Unit Tests

**Run incremental streaming tests:**

```bash
uv run python -m pytest tests/unit/scar/test_incremental_streaming.py -v
```

**Expected**: All tests pass

**Run existing SCAR client tests (regression check):**

```bash
uv run python -m pytest tests/unit/scar/test_client.py -v
```

**Expected**: All tests pass (no regressions)

### Level 4: Integration Tests

**Run activity streaming integration tests:**

```bash
uv run python -m pytest tests/integration/test_activity_streaming.py -v
```

**Expected**: All tests pass

**Run existing executor tests (regression check):**

```bash
uv run python -m pytest tests/services/test_scar_executor.py -v
```

**Expected**: All tests pass (activities created during execution)

### Level 5: Full Test Suite

**Run all tests:**

```bash
uv run python -m pytest tests/ -v
```

**Expected**: All tests pass, no regressions

### Level 6: Type Checking

**Run mypy type checking:**

```bash
uv run mypy src/scar/client.py src/services/scar_executor.py src/services/scar_feed_service.py
```

**Expected**: No type errors

### Level 7: Linting

**Run ruff linting:**

```bash
uv run ruff check src/scar/ src/services/scar_executor.py src/services/scar_feed_service.py
```

**Expected**: No linting errors

**Auto-fix issues:**

```bash
uv run ruff check --fix src/
```

### Level 8: Manual End-to-End Testing

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
4. Set verbosity to "High" (3) in right panel
5. Observe SSE feed in right panel
6. Verify activities appear line-by-line in real-time
7. Test all 3 verbosity levels (1, 2, 3)
8. Verify verbosity 1-2 unchanged (backward compatible)

**Expected Behavior**:
- Verbosity 1: Only "PRIME: RUNNING" → "PRIME: COMPLETED"
- Verbosity 2: Command executions with status updates (existing)
- Verbosity 3: Line-by-line SCAR output streaming in real-time

---

## ACCEPTANCE CRITERIA

- [ ] Feature implements line-by-line SCAR activity streaming
- [ ] All validation commands pass with zero errors
- [ ] Unit test coverage ≥80% for new code
- [ ] Integration tests verify end-to-end workflow
- [ ] Code follows project conventions (snake_case, PascalCase, async patterns)
- [ ] No regressions in existing functionality (all existing tests pass)
- [ ] Database migration applies successfully
- [ ] SSE feed streams activities in real-time (<1s latency)
- [ ] Frontend displays activities line-by-line without performance issues
- [ ] Verbosity filtering works correctly (1=low, 2=medium, 3=high)
- [ ] Backward compatibility maintained (verbosity 1-2 unchanged)
- [ ] Performance is acceptable (0.5s polling doesn't overload DB)
- [ ] Manual testing confirms real-time transparency

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
- [ ] SSE feed performance verified (multiple concurrent connections)

---

## NOTES

### Design Decisions

**Line-by-Line vs. Tool Parsing**:
- **Reality**: SCAR Test Adapter returns plain text agent responses, not structured tool invocations
- **Decision**: Stream messages line-by-line instead of attempting fragile regex parsing
- **Benefit**: Reliable, simple, transparent output without parsing brittleness
- **Trade-off**: Less semantic structure (no "bash command" vs "file read" distinction), but more reliable

**Polling Frequency**:
- **Decision**: Reduce from 2.0s to 0.5s for both SCAR client and SSE feed
- **Benefit**: Near real-time updates (500ms latency vs 2s)
- **Cost**: 4x more database queries
- **Mitigation**: Indexed queries on (project_id, timestamp), tested performance

**Database Storage**:
- **Decision**: Store each line as separate `ScarActivity` record
- **Benefit**: Historical view, replay capabilities, easy streaming
- **Cost**: ~50-200 activities per command execution
- **Storage**: Acceptable for MVP, can add retention policy later

**Backward Compatibility**:
- **Critical**: Verbosity levels 1-2 must remain unchanged
- **Approach**: Only query `ScarActivity` when `verbosity_level >= 3`
- **Validation**: Integration tests verify levels 1-2 unaffected

### Future Enhancements

**Performance Optimizations**:
- Virtual scrolling in frontend for large activity lists
- Activity aggregation (combine consecutive lines from same execution)
- Retention policy (delete activities >30 days)

**Advanced Features**:
- Filter by keyword/regex
- Search through historical activities
- Export execution trace
- "Replay" feature to step through execution

**True Streaming** (requires SCAR API change):
- If SCAR adds WebSocket/SSE support, replace polling with subscription
- Eliminate latency and reduce database load

### Breaking Changes

**None** - This is a pure enhancement. Existing verbosity levels 1-2 continue to work exactly as before. Level 3 gains new line-level detail.

### Migration Notes

**Database Migration Required**: Run `uv run alembic upgrade head` before deploying

**Backward Compatibility**: Existing `ScarCommandExecution` records continue to work. New `ScarActivity` table is additive.

**Rollback Plan**: If issues occur, run `uv run alembic downgrade -1` to remove `scar_activities` table

---

## RESEARCH VALIDATION

**Key Findings from Codebase Analysis**:
1. SCAR messages are plain text, not structured JSON (confirmed in `src/scar/types.py`)
2. Frontend already handles line-by-line display (confirmed in `ScarActivityFeed.tsx`)
3. Existing tests use respx for HTTP mocking (pattern to follow)
4. Database session pattern: commit immediately for SSE visibility (pattern from `scar_executor.py`)

**Gap Analysis from Previous Plan**:
- **Previous Assumption**: SCAR outputs structured tool invocations → **Incorrect**
- **Reality**: SCAR returns plain text agent responses → **Line-by-line streaming is correct approach**
- **Previous**: Complex regex parsing for tool types → **Unnecessary and fragile**
- **Current**: Simple line splitting → **Reliable and maintainable**

---

## CONFIDENCE ASSESSMENT

**One-Pass Implementation Confidence**: 8/10

**Rationale**:
- ✅ Clear understanding of SCAR message format (plain text, not structured)
- ✅ Simple line-by-line parsing (no complex regex)
- ✅ Existing patterns well-documented (async, database, SSE)
- ✅ Comprehensive test coverage plan
- ⚠️ Performance under load needs monitoring (0.5s polling frequency)
- ⚠️ Frontend volume handling needs manual testing

**Risks**:
1. **Database Performance**: 0.5s polling might cause connection pool exhaustion under load
   - **Mitigation**: Indexed queries, test with concurrent connections
2. **Frontend Performance**: Hundreds of activities might slow UI rendering
   - **Mitigation**: Manual testing with long commands, virtual scrolling if needed
3. **Message Ordering**: Activities must maintain strict sequence
   - **Mitigation**: `sequence_number` field ensures ordering

**Success Indicators**:
- All tests pass on first run
- No regressions in existing functionality
- Manual testing shows real-time updates within 1s
- Performance acceptable under normal load (5-10 concurrent projects)
