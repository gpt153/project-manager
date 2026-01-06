# Feature: Fix SSE Feed - Complete Root Cause Solution

The following plan should be complete, but its important that you validate documentation and codebase patterns and task sanity before you start implementing.

Pay special attention to naming of existing utils types and models. Import from the right files etc.

## Feature Description

The SSE feed (WebUI right panel) is completely broken - users cannot see real-time SCAR activity despite PM successfully executing SCAR commands. Issue #45 attempted fix but the root cause remains: **Direct SCAR execution in orchestrator_agent.py bypasses proper SSE event flow**. This plan fixes the complete event chain: SCAR execution → database records → SSE streaming → frontend display.

## User Story

As a user of the Project Manager WebUI
I want to see real-time SCAR command execution activity in the SSE feed right panel
So that I have full transparency into what SCAR is doing when analyzing my codebase

## Problem Statement

**Critical Issue**: SSE feed remains empty despite backend logs showing successful SCAR execution.

**Evidence from Issue #45**:
```
Backend logs (14:24):
"Executing SCAR command: prime"
"SCAR command completed successfully"

User experience:
Right pane: Empty (no activity shown)
PM response: Provides analysis WITHOUT visible SCAR activity
```

**Root Cause Analysis**:

The `execute_scar` tool in `orchestrator_agent.py` (lines 269-316) calls `execute_scar_command()` from `scar_executor.py`, which DOES create `ScarCommandExecution` records. However, the SSE feed service (`scar_feed_service.py`) has a critical flaw in its polling logic:

1. **Initial Query Problem** (lines 95-101): Gets initial activities and yields them
2. **Polling Logic Issue** (lines 104-148): Polls for NEW activities using `started_at > last_dt`
3. **Critical Bug**: When a SCAR command executes AFTER SSE connects, the record IS created but polling query might not detect it due to:
   - Session isolation (SSE uses own session)
   - Timestamp precision issues
   - Query execution timing (2s poll interval)

**Why Previous Fixes Failed**:
- PR #46: Fixed UUID comparison → timestamp (correct but insufficient)
- PR #48: Fixed frontend event listeners (correct but insufficient)
- **Missing**: Database session refresh, proper logging, and query validation

## Solution Statement

Implement comprehensive fix targeting the complete data flow:

1. **Enhanced Logging**: Add execution_id tracking throughout the entire flow
2. **Session Management**: Ensure database sessions properly commit and refresh records
3. **SSE Query Fix**: Improve polling query with better timestamp handling
4. **Diagnostic Tools**: Create scripts to validate each stage of the pipeline
5. **Integration Tests**: Add end-to-end tests to prevent regression

## Feature Metadata

**Feature Type**: Bug Fix / System Integration
**Estimated Complexity**: Medium-High
**Primary Systems Affected**:
- SCAR executor (`src/services/scar_executor.py`)
- SSE feed service (`src/services/scar_feed_service.py`)
- SSE endpoint (`src/api/sse.py`)
- Orchestrator agent (`src/agent/orchestrator_agent.py`)

**Dependencies**:
- `sse-starlette==2.1.0`
- `sqlalchemy[asyncio]>=2.0.36`
- `pydantic-ai>=0.0.14`
- `fastapi>=0.115.0`

---

## CONTEXT REFERENCES

### Relevant Codebase Files IMPORTANT: YOU MUST READ THESE FILES BEFORE IMPLEMENTING!

**Execution Layer**:
- `src/agent/orchestrator_agent.py` (lines 269-316) - Why: execute_scar tool implementation
- `src/services/scar_executor.py` (lines 49-233) - Why: Creates ScarCommandExecution records

**SSE Streaming Layer**:
- `src/services/scar_feed_service.py` (lines 71-149) - Why: CRITICAL - Polling logic with bug
- `src/api/sse.py` (lines 22-104) - Why: SSE endpoint and session management

**Database Layer**:
- `src/database/models.py` (lines 248-301) - Why: ScarCommandExecution model with @property methods
- `src/database/connection.py` (lines 32-62) - Why: Session factory configuration

