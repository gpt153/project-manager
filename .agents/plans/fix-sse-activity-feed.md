# Feature: Fix SSE Activity Feed - SCAR Commands Not Appearing in WebUI

The following plan should be complete, but it's important that you validate documentation and codebase patterns and task sanity before you start implementing.

Pay special attention to naming of existing utils types and models. Import from the right files etc.

## Feature Description

Investigate and fix the SSE (Server-Sent Events) activity feed in the WebUI that is not displaying SCAR command executions despite backend logs showing commands are executing successfully. The right pane SSE feed remains empty even when the Project Manager (PM) responds with SCAR-generated analysis.

## User Story

As a user of the Project Manager WebUI
I want to see real-time SCAR command execution activity in the right pane SSE feed
So that I can monitor what SCAR is doing while it processes my requests

## Problem Statement

**Symptoms:**
1. User sends message: "analyze the codebase"
2. PM responds with analysis results
3. SSE feed (right pane) remains completely empty
4. Backend logs show SCAR commands executing successfully

**Evidence from Issue #45:**
- Backend logs (14:24) show: "Executing SCAR command: prime" → "SCAR command completed successfully"
- User reports: "nothing turns up in right pane"
- PM provides detailed analysis WITHOUT user seeing SCAR activity in SSE feed

**Critical Impact:**
The entire PM + SCAR integration appears broken from user perspective. Even if working backend, users cannot see SCAR activity.

## Solution Statement

Perform Root Cause Analysis (RCA) to identify where in the flow from user message → PM → execute_scar → database → SSE feed → frontend the disconnect occurs. Implement targeted fixes to ensure SCAR command executions are reliably streamed to the SSE feed and displayed in the WebUI.

## Feature Metadata

**Feature Type**: Bug Fix / Investigation
**Estimated Complexity**: Medium
**Primary Systems Affected**:
- SSE endpoint (`src/api/sse.py`)
- SSE feed service (`src/services/scar_feed_service.py`)
- SCAR executor service (`src/services/scar_executor.py`)
- Database models (`src/database/models.py`)
- Frontend SSE client (`frontend/src/hooks/useScarFeed.ts`)

**Dependencies**:
- `sse-starlette` (SSE library)
- `SQLAlchemy` (async ORM)
- Browser `EventSource` API

---

## CONTEXT REFERENCES

### Relevant Codebase Files IMPORTANT: YOU MUST READ THESE FILES BEFORE IMPLEMENTING!

- `src/api/sse.py` (lines 22-104) - Why: SSE endpoint implementation, event streaming logic
- `src/services/scar_feed_service.py` (lines 71-149) - Why: Activity polling logic, timestamp-based querying
- `src/services/scar_executor.py` (lines 49-234) - Why: SCAR command execution, database record creation
- `src/database/models.py` (lines 248-301) - Why: ScarCommandExecution model definition
- `src/database/connection.py` (lines 32-38, 54-62) - Why: Session configuration and transaction management
- `src/agent/orchestrator_agent.py` (lines 269-316) - Why: Agent tool integration for execute_scar
- `src/agent/prompts.py` (lines 251-276) - Why: Proactive SCAR execution guidance
- `frontend/src/hooks/useScarFeed.ts` - Why: Frontend EventSource client implementation
- `frontend/src/components/RightPanel/ScarActivityFeed.tsx` - Why: UI component rendering activities

### Recent Fixes

**Commit d928ef6 (Jan 6, 2026)**: Fix SSE feed polling using timestamp comparison
- **Problem**: UUID comparison (`id > UUID(last_id)`) failed because UUIDs aren't chronological
- **Solution**: Changed to timestamp comparison (`started_at > last_dt`)
- **File**: `src/services/scar_feed_service.py` (lines 111-119)

**Commit 00f82a5 (Jan 5, 2026)**: Add direct SCAR execution tool to orchestrator agent
- Enabled agent to call `execute_scar()` proactively
- **File**: `src/agent/orchestrator_agent.py` (lines 269-316)

### Relevant Documentation YOU SHOULD READ THESE BEFORE IMPLEMENTING!

- [FastAPI Server-Sent Events](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)
  - Section: EventSourceResponse pattern
  - Why: Understanding SSE implementation in FastAPI
