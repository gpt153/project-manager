# Feature: Fix SSE Feed Completely - Root Cause Resolution

The following plan should be complete, but it's important that you validate documentation and codebase patterns and task sanity before you start implementing.

Pay special attention to naming of existing utils types and models. Import from the right files etc.

## Feature Description

Fix the broken Server-Sent Events (SSE) feed in the WebUI where users cannot see real-time SCAR activity despite PM successfully executing SCAR commands. The root cause is a broken event flow from SCAR execution → database → SSE endpoint → frontend. This plan implements a comprehensive fix with proper logging, session management, error handling, and reconnection logic.

## User Story

As a user of the Project Manager WebUI
I want to see real-time SCAR command execution activity in the right panel SSE feed
So that I have full transparency into what SCAR/Claude are doing when analyzing my codebase

## Problem Statement

**Current Symptoms:**
- User sends message: "analyze the codebase"
- PM responds with analysis results
- SSE feed (right pane) remains empty - NO activity shown
- Backend logs show: "Executing SCAR command: prime" → "SCAR command completed successfully"

**Root Cause Analysis:**

After reviewing the codebase and previous fix attempts (PR #46, #48), the issue stems from multiple problems:

1. **Database Session Isolation**: The `stream_scar_activity()` function uses a long-lived session but doesn't properly refresh to see new records committed by other sessions
2. **Polling Logic Gap**: The 2-second polling interval may miss records or fail to detect them due to timestamp precision issues
3. **Initial Load Issue**: When SSE connects, initial activities are sent, but subsequent polling query doesn't properly continue from the last timestamp
4. **No Error Recovery**: Frontend has no reconnection logic when SSE connection drops
5. **Insufficient Logging**: Cannot diagnose where in the pipeline events are lost

**Evidence:**
- Backend logs show successful SCAR execution and command completion
- `ScarCommandExecution` records ARE being created (via `scar_executor.py`)
- SSE endpoint is registered and accessible
- Frontend SSE connection establishes (PR #48 fixed event listeners)
- **Gap**: Records exist but SSE polling doesn't detect/stream them

## Solution Statement

Implement a complete fix addressing all layers of the SSE feed system:

1. **Fix SSE Polling Logic**: Ensure database session properly refreshes and queries detect new records
2. **Add Comprehensive Logging**: Track execution_id through entire flow for debugging
3. **Improve Error Handling**: Add proper error events and client-side reconnection
4. **Create Diagnostic Tools**: Build scripts to validate each stage of the pipeline
5. **Add Integration Tests**: Prevent future regressions with end-to-end tests

## Feature Metadata

**Feature Type**: Bug Fix / System Integration
**Estimated Complexity**: Medium-High
**Primary Systems Affected**:
- SSE feed service (`src/services/scar_feed_service.py`)
- SSE endpoint (`src/api/sse.py`)
- Frontend SSE hook (`frontend/src/hooks/useScarFeed.ts`)
- Frontend feed component (`frontend/src/components/RightPanel/ScarActivityFeed.tsx`)

**Dependencies**:
- `sse-starlette==2.1.0` - SSE streaming
- `sqlalchemy[asyncio]>=2.0.36` - Async database
- `pydantic-ai>=0.0.14` - Agent framework
- `fastapi>=0.115.0` - Web framework

---

## CONTEXT REFERENCES

### Relevant Codebase Files IMPORTANT: YOU MUST READ THESE FILES BEFORE IMPLEMENTING!

**Backend - SSE Streaming:**
- `src/services/scar_feed_service.py` (lines 71-149) - Why: Core polling logic with session management issues
- `src/api/sse.py` (lines 22-104) - Why: SSE endpoint, session lifecycle management
- `src/services/scar_executor.py` (lines 49-233) - Why: Creates ScarCommandExecution records

**Backend - Database:**
- `src/database/models.py` (lines 248-301) - Why: ScarCommandExecution model with @property methods
- `src/database/connection.py` (lines 32-62) - Why: Session factory configuration

**Backend - Agent:**
- `src/agent/orchestrator_agent.py` (lines 269-316) - Why: execute_scar tool that creates records

**Frontend:**
- `frontend/src/hooks/useScarFeed.ts` - Why: SSE client connection and event handling
- `frontend/src/components/RightPanel/ScarActivityFeed.tsx` - Why: UI component displaying feed

**Testing Patterns:**
- `tests/conftest.py` - Why: Test database session fixtures
- `tests/services/test_scar_executor.py` - Why: Example of testing SCAR execution

### New Files to Create

- `scripts/diagnose_sse_flow.py` - Diagnostic script to validate SSE pipeline
- `tests/integration/test_sse_feed_integration.py` - End-to-end SSE feed test

### Relevant Documentation YOU SHOULD READ THESE BEFORE IMPLEMENTING!

- [SSE-Starlette Documentation](https://github.com/sysid/sse-starlette#readme)
  - Section: EventSourceResponse and async generators
  - Why: Understand proper session management in long-lived SSE streams

- [SQLAlchemy Async Sessions](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#asyncio-orm-session)
  - Section: Session isolation and expire_on_commit behavior
  - Why: Critical for understanding why records aren't visible across sessions

- [EventSource API (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/EventSource)
  - Section: Error handling and reconnection
  - Why: Implement proper client-side error recovery

### Patterns to Follow

**Async Session Context Manager** (from `conftest.py`):
```python
async with async_session_maker() as session:
    # Use session
    await session.commit()
    await session.refresh(obj)  # Critical: refresh to see committed changes
```

**SSE Event Format** (from `sse.py`):
```python
yield {
    "event": "activity",  # Named event (PR #48 fix)
    "data": json.dumps(activity_dict)
}
```

**Frontend Event Listener** (from `useScarFeed.ts`):
```typescript
eventSource.addEventListener('activity', (event) => {
  const activity: ScarActivity = JSON.parse(event.data);
  setActivities((prev) => [...prev, activity]);
});
```

**Error Handling Pattern** (to add):
```python
# Backend
yield {
    "event": "error",
    "data": json.dumps({"code": "ERROR_CODE", "message": "..."})
}

# Frontend
eventSource.addEventListener('error', (event) => {
  // Trigger reconnection logic
});
```

---

## IMPLEMENTATION PLAN

### Phase 1: Backend - Fix SSE Polling and Session Management

Fix the core issue: SSE polling doesn't detect new ScarCommandExecution records.

**Tasks:**
- Fix session refresh logic in `stream_scar_activity()` to see new records
- Improve polling query to handle edge cases (empty initial state, timestamp precision)
- Add comprehensive logging with execution_id tracking
- Add error events for backend failures

### Phase 2: Backend - Enhance SSE Endpoint Error Handling

Improve SSE endpoint robustness and error reporting.

**Tasks:**
- Add try-except blocks for all potential failure points
- Send structured error events to frontend
- Improve heartbeat mechanism
- Add logging for connection lifecycle

### Phase 3: Frontend - Add Reconnection Logic

Make frontend resilient to connection failures.

**Tasks:**
- Implement automatic reconnection with exponential backoff
- Add connection status indicators
- Handle error events from backend
- Add retry limit to prevent infinite loops

### Phase 4: Frontend - Improve UX

Enhance user experience with better feedback.

**Tasks:**
- Show connection status (connecting, connected, disconnected, error)
- Display error messages when feed fails
- Add manual refresh button
- Improve empty state messaging

### Phase 5: Diagnostic Tools

Create tools to validate the fix.

**Tasks:**
- Create `scripts/diagnose_sse_flow.py` to check each pipeline stage
- Add database query validation
- Add SSE endpoint testing
- Create manual test checklist

### Phase 6: Testing & Validation

Ensure fix works and prevent regressions.

**Tasks:**
- Create end-to-end integration test
- Test SSE connection lifecycle
- Test polling with multiple concurrent executions
- Validate frontend reconnection logic

---

## STEP-BY-STEP TASKS

IMPORTANT: Execute every task in order, top to bottom. Each task is atomic and independently testable.

### UPDATE `src/services/scar_feed_service.py`

**Problem**: Polling query doesn't detect new records due to session isolation and query logic issues.

**IMPLEMENT**:
- **Fix Initial Query**: Ensure initial activities are properly loaded and last_timestamp is set correctly
- **Fix Polling Query**: Add session refresh before each query to see newly committed records
- **Add Logging**: Log every query with count of records found and execution_ids
- **Handle Edge Cases**: Deal with null timestamps, empty results, concurrent writes

**PATTERN**: Session refresh from `conftest.py` (line 77-78):
```python
async with session:
    result = await session.execute(query)
    # Session automatically sees committed changes from other sessions
```

**IMPORTS**: No new imports needed

**GOTCHA**: `expire_on_commit=False` in session factory means objects don't auto-refresh - must explicitly query

**VALIDATE**:
```bash
# After changes, check logs show:
# "SSE query found X new activities: [execution_ids...]"
python3 scripts/diagnose_sse_flow.py --project-id <uuid>
```

**Specific Changes**:
1. Lines 89-101 (Initial query): Add logging for initial activity count and IDs
2. Lines 104-148 (Polling loop):
   - Add `await session.refresh()` before query execution (if supported) OR create new session each poll
   - Add detailed logging: query parameters, result count, execution IDs found
   - Handle case where `last_timestamp` is None more explicitly
3. Add error handling around query execution with logging

---

### UPDATE `src/api/sse.py`

**Problem**: SSE endpoint doesn't properly handle errors or provide detailed error events to frontend.

**IMPLEMENT**:
- **Better Session Management**: Create fresh session for each poll cycle within the stream
- **Structured Error Events**: Send detailed error information to frontend
- **Connection Lifecycle Logging**: Log SSE connection establishment, data sent, errors, closure
- **Improve Heartbeat**: Ensure heartbeat doesn't interfere with activity events

**PATTERN**: Error event pattern (already exists in lines 86-91):
```python
yield {
    "event": "error",
    "data": json.dumps({"code": "ERROR_CODE", "message": "..."})
}
```

**IMPORTS**: No new imports needed

**GOTCHA**: EventSourceResponse consumes async generator - errors must be yielded, not raised

**VALIDATE**:
```bash
# Check SSE endpoint responds with events:
curl -N http://localhost:8000/api/sse/scar/<project-id>
# Should stream: event: activity, data: {...}
```

**Specific Changes**:
1. Lines 52-103 (event_generator):
   - Add logging when SSE connection opens: log project_id and verbosity
   - Add logging for each activity event sent: log activity id and source
   - Improve error logging: log full traceback for debugging
   - Add final log when connection closes with reason (cancelled vs error vs normal)
2. Consider session per-poll approach: Create new session in loop instead of one long-lived session

---

### UPDATE `frontend/src/hooks/useScarFeed.ts`

**Problem**: No reconnection logic when SSE connection drops or errors occur.

**IMPLEMENT**:
- **Automatic Reconnection**: Reconnect on error with exponential backoff
- **Connection State Tracking**: Track connecting/connected/disconnected/error states
- **Retry Limit**: Stop after N failed reconnection attempts
- **Error Event Handling**: Handle backend error events

**PATTERN**: React hooks with cleanup (already present):
```typescript
useEffect(() => {
  const eventSource = new EventSource(url);
  // Setup listeners
  return () => eventSource.close(); // Cleanup
}, [projectId, verbosity]);
```

**IMPORTS**: May need to add reconnection timer logic

**GOTCHA**: EventSource has built-in reconnection, but only for network errors, not explicit error events

**VALIDATE**:
```bash
# Test reconnection by restarting backend while frontend is open
# Frontend should show "Reconnecting..." then "Connected" when backend restarts
```

**Specific Changes**:
1. Add connection state tracking: `const [connectionState, setConnectionState] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('connecting')`
2. Add reconnection logic:
   - Track retry count and last retry timestamp
   - Implement exponential backoff (1s, 2s, 4s, 8s, max 30s)
   - Stop after 10 failed attempts
3. Handle error events from backend:
   ```typescript
   eventSource.addEventListener('error', (event) => {
     const errorData = JSON.parse(event.data);
     console.error('SSE error:', errorData);
     setConnectionState('error');
     // Trigger reconnection logic
   });
   ```
4. Return connection state from hook: `return { activities, isConnected, connectionState }`

---

### UPDATE `frontend/src/components/RightPanel/ScarActivityFeed.tsx`

**Problem**: No visual feedback when connection fails or is reconnecting.

**IMPLEMENT**:
- **Connection Status Display**: Show connection state with appropriate styling
- **Error Messages**: Display error messages from backend
- **Manual Refresh Button**: Allow user to manually reconnect
- **Improved Empty State**: Better messaging based on connection state

**PATTERN**: Conditional rendering based on state (already present):
```typescript
{activities.length === 0 ? (
  <div className="empty-state">...</div>
) : (
  activities.map(...)
)}
```

**IMPORTS**: No new imports needed

**GOTCHA**: Must handle all connection states gracefully

**VALIDATE**:
```bash
# Manual testing:
# 1. Load WebUI - should show "Connecting..."
# 2. Once connected - should show "● Live"
# 3. Stop backend - should show "Reconnecting..."
# 4. Start backend - should show "● Live" again
```

**Specific Changes**:
1. Update hook usage to get connection state: `const { activities, isConnected, connectionState } = useScarFeed(...)`
2. Lines 36-38 (Status indicator): Enhance to show all states:
   ```typescript
   <span className={`status ${connectionState}`}>
     {connectionState === 'connecting' && '○ Connecting...'}
     {connectionState === 'connected' && '● Live'}
     {connectionState === 'disconnected' && '○ Disconnected'}
     {connectionState === 'error' && '⚠ Error - Retrying...'}
   </span>
   ```
3. Lines 41-43 (Empty state): Improve message based on connection state:
   ```typescript
   {activities.length === 0 ? (
     <div className="empty-state">
       {connectionState === 'connected'
         ? 'No SCAR activity yet. Activity will appear here when commands are executed.'
         : connectionState === 'connecting'
         ? 'Connecting to activity feed...'
         : 'Connection lost. Reconnecting...'}
     </div>
   ) : ...}
   ```
4. Add manual refresh button in header (optional but helpful):
   ```typescript
   <button onClick={() => window.location.reload()}>Refresh</button>
   ```

---

### CREATE `scripts/diagnose_sse_flow.py`

**Purpose**: Diagnostic tool to validate each stage of the SSE pipeline.

**IMPLEMENT**: Create comprehensive diagnostic script that:
- Checks database for ScarCommandExecution records
- Queries records for a specific project
- Validates SSE endpoint responds
- Simulates SSE polling logic
- Reports on each stage: PASS/FAIL

**PATTERN**: Async database query pattern from `scar_feed_service.py`:
```python
from src.database.connection import async_session_maker
async with async_session_maker() as session:
    result = await session.execute(query)
    records = result.scalars().all()
```

**IMPORTS**:
```python
import asyncio
import sys
from uuid import UUID
from sqlalchemy import select, desc
from src.database.connection import async_session_maker
from src.database.models import ScarCommandExecution
from src.services.scar_feed_service import get_recent_scar_activity
```

**GOTCHA**: Must handle case where database is not initialized or project doesn't exist

**VALIDATE**:
```bash
python3 scripts/diagnose_sse_flow.py --project-id <uuid>
# Expected output:
# ✓ Database connection: OK
# ✓ Found X ScarCommandExecution records for project
# ✓ SSE feed service returns X activities
# ✓ SSE endpoint responds: OK
```

**Script Structure**:
```python
#!/usr/bin/env python3
"""Diagnostic script for SSE feed pipeline."""

async def check_database_records(project_id: UUID):
    """Check if ScarCommandExecution records exist."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(ScarCommandExecution)
            .where(ScarCommandExecution.project_id == project_id)
            .order_by(desc(ScarCommandExecution.started_at))
        )
        records = result.scalars().all()
        print(f"✓ Found {len(records)} ScarCommandExecution records")
        for record in records[:5]:  # Show latest 5
            print(f"  - {record.id}: {record.command_type.value} ({record.status.value})")
        return len(records) > 0

async def check_feed_service(project_id: UUID):
    """Check if feed service returns activities."""
    async with async_session_maker() as session:
        activities = await get_recent_scar_activity(session, project_id, limit=10)
        print(f"✓ Feed service returned {len(activities)} activities")
        for activity in activities[:3]:  # Show first 3
            print(f"  - {activity['source']}: {activity['message']}")
        return len(activities) > 0

async def check_sse_endpoint(project_id: UUID):
    """Check if SSE endpoint responds (basic check)."""
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            # Just check endpoint exists (won't consume stream)
            response = await client.get(
                f"http://localhost:8000/api/sse/scar/{project_id}",
                timeout=2.0
            )
            print(f"✓ SSE endpoint responds: {response.status_code}")
            return True
    except Exception as e:
        print(f"✗ SSE endpoint error: {e}")
        return False

async def main():
    if len(sys.argv) < 2:
        print("Usage: python3 diagnose_sse_flow.py --project-id <uuid>")
        sys.exit(1)

    project_id = UUID(sys.argv[2])
    print(f"Diagnosing SSE feed for project: {project_id}\n")

    # Run checks
    db_ok = await check_database_records(project_id)
    feed_ok = await check_feed_service(project_id)
    sse_ok = await check_sse_endpoint(project_id)

    print(f"\nSummary:")
    print(f"  Database records: {'✓' if db_ok else '✗'}")
    print(f"  Feed service: {'✓' if feed_ok else '✗'}")
    print(f"  SSE endpoint: {'✓' if sse_ok else '✗'}")

    if db_ok and feed_ok and sse_ok:
        print("\n✓ All checks passed - SSE feed should work!")
    else:
        print("\n✗ Some checks failed - see details above")

if __name__ == "__main__":
    asyncio.run(main())
```

---

### CREATE `tests/integration/test_sse_feed_integration.py`

**Purpose**: End-to-end integration test for SSE feed to prevent regressions.

**IMPLEMENT**: Create integration test that:
- Creates a project with ScarCommandExecution records
- Starts SSE stream
- Validates stream receives activity events
- Tests polling detects new records
- Validates frontend-compatible event format

**PATTERN**: Integration test pattern from `test_scar_executor.py`:
```python
@pytest.mark.asyncio
async def test_name(db_session):
    # Setup
    project = Project(...)
    db_session.add(project)
    await db_session.commit()

    # Execute
    result = await function(db_session, ...)

    # Assert
    assert result.success is True
```

**IMPORTS**:
```python
import pytest
import asyncio
from datetime import datetime
from uuid import uuid4
from src.database.models import Project, ScarCommandExecution, CommandType, ExecutionStatus, ProjectStatus
from src.services.scar_feed_service import stream_scar_activity, get_recent_scar_activity
```

**GOTCHA**: SSE stream is async generator - must consume it properly in tests

**VALIDATE**:
```bash
pytest tests/integration/test_sse_feed_integration.py -v
# All tests should pass
```

**Test Structure**:
```python
"""Integration tests for SSE feed functionality."""

import pytest
from datetime import datetime
from src.database.models import (
    Project, ScarCommandExecution,
    CommandType, ExecutionStatus, ProjectStatus
)
from src.services.scar_feed_service import (
    get_recent_scar_activity,
    stream_scar_activity
)


@pytest.mark.asyncio
async def test_get_recent_activity_returns_executions(db_session):
    """Test that get_recent_scar_activity returns ScarCommandExecution records."""
    # Create test project
    project = Project(
        name="Test Project",
        status=ProjectStatus.IN_PROGRESS,
        github_repo_url="https://github.com/test/repo"
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Create test execution records
    execution1 = ScarCommandExecution(
        project_id=project.id,
        command_type=CommandType.PRIME,
        command_args="",
        status=ExecutionStatus.COMPLETED,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow()
    )
    execution2 = ScarCommandExecution(
        project_id=project.id,
        command_type=CommandType.PLAN_FEATURE_GITHUB,
        command_args="test feature",
        status=ExecutionStatus.RUNNING,
        started_at=datetime.utcnow()
    )
    db_session.add(execution1)
    db_session.add(execution2)
    await db_session.commit()

    # Query activities
    activities = await get_recent_scar_activity(db_session, project.id, limit=10)

    # Validate
    assert len(activities) == 2
    assert activities[0]['source'] == 'scar'
    assert 'message' in activities[0]
    assert 'timestamp' in activities[0]
    assert 'id' in activities[0]


@pytest.mark.asyncio
async def test_stream_detects_new_activities(db_session):
    """Test that stream_scar_activity detects newly added records."""
    # Create test project
    project = Project(
        name="Test Project",
        status=ProjectStatus.IN_PROGRESS,
        github_repo_url="https://github.com/test/repo"
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Start stream (consume initial events)
    stream = stream_scar_activity(db_session, project.id)

    # Get initial activities (should be empty)
    try:
        # Consume with timeout since stream is infinite
        initial = await asyncio.wait_for(
            stream.__anext__(),
            timeout=0.5
        )
    except asyncio.TimeoutError:
        # No initial activities - expected
        pass

    # Add new execution in separate session to simulate real scenario
    from src.database.connection import async_session_maker
    async with async_session_maker() as new_session:
        new_execution = ScarCommandExecution(
            project_id=project.id,
            command_type=CommandType.PRIME,
            command_args="",
            status=ExecutionStatus.COMPLETED,
            started_at=datetime.utcnow()
        )
        new_session.add(new_execution)
        await new_session.commit()

    # Stream should detect new activity within polling interval (2 seconds)
    try:
        new_activity = await asyncio.wait_for(
            stream.__anext__(),
            timeout=5.0  # Give it 5 seconds (2s poll interval + buffer)
        )

        # Validate new activity
        assert new_activity['source'] == 'scar'
        assert 'PRIME' in new_activity['message']
    except asyncio.TimeoutError:
        pytest.fail("Stream did not detect new activity within 5 seconds")


@pytest.mark.asyncio
async def test_activity_format_matches_frontend_expectations(db_session):
    """Test that activity dictionaries match frontend ScarActivity interface."""
    # Create test project and execution
    project = Project(
        name="Test Project",
        status=ProjectStatus.IN_PROGRESS,
        github_repo_url="https://github.com/test/repo"
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    execution = ScarCommandExecution(
        project_id=project.id,
        command_type=CommandType.PRIME,
        command_args="",
        status=ExecutionStatus.COMPLETED,
        started_at=datetime.utcnow()
    )
    db_session.add(execution)
    await db_session.commit()

    # Get activities
    activities = await get_recent_scar_activity(db_session, project.id)

    # Validate frontend interface
    # interface ScarActivity { id, timestamp, source, message, phase? }
    assert len(activities) > 0
    activity = activities[0]

    assert 'id' in activity and isinstance(activity['id'], str)
    assert 'timestamp' in activity and isinstance(activity['timestamp'], str)
    assert 'source' in activity and activity['source'] in ['pm', 'scar', 'claude']
    assert 'message' in activity and isinstance(activity['message'], str)
    # phase is optional
    if 'phase' in activity:
        assert activity['phase'] is None or isinstance(activity['phase'], str)
```

---

## TESTING STRATEGY

### Unit Tests

**Scope**: Test individual functions in isolation
**Focus**: `get_recent_scar_activity()`, `stream_scar_activity()` polling logic

Already covered by existing test patterns in `tests/services/test_scar_executor.py`.

### Integration Tests

**Scope**: Test complete SSE feed pipeline from database to stream
**Requirements**:
- Test database session sees records from other sessions
- Test stream detects newly added records within polling interval
- Test activity format matches frontend expectations

Implemented in `tests/integration/test_sse_feed_integration.py` above.

### Manual Testing

**Scope**: End-to-end user workflow validation

**Test Cases**:
1. **Happy Path**:
   - Open WebUI, select project
   - Send message: "analyze the codebase"
   - Verify SSE feed shows: "scar: prime: COMPLETED"
   - Verify PM responds with analysis

2. **Reconnection**:
   - Open WebUI with SSE feed active
   - Restart backend server
   - Verify frontend shows "Reconnecting..." then "● Live"
   - Send message, verify feed still works

3. **Empty State**:
   - Open WebUI for new project with no SCAR activity
   - Verify shows: "No SCAR activity yet..."
   - Execute SCAR command
   - Verify activity appears in real-time

4. **Multiple Activities**:
   - Execute prime command
   - Execute plan-feature-github command
   - Verify both appear in feed with correct timestamps and sources

---

## VALIDATION COMMANDS

Execute every command to ensure zero regressions and 100% feature correctness.

### Level 1: Import Validation (CRITICAL)

**Verify all imports resolve before running tests:**

```bash
python3 -c "from src.services.scar_feed_service import stream_scar_activity; print('✓ All imports valid')"
```

**Expected:** "✓ All imports valid" (no ModuleNotFoundError or ImportError)

**Why:** Catches incorrect imports immediately.

### Level 2: Syntax & Style

**Run linting to catch syntax errors:**

```bash
ruff check src/services/scar_feed_service.py src/api/sse.py
ruff format src/services/scar_feed_service.py src/api/sse.py
```

**Expected:** No errors or warnings

### Level 3: Unit Tests

**Run existing unit tests to ensure no regressions:**

```bash
pytest tests/services/test_scar_executor.py -v
```

**Expected:** All tests pass

### Level 4: Integration Tests

**Run new integration tests:**

```bash
pytest tests/integration/test_sse_feed_integration.py -v
```

**Expected:** All tests pass, including:
- `test_get_recent_activity_returns_executions` - PASS
- `test_stream_detects_new_activities` - PASS
- `test_activity_format_matches_frontend_expectations` - PASS

### Level 5: Diagnostic Script

**Run diagnostic script on a test project:**

```bash
# First, get a project ID from database
python3 -c "
import asyncio
from src.database.connection import async_session_maker
from src.database.models import Project
from sqlalchemy import select

async def get_project_id():
    async with async_session_maker() as session:
        result = await session.execute(select(Project).limit(1))
        project = result.scalar_one_or_none()
        if project:
            print(project.id)
        else:
            print('No projects found')

asyncio.run(get_project_id())
"

# Then run diagnostic
python3 scripts/diagnose_sse_flow.py --project-id <uuid-from-above>
```

**Expected:**
```
✓ Found X ScarCommandExecution records
✓ Feed service returned X activities
✓ SSE endpoint responds: 200
✓ All checks passed - SSE feed should work!
```

### Level 6: Manual End-to-End Testing

**Start backend and frontend, test user workflow:**

```bash
# Terminal 1: Start backend
python3 -m src.main

# Terminal 2: Start frontend (if separate)
cd frontend && npm run dev

# Browser:
# 1. Open http://localhost:5173
# 2. Select a project
# 3. Send message: "analyze the codebase"
# 4. Verify SSE feed shows activity in real-time
# 5. Verify connection status shows "● Live"
```

**Expected:**
- SSE feed shows "scar: prime: RUNNING" immediately
- SSE feed updates to "scar: prime: COMPLETED" when done
- Connection status shows "● Live" throughout
- PM responds with analysis after SCAR completes

---

## ACCEPTANCE CRITERIA

- [ ] SSE feed displays SCAR activity in real-time when commands execute
- [ ] All validation commands pass with zero errors
- [ ] Integration tests pass (stream detects new records within 5 seconds)
- [ ] Frontend shows connection status (connecting/connected/reconnecting/error)
- [ ] Frontend automatically reconnects when backend restarts
- [ ] Diagnostic script confirms all pipeline stages working
- [ ] Manual testing confirms user can see SCAR activity for: prime, plan-feature-github, execute-github, validate
- [ ] No regressions in existing SCAR execution or agent functionality
- [ ] Code follows project conventions (async/await, error handling, logging)

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order (backend → frontend → diagnostic → tests)
- [ ] Each task validation passed immediately after implementation
- [ ] All validation commands executed successfully
- [ ] Full test suite passes (unit + integration)
- [ ] No linting or import errors
- [ ] Diagnostic script reports all checks passed
- [ ] Manual testing confirms end-to-end functionality
- [ ] Acceptance criteria all met
- [ ] Code reviewed for quality and maintainability
- [ ] Documentation updated (if applicable)

---

## NOTES

### Design Decisions

1. **Session Management**: Use fresh session for each poll cycle instead of one long-lived session to ensure visibility of committed records

2. **Polling Interval**: Keep 2-second interval - good balance between responsiveness and database load

3. **Reconnection Strategy**: Exponential backoff with max 10 retries prevents infinite reconnection loops while allowing recovery from temporary failures

4. **Error Handling**: Send structured error events to frontend instead of silently failing - better user experience and debugging

### Trade-offs

1. **Polling vs Pub/Sub**: Using polling (simpler, no external dependencies) instead of Redis pub/sub (more scalable). For MVP with <100 concurrent users, polling is sufficient.

2. **Frontend Reconnection**: Using custom reconnection logic instead of relying on EventSource's built-in reconnection because we need exponential backoff and retry limits.

### Future Improvements (Out of Scope)

1. Replace polling with Redis pub/sub for better scalability
2. Add WebSocket fallback for environments where SSE is blocked
3. Add activity filtering (by source, command type, time range)
4. Add activity search functionality
5. Add export/download activity log feature

### Known Limitations

1. SSE connections may be terminated by reverse proxies after long idle periods - heartbeat helps but not guaranteed
2. Browser limits concurrent SSE connections per domain (usually 6) - not an issue for single-project view
3. Historical activities loaded on initial connection are limited to most recent 50 (configurable in `limit` parameter)

### Success Metrics

**This fix is successful if:**
- User sends "analyze the codebase" and sees "scar: prime: RUNNING" within 1 second in SSE feed
- SSE feed updates to "scar: prime: COMPLETED" when execution finishes
- Connection survives for hours without breaking (tested via manual observation)
- Integration test `test_stream_detects_new_activities` passes consistently (no flakiness)
