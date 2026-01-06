# Feature: Debug and Fix SSE Feed Implementation

The following plan should be complete, but it's important that you validate documentation and codebase patterns and task sanity before you start implementing.

Pay special attention to naming of existing utils types and models. Import from the right files etc.

## Feature Description

The SCAR activity feed using Server-Sent Events (SSE) is not displaying real-time command executions in the WebUI frontend. Despite backend logs showing SCAR commands executing successfully, the right panel SSE feed remains empty. This investigation and fix will ensure users can monitor SCAR activity in real-time.

## User Story

As a user of the Project Manager WebUI
I want to see real-time SCAR command execution activity in the right pane SSE feed
So that I can monitor what SCAR is doing while it processes my requests and understand the system's progress

## Problem Statement

**Observed Symptoms:**
1. User sends message requesting code analysis or SCAR operations
2. Project Manager responds with results
3. SSE activity feed in right pane shows no activity (empty state persists)
4. Backend logs confirm SCAR commands are executing and completing successfully
5. Database may or may not contain ScarCommandExecution records

**Critical Impact:**
Users cannot see what SCAR is doing, making the system appear unresponsive or broken even when working correctly. This breaks the transparency and trust model of the application.

## Solution Statement

Perform systematic Root Cause Analysis to identify the exact failure point in the flow: User Message → WebSocket → Orchestrator Agent → SCAR Executor → Database → SSE Feed Service → SSE Endpoint → Frontend EventSource → UI Rendering. Implement targeted fixes to ensure reliable real-time streaming of SCAR activity to the frontend.

## Feature Metadata

**Feature Type**: Bug Fix / Investigation / Debugging
**Estimated Complexity**: Medium-High
**Primary Systems Affected**:
- SSE endpoint (`src/api/sse.py`)
- SSE feed service (`src/services/scar_feed_service.py`)
- SCAR executor service (`src/services/scar_executor.py`)
- Database models (`src/database/models.py` - ScarCommandExecution)
- Frontend SSE hook (`frontend/src/hooks/useScarFeed.ts`)
- Frontend activity feed UI (`frontend/src/components/RightPanel/ScarActivityFeed.tsx`)

**Dependencies**:
- `sse-starlette==2.1.0` (Server-Sent Events library)
- `sqlalchemy[asyncio]>=2.0.36` (Async ORM)
- Browser `EventSource` API (standard)
- `fastapi>=0.115.0`

---

## CONTEXT REFERENCES

### Relevant Codebase Files IMPORTANT: YOU MUST READ THESE FILES BEFORE IMPLEMENTING!

**Backend - SSE Implementation:**
- `src/api/sse.py` (lines 22-104) - **Why**: SSE endpoint that streams events to frontend
- `src/services/scar_feed_service.py` (lines 19-149) - **Why**: Database polling logic, activity formatting
- `src/database/connection.py` (lines 32-62) - **Why**: Session maker configuration (`expire_on_commit=False`)

**Backend - SCAR Execution:**
- `src/services/scar_executor.py` (lines 49-295) - **Why**: Creates ScarCommandExecution records in database
- `src/agent/orchestrator_agent.py` (lines 269-316) - **Why**: Agent tool that invokes SCAR executor
- `src/agent/prompts.py` (lines 251-276) - **Why**: System prompt guidance for proactive SCAR execution

**Database Models:**
- `src/database/models.py` (lines 248-301) - **Why**: ScarCommandExecution model, `@property source`

**Frontend - SSE Client:**
- `frontend/src/hooks/useScarFeed.ts` - **Why**: EventSource client implementation
- `frontend/src/components/RightPanel/ScarActivityFeed.tsx` - **Why**: UI rendering of activities

**Configuration:**
- `src/config.py` (lines 55-65) - **Why**: SCAR integration settings (`scar_base_url`, timeouts)
- `src/main.py` (lines 159-165) - **Why**: Router registration (`app.include_router(sse_router)`)

### Recent Fixes (From Existing Plan)

**Commit d928ef6 (Jan 6, 2026)**: Fixed SSE feed polling using timestamp comparison
- **Problem**: UUID comparison (`id > UUID(last_id)`) failed - UUIDs not chronological
- **Solution**: Changed to timestamp comparison (`started_at > last_dt`)
- **File**: `src/services/scar_feed_service.py` (lines 111-119)

**Commit 00f82a5 (Jan 5, 2026)**: Added direct SCAR execution tool to orchestrator agent
- Enabled agent to call `execute_scar()` proactively
- **File**: `src/agent/orchestrator_agent.py` (lines 269-316)