- [sse-starlette Documentation](https://github.com/sysid/sse-starlette)
  - Section: EventSourceResponse usage
  - Why: Proper SSE event formatting and streaming
- [MDN EventSource API](https://developer.mozilla.org/en-US/docs/Web/API/EventSource)
  - Section: Event handling and connection states
  - Why: Understanding frontend SSE client behavior
- [SQLAlchemy Async Sessions](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#using-asyncio-scoped-session)
  - Section: Session lifecycle and transaction management
  - Why: Understanding session isolation in async contexts

### Patterns to Follow

**Database Session Management Pattern:**
```python
# From src/database/connection.py (lines 32-38)
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # ← CRITICAL for SSE streaming
    autocommit=False,
    autoflush=False,
)

# From src/database/connection.py (lines 54-62)
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()  # ← Auto-commits on success
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

**SSE Event Streaming Pattern:**
```python
# From src/api/sse.py (lines 52-91)
async def event_generator():
    """Generate Server-Sent Events for SCAR activity."""
    try:
        async with async_session_maker() as session:
            activity_stream = stream_scar_activity(session, project_id, verbosity)

            async for activity in activity_stream:
                # Send activity event
                yield {"event": "activity", "data": json.dumps(activity)}

                # Send heartbeat every 30 seconds
                if current_time - last_heartbeat >= 30:
                    yield {"event": "heartbeat", "data": json.dumps({...})}
    except Exception as e:
        yield {"event": "error", "data": json.dumps({"error": str(e)})}

return EventSourceResponse(event_generator())
```

**Activity Polling Pattern (Post-Fix):**
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
                ScarCommandExecution.started_at > last_dt,  # ← Use timestamp, not UUID
            )
            .order_by(ScarCommandExecution.started_at.asc())
        )
```

**SCAR Execution Record Creation Pattern:**
```python
# From src/services/scar_executor.py (lines 85-95, 100-102)
execution = ScarCommandExecution(
    project_id=project_id,
    phase_id=phase_id,
    command_type=_command_to_type(command),
    command_args=args_str,
    status=ExecutionStatus.QUEUED,
    started_at=datetime.utcnow(),  # ← CRITICAL: Set timestamp immediately
)
session.add(execution)
await session.commit()  # ← Must commit to make visible to SSE polling
await session.refresh(execution)  # ← Refresh to get database-generated values

# Update to RUNNING
execution.status = ExecutionStatus.RUNNING
await session.commit()  # ← Another commit to update status
```

**Frontend EventSource Pattern:**
```typescript
// From frontend/src/hooks/useScarFeed.ts (lines 15-36)
useEffect(() => {
  const eventSource = new EventSource(`/api/sse/scar/${projectId}?verbosity=${verbosity}`);

  eventSource.onopen = () => setIsConnected(true);

  eventSource.onmessage = (event) => {
    const activity: ScarActivity = JSON.parse(event.data);
    setActivities((prev) => [...prev, activity]);
  };

  eventSource.onerror = (error) => {
    console.error('SSE error:', error);
    setIsConnected(false);
  };

  return () => eventSource.close();
}, [projectId, verbosity]);
```

**Logging Pattern:**
```python
# From src/services/scar_executor.py (lines 108-110)
logger.info(
    f"Executing SCAR command: {command.value}",
    extra={"project_id": str(project_id), "command": command.value, "command_args": args},
)
```

---

## IMPLEMENTATION PLAN

### Phase 1: Root Cause Analysis (RCA)

**Objective:** Systematically trace the execution flow to identify the exact point of failure.

**Tasks:**
- Create diagnostic script to verify each step in the flow
- Check database for ScarCommandExecution records
- Verify SSE endpoint is accessible and streaming
- Validate frontend EventSource connection

### Phase 2: Diagnostic Tooling

**Objective:** Create comprehensive diagnostic tools to test the SSE feed independently.

**Tasks:**
- Create database inspection script
- Create SSE client test script
- Create end-to-end integration test

### Phase 3: Issue Identification & Fix

**Objective:** Implement targeted fixes based on RCA findings.

**Tasks:**
- Fix identified issues (database, SSE, frontend)
- Add enhanced logging for troubleshooting
- Ensure proper transaction isolation

### Phase 4: Testing & Validation

**Objective:** Verify the fix works end-to-end.

**Tasks:**
- Test database record creation
- Test SSE streaming
- Test frontend rendering
- Validate with real SCAR execution

---

## STEP-BY-STEP TASKS

IMPORTANT: Execute every task in order, top to bottom. Each task is atomic and independently testable.

### Task 1: CREATE diagnostic database inspection script

- **IMPLEMENT**: Script to query ScarCommandExecution table directly
- **PURPOSE**: Verify if database records are being created when SCAR commands execute
- **LOCATION**: `scripts/debug_scar_executions.py`
- **IMPORTS**:
  ```python
  import asyncio
  from uuid import UUID
  from sqlalchemy import select, desc
  from src.database.connection import async_session_maker
  from src.database.models import ScarCommandExecution, Project
  ```
- **LOGIC**:
  ```python
  async def inspect_scar_executions():
      """Query and display ScarCommandExecution records."""
      async with async_session_maker() as session:
          # Get all projects
          projects = await session.execute(select(Project))
          projects = projects.scalars().all()

          print(f"Found {len(projects)} projects\n")

          for project in projects:
              print(f"Project: {project.name} ({project.id})")

              # Get recent executions
              query = (
                  select(ScarCommandExecution)
                  .where(ScarCommandExecution.project_id == project.id)
                  .order_by(desc(ScarCommandExecution.started_at))
                  .limit(10)
              )
              result = await session.execute(query)
              executions = result.scalars().all()

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
  **Expected**: Should list projects and their recent SCAR executions. If empty after user reported analysis, that's the smoking gun.

### Task 2: CREATE SSE endpoint diagnostic script

- **IMPLEMENT**: Script to connect to SSE endpoint and print events
- **PURPOSE**: Verify SSE endpoint is streaming events correctly
- **LOCATION**: `scripts/test_sse_feed.py`
- **IMPORTS**:
  ```python
  import asyncio
  import httpx
  import json
  from uuid import UUID
  ```
- **LOGIC**:
  ```python
  async def test_sse_feed(project_id: str, verbosity: int = 2):
      """Connect to SSE endpoint and print events."""
      url = f"http://localhost:8000/api/sse/scar/{project_id}?verbosity={verbosity}"

      print(f"Connecting to SSE feed: {url}\n")

      async with httpx.AsyncClient(timeout=None) as client:
          async with client.stream("GET", url) as response:
              print(f"Connected! Status: {response.status_code}\n")

              event_count = 0
              async for line in response.aiter_lines():
                  if line.startswith("data: "):
                      data = json.loads(line[6:])
                      print(f"[Event {event_count}] {data}")
                      event_count += 1
                  elif line.startswith("event: "):
                      event_type = line[7:]
                      print(f"Event type: {event_type}")

  if __name__ == "__main__":
      import sys
      if len(sys.argv) < 2:
          print("Usage: python scripts/test_sse_feed.py <project_id>")
          sys.exit(1)

      asyncio.run(test_sse_feed(sys.argv[1]))
  ```
- **VALIDATE**:
  ```bash
  # Get a project ID first
  PROJECT_ID=$(uv run python -c "import asyncio; from src.database.connection import async_session_maker; from src.database.models import Project; from sqlalchemy import select; async def get_id(): async with async_session_maker() as s: p = (await s.execute(select(Project).limit(1))).scalar_one(); print(p.id); asyncio.run(get_id())")

  # Test SSE feed (let it run for 10 seconds to see heartbeats)
  timeout 10s uv run python scripts/test_sse_feed.py $PROJECT_ID || true
  ```
  **Expected**: Should see connection established, then heartbeat events every 30s. If activities exist, should see them too.

### Task 3: CREATE end-to-end integration test

- **IMPLEMENT**: Test script that creates a ScarCommandExecution and verifies SSE streaming
- **PURPOSE**: Validate the complete flow from database → SSE feed
- **LOCATION**: `scripts/test_e2e_sse.py`
- **IMPORTS**:
  ```python
  import asyncio
  import httpx
  import json
  from datetime import datetime
  from uuid import UUID
  from sqlalchemy import select
  from src.database.connection import async_session_maker
  from src.database.models import Project, ScarCommandExecution, ScarCommandType, ExecutionStatus
  ```
- **LOGIC**:
  ```python
  async def test_e2e_sse():
      """End-to-end test: Create execution record → Verify SSE stream."""

      # Step 1: Get or create project
      async with async_session_maker() as session:
          project = (await session.execute(select(Project).limit(1))).scalar_one()
          project_id = project.id
          print(f"Using project: {project.name} ({project_id})\n")

      # Step 2: Start SSE client in background
      print("Starting SSE client...\n")
      sse_events = []

      async def sse_listener():
          url = f"http://localhost:8000/api/sse/scar/{project_id}?verbosity=2"
          async with httpx.AsyncClient(timeout=None) as client:
              async with client.stream("GET", url) as response:
                  async for line in response.aiter_lines():
                      if line.startswith("data: "):
                          data = json.loads(line[6:])
                          sse_events.append(data)
                          print(f"[SSE Event] {data['message']}")

      sse_task = asyncio.create_task(sse_listener())
      await asyncio.sleep(1)  # Let SSE connect

      # Step 3: Create test execution record
      print("\nCreating test SCAR execution record...\n")
      async with async_session_maker() as session:
          execution = ScarCommandExecution(
              project_id=project_id,
              command_type=ScarCommandType.PRIME,
              command_args="test",
              status=ExecutionStatus.COMPLETED,
              started_at=datetime.utcnow(),
              completed_at=datetime.utcnow(),
              output="Test execution for SSE verification",
          )
          session.add(execution)
          await session.commit()
          await session.refresh(execution)

          print(f"Created execution: {execution.id}")
          print(f"Command: {execution.command_type.value}")
          print(f"Status: {execution.status.value}")
          print(f"Timestamp: {execution.started_at}\n")

      # Step 4: Wait for SSE to pick it up (2s poll interval + buffer)
      print("Waiting 5 seconds for SSE to detect and stream...\n")
      await asyncio.sleep(5)

      # Step 5: Check results
      sse_task.cancel()

      if sse_events:
          print(f"✅ SUCCESS: SSE streamed {len(sse_events)} events")
          for event in sse_events:
              print(f"  - {event}")
      else:
          print("❌ FAILURE: SSE did not stream the execution record")
          print("This indicates a problem in the SSE feed service polling logic")

      return len(sse_events) > 0

  if __name__ == "__main__":
      success = asyncio.run(test_e2e_sse())
      exit(0 if success else 1)
  ```
- **VALIDATE**:
  ```bash
  uv run python scripts/test_e2e_sse.py
  ```
  **Expected**: Should create a test execution record and verify it appears in SSE feed within 5 seconds.

### Task 4: ADD enhanced diagnostic logging

- **IMPLEMENT**: Enhanced logging in SCAR executor and SSE feed service
- **PURPOSE**: Trace execution flow in production logs
- **FILE**: `src/services/scar_executor.py`
- **CHANGES**:
  ```python
  # After line 94 (after session.add(execution))
  logger.info(
      f"Created ScarCommandExecution record",
      extra={
          "execution_id": str(execution.id),
          "project_id": str(project_id),
          "command": command.value,
          "status": "QUEUED",
      }
  )

  # After line 102 (after updating to RUNNING)
  logger.info(
      f"Updated ScarCommandExecution to RUNNING",
      extra={"execution_id": str(execution.id), "project_id": str(project_id)}
  )

  # After line 139 (after updating to COMPLETED)
  logger.info(
      f"Updated ScarCommandExecution to COMPLETED",
      extra={
          "execution_id": str(execution.id),
          "project_id": str(project_id),
          "output_length": len(output),
      }
  )
  ```
- **FILE**: `src/services/scar_feed_service.py`
- **CHANGES**:
  ```python
  # After line 130 (after querying new activities)
  if new_activities:
      logger.debug(
          f"SSE feed detected {len(new_activities)} new activities",
          extra={
              "project_id": str(project_id),
              "activity_ids": [str(a.id) for a in new_activities],
          }
      )
  ```
- **VALIDATE**: Check that logs include execution_id tracking throughout lifecycle

### Task 5: INVESTIGATE database transaction isolation

- **IMPLEMENT**: Verify session isolation and commit timing
- **PURPOSE**: Ensure records are committed and visible to SSE polling
- **FILE**: `src/services/scar_executor.py`
- **CHECK**: Lines 94-95, 102, 139, 173, 197, 226
  - All show `await session.commit()` after critical updates
  - ✅ This should be working correctly
- **FILE**: `src/database/connection.py`
- **CHECK**: Lines 35-37
  ```python
  expire_on_commit=False,  # ← CRITICAL: Allows accessing objects after commit
  autocommit=False,        # ← Manual commit control
  autoflush=False,         # ← Manual flush control
  ```
  - ✅ Configuration is correct
- **POTENTIAL ISSUE**: WebSocket handler session vs SSE feed session
  - WebSocket uses dependency injection: `Depends(get_session)`
  - SSE creates its own session: `async with async_session_maker() as session`
  - Both should see committed data - isolation is working correctly
- **VALIDATE**: No changes needed if commits are happening

### Task 6: INVESTIGATE agent execute_scar invocation

- **IMPLEMENT**: Add logging to verify agent is calling execute_scar
- **PURPOSE**: Determine if agent is actually invoking SCAR or generating responses without it
- **FILE**: `src/agent/orchestrator_agent.py`
- **ADD**: Enhanced logging in execute_scar tool (after line 308)
  ```python
  logger.info(
      f"Agent calling execute_scar tool",
      extra={
          "project_id": str(ctx.deps.project_id),
          "command": command,
          "args": args,
      }
  )

  # Execute via scar_executor
  result = await execute_scar_command(ctx.deps.session, ctx.deps.project_id, scar_cmd, args or [])

  logger.info(
      f"execute_scar tool completed",
      extra={
          "project_id": str(ctx.deps.project_id),
          "command": command,
          "success": result.success,
          "duration": result.duration_seconds,
      }
  )
  ```
- **FILE**: `src/agent/orchestrator_agent.py`
- **CHECK**: System prompt (via prompts.py lines 251-276) includes proactive execution guidance
  - ✅ Prompt clearly instructs agent to call execute_scar for analysis
- **HYPOTHESIS**: Agent might be responding WITHOUT calling execute_scar in some cases
  - **Test**: Check logs for "Agent calling execute_scar tool" when user says "analyze codebase"
  - **If missing**: Agent is not invoking the tool despite system prompt guidance
- **VALIDATE**: Check application logs for tool invocation tracking

### Task 7: INVESTIGATE SCAR HTTP API connectivity

- **IMPLEMENT**: Test script to verify SCAR API is reachable
- **PURPOSE**: Rule out SCAR connectivity as the issue
- **LOCATION**: `scripts/test_scar_connection.py`
- **LOGIC**:
  ```python
  import httpx
  import asyncio
  from src.config import settings

  async def test_scar_connection():
      """Test if SCAR HTTP API is accessible."""
      url = settings.scar_base_url
      print(f"Testing SCAR connection: {url}\n")

      try:
          async with httpx.AsyncClient(timeout=5.0) as client:
              # Try health check or root endpoint
              response = await client.get(f"{url}/")
              print(f"✅ SCAR is reachable: HTTP {response.status_code}")
              return True
      except httpx.ConnectError as e:
          print(f"❌ SCAR connection failed: {e}")
          print(f"   Ensure SCAR is running at {url}")
          return False
      except Exception as e:
          print(f"❌ Unexpected error: {e}")
          return False

  if __name__ == "__main__":
      success = asyncio.run(test_scar_connection())
      exit(0 if success else 1)
  ```
- **VALIDATE**:
  ```bash
  uv run python scripts/test_scar_connection.py
  ```
  **Expected**: Should confirm SCAR is running or report connection failure

### Task 8: INVESTIGATE SSE feed message format

- **IMPLEMENT**: Verify activity dict format matches frontend expectations
- **PURPOSE**: Ensure SSE events have all required fields
- **FILE**: `src/services/scar_feed_service.py` (lines 132-148)
- **CHECK**: Activity dict structure
  ```python
  activity_dict = {
      "id": str(activity.id),
      "timestamp": activity.started_at.isoformat(),
      "source": activity.source,  # ← Uses @property, always "scar"
      "message": f"{activity.command_type.value}: {activity.status.value}",
      "phase": activity.phase.name if activity.phase else None,
  }
  ```
- **FILE**: `frontend/src/hooks/useScarFeed.ts` (lines 3-9)
- **CHECK**: Frontend interface
  ```typescript
  export interface ScarActivity {
    id: string;
    timestamp: string;
    source: 'po' | 'scar' | 'claude';
    message: string;
    phase?: string;
  }
  ```
- **MATCH**: ✅ Formats match perfectly
- **VALIDATE**: No changes needed

### Task 9: CREATE comprehensive RCA report

- **IMPLEMENT**: Execute all diagnostic scripts and compile findings
- **PURPOSE**: Identify the exact failure point
- **LOCATION**: `.agents/reports/rca-sse-feed-issue-45.md`
- **TEMPLATE**:
  ````markdown
  # Root Cause Analysis: SSE Feed Not Showing SCAR Activity (Issue #45)

  ## Investigation Date
  {DATE}

  ## Test Results

  ### 1. Database Inspection
  ```bash
  uv run python scripts/debug_scar_executions.py
  ```
  **Result**: {PASS/FAIL}
  **Findings**: {Description of what was found}

  ### 2. SSE Endpoint Test
  ```bash
  timeout 10s uv run python scripts/test_sse_feed.py <project_id>
  ```
  **Result**: {PASS/FAIL}
  **Findings**: {Description}

  ### 3. End-to-End Integration Test
  ```bash
  uv run python scripts/test_e2e_sse.py
  ```
  **Result**: {PASS/FAIL}
  **Findings**: {Description}

  ### 4. SCAR Connectivity Test
  ```bash
  uv run python scripts/test_scar_connection.py
  ```
  **Result**: {PASS/FAIL}
  **Findings**: {Description}

  ### 5. Application Logs Review
  **Command**: `tail -f logs/app.log | grep -E "execute_scar|ScarCommandExecution"`
  **Findings**: {Key log entries}

  ## Root Cause Hypothesis

  Based on test results, the most likely root cause is:

  {HYPOTHESIS WITH EVIDENCE}

  ## Recommended Fix

  {SPECIFIC FIX DESCRIPTION}

  ## Follow-Up Tasks

  - [ ] Implement fix
  - [ ] Re-run all diagnostic tests
  - [ ] Perform end-to-end manual test
  - [ ] Update documentation if needed
  ````
- **EXECUTE**: Run all diagnostic scripts and fill in the report
- **VALIDATE**: RCA report should clearly identify the root cause with evidence

### Task 10: IMPLEMENT targeted fix based on RCA findings

- **PATTERN**: This task is RCA-dependent and will be defined after Task 9
- **CONDITIONAL FIXES**:

**If RCA shows: Agent not calling execute_scar**
  - **FILE**: `src/agent/prompts.py`
  - **FIX**: Strengthen system prompt to ALWAYS call execute_scar for analysis requests
  - **ADD**: Tool use examples in prompt

**If RCA shows: Database records not created**
  - **FILE**: `src/services/scar_executor.py`
  - **FIX**: Ensure session.commit() is awaited properly
  - **CHECK**: Transaction rollback handling

**If RCA shows: SSE polling not detecting records**
  - **FILE**: `src/services/scar_feed_service.py`
  - **FIX**: Verify timestamp comparison logic
  - **NOTE**: Already fixed in commit d928ef6, but verify it's working

**If RCA shows: Frontend not receiving events**
  - **FILE**: `frontend/src/hooks/useScarFeed.ts`
  - **FIX**: Add error handling and connection retry logic
  - **ADD**: Console logging for debugging

**If RCA shows: CORS or network issues**
  - **FILE**: `src/main.py`
  - **FIX**: Verify CORS allows SSE connections
  - **CHECK**: EventSource headers are allowed

- **VALIDATE**: Re-run failing diagnostic test to confirm fix works

### Task 11: ADD integration test to prevent regression

- **IMPLEMENT**: Automated test in test suite
- **PURPOSE**: Ensure SSE feed always works going forward
- **LOCATION**: `tests/integration/test_sse_feed.py`
- **PATTERN**: Based on test patterns in existing test files
- **IMPORTS**:
  ```python
  import pytest
  import asyncio
  from uuid import UUID
  from datetime import datetime
  from httpx import AsyncClient, ASGITransport
  from sqlalchemy import select

  from src.main import app
  from src.database.connection import async_session_maker
  from src.database.models import Project, ScarCommandExecution, ScarCommandType, ExecutionStatus
  ```
- **TESTS**:
  ```python
  @pytest.mark.asyncio
  async def test_sse_feed_streams_scar_executions(test_project_id: UUID):
      """Test that SSE feed streams SCAR execution records."""

      # Create test execution
      async with async_session_maker() as session:
          execution = ScarCommandExecution(
              project_id=test_project_id,
              command_type=ScarCommandType.PRIME,
              command_args="test",
              status=ExecutionStatus.COMPLETED,
              started_at=datetime.utcnow(),
              output="Test output",
          )
          session.add(execution)
          await session.commit()
          await session.refresh(execution)
          execution_id = execution.id

      # Connect to SSE feed
      transport = ASGITransport(app=app)
      async with AsyncClient(transport=transport, base_url="http://test") as client:
          events = []

          async with client.stream(
              "GET", f"/api/sse/scar/{test_project_id}?verbosity=2"
          ) as response:
              assert response.status_code == 200

              # Collect events for 5 seconds
              timeout = asyncio.get_event_loop().time() + 5
              async for line in response.aiter_lines():
                  if asyncio.get_event_loop().time() > timeout:
                      break

                  if line.startswith("data: "):
                      import json
                      data = json.loads(line[6:])
                      events.append(data)

          # Verify execution appeared in feed
          execution_ids = [e["id"] for e in events]
          assert str(execution_id) in execution_ids, "Execution not found in SSE feed"
  ```
- **VALIDATE**:
  ```bash
  uv run pytest tests/integration/test_sse_feed.py -v
  ```

### Task 12: UPDATE documentation with troubleshooting guide

- **IMPLEMENT**: Add SSE feed troubleshooting section to README or docs
- **PURPOSE**: Help future developers debug SSE issues
- **LOCATION**: `docs/troubleshooting/sse-feed.md` (create if needed)
- **CONTENT**:
  ````markdown
  # SSE Feed Troubleshooting Guide

  ## Overview

  The SSE (Server-Sent Events) feed streams SCAR command execution activity to the WebUI in real-time.

  ## Architecture

  ```
  User Message → WebSocket → Orchestrator Agent → SCAR Executor → Database
                                                                      ↓
  Frontend ← SSE Endpoint ← SSE Feed Service ← Polling (2s) ← Database
  ```

  ## Common Issues

  ### SSE Feed Shows No Activity

  **Symptoms:** Right pane in WebUI remains empty even though PM responds.

  **Diagnostic Steps:**

  1. **Check database records:**
     ```bash
     uv run python scripts/debug_scar_executions.py
     ```
     - If no records: Agent is not calling execute_scar or SCAR executor is failing
     - If records exist: Problem is in SSE polling or streaming

  2. **Test SSE endpoint directly:**
     ```bash
     PROJECT_ID="<your-project-id>"
     timeout 10s uv run python scripts/test_sse_feed.py $PROJECT_ID
     ```
     - Should see heartbeat events every 30 seconds
     - Should see activity events if executions exist

  3. **Run end-to-end test:**
     ```bash
     uv run python scripts/test_e2e_sse.py
     ```
     - Creates test execution and verifies SSE streaming

  4. **Check application logs:**
     ```bash
     tail -f logs/app.log | grep -E "execute_scar|ScarCommandExecution|SSE"
     ```
     - Look for: "Agent calling execute_scar tool"
     - Look for: "Created ScarCommandExecution record"
     - Look for: "SSE feed detected N new activities"

  **Common Root Causes:**

  1. **Agent not calling execute_scar:** System prompt might need strengthening
  2. **Database transaction not committed:** Session configuration issue
  3. **SSE polling logic broken:** Timestamp comparison issue (fixed in d928ef6)
  4. **Frontend not connecting:** CORS or EventSource configuration issue
  5. **SCAR not running:** Backend can't connect to SCAR HTTP API

  ## Configuration

  **Backend** (`src/config.py`):
  ```python
  scar_base_url: str = "http://localhost:3000"
  ```

  **Frontend** (`frontend/src/hooks/useScarFeed.ts`):
  ```typescript
  const eventSource = new EventSource(`/api/sse/scar/${projectId}?verbosity=${verbosity}`);
  ```

  ## Manual Testing

  1. Start backend: `uv run uvicorn src.main:app --reload`
  2. Start frontend: `cd frontend && npm run dev`
  3. Open browser DevTools → Network tab
  4. Send message: "analyze the codebase"
  5. Check:
     - Network tab shows `/api/sse/scar/{id}` connection with type "eventsource"
     - Console shows "SSE connected"
     - Right pane shows activity items

  ## Debugging Tips

  - **SSE connections stay open:** Use browser DevTools to see event stream
  - **Heartbeats are normal:** Sent every 30 seconds to keep connection alive
  - **Polling is lazy:** 2-second intervals mean up to 2s delay for new activities
  - **Verbosity levels:** 1=low, 2=medium (default), 3=high
  ````
- **VALIDATE**: Documentation is clear and actionable

---

## TESTING STRATEGY

### Diagnostic Tests (Manual Execution)

**Purpose**: Identify root cause systematically

1. **Database Inspection Test**
   - Script: `scripts/debug_scar_executions.py`
   - Validates: ScarCommandExecution records exist in database
   - Expected: Lists recent executions per project

2. **SSE Endpoint Test**
   - Script: `scripts/test_sse_feed.py`
   - Validates: SSE endpoint is accessible and streaming
   - Expected: Receives heartbeat and activity events

3. **End-to-End Integration Test**
   - Script: `scripts/test_e2e_sse.py`
   - Validates: Complete flow from database write to SSE stream
   - Expected: Created execution appears in SSE feed within 5 seconds

4. **SCAR Connectivity Test**
   - Script: `scripts/test_scar_connection.py`
   - Validates: SCAR HTTP API is reachable
   - Expected: Connection succeeds or reports specific failure

### Integration Tests (Automated)

**Purpose**: Prevent regression

1. **SSE Feed Integration Test**
   - File: `tests/integration/test_sse_feed.py`
   - Validates: SSE feed streams execution records correctly
   - Framework: pytest with async support

### Manual Validation

**Purpose**: Verify user-facing functionality

1. **WebUI End-to-End Test**
   - Start backend and frontend
   - Send message: "analyze the codebase"
   - Verify:
     - PM responds with analysis
     - Right pane shows "prime" command execution
     - Activity updates in real-time

2. **Browser DevTools Inspection**
   - Network tab: Check `/api/sse/scar/{id}` connection
   - Console: Check for "SSE connected" message
   - Console: Check for any errors

---

## VALIDATION COMMANDS

Execute every command to ensure zero regressions and 100% feature correctness.

### Level 1: Import Validation (CRITICAL)

**Verify all imports resolve before running tests:**

```bash
uv run python -c "from src.main import app; from src.services.scar_feed_service import stream_scar_activity; from src.services.scar_executor import execute_scar_command; print('✓ All imports valid')"
```

**Expected:** "✓ All imports valid" (no ModuleNotFoundError or ImportError)

**Why:** Catches incorrect imports immediately. If this fails, fix imports before proceeding.

### Level 2: Diagnostic Scripts Execution

**Run all diagnostic scripts:**

```bash
echo "=== Database Inspection ==="
uv run python scripts/debug_scar_executions.py

echo -e "\n=== SCAR Connectivity ==="
uv run python scripts/test_scar_connection.py

echo -e "\n=== End-to-End SSE Test ==="
uv run python scripts/test_e2e_sse.py
```

**Expected:**
- Database inspection shows recent executions (if any have occurred)
- SCAR connectivity succeeds or reports clear failure
- E2E test creates record and detects it in SSE feed within 5 seconds

**Why:** Validates each component of the SSE flow independently.

### Level 3: Syntax & Style

**Run linting and formatting:**

```bash
uv run ruff check src/ scripts/ tests/
uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
```

**Expected:** No errors or warnings

### Level 4: Unit Tests

**Run existing unit tests:**

```bash
uv run pytest tests/unit/ -v
```

**Expected:** All tests pass

### Level 5: Integration Tests

**Run SSE feed integration tests:**

```bash
uv run pytest tests/integration/test_sse_feed.py -v
```

**Expected:** All tests pass, confirming SSE feed streams executions correctly

### Level 6: Manual WebUI Validation

**Start services and perform manual test:**

```bash
# Terminal 1: Start backend
uv run uvicorn src.main:app --reload --log-level debug

# Terminal 2: Start frontend
cd frontend && npm run dev

# Terminal 3: Monitor logs
tail -f logs/app.log | grep -E "execute_scar|ScarCommandExecution|SSE"
```

**Manual Steps:**
1. Open browser to `http://localhost:5173`
2. Select a project
3. Open browser DevTools (F12) → Console + Network tabs
4. Send message: "analyze the codebase"
5. Observe:
   - PM responds with analysis
   - Network tab shows active SSE connection
   - Console shows "SSE connected"
   - Right pane displays SCAR activity
   - Logs show execution flow

**Expected:**
- ✅ SSE connection established (Network tab)
- ✅ Activity appears in right pane within 2-5 seconds
- ✅ Logs show: "Agent calling execute_scar tool" → "Created ScarCommandExecution record" → "SSE feed detected 1 new activities"

### Level 7: Regression Check

**Verify no existing functionality broken:**

```bash
# Run full test suite
uv run pytest -v

# Spot-check critical endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/projects

# Test WebSocket chat (non-SSE messaging)
# Should still work normally
```

**Expected:** All tests pass, all endpoints respond correctly

---

## ACCEPTANCE CRITERIA

- [x] RCA completed with clear root cause identification
- [ ] All diagnostic scripts execute successfully
- [ ] Root cause fix implemented and tested
- [ ] SSE feed streams SCAR execution records within 2-5 seconds
- [ ] WebUI right pane displays SCAR activity in real-time
- [ ] Integration test added to prevent regression
- [ ] All existing tests pass
- [ ] Manual WebUI test confirms end-to-end functionality
- [ ] Enhanced logging added for troubleshooting
- [ ] Documentation updated with troubleshooting guide
- [ ] No regressions in WebSocket chat or other features

---

## COMPLETION CHECKLIST

- [ ] All diagnostic scripts created and validated
- [ ] RCA report completed with findings
- [ ] Root cause identified with evidence
- [ ] Targeted fix implemented
- [ ] Enhanced logging added
- [ ] Integration test created
- [ ] All validation commands executed successfully
- [ ] Manual WebUI test confirms fix works
- [ ] Documentation updated
- [ ] Code reviewed for quality
- [ ] Acceptance criteria all met

---

## NOTES

### Key Insights from Investigation

1. **Recent Fix Applied**: Commit d928ef6 (Jan 6, 2026) fixed UUID comparison bug in SSE polling
   - Changed from `id > UUID(last_id)` to `started_at > last_dt`
   - This was a critical fix for chronological ordering

2. **Session Configuration is Correct**:
   - `expire_on_commit=False` allows accessing objects after commit
   - Sessions properly commit after each operation
   - SSE feed creates independent session for polling

3. **Agent Tool Integration Exists**:
   - `execute_scar` tool added in commit 00f82a5 (Jan 5, 2026)
   - System prompt includes proactive execution guidance
   - **Hypothesis**: Agent might not be calling the tool despite guidance

4. **Most Likely Root Causes** (priority order):
   1. **Agent not invoking execute_scar**: Despite system prompt, agent might respond without calling tool
   2. **SCAR connectivity failure**: SCAR HTTP API not running or unreachable
   3. **Database record creation failure**: Unlikely given commit patterns, but possible
   4. **Frontend connection issue**: EventSource not connecting due to CORS or network issue
   5. **SSE polling regression**: Unlikely after d928ef6 fix, but should verify

### Implementation Strategy

- **Phase 1 (RCA)**: Run all diagnostic scripts to identify exact failure point
- **Phase 2 (Fix)**: Implement targeted fix based on RCA findings
- **Phase 3 (Test)**: Verify fix with automated and manual tests
- **Phase 4 (Document)**: Update troubleshooting guide for future reference

### Edge Cases to Consider

- **User sends message before SCAR execution completes**: SSE should show "RUNNING" status, then update to "COMPLETED"
- **Multiple concurrent SCAR executions**: SSE should stream all activities in chronological order
- **SSE connection drops**: Frontend should show "Disconnected" status and EventSource will auto-reconnect
- **Very long SCAR execution (>300s)**: May timeout, should handle gracefully

### Performance Considerations

- **2-second polling interval**: Acceptable latency for user feedback
- **30-second heartbeat**: Keeps connection alive, prevents timeout
- **Database query on each poll**: Efficient with timestamp index
- **Long-lived SSE connections**: Normal for SSE, FastAPI handles well

### Security Considerations

- **Project ID validation**: SSE endpoint should verify user has access to project
- **CORS configuration**: Allows all origins in development, restricted in production
- **Rate limiting**: Should apply to SSE endpoint to prevent abuse