**Frontend**:
- `frontend/src/hooks/useScarFeed.ts` (lines 23-32) - Why: EventSource client (already fixed in PR #48)

### New Files to Create

- `scripts/debug_sse_flow.py` - Complete diagnostic tool
- `tests/integration/test_sse_feed_e2e.py` - End-to-end integration test

### Relevant Documentation YOU SHOULD READ THESE BEFORE IMPLEMENTING!

- [sse-starlette EventSourceResponse](https://github.com/sysid/sse-starlette#usage)
  - Why: Proper SSE event formatting and session handling
- [SQLAlchemy Async Session Lifecycle](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#asyncio-session-lifecycle)
  - Why: Understanding expire_on_commit and session isolation
- [FastAPI Async Dependencies](https://fastapi.tiangolo.com/async/#asynchronous-code)
  - Why: Session management in long-lived SSE connections

### Patterns to Follow

**Enhanced Logging Pattern**:
```python
# From src/services/scar_executor.py (lines 108-111)
logger.info(
    "SCAR command execution",
    extra={
        "execution_id": str(execution.id),
        "project_id": str(project_id),
        "command": command.value,
    }
)
```

**Database Record Creation**:
```python
# From src/services/scar_executor.py (lines 85-95)
execution = ScarCommandExecution(
    project_id=project_id,
    command_type=_command_to_type(command),
    status=ExecutionStatus.QUEUED,
    started_at=datetime.utcnow(),
)
session.add(execution)
await session.commit()  # CRITICAL: Makes record visible to other sessions
await session.refresh(execution)  # CRITICAL: Refreshes instance
```

**SSE Polling Pattern** (CURRENT - HAS BUG):
```python
# From src/services/scar_feed_service.py (lines 105-119)
if last_timestamp:
    last_dt = datetime.fromisoformat(last_timestamp)
    query = (
        select(ScarCommandExecution)
        .where(
            ScarCommandExecution.project_id == project_id,
            ScarCommandExecution.started_at > last_dt,  # Can miss records
        )
        .order_by(ScarCommandExecution.started_at.asc())
    )
```

**Frontend Event Listener** (FIXED in PR #48):
```typescript
// From frontend/src/hooks/useScarFeed.ts (lines 23-27)
eventSource.addEventListener('activity', (event) => {
  const activity: ScarActivity = JSON.parse(event.data);
  setActivities((prev) => [...prev, activity]);
});
```

---

## IMPLEMENTATION PLAN

### Phase 1: Diagnostic Foundation

Create comprehensive diagnostic tools to validate each stage of the pipeline.

**Tasks**:
- Create database inspection script
- Create SSE endpoint test script
- Create end-to-end validation script

### Phase 2: Enhanced Logging

Add execution_id tracking throughout the complete flow to enable debugging.

**Tasks**:
- Add logging to orchestrator_agent.py
- Add logging to scar_executor.py
- Add logging to scar_feed_service.py

### Phase 3: Core SSE Polling Fix

Fix the SSE feed service polling logic to reliably detect new records.

**Tasks**:
- Improve timestamp handling in polling query
- Add session refresh before querying
- Add explicit logging for detected activities

### Phase 4: Integration Testing

Create automated tests to prevent regression.

**Tasks**:
- Create E2E integration test
- Add unit tests for polling logic
- Manual WebUI validation

---

## STEP-BY-STEP TASKS

IMPORTANT: Execute every task in order, top to bottom. Each task is atomic and independently testable.

### CREATE scripts/debug_sse_flow.py

- **IMPLEMENT**: Comprehensive diagnostic script
- **PURPOSE**: Validate each stage: database → SSE query → SSE stream
- **IMPORTS**:
  ```python
  import asyncio
  import sys
  from datetime import datetime
  from sqlalchemy import select, desc
  from src.database.connection import async_session_maker
  from src.database.models import ScarCommandExecution, Project
  ```
- **LOGIC**:
  ```python
  async def check_database_records(project_id=None):
      """Check if ScarCommandExecution records exist."""
      async with async_session_maker() as session:
          if project_id:
              query = select(ScarCommandExecution).where(
                  ScarCommandExecution.project_id == project_id
              ).order_by(desc(ScarCommandExecution.started_at)).limit(10)
          else:
              query = select(ScarCommandExecution).order_by(
                  desc(ScarCommandExecution.started_at)
              ).limit(10)

          result = await session.execute(query)
          executions = result.scalars().all()

          print(f"\n=== Database Records ===")
          print(f"Found {len(executions)} SCAR executions\n")

          for exec in executions:
              print(f"ID: {exec.id}")
              print(f"  Project: {exec.project_id}")
              print(f"  Command: {exec.command_type.value}")
              print(f"  Status: {exec.status.value}")
              print(f"  Started: {exec.started_at}")
              print(f"  Completed: {exec.completed_at}")
              print()

          return len(executions) > 0

  async def test_sse_query(project_id):
      """Test SSE feed service query logic."""
      from src.services.scar_feed_service import get_recent_scar_activity

      async with async_session_maker() as session:
          activities = await get_recent_scar_activity(session, project_id, limit=10)

          print(f"\n=== SSE Feed Query Result ===")
          print(f"Found {len(activities)} activities\n")

          for activity in activities:
              print(f"Activity: {activity['id']}")
              print(f"  Message: {activity['message']}")
              print(f"  Timestamp: {activity['timestamp']}")
              print(f"  Source: {activity['source']}")
              print()

          return len(activities) > 0

  async def main():
      if len(sys.argv) > 1:
          project_id = sys.argv[1]
      else:
          # Get first project
          async with async_session_maker() as session:
              result = await session.execute(select(Project).limit(1))
              project = result.scalar_one_or_none()
              if not project:
                  print("ERROR: No projects found in database")
                  return False
              project_id = project.id
              print(f"Using project: {project.name} ({project_id})")

      # Test database records
      has_records = await check_database_records(project_id)

      if not has_records:
          print("❌ FAIL: No ScarCommandExecution records in database")
          print("   → Root cause: Agent not calling execute_scar tool")
          return False

      # Test SSE query
      has_activities = await test_sse_query(project_id)

      if not has_activities:
          print("❌ FAIL: Records exist but SSE query returns empty")
          print("   → Root cause: SSE feed service query logic broken")
          return False

      print("✅ PASS: Pipeline validated - records exist and SSE query works")
      return True

  if __name__ == "__main__":
      success = asyncio.run(main())
      sys.exit(0 if success else 1)
  ```
- **VALIDATE**:
  ```bash
  uv run python scripts/debug_sse_flow.py
  ```
  **Expected**: Shows database records and SSE query results

### CREATE scripts/test_sse_endpoint.py

- **IMPLEMENT**: SSE endpoint connection test
- **PURPOSE**: Verify SSE endpoint streams events correctly
- **IMPORTS**:
  ```python
  import asyncio
  import httpx
  import json
  import sys
  from datetime import datetime
  ```
- **LOGIC**:
  ```python
  async def test_sse_connection(project_id, duration=15):
      """Connect to SSE endpoint and collect events."""
      url = f"http://localhost:8000/api/sse/scar/{project_id}?verbosity=2"
      print(f"Connecting to: {url}\n")

      events = []

      try:
          async with httpx.AsyncClient(timeout=None) as client:
              async with client.stream("GET", url) as response:
                  if response.status_code != 200:
                      print(f"❌ Connection failed: HTTP {response.status_code}")
                      return False

                  print(f"✅ Connected (HTTP {response.status_code})\n")
                  print(f"Listening for {duration} seconds...\n")

                  start = asyncio.get_event_loop().time()

                  async for line in response.aiter_lines():
                      if asyncio.get_event_loop().time() - start > duration:
                          break

                      if line.startswith("event: "):
                          event_type = line[7:]
                          print(f"[Event Type] {event_type}")
                      elif line.startswith("data: "):
                          data = json.loads(line[6:])
                          events.append(data)
                          print(f"[Event] {data.get('message', data)}")

                  print(f"\n=== Summary ===")
                  print(f"Received {len(events)} events")

                  if events:
                      activity_events = [e for e in events if 'id' in e]
                      heartbeat_events = [e for e in events if 'status' in e]
                      print(f"  - Activity events: {len(activity_events)}")
                      print(f"  - Heartbeat events: {len(heartbeat_events)}")

                  return len(events) > 0

      except Exception as e:
          print(f"❌ Error: {e}")
          return False

  if __name__ == "__main__":
      if len(sys.argv) < 2:
          print("Usage: python scripts/test_sse_endpoint.py <project_id> [duration]")
          sys.exit(1)

      project_id = sys.argv[1]
      duration = int(sys.argv[2]) if len(sys.argv) > 2 else 15

      success = asyncio.run(test_sse_connection(project_id, duration))
      sys.exit(0 if success else 1)
  ```
- **VALIDATE**:
  ```bash
  # Get project ID first
  PROJECT_ID=$(uv run python -c "import asyncio; from src.database.connection import async_session_maker; from src.database.models import Project; from sqlalchemy import select; async def f(): async with async_session_maker() as s: p = (await s.execute(select(Project).limit(1))).scalar_one(); print(str(p.id)); asyncio.run(f())")

  # Test SSE endpoint (15 seconds)
  uv run python scripts/test_sse_endpoint.py $PROJECT_ID 15
  ```
  **Expected**: Shows connection success and streams events

### CREATE scripts/create_test_execution.py

- **IMPLEMENT**: Manual execution record creator
- **PURPOSE**: Create test record to validate SSE detection
- **IMPORTS**:
  ```python
  import asyncio
  from datetime import datetime
  from src.database.connection import async_session_maker
  from src.database.models import ScarCommandExecution, CommandType, ExecutionStatus, Project
  from sqlalchemy import select
  ```
- **LOGIC**:
  ```python
  async def create_test_execution():
      """Create a test SCAR execution record."""
      async with async_session_maker() as session:
          # Get first project
          result = await session.execute(select(Project).limit(1))
          project = result.scalar_one()

          print(f"Creating test execution for project: {project.name}")

          execution = ScarCommandExecution(
              project_id=project.id,
              command_type=CommandType.PRIME,
              command_args="test diagnostic",
              status=ExecutionStatus.COMPLETED,
              started_at=datetime.utcnow(),
              completed_at=datetime.utcnow(),
              output="Test execution created for SSE diagnostic"
          )

          session.add(execution)
          await session.commit()
          await session.refresh(execution)

          print(f"Created execution: {execution.id}")
          print(f"  Status: {execution.status.value}")
          print(f"  Started: {execution.started_at}")
          print(f"\n✅ Test record created successfully")
          print(f"\nSSE feed should detect this within 2-5 seconds")

          return str(execution.id)

  if __name__ == "__main__":
      execution_id = asyncio.run(create_test_execution())
      print(f"\nExecution ID: {execution_id}")
  ```
- **VALIDATE**:
  ```bash
  uv run python scripts/create_test_execution.py
  ```
  **Expected**: Creates record and prints execution ID

### ADD enhanced logging to orchestrator_agent.py

- **FILE**: `src/agent/orchestrator_agent.py`
- **PATTERN**: Add structured logging
- **LOCATION**: Lines 269-316 (execute_scar tool)
- **ADD** after line 289 (before executing command):
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
- **ADD** at top of file if not present:
  ```python
  import logging

  logger = logging.getLogger(__name__)
  ```
- **ADD** after line 309 (after result received):
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
- **VALIDATE**: Check imports resolve
  ```bash
  uv run python -c "from src.agent.orchestrator_agent import orchestrator_agent; print('✓ Imports valid')"
  ```

### ADD enhanced logging to scar_executor.py

- **FILE**: `src/services/scar_executor.py`
- **LOCATION**: Throughout execute_scar_command function
- **ADD** after line 95 (after creating execution record):
  ```python
  logger.info(
      "Created ScarCommandExecution record",
      extra={
          "execution_id": str(execution.id),
          "project_id": str(project_id),
          "command": command.value,
          "status": "QUEUED",
      }
  )
  ```
- **ADD** after line 102 (after status update to RUNNING):
  ```python
  logger.info(
      "ScarCommandExecution status updated",
      extra={
          "execution_id": str(execution.id),
          "status": "RUNNING",
      }
  )
  ```
- **ADD** after line 139 (after status update to COMPLETED):
  ```python
  logger.info(
      "ScarCommandExecution completed",
      extra={
          "execution_id": str(execution.id),
          "status": "COMPLETED",
          "output_length": len(output) if output else 0,
          "duration": duration,
      }
  )
  ```
- **VALIDATE**: Check imports resolve
  ```bash
  uv run python -c "from src.services.scar_executor import execute_scar_command; print('✓ Imports valid')"
  ```

### FIX SSE polling logic in scar_feed_service.py

- **FILE**: `src/services/scar_feed_service.py`
- **PATTERN**: Improve timestamp handling and add logging
- **LOCATION**: Lines 104-148 (stream_scar_activity polling loop)
- **REPLACE** lines 105-148 with:
  ```python
  # Poll for new activities
  while True:
      await asyncio.sleep(2)  # Poll every 2 seconds

      # Query for activities newer than last_timestamp
      if last_timestamp:
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
      else:
          query = (
              select(ScarCommandExecution)
              .where(ScarCommandExecution.project_id == project_id)
              .order_by(desc(ScarCommandExecution.started_at))
              .limit(1)
          )

      result = await session.execute(query)
      new_activities = result.scalars().all()

      # Log polling results
      if new_activities:
          logger.info(
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
              extra={
                  "project_id": str(project_id),
                  "last_timestamp": last_timestamp,
              }
          )

      for activity in new_activities:
          activity_dict = {
              "id": str(activity.id),
              "timestamp": (
                  activity.started_at.isoformat()
                  if activity.started_at
                  else datetime.utcnow().isoformat()
              ),
              "source": activity.source,
              "message": (
                  f"{activity.command_type.value}: {activity.status.value}"
                  if activity.status
                  else activity.command_type.value
              ),
              "phase": activity.phase.name if activity.phase else None,
          }
          last_timestamp = activity_dict["timestamp"]

          logger.debug(
              "Yielding SSE activity",
              extra={
                  "activity_id": activity_dict["id"],
                  "message": activity_dict["message"],
              }
          )

          yield activity_dict
  ```
- **VALIDATE**: Check imports resolve
  ```bash
  uv run python -c "from src.services.scar_feed_service import stream_scar_activity; print('✓ Imports valid')"
  ```

### ADD session refresh in SSE endpoint

- **FILE**: `src/api/sse.py`
- **PATTERN**: Ensure fresh session for each SSE connection
- **LOCATION**: Lines 52-104 (event_generator function)
- **NO CHANGES NEEDED**: Current implementation already creates fresh session per connection (line 56)
- **VALIDATE**: Verify session management is correct
  ```bash
  uv run python -c "from src.api.sse import router; print('✓ SSE endpoint valid')"
  ```

### CREATE integration test

- **CREATE**: `tests/integration/test_sse_feed_e2e.py`
- **PATTERN**: End-to-end test for complete flow
- **IMPORTS**:
  ```python
  import pytest
  import asyncio
  import json
  from datetime import datetime
  from httpx import AsyncClient, ASGITransport
  from src.main import app
  from src.database.connection import async_session_maker
  from src.database.models import ScarCommandExecution, CommandType, ExecutionStatus, Project
  from sqlalchemy import select
  ```
- **TEST**:
  ```python
  @pytest.mark.asyncio
  async def test_sse_feed_streams_new_executions():
      """
      End-to-end test: Create execution record → Verify SSE streams it.

      This test validates the complete pipeline:
      1. Create ScarCommandExecution record in database
      2. SSE feed service polls and detects it
      3. SSE endpoint streams it to client
      4. Client receives activity event
      """
      # Get or create test project
      async with async_session_maker() as session:
          result = await session.execute(select(Project).limit(1))
          project = result.scalar_one_or_none()

          if not project:
              pytest.skip("No test project available")

          project_id = project.id

      # Start SSE client in background
      received_events = []

      async def sse_listener():
          """Listen to SSE endpoint and collect events."""
          transport = ASGITransport(app=app)
          async with AsyncClient(transport=transport, base_url="http://test", timeout=None) as client:
              async with client.stream("GET", f"/api/sse/scar/{project_id}?verbosity=2") as response:
                  assert response.status_code == 200

                  async for line in response.aiter_lines():
                      if line.startswith("data: "):
                          data = json.loads(line[6:])
                          received_events.append(data)

      # Start SSE listener
      sse_task = asyncio.create_task(sse_listener())
      await asyncio.sleep(1)  # Let SSE connect

      # Create test execution record
      async with async_session_maker() as session:
          execution = ScarCommandExecution(
              project_id=project_id,
              command_type=CommandType.PRIME,
              command_args="test e2e",
              status=ExecutionStatus.COMPLETED,
              started_at=datetime.utcnow(),
              completed_at=datetime.utcnow(),
              output="Test execution for E2E SSE validation"
          )
          session.add(execution)
          await session.commit()
          await session.refresh(execution)

          execution_id = str(execution.id)

      # Wait for SSE to detect (2s poll + 1s buffer)
      await asyncio.sleep(5)

      # Cancel SSE task
      sse_task.cancel()
      try:
          await sse_task
      except asyncio.CancelledError:
          pass

      # Verify execution was streamed
      event_ids = [e.get("id") for e in received_events if "id" in e]

      assert execution_id in event_ids, (
          f"Execution {execution_id} not found in SSE feed. "
          f"Received {len(event_ids)} events: {event_ids}"
      )
  ```
- **VALIDATE**:
  ```bash
  uv run pytest tests/integration/test_sse_feed_e2e.py -v
  ```
  **Expected**: Test passes

### RUN complete diagnostic suite

- **EXECUTE**: Run all diagnostic scripts sequentially
- **PURPOSE**: Validate complete pipeline before manual testing
- **COMMANDS**:
  ```bash
  # Start backend in background
  uv run uvicorn src.main:app --reload > /tmp/backend.log 2>&1 &
  BACKEND_PID=$!
  sleep 5

  echo "=== 1. Database Flow Diagnostic ==="
  uv run python scripts/debug_sse_flow.py

  echo -e "\n=== 2. SSE Endpoint Test ==="
  PROJECT_ID=$(uv run python -c "import asyncio; from src.database.connection import async_session_maker; from src.database.models import Project; from sqlalchemy import select; async def f(): async with async_session_maker() as s: p = (await s.execute(select(Project).limit(1))).scalar_one(); print(str(p.id)); asyncio.run(f())")
  uv run python scripts/test_sse_endpoint.py $PROJECT_ID 15 &
  SSE_PID=$!

  # Create test execution while SSE is listening
  sleep 2
  echo -e "\n=== 3. Creating Test Execution ==="
  uv run python scripts/create_test_execution.py

  # Wait for SSE to finish
  wait $SSE_PID

  echo -e "\n=== 4. Checking Application Logs ==="
  tail -50 /tmp/backend.log | grep -E "execute_scar|ScarCommandExecution|SSE"

  # Cleanup
  kill $BACKEND_PID
  ```
- **VALIDATE**: All diagnostics pass, SSE detects test execution

### CREATE troubleshooting documentation

- **CREATE**: `docs/troubleshooting-sse-feed.md`
- **PATTERN**: Step-by-step diagnostic guide
- **CONTENT**:
  ```markdown
  # SSE Feed Troubleshooting Guide

  ## System Architecture

  \```
  User → WebUI → SSE Endpoint → SSE Feed Service → Database
                                        ↑                ↓
                                        |    Polling (2s)
                                        |                |
                      PM Agent → SCAR Executor → ScarCommandExecution
  \```

  ## Common Issue: Empty SSE Feed

  **Symptoms**: Right panel shows "No SCAR activity" despite PM responding.

  **Diagnostic Steps**:

  ### 1. Check Database Records

  \```bash
  uv run python scripts/debug_sse_flow.py
  \```

  **If no records found**:
  - Root cause: PM agent not calling execute_scar tool
  - Check: `src/agent/prompts.py` (system prompt)
  - Check: Application logs for "Agent invoking execute_scar"

  **If records exist**:
  - Proceed to step 2

  ### 2. Test SSE Query

  The debug script also tests SSE query. If query returns empty:
  - Root cause: SSE feed service query logic issue
  - Check: `src/services/scar_feed_service.py` polling logic
  - Check: Timestamp comparison in query

  ### 3. Test SSE Endpoint

  \```bash
  PROJECT_ID=<your-project-id>
  uv run python scripts/test_sse_endpoint.py $PROJECT_ID 15
  \```

  **If connection fails**:
  - Check: Backend is running (`uvicorn src.main:app`)
  - Check: Port 8000 is accessible

  **If no events received**:
  - Root cause: SSE stream not yielding events
  - Check: Application logs for "SSE feed detected new activities"

  ### 4. Create Test Execution

  \```bash
  # Terminal 1: Start SSE listener
  uv run python scripts/test_sse_endpoint.py $PROJECT_ID 30

  # Terminal 2: Create test record (while SSE listening)
  uv run python scripts/create_test_execution.py
  \```

  **Expected**: SSE listener receives activity event within 5 seconds

  **If not received**:
  - Root cause: Polling not detecting new records
  - Check: Session isolation or timestamp precision

  ### 5. Check Application Logs

  \```bash
  tail -f logs/app.log | grep -E "execute_scar|ScarCommandExecution|SSE"
  \```

  **Key log messages**:
  - "Agent invoking execute_scar tool" - Confirms tool called
  - "Created ScarCommandExecution record" - Confirms DB write
  - "SSE feed detected new activities" - Confirms polling works
  - "Yielding SSE activity" - Confirms streaming works

  ## Manual WebUI Testing

  1. Open browser DevTools (F12)
  2. Go to Network tab, filter "eventsource"
  3. Open WebUI, select project
  4. Send message: "analyze the codebase"
  5. Verify:
     - Network shows `/api/sse/scar/{id}` connection
     - Console shows "SSE connected"
     - Right panel shows activity within 5 seconds

  ## Common Root Causes

  1. **PM not calling tool**: System prompt issue
  2. **No database records**: SCAR executor not running
  3. **SSE query empty**: Query logic or session isolation
  4. **SSE not streaming**: Event generator issue
  5. **Frontend not receiving**: CORS or EventSource issue
  \```
- **VALIDATE**: Documentation is clear and actionable

---

## TESTING STRATEGY

### Unit Tests

**Existing tests** (should still pass):
- `tests/services/test_scar_executor.py` - SCAR executor functions
- `tests/agent/test_orchestrator_agent.py` - Agent tool definitions

**New tests**:
- `tests/integration/test_sse_feed_e2e.py` - End-to-end SSE feed test

### Integration Tests

**Manual diagnostic scripts**:
1. `scripts/debug_sse_flow.py` - Validates database and query
2. `scripts/test_sse_endpoint.py` - Validates SSE streaming
3. `scripts/create_test_execution.py` - Creates test records

### Manual Testing

**WebUI validation**:
1. Start backend: `uv run uvicorn src.main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Open browser DevTools
4. Send: "analyze the codebase"
5. Verify right panel shows activity

---

## VALIDATION COMMANDS

Execute every command to ensure zero regressions and 100% feature correctness.

### Level 1: Import Validation (CRITICAL)

```bash
uv run python -c "from src.main import app; from src.services.scar_feed_service import stream_scar_activity; from src.services.scar_executor import execute_scar_command; print('✓ All imports valid')"
```

**Expected**: "✓ All imports valid"

### Level 2: Diagnostic Scripts

```bash
# Database and SSE query test
uv run python scripts/debug_sse_flow.py

# SSE endpoint connection test (requires backend running)
uv run uvicorn src.main:app --reload &
BACKEND_PID=$!
sleep 3
PROJECT_ID=$(uv run python -c "import asyncio; from src.database.connection import async_session_maker; from src.database.models import Project; from sqlalchemy import select; async def f(): async with async_session_maker() as s: p = (await s.execute(select(Project).limit(1))).scalar_one(); print(str(p.id)); asyncio.run(f())")
uv run python scripts/test_sse_endpoint.py $PROJECT_ID 10
kill $BACKEND_PID
```

**Expected**: Both scripts pass

### Level 3: Linting & Type Checking

```bash
uv run ruff check src/ scripts/ tests/
uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
```

**Expected**: No errors

### Level 4: Unit Tests

```bash
uv run pytest tests/unit/ -v
uv run pytest tests/services/ -v
```

**Expected**: All tests pass

### Level 5: Integration Tests

```bash
uv run pytest tests/integration/test_sse_feed_e2e.py -v -s
```

**Expected**: E2E test passes

### Level 6: Manual WebUI Validation

```bash
# Terminal 1: Backend with logging
uv run uvicorn src.main:app --reload

# Terminal 2: Frontend
cd frontend && npm run dev

# Terminal 3: Watch logs
tail -f logs/app.log | grep -E "execute_scar|ScarCommandExecution|SSE"
```

**Manual steps**:
1. Open `http://localhost:5173`
2. Open DevTools (F12) → Console + Network tabs
3. Select a project
4. Send message: "analyze the codebase"
5. Verify:
   - ✅ Console shows "SSE connected"
   - ✅ Network shows `/api/sse/scar/{id}` (eventsource)
   - ✅ Right panel shows activity within 5s
   - ✅ Logs show complete flow

### Level 7: Regression Check

```bash
# Full test suite
uv run pytest -v

# API health check
curl http://localhost:8000/health
curl http://localhost:8000/api/projects
```

**Expected**: All tests pass, endpoints respond

---

## ACCEPTANCE CRITERIA

- [ ] Database records are created when PM calls execute_scar
- [ ] SSE feed service detects new records within 2-5 seconds
- [ ] SSE endpoint streams activity events to frontend
- [ ] Frontend displays activities in real-time
- [ ] Enhanced logging tracks execution_id throughout flow
- [ ] Diagnostic scripts validate each pipeline stage
- [ ] Integration test prevents future regressions
- [ ] All existing tests continue to pass
- [ ] Manual WebUI test confirms functionality
- [ ] Troubleshooting documentation is complete

---

## COMPLETION CHECKLIST

- [ ] All diagnostic scripts created and working
- [ ] Enhanced logging added (agent, executor, feed service)
- [ ] SSE polling logic improved with logging
- [ ] Integration test created and passing
- [ ] Troubleshooting documentation created
- [ ] All validation commands executed successfully
- [ ] Manual WebUI test confirms fix
- [ ] Full test suite passes
- [ ] No regressions in other features
- [ ] Code reviewed for quality

---

## NOTES

### Key Implementation Insights

**Root Cause**: SSE polling logic works correctly (after PR #46, #48), but the issue is likely:
1. **Session Isolation**: SSE uses separate session, might not see recent commits immediately
2. **Timing**: Initial query gets old records, polling starts before new records created
3. **Logging Gap**: No visibility into whether polling detects records

**Solution**: Enhanced logging + improved polling query validation

### Critical Code Paths

1. **Write Path**: `orchestrator_agent.py` → `scar_executor.py` → Database
2. **Read Path**: `scar_feed_service.py` → Database → `sse.py` → Frontend
3. **Critical Points**: Database commit, session refresh, timestamp comparison

### Edge Cases

- **Concurrent executions**: Multiple SCAR commands running simultaneously
- **SSE reconnection**: Frontend reconnects after connection drop
- **Long executions**: Commands taking >300s (timeout handling)
- **Empty project**: No SCAR executions yet (initial state)

### Performance Considerations

- **Polling interval**: 2 seconds (acceptable latency)
- **Query efficiency**: Indexed on `started_at` and `project_id`
- **Session lifetime**: SSE connections can be long-lived (handled by FastAPI)
- **Event buffer**: No buffering needed (real-time stream)

### Security Considerations

- **Project access**: Validate user has access to project_id
- **CORS**: Properly configured for frontend origin
- **Rate limiting**: Apply to SSE endpoint to prevent abuse