### Relevant Documentation YOU SHOULD READ THESE BEFORE IMPLEMENTING!

- [FastAPI Server-Sent Events](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)
  - Section: EventSourceResponse with async generators
  - **Why**: Understanding SSE implementation pattern in FastAPI
- [sse-starlette GitHub](https://github.com/sysid/sse-starlette)
  - Section: EventSourceResponse API and event formatting
  - **Why**: Proper SSE event structure `{"event": "type", "data": "json"}`
- [MDN EventSource API](https://developer.mozilla.org/en-US/docs/Web/API/EventSource)
  - Section: Event listeners, connection states, error handling
  - **Why**: Frontend EventSource behavior and debugging
- [SQLAlchemy Async Sessions](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
  - Section: Session lifecycle, `expire_on_commit`, transaction isolation
  - **Why**: Understanding how SSE long-lived sessions interact with database

### Patterns to Follow

**Database Session Pattern for SSE:**
```python
# From src/database/connection.py (lines 32-38)
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # ← CRITICAL: Access objects after commit in long-lived SSE sessions
    autocommit=False,
    autoflush=False,
)

# SSE endpoint creates independent session
async def event_generator():
    async with async_session_maker() as session:
        activity_stream = stream_scar_activity(session, project_id, verbosity)
        async for activity in activity_stream:
            yield {"event": "activity", "data": json.dumps(activity)}
```

**SSE Event Format:**
```python
# Backend sends
yield {
    "event": "activity",  # Event type
    "data": json.dumps({  # Must be JSON string
        "id": str(uuid),
        "timestamp": iso_string,
        "source": "scar",
        "message": "Command: Status",
        "phase": "phase_name" or None
    })
}

# Frontend receives
eventSource.addEventListener('activity', (event) => {
    const activity: ScarActivity = JSON.parse(event.data);
    setActivities(prev => [...prev, activity]);
});
```

**SCAR Execution Record Creation:**
```python
# From src/services/scar_executor.py (lines 85-102)
execution = ScarCommandExecution(
    project_id=project_id,
    phase_id=phase_id,
    command_type=_command_to_type(command),
    command_args=args_str,
    status=ExecutionStatus.QUEUED,
    started_at=datetime.utcnow(),  # ← CRITICAL: Timestamp for polling
)
session.add(execution)
await session.commit()  # ← Must commit to make visible to SSE polling
await session.refresh(execution)

execution.status = ExecutionStatus.RUNNING
await session.commit()  # ← Commit again after status change
```

**Activity Polling Pattern (Post-d928ef6 Fix):**
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
            .order_by(ScarCommandExecution.started_at.asc())  # ← Chronological order
        )
```

**Logging Pattern:**
```python
# From src/services/scar_executor.py (lines 108-111)
logger.info(
    f"Executing SCAR command: {command.value}",
    extra={"project_id": str(project_id), "command": command.value, "command_args": args}
)
```

---

## IMPLEMENTATION PLAN

### Phase 1: Root Cause Analysis (Diagnostic)

**Objective**: Systematically identify the exact failure point using diagnostic scripts.

**Approach**: Test each component in isolation to pinpoint where the flow breaks.

### Phase 2: Targeted Fix Implementation

**Objective**: Fix identified issues based on RCA findings.

**Approach**: Implement minimal, targeted fixes for each identified failure point.

### Phase 3: Testing & Validation

**Objective**: Verify fix works end-to-end and prevent regression.

**Approach**: Automated integration tests + manual WebUI validation.

---

## STEP-BY-STEP TASKS

IMPORTANT: Execute every task in order, top to bottom. Each task is atomic and independently testable.

### CREATE scripts/debug_scar_executions.py

- **IMPLEMENT**: Database inspection script to verify ScarCommandExecution records exist
- **PURPOSE**: Identify if SCAR executor is writing to database
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
      """Query and display all ScarCommandExecution records."""
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
  python scripts/debug_scar_executions.py
  ```
  **Expected**: Lists projects with their SCAR execution history. Empty list indicates SCAR executor not creating records.

### CREATE scripts/test_sse_endpoint.py

- **IMPLEMENT**: SSE client to connect to endpoint and print events
- **PURPOSE**: Verify SSE endpoint is streaming correctly
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
      """Connect to SSE endpoint and print received events."""
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
  # Get a project ID
  PROJECT_ID=$(python -c "import asyncio; from src.database.connection import async_session_maker; from src.database.models import Project; from sqlalchemy import select; async def f(): async with async_session_maker() as s: p = (await s.execute(select(Project).limit(1))).scalar_one(); print(p.id); asyncio.run(f())")

  # Test SSE endpoint (run for 10 seconds)
  python scripts/test_sse_endpoint.py $PROJECT_ID 2 10
  ```
  **Expected**: Connection succeeds, heartbeat events received. Activities received if database has records.

### CREATE scripts/test_e2e_sse.py

- **IMPLEMENT**: End-to-end test that creates execution record and verifies SSE streaming
- **PURPOSE**: Validate complete flow from database write to SSE delivery
- **IMPORTS**:
  ```python
  import asyncio
  import httpx
  import json
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
  python scripts/test_e2e_sse.py
  ```
  **Expected**: Creates execution record, SSE detects and streams it within 5 seconds.

### ADD enhanced logging to scar_executor.py

- **IMPLEMENT**: Detailed logging for execution lifecycle
- **FILE**: `src/services/scar_executor.py`
- **PATTERN**: Existing logger (line 28)
- **ADD AFTER LINE 95** (after `session.add(execution)`):
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
          "output_length": len(output),
          "duration": result.duration_seconds,
      }
  )
  ```
- **VALIDATE**: Logs include `execution_id` throughout lifecycle for tracking

### ADD enhanced logging to scar_feed_service.py

- **IMPLEMENT**: Log when SSE feed detects new activities
- **FILE**: `src/services/scar_feed_service.py`
- **PATTERN**: Existing logger (line 16)
- **ADD AFTER LINE 129** (after querying new activities):
  ```python
  if new_activities:
      logger.debug(
          f"SSE feed detected new activities",
          extra={
              "project_id": str(project_id),
              "count": len(new_activities),
              "activity_ids": [str(a.id) for a in new_activities],
          }
      )
  else:
      logger.debug(
          f"SSE feed poll: no new activities",
          extra={"project_id": str(project_id), "last_timestamp": last_timestamp}
      )
  ```
- **VALIDATE**: Logs show SSE polling activity and detection

### ADD enhanced logging to orchestrator_agent.py

- **IMPLEMENT**: Track when agent invokes execute_scar tool
- **FILE**: `src/agent/orchestrator_agent.py`
- **PATTERN**: Existing logger
- **ADD AFTER LINE 285** (in execute_scar tool, before calling executor):
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
- **VALIDATE**: Logs show when agent calls the tool

### RUN full diagnostic suite and create RCA report

- **IMPLEMENT**: Execute all diagnostic scripts and document findings
- **PURPOSE**: Identify exact failure point with evidence
- **LOCATION**: `.agents/reports/rca-sse-feed.md`
- **EXECUTE**:
  ```bash
  # Ensure backend is running
  python -m src.main &
  BACKEND_PID=$!
  sleep 5

  # Run diagnostics
  echo "=== 1. Database Inspection ===" > rca-output.txt
  python scripts/debug_scar_executions.py >> rca-output.txt 2>&1

  echo -e "\n=== 2. SSE Endpoint Test ===" >> rca-output.txt
  PROJECT_ID=$(python -c "import asyncio; from src.database.connection import async_session_maker; from src.database.models import Project; from sqlalchemy import select; async def f(): async with async_session_maker() as s: p = (await s.execute(select(Project).limit(1))).scalar_one(); print(p.id); asyncio.run(f())")
  python scripts/test_sse_endpoint.py $PROJECT_ID 2 10 >> rca-output.txt 2>&1

  echo -e "\n=== 3. End-to-End SSE Test ===" >> rca-output.txt
  python scripts/test_e2e_sse.py >> rca-output.txt 2>&1

  # Check application logs
  echo -e "\n=== 4. Application Logs ===" >> rca-output.txt
  tail -100 logs/app.log | grep -E "execute_scar|ScarCommandExecution|SSE" >> rca-output.txt 2>&1

  kill $BACKEND_PID

  cat rca-output.txt
  ```
- **CREATE REPORT** in `.agents/reports/rca-sse-feed.md`:
  ```markdown
  # Root Cause Analysis: SSE Feed Not Displaying SCAR Activity

  ## Investigation Date
  {DATE}

  ## Diagnostic Test Results

  ### 1. Database Inspection Test
  **Result**: [PASS/FAIL]
  **Findings**:
  - Projects found: X
  - SCAR execution records: X
  - If FAIL: No records found → SCAR executor not writing to database

  ### 2. SSE Endpoint Test
  **Result**: [PASS/FAIL]
  **Findings**:
  - Connection established: [YES/NO]
  - Heartbeat events received: [YES/NO]
  - Activity events received: [YES/NO]
  - If FAIL: SSE endpoint not accessible or not streaming

  ### 3. End-to-End Integration Test
  **Result**: [PASS/FAIL]
  **Findings**:
  - Test record created: [YES/NO]
  - SSE detected record: [YES/NO]
  - Detection latency: Xs
  - If FAIL: Polling logic or session isolation issue

  ### 4. Application Logs Analysis
  **Key Observations**:
  - "Agent invoking execute_scar tool": [FOUND/NOT FOUND]
  - "Created ScarCommandExecution record": [FOUND/NOT FOUND]
  - "SSE feed detected new activities": [FOUND/NOT FOUND]

  ## Root Cause Hypothesis

  Based on test results, the most likely root cause is:

  [HYPOTHESIS WITH SUPPORTING EVIDENCE]

  ## Recommended Fix

  [SPECIFIC FIX DESCRIPTION]
  ```
- **VALIDATE**: RCA report clearly identifies failure point with evidence

### IMPLEMENT fix based on RCA findings

- **CONDITIONAL**: This task depends on RCA results
- **PATTERN**: Implement minimal targeted fix

**If RCA shows: No database records**
  - **ROOT CAUSE**: SCAR executor not being called or failing silently
  - **FILE**: `src/agent/orchestrator_agent.py` + `src/agent/prompts.py`
  - **FIX**: Strengthen system prompt, add examples, ensure tool is always called for analysis requests
  - **VALIDATE**: Re-run database inspection after fix

**If RCA shows: Database records exist but SSE not streaming**
  - **ROOT CAUSE**: SSE polling logic or session isolation issue
  - **FILE**: `src/services/scar_feed_service.py`
  - **CHECK**: Timestamp comparison (should be fixed in d928ef6)
  - **FIX**: Verify query is correct, add debug logging
  - **VALIDATE**: Re-run E2E SSE test

**If RCA shows: SSE streaming but frontend not receiving**
  - **ROOT CAUSE**: Frontend EventSource connection or event handling
  - **FILE**: `frontend/src/hooks/useScarFeed.ts`
  - **FIX**: Add error handling, connection retry, console logging
  - **CHECK**: CORS configuration in `src/main.py`
  - **VALIDATE**: Browser DevTools Network tab inspection

**If RCA shows: Agent not calling execute_scar**
  - **ROOT CAUSE**: System prompt insufficient or agent bypassing tool
  - **FILE**: `src/agent/prompts.py`
  - **FIX**: Make execute_scar invocation mandatory for analysis requests
  - **ADD**: Explicit examples in prompt
  - **VALIDATE**: Check logs for "Agent invoking execute_scar tool"

- **GENERAL VALIDATION**:
  ```bash
  # Re-run diagnostic suite
  python scripts/test_e2e_sse.py

  # Check logs for fix confirmation
  tail -f logs/app.log | grep -E "execute_scar|ScarCommandExecution|SSE"
  ```

### CREATE integration test for SSE feed

- **IMPLEMENT**: Automated regression prevention test
- **PURPOSE**: Ensure SSE feed always works in CI/CD
- **LOCATION**: `tests/api/test_sse_feed.py`
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

      # Create test execution in database
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

          # Verify execution appeared in feed
          event_ids = [e["id"] for e in events]
          assert execution_id in event_ids, f"Execution {execution_id} not found in SSE feed"
  ```
- **VALIDATE**:
  ```bash
  pytest tests/api/test_sse_feed.py -v
  ```
  **Expected**: Test passes, confirming SSE streams execution records

### UPDATE documentation with troubleshooting guide

- **IMPLEMENT**: Comprehensive troubleshooting guide for SSE feed
- **LOCATION**: `docs/troubleshooting-sse-feed.md`
- **CONTENT**:
  ```markdown
  # SSE Feed Troubleshooting Guide

  ## Architecture

  ```
  User Message → WebSocket → Orchestrator Agent → SCAR Executor → Database (ScarCommandExecution)
                                                                        ↓
  Frontend ← SSE Endpoint ← SSE Feed Service (Polling every 2s) ← Database
  ```

  ## Common Issue: SSE Feed Shows No Activity

  **Symptoms**: Right pane in WebUI remains empty despite PM responding.

  **Diagnostic Steps**:

  1. **Check if database has execution records:**
     ```bash
     python scripts/debug_scar_executions.py
     ```
     - If NO records: Agent not calling `execute_scar` or SCAR executor failing
     - If YES records: Problem is in SSE polling or frontend

  2. **Test SSE endpoint directly:**
     ```bash
     python scripts/test_sse_endpoint.py <project-id> 2 10
     ```
     - Should see heartbeat events every 30s
     - Should see activity events if database has records

  3. **Run end-to-end test:**
     ```bash
     python scripts/test_e2e_sse.py
     ```
     - Creates test record, verifies SSE streams it within 5s

  4. **Check application logs:**
     ```bash
     tail -f logs/app.log | grep -E "execute_scar|ScarCommandExecution|SSE"
     ```
     - Look for: "Agent invoking execute_scar tool"
     - Look for: "Created ScarCommandExecution record"
     - Look for: "SSE feed detected new activities"

  **Common Root Causes**:

  1. **Agent not calling execute_scar**: System prompt needs strengthening
  2. **Database transaction not committed**: Check `await session.commit()`
  3. **SSE polling logic broken**: Timestamp comparison issue (fixed in d928ef6)
  4. **Frontend EventSource not connecting**: CORS or network issue
  5. **SCAR not running**: Backend can't reach SCAR HTTP API

  ## Manual WebUI Testing

  1. Start backend: `python -m src.main`
  2. Start frontend: `cd frontend && npm run dev`
  3. Open browser DevTools (F12) → Network tab
  4. Send message: "analyze the codebase"
  5. Verify:
     - Network tab shows `/api/sse/scar/{id}` connection (type: eventsource)
     - Console shows "SSE connected"
     - Right pane shows activity items

  ## Configuration

  **Backend** (`src/config.py`):
  ```python
  scar_base_url: str = "http://localhost:3000"
  scar_timeout_seconds: int = 300
  ```

  **Frontend** (`frontend/src/hooks/useScarFeed.ts`):
  ```typescript
  const eventSource = new EventSource(`/api/sse/scar/${projectId}?verbosity=${verbosity}`);
  ```
  ```
- **VALIDATE**: Documentation is clear, actionable, and complete

---

## TESTING STRATEGY

### Diagnostic Tests (Manual)

**Purpose**: Identify root cause

1. **Database Inspection**: `scripts/debug_scar_executions.py`
   - Validates: ScarCommandExecution records exist

2. **SSE Endpoint Test**: `scripts/test_sse_endpoint.py`
   - Validates: SSE endpoint streams events

3. **End-to-End Test**: `scripts/test_e2e_sse.py`
   - Validates: Complete flow works

### Integration Tests (Automated)

**Purpose**: Prevent regression

1. **SSE Feed Integration Test**: `tests/api/test_sse_feed.py`
   - Framework: pytest with async
   - Validates: SSE streams execution records correctly

### Manual WebUI Validation

**Purpose**: Verify user-facing functionality

1. Open WebUI, send "analyze the codebase"
2. Check right pane shows SCAR activity
3. Verify real-time updates

---

## VALIDATION COMMANDS

Execute every command to ensure zero regressions and 100% feature correctness.

### Level 1: Import Validation (CRITICAL)

```bash
python -c "from src.main import app; from src.services.scar_feed_service import stream_scar_activity; from src.services.scar_executor import execute_scar_command; print('✓ All imports valid')"
```

**Expected**: "✓ All imports valid" (no errors)

### Level 2: Diagnostic Suite

```bash
# Start backend
python -m src.main &
BACKEND_PID=$!
sleep 5

# Run diagnostics
echo "=== Database Inspection ==="
python scripts/debug_scar_executions.py

echo -e "\n=== SSE Endpoint Test ==="
PROJECT_ID=$(python -c "import asyncio; from src.database.connection import async_session_maker; from src.database.models import Project; from sqlalchemy import select; async def f(): async with async_session_maker() as s: p = (await s.execute(select(Project).limit(1))).scalar_one(); print(p.id); asyncio.run(f())")
python scripts/test_sse_endpoint.py $PROJECT_ID 2 10

echo -e "\n=== End-to-End SSE Test ==="
python scripts/test_e2e_sse.py

kill $BACKEND_PID
```

**Expected**: All diagnostics pass

### Level 3: Linting & Formatting

```bash
ruff check src/ scripts/ tests/
ruff format --check src/ scripts/ tests/
mypy src/ scripts/
```

**Expected**: No errors

### Level 4: Unit Tests

```bash
pytest tests/unit/ -v
```

**Expected**: All tests pass

### Level 5: Integration Tests

```bash
pytest tests/api/test_sse_feed.py -v
```

**Expected**: SSE feed integration test passes

### Level 6: Manual WebUI Validation

```bash
# Terminal 1: Backend
python -m src.main

# Terminal 2: Frontend
cd frontend && npm run dev

# Terminal 3: Logs
tail -f logs/app.log | grep -E "execute_scar|ScarCommandExecution|SSE"
```

**Manual Steps**:
1. Open browser to `http://localhost:5173`
2. Open DevTools (F12) → Console + Network tabs
3. Select a project
4. Send message: "analyze the codebase"
5. Verify:
   - ✅ Network tab shows active SSE connection (`/api/sse/scar/{id}`)
   - ✅ Console shows "SSE connected"
   - ✅ Right pane displays SCAR activity within 2-5 seconds
   - ✅ Logs show: "Agent invoking execute_scar" → "Created ScarCommandExecution" → "SSE feed detected"

### Level 7: Regression Check

```bash
pytest -v
curl http://localhost:8000/health
curl http://localhost:8000/api/projects
```

**Expected**: All tests pass, all endpoints respond

---

## ACCEPTANCE CRITERIA

- [ ] RCA completed with clear root cause identification and evidence
- [ ] All diagnostic scripts execute successfully
- [ ] Root cause fix implemented and tested
- [ ] SSE feed streams SCAR execution records within 2-5 seconds of creation
- [ ] WebUI right pane displays SCAR activity in real-time
- [ ] Enhanced logging added for troubleshooting (execution_id tracking)
- [ ] Integration test added to prevent regression (`tests/api/test_sse_feed.py`)
- [ ] All existing tests pass (no regressions)
- [ ] Manual WebUI test confirms end-to-end functionality
- [ ] Documentation updated with troubleshooting guide
- [ ] No regressions in WebSocket chat or other features

---

## COMPLETION CHECKLIST

- [ ] All diagnostic scripts created (`scripts/debug_scar_executions.py`, `scripts/test_sse_endpoint.py`, `scripts/test_e2e_sse.py`)
- [ ] Enhanced logging added to `scar_executor.py`, `scar_feed_service.py`, `orchestrator_agent.py`
- [ ] Diagnostic suite executed, RCA report created
- [ ] Root cause identified with supporting evidence
- [ ] Targeted fix implemented
- [ ] Integration test created (`tests/api/test_sse_feed.py`)
- [ ] All validation commands executed successfully
- [ ] Manual WebUI test confirms fix works
- [ ] Troubleshooting guide created (`docs/troubleshooting-sse-feed.md`)
- [ ] Code reviewed for quality and correctness
- [ ] All acceptance criteria met

---

## NOTES

### Key Insights

1. **Recent Timestamp Fix (d928ef6)**: Changed from UUID to timestamp comparison for chronological polling
2. **Session Configuration**: `expire_on_commit=False` is critical for SSE long-lived sessions
3. **Agent Tool Integration**: `execute_scar` tool exists but may not be consistently invoked

### Most Likely Root Causes (Priority Order)

1. **Agent not invoking execute_scar**: Despite system prompt, agent may respond without calling tool
2. **SCAR connectivity failure**: SCAR HTTP API not running or unreachable
3. **Database record creation failure**: Unlikely given commit patterns, but possible
4. **Frontend EventSource issue**: Not connecting due to CORS or network problem
5. **SSE polling regression**: Unlikely after d928ef6 fix, but verify

### Implementation Strategy

1. **Phase 1 (RCA)**: Run diagnostics to identify exact failure point
2. **Phase 2 (Fix)**: Implement targeted fix based on RCA findings
3. **Phase 3 (Test)**: Verify with automated and manual tests
4. **Phase 4 (Document)**: Update troubleshooting guide

### Edge Cases

- **Concurrent SCAR executions**: SSE should stream all in chronological order
- **SSE connection drops**: Frontend EventSource auto-reconnects
- **Very long execution (>300s)**: May timeout, handle gracefully
- **User sends message before completion**: SSE should show RUNNING then COMPLETED

### Performance Considerations

- **2-second polling interval**: Acceptable latency, efficient with timestamp index
- **30-second heartbeat**: Keeps connection alive
- **Long-lived SSE connections**: Normal for SSE, FastAPI handles well

### Security Considerations

- **Project ID validation**: SSE endpoint should verify user access
- **CORS configuration**: Permissive in development, strict in production
- **Rate limiting**: Should apply to SSE endpoint
