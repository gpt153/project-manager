# Feature: Fix SSE Feed - Complete Root Cause Analysis and Implementation

The following plan should be complete, but it's important that you validate documentation and codebase patterns and task sanity before you start implementing.

Pay special attention to naming of existing utils types and models. Import from the right files etc.

## Feature Description

Fix the Server-Sent Events (SSE) activity feed in the WebUI that is not displaying real-time SCAR command executions despite:
- Backend logs showing successful SCAR execution
- Previous fixes for timestamp comparison (PR #46)
- Previous fixes for event listeners (PR #48)

The issue persists in Issue #45 and new Issue #49, indicating a deeper problem in the execution flow.

## User Story

As a user of the Project Manager WebUI
I want to see real-time SCAR command execution activity in the right pane SSE feed
So that I can monitor what SCAR is doing and have transparency into system operations

## Problem Statement

**Current Symptoms:**
1. User sends message requesting codebase analysis
2. PM responds with analysis results
3. SSE feed (right pane) remains completely empty - NO activity shown
4. Backend logs show SCAR commands executing successfully
5. Database may or may not have ScarCommandExecution records

**Evidence from Issue #45:**
- Backend logs: "Executing SCAR command: prime" → "SCAR command completed successfully"
- User: "nothing turns up in right pane"
- PM provides analysis WITHOUT visible SCAR activity

**Critical Questions:**
1. Is the Agent actually calling `execute_scar()` tool?
2. Are ScarCommandExecution records being created in database?
3. Is SSE feed service querying correctly?
4. Is frontend receiving SSE events?

## Solution Statement

Perform systematic Root Cause Analysis with diagnostic scripts to identify the exact failure point. Based on findings, implement targeted fixes ensuring:
1. Agent reliably invokes execute_scar tool for analysis requests
2. ScarCommandExecution records are created and committed to database
3. SSE feed service detects and streams new records
4. Frontend receives and displays activities in real-time

## Feature Metadata

**Feature Type**: Bug Fix / Root Cause Analysis
**Estimated Complexity**: Medium-High
**Primary Systems Affected**:
- Agent orchestrator (`src/agent/orchestrator_agent.py`)
- Agent prompts (`src/agent/prompts.py`)
- SCAR executor (`src/services/scar_executor.py`)
- SSE feed service (`src/services/scar_feed_service.py`)
- SSE endpoint (`src/api/sse.py`)
- Database models (`src/database/models.py`)
- Frontend hook (`frontend/src/hooks/useScarFeed.ts`)

**Dependencies**:
- `sse-starlette==2.1.0`
- `sqlalchemy[asyncio]>=2.0.36`
- `pydantic-ai>=0.0.65`
- `fastapi>=0.115.0`

---

## CONTEXT REFERENCES

### Relevant Codebase Files IMPORTANT: YOU MUST READ THESE FILES BEFORE IMPLEMENTING!

**Agent & Tool Layer:**
- `src/agent/orchestrator_agent.py` (lines 269-316) - **Why**: execute_scar tool definition and invocation
- `src/agent/prompts.py` (lines 251-276) - **Why**: System prompt guidance for SCAR execution
- `src/agent/tools.py` - **Why**: Tool registration patterns

**SCAR Execution Layer:**
- `src/services/scar_executor.py` (lines 49-150) - **Why**: Creates ScarCommandExecution records, commits to database
- `src/scar/client.py` - **Why**: SCAR HTTP client implementation

**SSE Streaming Layer:**
- `src/api/sse.py` (lines 22-104) - **Why**: SSE endpoint that streams events to frontend
- `src/services/scar_feed_service.py` (lines 71-149) - **Why**: Database polling logic for new activities

**Database Layer:**
- `src/database/models.py` (lines 248-301) - **Why**: ScarCommandExecution model with @property methods
- `src/database/connection.py` (lines 32-62) - **Why**: Session configuration (expire_on_commit=False)

**Frontend Layer:**
- `frontend/src/hooks/useScarFeed.ts` - **Why**: EventSource client, event listeners
- `frontend/src/components/RightPanel/ScarActivityFeed.tsx` - **Why**: UI rendering of activities

### Recent Fixes (Already Merged)

**Commit d928ef6 (Jan 6, 2026) - PR #46**: Fixed SSE polling timestamp comparison
- **Problem**: UUID comparison failed (UUIDs not chronological)
- **Solution**: Changed to `started_at > last_dt`
- **File**: `src/services/scar_feed_service.py` (lines 111-119)

**Commit 8d8ceb3 (Jan 6, 2026) - PR #48**: Fixed frontend event listeners
- **Problem**: Using `onmessage` which only catches unnamed events
- **Solution**: Changed to `addEventListener('activity', ...)`
- **File**: `frontend/src/hooks/useScarFeed.ts` (lines 23-32)

**Commit 00f82a5 (Jan 5, 2026) - PR #41**: Added execute_scar tool to agent
- Enabled agent to call SCAR executor directly
- **File**: `src/agent/orchestrator_agent.py` (lines 269-316)

### Relevant Documentation YOU SHOULD READ THESE BEFORE IMPLEMENTING!

- [Pydantic AI Tools](https://ai.pydantic.dev/tools/)
  - Section: Tool definition with RunContext
  - **Why**: Understanding agent tool invocation patterns
- [FastAPI Server-Sent Events](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)
  - Section: EventSourceResponse with async generators
  - **Why**: SSE implementation patterns
- [sse-starlette](https://github.com/sysid/sse-starlette)
  - Section: Event formatting `{"event": "type", "data": "json"}`
  - **Why**: Proper SSE event structure
- [SQLAlchemy Async Sessions](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
  - Section: Session lifecycle, transaction isolation
  - **Why**: Database session management in SSE streams

### Patterns to Follow

**Agent Tool Pattern with RunContext:**
```python
# From src/agent/orchestrator_agent.py (lines 280-316)
@agent.tool
async def execute_scar(
    ctx: RunContext[AgentDependencies],
    command: str,
    args: Optional[list[str]] = None
) -> dict:
    """Execute a SCAR command."""
    # Tool implementation with ctx.deps access
    result = await execute_scar_command(
        ctx.deps.session,
        ctx.deps.project_id,
        scar_cmd,
        args or []
    )
    return {
        "success": result.success,
        "output": result.output,
        "duration": result.duration_seconds
    }
```

**Database Record Creation Pattern:**
```python
# From src/services/scar_executor.py (lines 85-95)
execution = ScarCommandExecution(
    project_id=project_id,
    phase_id=phase_id,
    command_type=_command_to_type(command),
    command_args=args_str,
    status=ExecutionStatus.QUEUED,
    started_at=datetime.utcnow(),  # ← CRITICAL for polling
)
session.add(execution)
await session.commit()  # ← Must commit to make visible
await session.refresh(execution)
```

**SSE Polling Pattern (Post-Fixes):**
```python
# From src/services/scar_feed_service.py (lines 105-119)
while True:
    await asyncio.sleep(2)  # Poll every 2 seconds

    if last_timestamp:
        last_dt = datetime.fromisoformat(last_timestamp)
        query = (
            select(ScarCommandExecution)
            .where(
                ScarCommandExecution.project_id == project_id,
                ScarCommandExecution.started_at > last_dt,  # ← Timestamp comparison
            )
            .order_by(ScarCommandExecution.started_at.asc())
        )
```

**Enhanced Logging Pattern:**
```python
logger.info(
    "Agent invoking execute_scar tool",
    extra={
        "execution_id": str(execution.id),
        "project_id": str(project_id),
        "command": command.value,
    }
)
```

---

## IMPLEMENTATION PLAN

### Phase 1: Root Cause Analysis (Diagnostic)

**Objective**: Systematically identify where the execution flow breaks using diagnostic scripts and enhanced logging.

### Phase 2: Targeted Fix Implementation

**Objective**: Fix identified issues with minimal, targeted changes.

### Phase 3: Regression Prevention

**Objective**: Add integration tests and monitoring to prevent future regressions.

---

## STEP-BY-STEP TASKS

IMPORTANT: Execute every task in order, top to bottom. Each task is atomic and independently testable.

### CREATE scripts/debug_scar_executions.py

- **IMPLEMENT**: Database inspection script
- **PURPOSE**: Verify if ScarCommandExecution records exist
- **IMPORTS**:
  ```python
  import asyncio
  from sqlalchemy import select, desc
  from src.database.connection import async_session_maker
  from src.database.models import ScarCommandExecution, Project
  ```
- **LOGIC**:
  ```python
  async def inspect_scar_executions():
      """Query and display ScarCommandExecution records."""
      async with async_session_maker() as session:
          projects = (await session.execute(select(Project))).scalars().all()

          print(f"Found {len(projects)} projects\n")

          for project in projects:
              print(f"Project: {project.name} ({project.id})")

              query = (
                  select(ScarCommandExecution)
                  .where(ScarCommandExecution.project_id == project.id)
                  .order_by(desc(ScarCommandExecution.started_at))
                  .limit(10)
              )
              executions = (await session.execute(query)).scalars().all()

              if executions:
                  print(f"  Recent SCAR executions: {len(executions)}")
                  for exec in executions:
                      print(f"    - {exec.command_type.value}: {exec.status.value} at {exec.started_at}")
              else:
                  print("  ⚠️  No SCAR executions found!")
              print()

  if __name__ == "__main__":
      asyncio.run(inspect_scar_executions())
  ```
- **VALIDATE**:
  ```bash
  uv run python scripts/debug_scar_executions.py
  ```
  **Expected**: Lists projects with execution history. Empty = SCAR executor not creating records.

### CREATE scripts/test_sse_endpoint.py

- **IMPLEMENT**: SSE client test script
- **PURPOSE**: Verify SSE endpoint streams correctly
- **IMPORTS**:
  ```python
  import asyncio
  import httpx
  import json
  import sys
  ```
- **LOGIC**:
  ```python
  async def test_sse_endpoint(project_id: str, verbosity: int = 2, duration: int = 30):
      """Connect to SSE endpoint and print events."""
      url = f"http://localhost:8000/api/sse/scar/{project_id}?verbosity={verbosity}"
      print(f"Connecting to: {url}\n")

      async with httpx.AsyncClient(timeout=None) as client:
          async with client.stream("GET", url) as response:
              if response.status_code != 200:
                  print(f"❌ HTTP {response.status_code}: {response.text}")
                  return False

              print(f"✅ Connected (HTTP {response.status_code})\n")

              event_count = 0
              start_time = asyncio.get_event_loop().time()

              async for line in response.aiter_lines():
                  if asyncio.get_event_loop().time() - start_time > duration:
                      break

                  if line.startswith("event: "):
                      event_type = line[7:]
                      print(f"[Event Type] {event_type}")
                  elif line.startswith("data: "):
                      data = json.loads(line[6:])
                      print(f"[Event {event_count}] {data}")
                      event_count += 1

              print(f"\nReceived {event_count} events in {duration}s")
              return event_count > 0

  if __name__ == "__main__":
      if len(sys.argv) < 2:
          print("Usage: python scripts/test_sse_endpoint.py <project_id> [verbosity] [duration]")
          sys.exit(1)

      project_id = sys.argv[1]
      verbosity = int(sys.argv[2]) if len(sys.argv) > 2 else 2
      duration = int(sys.argv[3]) if len(sys.argv) > 3 else 30

      success = asyncio.run(test_sse_endpoint(project_id, verbosity, duration))
      sys.exit(0 if success else 1)
  ```
- **VALIDATE**:
  ```bash
  # Get project ID
  PROJECT_ID=$(uv run python -c "import asyncio; from src.database.connection import async_session_maker; from src.database.models import Project; from sqlalchemy import select; async def f(): async with async_session_maker() as s: p = (await s.execute(select(Project).limit(1))).scalar_one(); print(p.id); asyncio.run(f())")

  # Test SSE (run for 10 seconds)
  uv run python scripts/test_sse_endpoint.py $PROJECT_ID 2 10
  ```
  **Expected**: Connection succeeds, heartbeat events received

### CREATE scripts/test_e2e_sse.py

- **IMPLEMENT**: End-to-end integration test
- **PURPOSE**: Create execution record and verify SSE streams it
- **IMPORTS**:
  ```python
  import asyncio
  import httpx
  import json
  import sys
  from datetime import datetime
  from sqlalchemy import select
  from src.database.connection import async_session_maker
  from src.database.models import Project, ScarCommandExecution, CommandType, ExecutionStatus
  ```
- **LOGIC**:
  ```python
  async def test_e2e_sse():
      """End-to-end: Create execution → Verify SSE streams it."""

      # Get test project
      async with async_session_maker() as session:
          project = (await session.execute(select(Project).limit(1))).scalar_one()
          project_id = project.id
          print(f"Using project: {project.name} ({project_id})\n")

      # Start SSE listener in background
      sse_events = []

      async def sse_listener():
          url = f"http://localhost:8000/api/sse/scar/{project_id}?verbosity=2"
          async with httpx.AsyncClient(timeout=None) as client:
              async with client.stream("GET", url) as response:
                  async for line in response.aiter_lines():
                      if line.startswith("data: "):
                          data = json.loads(line[6:])
                          sse_events.append(data)
                          print(f"[SSE] {data.get('message')}")

      sse_task = asyncio.create_task(sse_listener())
      await asyncio.sleep(1)  # Let SSE connect

      # Create test execution
      print("Creating test SCAR execution record...\n")
      async with async_session_maker() as session:
          execution = ScarCommandExecution(
              project_id=project_id,
              command_type=CommandType.PRIME,
              command_args="test e2e",
              status=ExecutionStatus.COMPLETED,
              started_at=datetime.utcnow(),
              completed_at=datetime.utcnow(),
              output="Test execution for SSE e2e validation"
          )
          session.add(execution)
          await session.commit()
          await session.refresh(execution)

          execution_id = str(execution.id)
          print(f"Created: {execution.command_type.value} ({execution_id})\n")

      # Wait for SSE to detect (2s poll + buffer)
      print("Waiting 5 seconds for SSE to detect and stream...\n")
      await asyncio.sleep(5)

      sse_task.cancel()

      # Check results
      execution_ids = [e.get("id") for e in sse_events]

      if execution_id in execution_ids:
          print(f"✅ SUCCESS: SSE streamed the execution record")
          print(f"   Received {len(sse_events)} events")
          return True
      else:
          print(f"❌ FAILURE: Execution {execution_id} not in SSE feed")
          print(f"   SSE events received: {len(sse_events)}")
          if sse_events:
              print(f"   Event IDs: {execution_ids}")
          return False

  if __name__ == "__main__":
      success = asyncio.run(test_e2e_sse())
      sys.exit(0 if success else 1)
  ```
- **VALIDATE**:
  ```bash
  uv run python scripts/test_e2e_sse.py
  ```
  **Expected**: Creates record, SSE detects within 5 seconds

### ADD enhanced logging to orchestrator_agent.py

- **FILE**: `src/agent/orchestrator_agent.py`
- **PATTERN**: Existing logger
- **ADD AFTER LINE 285** (in execute_scar tool, before executor call):
  ```python
  logger.info(
      "Agent invoking execute_scar tool",
      extra={
          "project_id": str(ctx.deps.project_id),
          "command": command,
          "args": args,
      }
  )
  ```
- **ADD AFTER LINE 310** (after executor returns):
  ```python
  logger.info(
      "execute_scar tool completed",
      extra={
          "project_id": str(ctx.deps.project_id),
          "command": command,
          "success": result.success,
          "duration": result.duration_seconds,
      }
  )
  ```
- **VALIDATE**: Logs show when agent calls tool

### ADD enhanced logging to scar_executor.py

- **FILE**: `src/services/scar_executor.py`
- **ADD AFTER LINE 95** (after session.add(execution)):
  ```python
  logger.info(
      "Created ScarCommandExecution record in database",
      extra={
          "execution_id": str(execution.id),
          "project_id": str(project_id),
          "command": command.value,
          "status": "QUEUED",
      }
  )
  ```
- **ADD AFTER LINE 102** (after updating to RUNNING):
  ```python
  logger.info(
      "Updated ScarCommandExecution status to RUNNING",
      extra={"execution_id": str(execution.id), "status": "RUNNING"}
  )
  ```
- **ADD AFTER LINE 139** (after updating to COMPLETED):
  ```python
  logger.info(
      "Updated ScarCommandExecution status to COMPLETED",
      extra={
          "execution_id": str(execution.id),
          "output_length": len(output) if output else 0,
          "duration": result.duration_seconds if result else 0,
      }
  )
  ```
- **VALIDATE**: Logs include execution_id throughout lifecycle

### ADD enhanced logging to scar_feed_service.py

- **FILE**: `src/services/scar_feed_service.py`
- **ADD AFTER LINE 129** (after querying new activities):
  ```python
  if new_activities:
      logger.debug(
          "SSE feed detected new activities",
          extra={
              "project_id": str(project_id),
              "count": len(new_activities),
              "activity_ids": [str(a.id) for a in new_activities],
          }
      )
  else:
      logger.debug(
          "SSE feed poll: no new activities",
          extra={"project_id": str(project_id), "last_timestamp": last_timestamp}
      )
  ```
- **VALIDATE**: Logs show SSE polling activity

### RUN diagnostic suite and create RCA report

- **EXECUTE**: Run all diagnostic scripts
- **CREATE**: `.agents/reports/rca-sse-feed-issue-49.md`
- **COMMANDS**:
  ```bash
  # Start backend
  uv run uvicorn src.main:app --reload &
  BACKEND_PID=$!
  sleep 5

  # Run diagnostics
  echo "=== 1. Database Inspection ===" > rca-output.txt
  uv run python scripts/debug_scar_executions.py >> rca-output.txt 2>&1

  echo -e "\n=== 2. SSE Endpoint Test ===" >> rca-output.txt
  PROJECT_ID=$(uv run python -c "import asyncio; from src.database.connection import async_session_maker; from src.database.models import Project; from sqlalchemy import select; async def f(): async with async_session_maker() as s: p = (await s.execute(select(Project).limit(1))).scalar_one(); print(p.id); asyncio.run(f())")
  uv run python scripts/test_sse_endpoint.py $PROJECT_ID 2 10 >> rca-output.txt 2>&1

  echo -e "\n=== 3. End-to-End SSE Test ===" >> rca-output.txt
  uv run python scripts/test_e2e_sse.py >> rca-output.txt 2>&1

  echo -e "\n=== 4. Application Logs ===" >> rca-output.txt
  tail -100 logs/app.log | grep -E "execute_scar|ScarCommandExecution|SSE" >> rca-output.txt 2>&1

  kill $BACKEND_PID
  cat rca-output.txt
  ```
- **CREATE REPORT** with structure:
  ```markdown
  # Root Cause Analysis: SSE Feed Not Displaying (Issue #49)

  ## Investigation Date
  {DATE}

  ## Diagnostic Test Results

  ### 1. Database Inspection Test
  **Result**: [PASS/FAIL]
  **Findings**: {details}

  ### 2. SSE Endpoint Test
  **Result**: [PASS/FAIL]
  **Findings**: {details}

  ### 3. End-to-End Integration Test
  **Result**: [PASS/FAIL]
  **Findings**: {details}

  ### 4. Application Logs Analysis
  **Key Observations**: {details}

  ## Root Cause Hypothesis
  {hypothesis with evidence}

  ## Recommended Fix
  {specific fix description}
  ```
- **VALIDATE**: RCA clearly identifies failure point

### IMPLEMENT fix based on RCA findings

- **CONDITIONAL**: Depends on RCA results
- **PATTERN**: Minimal targeted fix

**If RCA shows: No database records**
  - **ROOT CAUSE**: Agent not calling execute_scar or executor failing
  - **FILES**: `src/agent/prompts.py`, `src/agent/orchestrator_agent.py`
  - **FIX**: Strengthen system prompt, ensure tool is always called
  - **VALIDATE**: Re-run database inspection

**If RCA shows: Database records exist but SSE not streaming**
  - **ROOT CAUSE**: SSE polling logic issue
  - **FILE**: `src/services/scar_feed_service.py`
  - **FIX**: Debug query, verify timestamp comparison
  - **VALIDATE**: Re-run E2E test

**If RCA shows: SSE streaming but frontend not receiving**
  - **ROOT CAUSE**: Frontend EventSource or CORS issue
  - **FILES**: `frontend/src/hooks/useScarFeed.ts`, `src/main.py`
  - **FIX**: Add error handling, check CORS config
  - **VALIDATE**: Browser DevTools inspection

**If RCA shows: Agent not calling execute_scar**
  - **ROOT CAUSE**: System prompt insufficient
  - **FILE**: `src/agent/prompts.py`
  - **FIX**: Make tool invocation mandatory for analysis
  - **VALIDATE**: Check logs for tool invocation

### CREATE integration test

- **LOCATION**: `tests/api/test_sse_feed.py`
- **PURPOSE**: Prevent regression
- **IMPORTS**:
  ```python
  import pytest
  import asyncio
  import json
  from datetime import datetime
  from httpx import AsyncClient, ASGITransport
  from src.main import app
  from src.database.connection import async_session_maker
  from src.database.models import ScarCommandExecution, CommandType, ExecutionStatus
  ```
- **TEST**:
  ```python
  @pytest.mark.asyncio
  async def test_sse_feed_streams_scar_executions(test_project):
      """Test that SSE feed streams SCAR execution records."""

      # Create test execution
      async with async_session_maker() as session:
          execution = ScarCommandExecution(
              project_id=test_project.id,
              command_type=CommandType.PRIME,
              command_args="test",
              status=ExecutionStatus.COMPLETED,
              started_at=datetime.utcnow(),
              output="Test output"
          )
          session.add(execution)
          await session.commit()
          await session.refresh(execution)
          execution_id = str(execution.id)

      # Connect to SSE endpoint
      transport = ASGITransport(app=app)
      async with AsyncClient(transport=transport, base_url="http://test") as client:
          events = []

          async with client.stream(
              "GET", f"/api/sse/scar/{test_project.id}?verbosity=2"
          ) as response:
              assert response.status_code == 200

              # Collect events for 5 seconds
              timeout = asyncio.get_event_loop().time() + 5
              async for line in response.aiter_lines():
                  if asyncio.get_event_loop().time() > timeout:
                      break

                  if line.startswith("data: "):
                      data = json.loads(line[6:])
                      events.append(data)

          # Verify execution appeared
          event_ids = [e["id"] for e in events]
          assert execution_id in event_ids, f"Execution {execution_id} not found in SSE feed"
  ```
- **VALIDATE**:
  ```bash
  uv run pytest tests/api/test_sse_feed.py -v
  ```

### CREATE troubleshooting documentation

- **LOCATION**: `docs/troubleshooting-sse-feed.md`
- **CONTENT**:
  ```markdown
  # SSE Feed Troubleshooting Guide

  ## Architecture

  \```
  User Message → WebSocket → Orchestrator Agent → SCAR Executor → Database
                                                                      ↓
  Frontend ← SSE Endpoint ← SSE Feed Service (Polling 2s) ← Database
  \```

  ## Common Issue: Empty SSE Feed

  **Symptoms**: Right pane shows no activity despite PM responding.

  **Diagnostic Steps**:

  1. **Check database records:**
     \```bash
     uv run python scripts/debug_scar_executions.py
     \```
     - No records = Agent not calling execute_scar
     - Has records = SSE polling issue

  2. **Test SSE endpoint:**
     \```bash
     uv run python scripts/test_sse_endpoint.py <project-id> 2 10
     \```
     - Should see heartbeat events

  3. **Run E2E test:**
     \```bash
     uv run python scripts/test_e2e_sse.py
     \```
     - Creates record, verifies SSE streams it

  4. **Check logs:**
     \```bash
     tail -f logs/app.log | grep -E "execute_scar|ScarCommandExecution|SSE"
     \```
     - Look for: "Agent invoking execute_scar tool"
     - Look for: "Created ScarCommandExecution record"
     - Look for: "SSE feed detected new activities"

  **Common Root Causes**:
  1. Agent not calling execute_scar
  2. Database transaction not committed
  3. SSE polling logic broken
  4. Frontend EventSource not connecting
  5. SCAR service not running

  ## Manual Testing

  1. Start backend: `uv run uvicorn src.main:app`
  2. Start frontend: `cd frontend && npm run dev`
  3. Open DevTools → Network tab
  4. Send: "analyze the codebase"
  5. Verify:
     - Network shows `/api/sse/scar/{id}` (type: eventsource)
     - Console shows "SSE connected"
     - Right pane shows activities
  ```
- **VALIDATE**: Documentation is clear and complete

---

## TESTING STRATEGY

### Diagnostic Tests (Manual)

1. **Database Inspection**: `scripts/debug_scar_executions.py`
   - Validates: Records exist in database

2. **SSE Endpoint Test**: `scripts/test_sse_endpoint.py`
   - Validates: Endpoint streams events

3. **End-to-End Test**: `scripts/test_e2e_sse.py`
   - Validates: Complete flow works

### Integration Tests (Automated)

1. **SSE Feed Test**: `tests/api/test_sse_feed.py`
   - Framework: pytest async
   - Validates: SSE streams execution records

### Manual WebUI Validation

1. Send "analyze the codebase"
2. Check right pane shows activity
3. Verify real-time updates

---

## VALIDATION COMMANDS

Execute every command to ensure zero regressions and 100% feature correctness.

### Level 1: Import Validation (CRITICAL)

```bash
uv run python -c "from src.main import app; from src.services.scar_feed_service import stream_scar_activity; from src.services.scar_executor import execute_scar_command; print('✓ All imports valid')"
```

**Expected**: "✓ All imports valid"

### Level 2: Diagnostic Suite

```bash
# Start backend
uv run uvicorn src.main:app --reload &
BACKEND_PID=$!
sleep 5

# Run diagnostics
echo "=== Database Inspection ==="
uv run python scripts/debug_scar_executions.py

echo -e "\n=== SSE Endpoint Test ==="
PROJECT_ID=$(uv run python -c "import asyncio; from src.database.connection import async_session_maker; from src.database.models import Project; from sqlalchemy import select; async def f(): async with async_session_maker() as s: p = (await s.execute(select(Project).limit(1))).scalar_one(); print(p.id); asyncio.run(f())")
uv run python scripts/test_sse_endpoint.py $PROJECT_ID 2 10

echo -e "\n=== End-to-End SSE Test ==="
uv run python scripts/test_e2e_sse.py

kill $BACKEND_PID
```

**Expected**: All diagnostics pass

### Level 3: Linting & Formatting

```bash
uv run ruff check src/ scripts/ tests/
uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
```

**Expected**: No errors

### Level 4: Unit Tests

```bash
uv run pytest tests/unit/ -v
```

**Expected**: All tests pass

### Level 5: Integration Tests

```bash
uv run pytest tests/api/test_sse_feed.py -v
```

**Expected**: SSE feed test passes

### Level 6: Manual WebUI Validation

```bash
# Terminal 1: Backend
uv run uvicorn src.main:app --reload

# Terminal 2: Frontend
cd frontend && npm run dev

# Terminal 3: Logs
tail -f logs/app.log | grep -E "execute_scar|ScarCommandExecution|SSE"
```

**Manual Steps**:
1. Open `http://localhost:5173`
2. Open DevTools (F12) → Console + Network
3. Select project
4. Send: "analyze the codebase"
5. Verify:
   - ✅ Network shows SSE connection
   - ✅ Console shows "SSE connected"
   - ✅ Right pane shows activity within 2-5s
   - ✅ Logs show complete flow

### Level 7: Regression Check

```bash
uv run pytest -v
curl http://localhost:8000/health
curl http://localhost:8000/api/projects
```

**Expected**: All tests pass, endpoints respond

---

## ACCEPTANCE CRITERIA

- [ ] RCA completed with clear root cause identification
- [ ] All diagnostic scripts execute successfully
- [ ] Root cause fix implemented and tested
- [ ] SSE feed streams SCAR records within 2-5 seconds
- [ ] WebUI displays SCAR activity in real-time
- [ ] Enhanced logging added (execution_id tracking)
- [ ] Integration test added (`tests/api/test_sse_feed.py`)
- [ ] All existing tests pass
- [ ] Manual WebUI test confirms functionality
- [ ] Troubleshooting documentation created
- [ ] No regressions in other features

---

## COMPLETION CHECKLIST

- [ ] All diagnostic scripts created
- [ ] Enhanced logging added to agent, executor, feed service
- [ ] Diagnostic suite executed
- [ ] RCA report created with findings
- [ ] Root cause identified with evidence
- [ ] Targeted fix implemented
- [ ] Integration test created
- [ ] All validation commands executed successfully
- [ ] Manual WebUI test confirms fix
- [ ] Troubleshooting guide created
- [ ] Code reviewed for quality
- [ ] All acceptance criteria met

---

## NOTES

### Key Insights

1. **Previous Fixes Applied**:
   - d928ef6: Timestamp comparison (UUID → timestamp)
   - 8d8ceb3: Event listeners (onmessage → addEventListener)
   - 00f82a5: execute_scar tool added to agent

2. **Session Configuration Correct**:
   - `expire_on_commit=False` allows object access after commit
   - Sessions commit after operations
   - SSE uses independent session

3. **Most Likely Root Causes** (priority order):
   1. **Agent not invoking execute_scar**: Despite prompt, may not call tool
   2. **SCAR connectivity failure**: SCAR HTTP API unreachable
   3. **Database commit issue**: Records not persisted
   4. **Frontend connection issue**: EventSource not connecting
   5. **SSE polling regression**: Query not detecting records

### Implementation Strategy

1. **Phase 1 (RCA)**: Run diagnostics to identify exact failure
2. **Phase 2 (Fix)**: Implement targeted fix
3. **Phase 3 (Test)**: Verify with automated and manual tests
4. **Phase 4 (Document)**: Update troubleshooting guide

### Edge Cases

- Concurrent SCAR executions: Stream all chronologically
- SSE connection drops: EventSource auto-reconnects
- Long execution (>300s): Handle timeout gracefully
- Message before completion: Show RUNNING then COMPLETED

### Performance Considerations

- 2-second polling: Acceptable latency
- 30-second heartbeat: Keeps connection alive
- Timestamp index: Efficient querying
- Long-lived connections: FastAPI handles well

### Security Considerations

- Project ID validation: Verify user access
- CORS: Permissive in dev, strict in prod
- Rate limiting: Apply to SSE endpoint
