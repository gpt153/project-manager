# Feature: Real-Time Detailed SCAR Subprocess Output Streaming via SSE

The following plan should be complete, but it's important that you validate documentation and codebase patterns before implementing.

Pay special attention to naming of existing utils, types, and models. Import from the right files etc.

## Feature Description

Replace simulated SCAR execution with real Claude Agent SDK integration, capturing and streaming detailed subprocess output (bash commands, file operations, tool invocations) in real-time via Server-Sent Events (SSE) to the WebUI. Users will see granular execution details like "🔧 BASH: git ls-files" and "📖 READ: README.md" as they happen, matching the transparency of Claude Code CLI.

## User Story

As a Project Manager WebUI user
I want to see detailed, real-time SCAR execution output showing individual tool invocations (bash, file reads, searches)
So that I can understand exactly what operations are being performed and track progress during long-running commands like `/command-invoke prime`

## Problem Statement

**Current State**:
- SCAR execution is completely simulated via `_simulate_scar_execution()` in `scar_executor.py`
- No actual integration with Claude Code/SCAR exists
- SSE feed shows only high-level status updates: "PRIME: COMPLETED"
- Users have no visibility into what SCAR is actually doing

**Root Cause**:
- No Claude Agent SDK integration (dependency missing)
- No SCAR client implementation (src/scar/ is empty)
- SSE feed has no structured activity data to stream

**Desired State**:
- Real Claude Agent SDK subprocess integration
- Stream tool-level events as they occur
- Parse and store structured activities in database
- SSE feed shows granular, real-time activity stream

## Solution Statement

Implement full Claude Agent SDK integration with real-time activity streaming:

1. **SDK Integration**: Use `claude-agent-sdk` to spawn Claude Code subprocess and stream tool events
2. **Activity Extraction**: Parse tool blocks (bash, read, write, grep, etc.) into structured activities
3. **Database Model**: Store activities with type, tool name, parameters, output
4. **Real-Time Streaming**: Create activities during execution, poll database for SSE feed
5. **Frontend Enhancement**: Map activity types to icons (bash → 🔧, read → 📖)

## Feature Metadata

**Feature Type**: New Capability + Enhancement
**Estimated Complexity**: High
**Primary Systems Affected**: SCAR integration, Database schema, SCAR executor, SSE feed service

**Dependencies**:
- **NEW**: `claude-agent-sdk>=0.1.0`
- Existing: `sse-starlette`, `sqlalchemy[asyncio]`, `httpx`

---

## CONTEXT REFERENCES

### Relevant Codebase Files IMPORTANT: YOU MUST READ THESE FILES BEFORE IMPLEMENTING!

**SCAR Integration (Currently Simulated)**:
- `src/services/scar_executor.py` (lines 46-204) - Current execution logic, replace simulation with real SDK
- `src/scar/__init__.py` - Empty module, add client implementation

**Database Layer**:
- `src/database/models.py` (lines 247-298) - `ScarCommandExecution` model, add `ScarActivity` and relationship
- `src/database/connection.py` (lines 14-25) - Async session maker pattern

**SSE Streaming**:
- `src/services/scar_feed_service.py` (lines 18-131) - Activity retrieval and streaming, query `ScarActivity` table
- `src/api/sse.py` (lines 22-108) - SSE endpoint configuration

**Configuration**:
- `src/config.py` (lines 12-71) - Settings pattern, add SCAR config (timeout, working directory)

### New Files to Create

- `src/scar/client.py` - Claude Agent SDK wrapper
- `src/scar/types.py` - Pydantic models for activities
- `src/scar/activity_extractor.py` - Parse SDK messages to activities
- `src/database/migrations/versions/XXX_add_scar_activity.py` - Alembic migration
- `tests/unit/scar/test_client.py` - Client unit tests
- `tests/unit/scar/test_activity_extractor.py` - Extractor tests
- `tests/services/test_scar_integration.py` - Integration tests

### Relevant Documentation

