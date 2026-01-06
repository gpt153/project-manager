# Feature: Fix SSE Feed End-to-End - Complete Root Cause Analysis and Solution

The following plan should be complete, but it's important that you validate documentation and codebase patterns and task sanity before you start implementing.

Pay special attention to naming of existing utils types and models. Import from the right files etc.

## Feature Description

Fix the Server-Sent Events (SSE) feed in the WebUI that fails to display real-time SCAR command execution activity, despite backend logs showing successful SCAR operations. This is a complete end-to-end debugging and fixing effort covering the entire data flow: SCAR execution → database persistence → SSE streaming → frontend display.

## User Story

As a user of the Project Manager WebUI
I want to see real-time SCAR command execution activity in the SSE feed (right pane)
So that I have transparency into what SCAR is doing and can monitor system operations

## Problem Statement

**Current Symptoms (Issue #45, #49):**
1. User sends message requesting codebase analysis
2. PM responds with analysis results
3. SSE feed (right pane) remains completely empty - NO activity shown
4. Backend logs show: "Executing SCAR command: prime" → "SCAR command completed successfully"
5. Unknown: Are ScarCommandExecution records being created in database?

**Evidence from Issue #45:**
```
Backend Logs (14:24):
2026-01-06 14:24:15 - Executing SCAR command: prime
2026-01-06 14:24:15 - Switching SCAR to codebase: health-agent
2026-01-06 14:24:15 - SCAR codebase switched successfully
2026-01-06 14:24:15 - SCAR command sent successfully
2026-01-06 14:24:21 - SCAR command completed successfully

User Experience:
- Right pane shows "No SCAR activity yet"
- PM provides detailed analysis WITHOUT visible SCAR activity
```

**Previous Fix Attempts:**
- **PR #46 (d928ef6)**: Fixed SSE polling timestamp comparison (was comparing UUIDs incorrectly)
- **PR #48 (8d8ceb3)**: Fixed frontend to listen for named 'activity' events
- **Both merged but issue persists** - indicates deeper systemic problem

**Critical Questions to Answer:**
1. ✅ Is `execute_scar_command()` being called? (YES - logs confirm)
2. ❓ Are ScarCommandExecution records being created in database?
3. ❓ Is SSE feed service querying the database correctly?
4. ❓ Is SSE endpoint streaming events to frontend?
5. ❓ Is frontend receiving and displaying SSE events?

## Solution Statement

Perform systematic end-to-end Root Cause Analysis with diagnostic scripts and database inspection to identify the exact failure point in the data flow chain:

**SCAR Execution** → **Database Write** → **SSE Query** → **SSE Stream** → **Frontend Display**

Based on findings, implement targeted fixes ensuring:
1. ScarCommandExecution records are reliably created and committed to database
2. SSE feed service detects new records via polling
3. SSE endpoint streams events with correct format
4. Frontend receives and displays activities in real-time

## Feature Metadata

**Feature Type**: Bug Fix / Root Cause Analysis
**Estimated Complexity**: High
**Primary Systems Affected**:
- SCAR executor service (`src/services/scar_executor.py`)
- Database models and session management (`src/database/models.py`, `src/database/connection.py`)
- SSE feed service (`src/services/scar_feed_service.py`)
- SSE endpoint (`src/api/sse.py`)
- Frontend SSE hook (`frontend/src/hooks/useScarFeed.ts`)
- Frontend activity feed component (`frontend/src/components/RightPanel/ScarActivityFeed.tsx`)

**Dependencies**:
- `sse-starlette==2.1.0` - SSE streaming library
- `sqlalchemy[asyncio]>=2.0.36` - Async database ORM
- `pydantic-ai>=0.0.65` - Agent framework
- `fastapi>=0.115.0` - Web framework
- `httpx` - HTTP client for SCAR communication

---

## CONTEXT REFERENCES

### Relevant Codebase Files IMPORTANT: YOU MUST READ THESE FILES BEFORE IMPLEMENTING!

**SCAR Execution Layer:**
- `src/services/scar_executor.py` (lines 49-233) - **Why**: Creates ScarCommandExecution records, database commits
- `src/scar/client.py` (lines 112-290) - **Why**: HTTP client for SCAR communication, workspace setup
- `src/agent/orchestrator_agent.py` (lines 270-316) - **Why**: execute_scar tool invocation by agent

**Database Layer:**
- `src/database/models.py` (lines 248-301) - **Why**: ScarCommandExecution model definition, @property methods
- `src/database/connection.py` (lines 32-62) - **Why**: Session factory configuration (expire_on_commit setting critical)
- `src/config.py` (lines 22-26) - **Why**: Database connection settings

**SSE Streaming Layer:**
- `src/api/sse.py` (lines 22-104) - **Why**: SSE endpoint, event generator, heartbeat logic
- `src/services/scar_feed_service.py` (lines 71-149) - **Why**: Database polling, activity streaming logic
- `src/main.py` (line 165) - **Why**: SSE router registration

**Frontend Layer:**
- `frontend/src/hooks/useScarFeed.ts` (lines 15-42) - **Why**: EventSource client, activity/heartbeat listeners
- `frontend/src/components/RightPanel/ScarActivityFeed.tsx` (lines 8-61) - **Why**: UI rendering, verbosity control

**Testing:**
- `tests/services/test_scar_executor.py` (lines 135-160) - **Why**: Test pattern for command execution tracking

### New Files to Create

**Diagnostic Scripts:**
- `scripts/debug_sse_feed.py` - End-to-end diagnostic script to trace data flow
- `scripts/test_sse_endpoint.py` - Manual SSE endpoint testing with curl/httpx
- `scripts/inspect_database.py` - Query ScarCommandExecution records directly

**Tests:**
- `tests/api/test_sse.py` - SSE endpoint unit tests (if doesn't exist)
- `tests/services/test_scar_feed_service.py` - Feed service unit tests (if doesn't exist)

### Relevant Documentation YOU SHOULD READ THESE BEFORE IMPLEMENTING!

**SSE Starlette:**
- [sse-starlette Documentation](https://github.com/sysid/sse-starlette)
  - Section: EventSourceResponse usage
  - **Why**: Understand correct SSE event format and streaming patterns

**Server-Sent Events Spec:**
- [MDN SSE Guide](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)
  - Section: Event stream format
  - **Why**: Understand event/data format that frontend EventSource expects

**SQLAlchemy Async:**
- [SQLAlchemy AsyncIO Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
  - Section: Session management and expire_on_commit
  - **Why**: Understand session lifecycle and when objects become detached

**FastAPI SSE:**
- [FastAPI StreamingResponse](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)
  - Section: Async generators
  - **Why**: Understand FastAPI streaming patterns

### Patterns to Follow

**Naming Conventions:**
```python
# Snake case for functions and variables
async def execute_scar_command(session: AsyncSession, ...) -> CommandResult:
    pass

# PascalCase for classes
class ScarCommandExecution(Base):
    pass

# SCREAMING_SNAKE_CASE for constants
HEARTBEAT_INTERVAL = 30
```

**Error Handling:**
```python
# From src/scar/client.py (lines 158-162)
try:
    response = await client.post(url, json=body)
    response.raise_for_status()
except httpx.HTTPError as e:
    logger.error(f"Request failed: {e}")
    raise
```

**Logging Pattern:**
```python
# From src/services/scar_executor.py (lines 108-111)
logger.info(
    f"Executing SCAR command: {command.value}",
    extra={"project_id": str(project_id), "command": command.value}
)
```

**Database Session Pattern:**
```python
# From src/api/sse.py (lines 55-60)
async with async_session_maker() as session:
    # Use session
    activity_stream = stream_scar_activity(session, project_id)
    async for activity in activity_stream:
        yield activity
```

**SSE Event Format:**
```python
# From src/api/sse.py (lines 69-79)
# CORRECT: Named event with JSON data
yield {
    "event": "activity",
    "data": json.dumps({
        "id": "...",
        "timestamp": "...",
        "source": "scar",
        "message": "..."
    })
}

# CORRECT: Heartbeat event
yield {
    "event": "heartbeat",
    "data": json.dumps({"status": "alive", "timestamp": "..."})
}
```

**Frontend EventSource Pattern:**
```typescript
// From frontend/src/hooks/useScarFeed.ts (lines 15-32)
const eventSource = new EventSource(`/api/sse/scar/${projectId}?verbosity=${verbosity}`);

eventSource.addEventListener('activity', (event) => {
  const activity: ScarActivity = JSON.parse(event.data);
  setActivities((prev) => [...prev, activity]);
});

eventSource.addEventListener('heartbeat', (event) => {
  console.log('SSE heartbeat:', event.data);
});
```

---

## IMPLEMENTATION PLAN

### Phase 1: Root Cause Analysis - Diagnostic Scripts

Create diagnostic tools to systematically trace the data flow and identify the exact failure point.

**Objective**: Answer all critical questions with concrete evidence from production system.

### Phase 2: Database Inspection

Verify ScarCommandExecution records are being created and persisted correctly.

**Objective**: Confirm database write operations are working.

### Phase 3: SSE Service Validation

Test the SSE feed service in isolation to verify polling and streaming logic.

**Objective**: Confirm SSE service can query and stream existing records.

### Phase 4: End-to-End Integration Fix

Based on RCA findings, implement targeted fixes to broken components.

**Objective**: Restore full data flow from SCAR execution to frontend display.

### Phase 5: Testing & Validation

Comprehensive testing to ensure fix works end-to-end and doesn't regress.

**Objective**: Verify 100% reliability of SSE feed under various scenarios.

---

## STEP-BY-STEP TASKS

IMPORTANT: Execute every task in order, top to bottom. Each task is atomic and independently testable.

### CREATE scripts/debug_sse_feed.py

- **IMPLEMENT**: End-to-end diagnostic script that traces entire data flow
- **FEATURES**:
  1. Query database for ScarCommandExecution records
  2. Test SSE endpoint by making HTTP request
  3. Parse SSE stream and verify events
  4. Report findings with clear pass/fail for each component
- **IMPORTS**: `asyncio`, `httpx`, `sqlalchemy`, `src.database.connection`, `src.database.models`
- **PATTERN**: Mirror `tests/conftest.py` for database session setup
- **VALIDATE**: `python scripts/debug_sse_feed.py <project-id>`

**Implementation Details:**
```python
"""
End-to-end diagnostic script for SSE feed debugging.

Usage:
    python scripts/debug_sse_feed.py <project-id>

Output:
    ✓/✗ for each component in the data flow chain
"""

import asyncio
import sys
from uuid import UUID
import httpx
from sqlalchemy import select, desc
from src.database.connection import async_session_maker
from src.database.models import ScarCommandExecution, Project

async def diagnose_sse_feed(project_id: UUID):
    """Diagnose SSE feed end-to-end"""

    print(f"\n=== SSE Feed Diagnostic Report ===")
    print(f"Project ID: {project_id}\n")

    # Step 1: Check database for ScarCommandExecution records
    print("Step 1: Database - Query ScarCommandExecution records...")
    async with async_session_maker() as session:
        result = await session.execute(
            select(ScarCommandExecution)
            .where(ScarCommandExecution.project_id == project_id)
            .order_by(desc(ScarCommandExecution.started_at))
            .limit(10)
        )
        executions = result.scalars().all()

        if executions:
            print(f"✓ Found {len(executions)} ScarCommandExecution records")
            for ex in executions[:3]:
                print(f"  - ID: {ex.id}, Command: {ex.command_type.value}, Status: {ex.status.value}")
                print(f"    Started: {ex.started_at}, Completed: {ex.completed_at}")
        else:
            print(f"✗ NO ScarCommandExecution records found!")
            print(f"  → This is the root cause: execute_scar_command not creating records")
            return

    # Step 2: Test SSE feed service directly
    print("\nStep 2: SSE Service - Query via API endpoint...")
    try:
        async with httpx.AsyncClient() as client:
            # Connect to SSE endpoint
            url = f"http://localhost:8000/api/sse/scar/{project_id}?verbosity=2"

            async with client.stream('GET', url, timeout=10.0) as response:
                if response.status_code != 200:
                    print(f"✗ SSE endpoint returned {response.status_code}")
                    return

                print(f"✓ SSE endpoint connected (status 200)")

                # Read first few events
                event_count = 0
                async for line in response.aiter_lines():
                    if line.startswith('event:'):
                        event_type = line.split(':', 1)[1].strip()
                        print(f"  - Received event: {event_type}")
                        event_count += 1
                    elif line.startswith('data:'):
                        data = line.split(':', 1)[1].strip()
                        print(f"    Data: {data[:100]}...")

                    if event_count >= 3:
                        break

                if event_count == 0:
                    print(f"✗ No events received from SSE stream")
                    print(f"  → SSE service not streaming events (polling issue?)")
                else:
                    print(f"✓ Received {event_count} events from SSE stream")

    except Exception as e:
        print(f"✗ SSE endpoint test failed: {e}")
        return

    # Step 3: Summary
    print("\n=== Diagnostic Complete ===")
    print("Next steps: Review output above to identify failure point\n")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/debug_sse_feed.py <project-id>")
        sys.exit(1)

    project_id = UUID(sys.argv[1])
    asyncio.run(diagnose_sse_feed(project_id))
```

### CREATE scripts/inspect_database.py

- **IMPLEMENT**: Direct database inspection to view ScarCommandExecution records
- **FEATURES**:
  1. List all projects with their latest SCAR executions
  2. Show detailed execution info (timestamps, status, output)
  3. Identify projects with missing executions despite activity
- **IMPORTS**: `asyncio`, `sqlalchemy`, `src.database.connection`, `src.database.models`
- **PATTERN**: Use `select()` with joins to get project + execution data
- **VALIDATE**: `python scripts/inspect_database.py`

**Implementation Details:**
```python
"""
Database inspection script for ScarCommandExecution records.

Usage:
    python scripts/inspect_database.py
    python scripts/inspect_database.py --project <project-id>
"""

import asyncio
import sys
from uuid import UUID
from sqlalchemy import select, desc
from src.database.connection import async_session_maker
from src.database.models import ScarCommandExecution, Project

async def inspect_all_projects():
    """List all projects and their SCAR execution counts"""
    async with async_session_maker() as session:
        result = await session.execute(select(Project))
        projects = result.scalars().all()

        print("\n=== All Projects ===\n")
        for project in projects:
            exec_result = await session.execute(
                select(ScarCommandExecution)
                .where(ScarCommandExecution.project_id == project.id)
            )
            exec_count = len(exec_result.scalars().all())

            print(f"Project: {project.name} ({project.id})")
            print(f"  GitHub: {project.github_repo_url}")
            print(f"  SCAR Executions: {exec_count}")
            print()

async def inspect_project(project_id: UUID):
    """Inspect specific project's SCAR executions in detail"""
    async with async_session_maker() as session:
        # Get project
        result = await session.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()

        if not project:
            print(f"✗ Project {project_id} not found")
            return

        print(f"\n=== Project: {project.name} ===\n")

        # Get all executions
        result = await session.execute(
            select(ScarCommandExecution)
            .where(ScarCommandExecution.project_id == project_id)
            .order_by(desc(ScarCommandExecution.started_at))
        )
        executions = result.scalars().all()

        if not executions:
            print("✗ NO SCAR executions found for this project")
            return

        print(f"Total Executions: {len(executions)}\n")

        for idx, ex in enumerate(executions, 1):
            print(f"--- Execution #{idx} ---")
            print(f"ID: {ex.id}")
            print(f"Command: {ex.command_type.value}")
            print(f"Args: {ex.command_args}")
            print(f"Status: {ex.status.value}")
            print(f"Started: {ex.started_at}")
            print(f"Completed: {ex.completed_at}")
            if ex.output:
                print(f"Output: {ex.output[:200]}...")
            if ex.error:
                print(f"Error: {ex.error}")
            print()

if __name__ == "__main__":
    if "--project" in sys.argv:
        idx = sys.argv.index("--project")
        project_id = UUID(sys.argv[idx + 1])
        asyncio.run(inspect_project(project_id))
    else:
        asyncio.run(inspect_all_projects())
```

### RUN scripts/inspect_database.py

- **OBJECTIVE**: Determine if ScarCommandExecution records exist in database
- **EXPECTED**: Records should exist for recent SCAR command executions
- **VALIDATE**: Check output - if NO records found, issue is in `execute_scar_command()`

### RUN scripts/debug_sse_feed.py <project-id>

- **OBJECTIVE**: Trace complete data flow from database → SSE → frontend
- **EXPECTED**: Script should identify exact failure point
- **VALIDATE**: Review diagnostic output for ✓/✗ markers

### ANALYZE RCA Findings & Create Fix Plan

- **OBJECTIVE**: Based on diagnostic output, identify root cause
- **POSSIBLE FINDINGS**:
  1. **No database records**: Bug in `src/services/scar_executor.py` - transaction not committing
  2. **Records exist but SSE doesn't stream**: Bug in `src/services/scar_feed_service.py` - polling logic broken
  3. **SSE streams but frontend doesn't receive**: CORS, network, or EventSource configuration issue
  4. **Frontend receives but doesn't display**: React state update or rendering bug
- **IMPLEMENTATION**: Document findings in `.agents/rca-reports/sse-feed-rca-final.md`

### FIX: Database Transaction Commit (if RCA shows no records)

- **CONDITION**: Only if `scripts/inspect_database.py` shows NO ScarCommandExecution records
- **FILE**: `src/services/scar_executor.py`
- **ISSUE**: Transaction may not be committing properly
- **CHANGES**:
  1. Verify `await session.commit()` is called after creating execution record (line 94)
  2. Verify `await session.refresh(execution)` after commit (line 95)
  3. Add explicit commit after status updates (lines 102, 135, 173, 197, 226)
  4. Add logging to confirm commits: `logger.debug(f"Committed execution {execution.id} to database")`
- **PATTERN**: Mirror `tests/services/test_scar_executor.py` (line 26) - uses same session pattern
- **GOTCHA**: If using different session instance, records won't persist
- **VALIDATE**:
  ```bash
  # After fix, re-run inspection script
  python scripts/inspect_database.py --project <project-id>
  # Should see new ScarCommandExecution records
  ```

### FIX: SSE Polling Logic (if RCA shows records exist but not streaming)

- **CONDITION**: Only if records exist in DB but SSE doesn't stream them
- **FILE**: `src/services/scar_feed_service.py`
- **ISSUE**: Polling query may have incorrect timestamp comparison or session issues
- **CHANGES**:
  1. Review timestamp comparison logic (lines 111-119)
  2. Ensure `started_at` is not None before comparison
  3. Add logging: `logger.debug(f"Polling for activities after {last_timestamp}")`
  4. Verify session is not expired (detached objects)
- **PATTERN**: Use same session pattern as SSE endpoint (lines 55-60 in `src/api/sse.py`)
- **GOTCHA**: If `last_timestamp` is newer than all records, nothing streams
- **VALIDATE**:
  ```bash
  python scripts/debug_sse_feed.py <project-id>
  # Should see "✓ Received N events from SSE stream"
  ```

### FIX: Frontend EventSource Connection (if SSE streams but frontend doesn't receive)

- **CONDITION**: Only if SSE endpoint streams but frontend shows no activity
- **FILE**: `frontend/src/hooks/useScarFeed.ts`
- **ISSUE**: EventSource not connecting or event listeners not registered
- **CHANGES**:
  1. Add detailed console logging to track connection lifecycle
  2. Log all events received (not just activity/heartbeat)
  3. Add error details to console.error
  4. Verify API URL is correct (`/api/sse/scar/${projectId}`)
- **PATTERN**: Already correct (lines 15-42) but add more logging
- **GOTCHA**: CORS issues if API and frontend on different origins
- **VALIDATE**: Open browser DevTools → Console → should see connection logs

### ADD Comprehensive Logging to All Components

- **OBJECTIVE**: Add detailed logging to every component in the data flow chain
- **FILES**:
  - `src/services/scar_executor.py`: Log before/after database commits
  - `src/services/scar_feed_service.py`: Log poll queries and results
  - `src/api/sse.py`: Log when events are yielded
  - `frontend/src/hooks/useScarFeed.ts`: Log all EventSource events
- **PATTERN**: Use structured logging with extra fields
  ```python
  logger.debug(
      "Event yielded to SSE stream",
      extra={"project_id": str(project_id), "event_type": "activity", "activity_id": activity["id"]}
  )
  ```
- **VALIDATE**: Check logs during test run - should see complete trace

### CREATE tests/api/test_sse.py

- **IMPLEMENT**: Unit tests for SSE endpoint
- **TEST CASES**:
  1. `test_sse_endpoint_returns_200` - Verify endpoint exists and responds
  2. `test_sse_streams_initial_activities` - Verify initial activities are streamed
  3. `test_sse_streams_new_activities` - Verify polling detects new records
  4. `test_sse_heartbeat_events` - Verify heartbeat events sent every 30s
  5. `test_sse_event_format` - Verify event/data format matches spec
- **IMPORTS**: `pytest`, `httpx`, `src.database.models`, `src.database.connection`
- **PATTERN**: Use `httpx.AsyncClient().stream()` to test SSE endpoint
- **GOTCHA**: SSE endpoint streams indefinitely - use timeout to read limited events
- **VALIDATE**: `pytest tests/api/test_sse.py -v`

**Implementation Details:**
```python
"""Tests for SSE endpoint."""

import pytest
import asyncio
import json
from uuid import uuid4
from httpx import AsyncClient
from src.database.models import Project, ScarCommandExecution, ProjectStatus, CommandType, ExecutionStatus
from datetime import datetime

@pytest.mark.asyncio
async def test_sse_endpoint_returns_200(db_session, test_client):
    """Test SSE endpoint exists and returns 200"""
    project = Project(
        name="Test Project",
        status=ProjectStatus.PLANNING,
        github_repo_url="https://github.com/test/repo"
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Connect to SSE endpoint with short timeout
    async with AsyncClient(app=test_client.app, base_url="http://test") as client:
        async with client.stream('GET', f'/api/sse/scar/{project.id}?verbosity=2', timeout=2.0) as response:
            assert response.status_code == 200
            assert 'text/event-stream' in response.headers.get('content-type', '')

@pytest.mark.asyncio
async def test_sse_streams_initial_activities(db_session, test_client):
    """Test SSE streams existing activities on connection"""
    # Create project
    project = Project(
        name="Test Project",
        status=ProjectStatus.PLANNING,
        github_repo_url="https://github.com/test/repo"
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Create SCAR execution records
    execution = ScarCommandExecution(
        project_id=project.id,
        command_type=CommandType.PRIME,
        command_args="",
        status=ExecutionStatus.COMPLETED,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        output="Test output"
    )
    db_session.add(execution)
    await db_session.commit()

    # Connect to SSE and read events
    async with AsyncClient(app=test_client.app, base_url="http://test") as client:
        async with client.stream('GET', f'/api/sse/scar/{project.id}?verbosity=2', timeout=3.0) as response:
            events = []
            async for line in response.aiter_lines():
                if line.startswith('event:'):
                    event_type = line.split(':', 1)[1].strip()
                    events.append({'type': event_type})
                elif line.startswith('data:') and events:
                    data = line.split(':', 1)[1].strip()
                    events[-1]['data'] = json.loads(data)

                # Stop after receiving first activity event
                if any(e['type'] == 'activity' for e in events):
                    break

            # Verify activity event received
            activity_events = [e for e in events if e['type'] == 'activity']
            assert len(activity_events) > 0, "Should receive at least one activity event"

            # Verify event format
            activity = activity_events[0]['data']
            assert 'id' in activity
            assert 'timestamp' in activity
            assert 'source' in activity
            assert 'message' in activity
```

### CREATE tests/services/test_scar_feed_service.py

- **IMPLEMENT**: Unit tests for SSE feed service
- **TEST CASES**:
  1. `test_get_recent_scar_activity` - Verify fetching recent activities
  2. `test_stream_scar_activity_initial` - Verify initial activity stream
  3. `test_stream_scar_activity_polling` - Verify new activities detected via polling
  4. `test_verbosity_filtering` - Verify verbosity levels filter correctly
- **IMPORTS**: `pytest`, `asyncio`, `src.services.scar_feed_service`, `src.database.models`
- **PATTERN**: Test service functions directly (NOT via HTTP endpoint)
- **VALIDATE**: `pytest tests/services/test_scar_feed_service.py -v`

### UPDATE src/services/scar_executor.py - Add Explicit Session Flush

- **IMPLEMENT**: Ensure database records are immediately visible to other sessions
- **CHANGE**: After creating ScarCommandExecution record (line 94):
  ```python
  session.add(execution)
  await session.commit()
  await session.flush()  # Ensure write is visible to other sessions
  await session.refresh(execution)
  ```
- **PATTERN**: SQLAlchemy async session flush pattern
- **GOTCHA**: Without flush, record may not be visible to SSE polling query
- **VALIDATE**: Run `scripts/inspect_database.py` - records should appear immediately

### UPDATE src/api/sse.py - Add Connection Logging

- **IMPLEMENT**: Log SSE connection lifecycle for debugging
- **CHANGES**:
  1. Log when connection established (already at line 50)
  2. Log when events are yielded (add after line 69)
  3. Log when connection closes (already at line 102)
  4. Log errors with full context (already at line 86-90)
- **PATTERN**: Use structured logging with extra fields
- **VALIDATE**: Check logs show "SSE connection established" → "Event yielded" → "Connection closed"

### UPDATE frontend/src/hooks/useScarFeed.ts - Enhanced Logging

- **IMPLEMENT**: Detailed console logging for debugging EventSource
- **CHANGES**:
  ```typescript
  eventSource.onopen = () => {
    setIsConnected(true);
    console.log('[SSE] Connection opened to', `/api/sse/scar/${projectId}`);
  };

  eventSource.addEventListener('activity', (event) => {
    console.log('[SSE] Activity event received:', event.data);
    const activity: ScarActivity = JSON.parse(event.data);
    setActivities((prev) => [...prev, activity]);
  });

  eventSource.addEventListener('heartbeat', (event) => {
    console.log('[SSE] Heartbeat:', event.data);
  });

  eventSource.onerror = (error) => {
    console.error('[SSE] Connection error:', error);
    console.error('[SSE] EventSource state:', eventSource.readyState);
    setIsConnected(false);
  };
  ```
- **PATTERN**: Prefix all logs with `[SSE]` for easy filtering
- **VALIDATE**: Open browser DevTools → Console → filter for "[SSE]"

### MANUAL TEST: End-to-End User Flow

- **OBJECTIVE**: Manually test complete user journey
- **STEPS**:
  1. Start backend: `uvicorn src.main:app --reload`
  2. Start frontend: `cd frontend && npm run dev`
  3. Open WebUI: `http://localhost:3002`
  4. Create or select a project
  5. Send message: "Analyze the codebase"
  6. **OBSERVE**: Right pane SSE feed should show SCAR activity in real-time
  7. Verify activities appear as SCAR executes
- **EXPECTED**: Activities stream into right pane with timestamps and sources
- **VALIDATE**: Screenshot or video recording of working SSE feed

### MANUAL TEST: Network Inspection

- **OBJECTIVE**: Verify SSE connection in browser DevTools Network tab
- **STEPS**:
  1. Open browser DevTools → Network tab
  2. Filter for "sse" or "EventStream"
  3. Trigger SCAR command (send message to PM)
  4. Click on SSE request in Network tab
  5. **OBSERVE**: Response should be "text/event-stream" with streaming events
- **EXPECTED**: See `event: activity` and `data: {...}` lines in response
- **VALIDATE**: Screenshot of Network tab showing SSE events

---

## TESTING STRATEGY

### Unit Tests

**Scope**: Test individual components in isolation

**Required Tests:**
- `tests/api/test_sse.py` - SSE endpoint tests
- `tests/services/test_scar_feed_service.py` - Feed service tests
- `tests/services/test_scar_executor.py` - Executor tests (already exist, expand if needed)

**Patterns:**
```python
@pytest.mark.asyncio
async def test_function_name(db_session):
    # Arrange: Create test data
    project = Project(...)
    db_session.add(project)
    await db_session.commit()

    # Act: Call function under test
    result = await function_under_test(db_session, project.id)

    # Assert: Verify result
    assert result.success is True
    assert len(result.data) > 0
```

### Integration Tests

**Scope**: Test complete workflows end-to-end

**Required Tests:**
- SSE connection → activity streaming → frontend reception
- SCAR execution → database write → SSE query → SSE stream

**Pattern**: Use FastAPI TestClient with async support

### Manual Tests

**Scope**: Human verification of UI and real-time behavior

**Required:**
1. Visual verification of SSE feed populating
2. Network tab inspection showing SSE events
3. Console log inspection for errors
4. Test with multiple projects simultaneously
5. Test reconnection after network interruption

---

## VALIDATION COMMANDS

Execute every command to ensure zero regressions and 100% feature correctness.

### Level 1: Diagnostic Scripts

**Run database inspection:**
```bash
python scripts/inspect_database.py
# Expected: List of projects with SCAR execution counts
# If counts are 0, database write is broken
```

**Run end-to-end diagnostic:**
```bash
python scripts/debug_sse_feed.py <project-id>
# Expected: ✓ markers for each component
# ✗ markers indicate exact failure point
```

### Level 2: Unit Tests

**Run SSE endpoint tests:**
```bash
pytest tests/api/test_sse.py -v
# Expected: All tests pass
```

**Run feed service tests:**
```bash
pytest tests/services/test_scar_feed_service.py -v
# Expected: All tests pass
```

**Run SCAR executor tests:**
```bash
pytest tests/services/test_scar_executor.py -v
# Expected: All tests pass (including new commit verification tests)
```

### Level 3: Integration Tests

**Run full test suite:**
```bash
pytest tests/ -v --cov=src --cov-report=term-missing
# Expected: All tests pass, coverage > 80%
```

### Level 4: Manual Validation - Backend

**Start backend with logging:**
```bash
LOG_LEVEL=DEBUG uvicorn src.main:app --reload --log-config logging_config.yaml
# Expected: Server starts on http://localhost:8000
```

**Test SSE endpoint with curl:**
```bash
curl -N http://localhost:8000/api/sse/scar/<project-id>?verbosity=2
# Expected: Stream of SSE events (event: activity, data: {...})
# Use Ctrl+C to stop after seeing events
```

### Level 5: Manual Validation - Frontend

**Start frontend:**
```bash
cd frontend
npm run dev
# Expected: Dev server on http://localhost:3002
```

**Test in browser:**
1. Open http://localhost:3002
2. Open DevTools → Console
3. Open DevTools → Network tab (filter for "sse")
4. Select a project
5. Send message: "Analyze the codebase"
6. **Verify**:
   - Console shows `[SSE] Connection opened`
   - Console shows `[SSE] Activity event received`
   - Network tab shows SSE request with streaming events
   - Right pane shows activity feed populating

### Level 6: Stress Testing

**Test with rapid SCAR commands:**
```python
# Create test script: scripts/stress_test_sse.py
import asyncio
from src.services.scar_executor import execute_scar_command, ScarCommand
from src.database.connection import async_session_maker

async def stress_test(project_id):
    for i in range(5):
        async with async_session_maker() as session:
            await execute_scar_command(session, project_id, ScarCommand.PRIME)
        print(f"Command {i+1} completed")

# Run: python scripts/stress_test_sse.py
# Expected: All commands create visible SSE events
```

---

## ACCEPTANCE CRITERIA

- [ ] **Database writes verified**: `scripts/inspect_database.py` shows ScarCommandExecution records for all SCAR commands
- [ ] **SSE endpoint verified**: `curl` to SSE endpoint streams activity events in correct format
- [ ] **Frontend verified**: Browser shows real-time activity in SSE feed pane
- [ ] **Diagnostic script passes**: `scripts/debug_sse_feed.py` shows all ✓ markers
- [ ] **Unit tests pass**: All new tests in `tests/api/test_sse.py` and `tests/services/test_scar_feed_service.py` pass
- [ ] **Integration tests pass**: Full test suite passes with > 80% coverage
- [ ] **Manual test passes**: User can see SCAR activity in real-time when sending messages
- [ ] **Network inspection passes**: Browser DevTools shows SSE events streaming
- [ ] **No regressions**: Existing tests still pass, no broken functionality
- [ ] **Logging complete**: All components log key events for future debugging
- [ ] **RCA documented**: Findings written to `.agents/rca-reports/sse-feed-rca-final.md`
- [ ] **Fix applied**: Root cause addressed with targeted code changes

---

## COMPLETION CHECKLIST

- [ ] All diagnostic scripts created and run successfully
- [ ] RCA report created documenting exact failure point
- [ ] Root cause fix implemented (database commit / SSE polling / frontend)
- [ ] Comprehensive logging added to all components
- [ ] Unit tests created and passing (SSE endpoint, feed service)
- [ ] Integration tests passing
- [ ] Manual testing confirms SSE feed works end-to-end
- [ ] Browser DevTools shows SSE connection and events
- [ ] No console errors or warnings
- [ ] Stress testing confirms reliability under load
- [ ] Code reviewed for quality and maintainability
- [ ] Documentation updated (if needed)

---

## NOTES

### Key Insights from Previous Attempts

1. **PR #46 fixed timestamp comparison** - Changed from UUID comparison (non-chronological) to `started_at > last_dt` comparison. This is correct.

2. **PR #48 fixed event listeners** - Changed frontend to listen for named 'activity' events instead of generic message events. This is correct.

3. **Issue persists despite fixes** - This indicates the problem is NOT in SSE polling logic or frontend event listeners. The issue is likely earlier in the chain:
   - Database records not being created
   - Database records not being committed/flushed
   - Database session isolation issues

### Root Cause Hypothesis

Based on code review and issue symptoms, the most likely root cause is:

**Database Transaction Isolation**: ScarCommandExecution records are created but not immediately visible to the SSE polling query due to:
- Missing `session.flush()` after commit
- Different session instances (SSE service vs executor)
- Transaction isolation level preventing read of uncommitted data

**Diagnostic Approach**: The diagnostic scripts will confirm or refute this hypothesis by directly querying the database and testing the SSE stream.

### Design Decisions

**Decision**: Use diagnostic-first approach before implementing fixes
**Rationale**: Previous fixes didn't work because root cause wasn't identified. Diagnostic scripts will provide concrete evidence of failure point.

**Decision**: Add comprehensive logging to all components
**Rationale**: Future debugging will be easier with detailed logs showing data flow.

**Decision**: Create unit tests for SSE components
**Rationale**: Prevent future regressions and enable test-driven fixes.

### Performance Considerations

- SSE polling every 2 seconds is acceptable for low-volume usage
- For production scale, consider Redis pub/sub for real-time event streaming
- Current implementation is MVP-appropriate

### Security Considerations

- Project ID in URL is UUID (not predictable)
- Authentication should be added in production (not in scope for this fix)
- CORS configuration must allow SSE connections from frontend origin