**Claude Agent SDK**:
- [Agent SDK Python Reference](https://platform.claude.com/docs/en/agent-sdk/python) - Core SDK API
- [GitHub - claude-agent-sdk-python](https://github.com/anthropics/claude-agent-sdk-python) - Examples in examples/
- [Building agents with Claude SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk) - Tool event handling

**Server-Sent Events**:
- [sse-starlette GitHub](https://github.com/sysid/sse-starlette) - EventSourceResponse patterns

### Patterns to Follow

**Async Session Pattern**:
```python
async with async_session_maker() as session:
    await session.commit()
```

**Database Model Pattern**:
```python
class Model(Base):
    __tablename__ = "table"
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    relationship_name = relationship("OtherModel", back_populates="this")
```

**Claude SDK Streaming Pattern**:
```python
from claude_agent_sdk import ClaudeSDKClient

async with ClaudeSDKClient() as client:
    await client.query("Analyze this codebase")
    async for msg in client.receive_response():
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, ToolUseBlock):
                    # Extract tool: block.name, block.input
```

---

## IMPLEMENTATION PLAN

### Phase 1: Foundation - SDK Integration and Types

**Tasks**:
- Add `claude-agent-sdk` dependency to `pyproject.toml`
- Create `ScarClient` wrapping Claude Agent SDK
- Define Pydantic types for activities
- Add SCAR configuration to settings

### Phase 2: Activity Extraction and Database

**Tasks**:
- Create `ActivityExtractor` to parse `ToolUseBlock` and `ToolResultBlock`
- Add `ScarActivity` model to database
- Create Alembic migration
- Write unit tests for activity extraction

### Phase 3: Replace Simulation with Real SDK

**Tasks**:
- Replace `_simulate_scar_execution()` with real SDK integration
- Stream messages from SDK and create activities incrementally
- Update status tracking for real execution
- Handle SDK errors gracefully

### Phase 4: Real-Time SSE Feed

**Tasks**:
- Update `scar_feed_service.py` to query `ScarActivity` table
- Implement timestamp-based polling
- Maintain backward compatibility

### Phase 5: Testing and Validation

**Tasks**:
- Unit tests for client and extractor
- Integration tests for full execution flow
- E2E test for SSE feed streaming

---

## STEP-BY-STEP TASKS

### UPDATE pyproject.toml - Add dependency

- **ADD**: `"claude-agent-sdk>=0.1.0",` after line 18
- **VALIDATE**: `uv sync && uv run python -c "import claude_agent_sdk; print('✓ SDK installed')"`

### UPDATE src/config.py - Add SCAR settings

- **ADD** after line 40:
```python
# SCAR / Claude Code Integration
scar_working_directory: str = "/tmp/scar-workspace"
scar_timeout_seconds: int = 300  # 5 minutes
scar_poll_interval: float = 0.5
claude_code_cli_path: Optional[str] = None
```
- **VALIDATE**: `uv run python -c "from src.config import settings; print(f'✓ Timeout: {settings.scar_timeout_seconds}s')"`

### CREATE src/scar/types.py - Define types

- **IMPLEMENT**: `ActivityType` enum, `ScarMessage`, `ParsedActivity` models
- **PATTERN**: Use Pydantic BaseModel, match SDK message structure
- **VALIDATE**: `uv run python -c "from src.scar.types import ActivityType; print('✓ Types valid')"`

**Key Types**:
```python
class ActivityType(str, Enum):
    BASH_COMMAND = "bash_command"
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_EDIT = "file_edit"
    GREP_SEARCH = "grep_search"
    GLOB_SEARCH = "glob_search"
    TASK_SPAWN = "task_spawn"
    AGENT_RESPONSE = "agent_response"
    ERROR = "error"

class ScarMessage(BaseModel):
    message_type: str  # "ToolUseBlock", "TextBlock", etc.
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tool_name: Optional[str] = None
    tool_input: Optional[dict] = None
    tool_output: Optional[str] = None

class ParsedActivity(BaseModel):
    activity_type: ActivityType
    message: str
    tool_name: Optional[str] = None
    parameters: dict = Field(default_factory=dict)
    output: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

### CREATE src/scar/client.py - SDK wrapper

- **IMPLEMENT**: `ScarClient` class with async context manager
- **PATTERN**: Wrap `ClaudeSDKClient`, stream messages
- **IMPORTS**: `claude_agent_sdk`, `asyncio`, `logging`, `src.scar.types`, `src.config`
- **VALIDATE**: `uv run python -c "from src.scar.client import ScarClient; print('✓ Client valid')"`

**Key Methods**:
```python
class ScarClient:
    async def __aenter__(self) -> "ScarClient":
        self._client = ClaudeSDKClient()
        await self._client.__aenter__()
        return self

    async def stream_messages(self, command: str) -> AsyncGenerator[ScarMessage, None]:
        await self._client.query(command)
        async for msg in self._client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, ToolUseBlock):
                        yield ScarMessage(
                            message_type="ToolUseBlock",
                            tool_name=block.name,
                            tool_input=block.input,
                        )
```

### CREATE src/scar/activity_extractor.py - Parse messages

- **IMPLEMENT**: `ActivityExtractor.extract(message)` static method
- **PATTERN**: Map tool names (bash, read, write, etc.) to activity types
- **VALIDATE**: `uv run python -c "from src.scar.activity_extractor import ActivityExtractor; print('✓ Extractor valid')"`

**Extraction Logic**:
```python
class ActivityExtractor:
    @staticmethod
    def extract(message: ScarMessage) -> Optional[ParsedActivity]:
        if message.message_type == "ToolUseBlock":
            tool_name = message.tool_name or "unknown"
            if tool_name == "bash":
                return ParsedActivity(
                    activity_type=ActivityType.BASH_COMMAND,
                    message=f"Running: {message.tool_input.get('command')}",
                    tool_name=tool_name,
                    parameters=message.tool_input,
                )
            elif tool_name == "read":
                return ParsedActivity(
                    activity_type=ActivityType.FILE_READ,
                    message=f"Reading: {message.tool_input.get('file_path')}",
                    tool_name=tool_name,
                    parameters=message.tool_input,
                )
            # ... similar for write, edit, grep, glob, task
        elif message.message_type == "TextBlock":
            return ParsedActivity(
                activity_type=ActivityType.AGENT_RESPONSE,
                message=message.content,
            )
        return None
```

### UPDATE src/database/models.py - Add ScarActivity

- **ADD** after line 298:
```python
class ScarActivity(Base):
    __tablename__ = "scar_activities"
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    execution_id = Column(PGUUID(as_uuid=True), ForeignKey("scar_executions.id"), nullable=False)
    activity_type = Column(String(50), nullable=False)
    tool_name = Column(String(50), nullable=True)
    message = Column(Text, nullable=False)
    parameters = Column(JSONB, nullable=True)
    output = Column(Text, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    execution = relationship("ScarCommandExecution", back_populates="activities")
```
- **UPDATE** ScarCommandExecution (line 266): Add `activities = relationship("ScarActivity", back_populates="execution", cascade="all, delete-orphan")`
- **VALIDATE**: `uv run python -c "from src.database.models import ScarActivity; print('✓ Model valid')"`

### CREATE Migration - scar_activities table

- **RUN**: `alembic revision --autogenerate -m "Add scar_activities table"`
- **VERIFY**: Migration includes table, foreign key, indexes on execution_id and timestamp
- **RUN**: `alembic upgrade head`
- **VALIDATE**: `uv run python -c "from sqlalchemy import inspect; from src.database.connection import engine; assert 'scar_activities' in inspect(engine).get_table_names(); print('✓ Migration applied')"`

### UPDATE src/services/scar_executor.py - Real SDK integration

- **REPLACE** `_simulate_scar_execution()` (lines 148-204) with `_execute_with_sdk()`
- **ADD**: Import `ScarClient`, `ActivityExtractor`, `ScarActivity`
- **PATTERN**: Stream messages, create activities incrementally, commit during stream
- **VALIDATE**: `uv run python -c "from src.services.scar_executor import execute_scar_command; print('✓ Executor valid')"`

**New Implementation**:
```python
async def _execute_with_sdk(
    session: AsyncSession, execution: ScarCommandExecution, prompt: str
) -> tuple[str, Optional[str], int]:
    from src.scar.client import ScarClient
    from src.scar.activity_extractor import ActivityExtractor
    from src.database.models import ScarActivity

    message_texts, activity_count, error = [], 0, None

    try:
        async with ScarClient() as client:
            async for message in client.stream_messages(prompt):
                message_texts.append(message.content)
                parsed = ActivityExtractor.extract(message)
                if parsed:
                    activity = ScarActivity(
                        execution_id=execution.id,
                        activity_type=parsed.activity_type.value,
                        tool_name=parsed.tool_name,
                        message=parsed.message,
                        parameters=parsed.parameters,
                        output=parsed.output,
                        timestamp=parsed.timestamp,
                    )
                    session.add(activity)
                    activity_count += 1
                    await session.commit()  # Incremental commit for real-time
    except Exception as e:
        error = str(e)

    return "\n".join(message_texts), error, activity_count

def _command_to_prompt(command: ScarCommand, args: Optional[list[str]]) -> str:
    """Convert SCAR command to natural language prompt"""
    if command == ScarCommand.PRIME:
        return "Analyze this codebase thoroughly. Read key files, understand architecture."
    # ... similar for other commands
```

### UPDATE src/services/scar_feed_service.py - Query activities

- **REFACTOR** `get_recent_scar_activity()` to query `ScarActivity` table (lines 18-58)
- **UPDATE** `stream_scar_activity()` to poll for new activities (lines 94-130)
- **PATTERN**: Join `ScarActivity` with `ScarCommandExecution` on `execution_id`
- **VALIDATE**: `uv run python -c "from src.services.scar_feed_service import stream_scar_activity; print('✓ Feed service valid')"`

**Updated Queries**:
```python
async def get_recent_scar_activity(...) -> List[Dict]:
    from src.database.models import ScarActivity, ScarCommandExecution

    query = (
        select(ScarActivity)
        .join(ScarCommandExecution, ScarActivity.execution_id == ScarCommandExecution.id)
        .where(ScarCommandExecution.project_id == project_id)
        .order_by(ScarActivity.timestamp.desc())
        .limit(limit)
    )

    result = await session.execute(query)
    activities = result.scalars().all()

    return [{
        "id": str(activity.id),
        "timestamp": activity.timestamp.isoformat(),
        "source": activity.activity_type,  # bash_command, file_read, etc.
        "tool_name": activity.tool_name,
        "message": activity.message,
        "parameters": activity.parameters or {},
        "output": activity.output,
    } for activity in reversed(activities)]
```

### CREATE tests/unit/scar/test_client.py - Client tests

- **IMPLEMENT**: Test initialization, context manager, message streaming
- **PATTERN**: Mock `ClaudeSDKClient` to avoid real subprocess
- **VALIDATE**: `pytest tests/unit/scar/test_client.py -v`

### CREATE tests/unit/scar/test_activity_extractor.py - Extractor tests

- **IMPLEMENT**: Test all tool types (bash, read, write, grep, glob), unknown tools, text blocks
- **PATTERN**: Parametrized tests
- **VALIDATE**: `pytest tests/unit/scar/test_activity_extractor.py -v`

### CREATE tests/services/test_scar_integration.py - Integration tests

- **IMPLEMENT**: E2E test of command execution with activity creation
- **PATTERN**: Mock SDK client, verify activities in database
- **VALIDATE**: `pytest tests/services/test_scar_integration.py -v`

---

## TESTING STRATEGY

### Unit Tests
- `test_client.py`: Client initialization, streaming, error handling
- `test_activity_extractor.py`: All tool types, edge cases
- Coverage target: ≥ 90% for new modules

### Integration Tests
- `test_scar_integration.py`: Full execution flow, activity creation
- Coverage target: All command types

### Manual Testing (Optional)
- Requires Anthropic API key
- Run backend, trigger SCAR command, verify SSE feed shows real-time activities

---

## VALIDATION COMMANDS

### Level 1: Dependency Installation
```bash
uv sync
uv run python -c "import claude_agent_sdk; print('✓ SDK installed')"
```

### Level 2: Import Validation
```bash
uv run python -c "from src.scar.types import ActivityType; print('✓ Types valid')"
uv run python -c "from src.scar.client import ScarClient; print('✓ Client valid')"
uv run python -c "from src.scar.activity_extractor import ActivityExtractor; print('✓ Extractor valid')"
uv run python -c "from src.database.models import ScarActivity; print('✓ Model valid')"
```

### Level 3: Database Migration
```bash
alembic upgrade head
uv run python -c "from sqlalchemy import inspect; from src.database.connection import engine; assert 'scar_activities' in inspect(engine).get_table_names(); print('✓ Migration applied')"
```

### Level 4: Unit Tests
```bash
pytest tests/unit/scar/ -v
```

### Level 5: Integration Tests
```bash
pytest tests/services/test_scar_integration.py -v
```

### Level 6: Full Test Suite
```bash
pytest tests/ -v --tb=short
```

---

## ACCEPTANCE CRITERIA

- [ ] Claude Agent SDK installed and importable
- [ ] `ScarClient` successfully wraps SDK and streams messages
- [ ] `ActivityExtractor` parses tool events with ≥ 90% accuracy
- [ ] `ScarActivity` table created with proper indexes
- [ ] Activities created incrementally during execution (real-time)
- [ ] SSE feed streams activities from database
- [ ] All validation commands pass
- [ ] Unit test coverage ≥ 90% for new modules
- [ ] Integration tests verify end-to-end SDK usage
- [ ] No regressions in existing functionality

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Each task validated immediately
- [ ] All validation commands passed
- [ ] Full test suite passes
- [ ] No linting or type errors
- [ ] Database migration runs cleanly
- [ ] Acceptance criteria all met
- [ ] Code reviewed for quality

---

## NOTES

### Design Decisions

**Why Claude Agent SDK?**
- Handles subprocess lifecycle, JSON streaming
- Provides typed message structures
- Officially supported by Anthropic

**Why incremental activity creation?**
- Real-time visibility into SCAR progress
- Matches Claude Code CLI UX
- Reduces perceived latency

**Why separate ScarActivity table?**
- Efficient timestamp-based polling
- Rich frontend rendering
- Easier debugging

### Trade-offs

**Pros**:
- ✅ Real SCAR integration
- ✅ Structured activity data
- ✅ Real-time streaming
- ✅ Activity history

**Cons**:
- ⚠️ Requires Claude Agent SDK dependency
- ⚠️ Requires Anthropic API key
- ⚠️ Subprocess complexity
- ⚠️ Increased database writes

### Research Sources

- [Agent SDK Python Reference](https://platform.claude.com/docs/en/agent-sdk/python)
- [GitHub - claude-agent-sdk-python](https://github.com/anthropics/claude-agent-sdk-python)
- [Building agents with Claude SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk)
- [sse-starlette GitHub](https://github.com/sysid/sse-starlette)
