# Feature: Fix SSE Feed - Complete Root Cause Diagnosis and Resolution

The following plan should be complete, but it's important that you validate documentation and codebase patterns and task sanity before you start implementing.

Pay special attention to naming of existing utils types and models. Import from the right files etc.

## Feature Description

Fix the persistent Server-Sent Events (SSE) feed issue where SCAR command execution activity fails to display in the WebUI right pane, despite backend logs confirming successful SCAR operations. This is a **root cause analysis and fix** effort after two previous partial fixes (PR #46, #48) failed to resolve the issue completely.

## User Story

As a user of the Project Manager WebUI
I want to see real-time SCAR command execution activity in the SSE feed (right pane)
So that I have transparency into what SCAR is doing when PM delegates work to it

## Problem Statement

**Current Symptoms (Issue #45):**
1. User sends message: "analyze the codebase"
2. PM responds with analysis results
3. SSE feed (right pane) remains completely empty - NO activity shown
4. Backend logs show: "Executing SCAR command: prime" → "SCAR command completed successfully"
5. **Unknown:** Are ScarCommandExecution records being created? Is SSE polling finding them?

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
- **Both merged but issue persists** - indicates deeper problem

**Root Cause Hypothesis:**

The issue persists despite fixes to SSE polling logic and frontend event listening. This suggests one of:

1. **Database Transaction Visibility**: ScarCommandExecution records created but not visible to SSE polling due to session isolation
2. **SSE Timing Race**: SSE connects before first record is created, initial query returns empty, polling never triggers
3. **Agent Tool Invocation**: execute_scar tool not being called consistently by PM agent
4. **Session Configuration**: expire_on_commit or other session settings preventing cross-session data visibility

## Solution Statement

Perform systematic diagnostic testing to identify the EXACT breaking point in the data flow chain:

**User Message** → **PM Agent** → **execute_scar tool** → **Database Write** → **SSE Query** → **SSE Stream** → **Frontend Display**

Then implement targeted fix with comprehensive logging and validation.

## Feature Metadata

**Feature Type**: Bug Fix / Root Cause Analysis
**Estimated Complexity**: High
**Primary Systems Affected**:
- SCAR executor service (`src/services/scar_executor.py`)
- SSE feed service (`src/services/scar_feed_service.py`)
- SSE endpoint (`src/api/sse.py`)
- Database session management (`src/database/connection.py`)
- PM agent prompt (`src/agent/prompts.py`)

**Dependencies**:
- `sse-starlette==2.1.0` - SSE streaming library
- `sqlalchemy[asyncio]>=2.0.36` - Async database ORM
- `pydantic-ai>=0.0.14` - Agent framework
- `fastapi>=0.115.0` - Web framework
- `httpx` - HTTP client for SCAR communication

---

## CONTEXT REFERENCES

### Relevant Codebase Files IMPORTANT: YOU MUST READ THESE FILES BEFORE IMPLEMENTING!

**SCAR Execution Layer:**
- `src/services/scar_executor.py` (lines 49-233) - **Why**: Creates ScarCommandExecution records, database commit logic
- `src/agent/orchestrator_agent.py` (lines 269-316) - **Why**: execute_scar tool definition and invocation
- `src/agent/prompts.py` (line 49) - **Why**: System prompt that should trigger execute_scar for "analyze" requests

**Database Layer:**
- `src/database/models.py` (lines 248-301) - **Why**: ScarCommandExecution model, @property methods for SSE feed
- `src/database/connection.py` (lines 32-38) - **Why**: Session factory config (expire_on_commit critical for visibility)

**SSE Streaming Layer:**
- `src/services/scar_feed_service.py` (lines 71-149) - **Why**: SSE polling query (timestamp fix applied in PR #46)
- `src/api/sse.py` (lines 22-104) - **Why**: SSE endpoint, session management, event generator

**Frontend Layer:**
- `frontend/src/hooks/useScarFeed.ts` (lines 23-32) - **Why**: Event listener (activity event fix applied in PR #48)

### New Files to Create

- `scripts/diagnose_sse_feed.py` - Diagnostic script to check database records and SSE queries
- `tests/integration/test_sse_feed_e2e.py` - End-to-end integration test for SSE feed flow

### Relevant Documentation YOU SHOULD READ THESE BEFORE IMPLEMENTING!

- [SSE-Starlette Documentation](https://github.com/sysid/sse-starlette#readme)
  - Why: Understand EventSourceResponse behavior and session management
- [SQLAlchemy Async Sessions](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#asyncio-orm-session)
  - Why: Session isolation and expire_on_commit behavior critical for cross-session data visibility
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
  - Why: Understanding async context and session lifecycle in SSE streams

### Patterns to Follow

**Database Query Pattern** (from `scar_feed_service.py`):
```python
# Timestamp-based polling (PR #46 fix)
if last_timestamp:
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

**SSE Event Streaming Pattern** (from `sse.py`):
```python
# Named events (PR #48 fix)
yield {
    "event": "activity",
    "data": json.dumps(activity)
}
```

**Frontend Event Listening Pattern** (from `useScarFeed.ts`):
```python
# Listen for named events (PR #48 fix)
eventSource.addEventListener('activity', (event) => {
    const activity: ScarActivity = JSON.parse(event.data);
    setActivities((prev) => [...prev, activity]);
});
```

**Test Pattern** (from `test_scar_executor.py`):
```python
# Create project, execute command, verify result
project = Project(
    name="Test Project",
    status=ProjectStatus.PLANNING,
    github_repo_url="https://github.com/test/repo",
)
db_session.add(project)
await db_session.commit()
await db_session.refresh(project)

result = await execute_scar_command(db_session, project.id, ScarCommand.PRIME)
assert result.success is True
```

---

## IMPLEMENTATION PLAN

### Phase 1: Diagnostic Investigation

**Objective**: Identify the EXACT breaking point in the data flow using diagnostic scripts and manual testing.

**Tasks:**

1. Create comprehensive diagnostic script
2. Run manual SSE endpoint tests
3. Check database transaction isolation
4. Verify agent tool invocation

### Phase 2: Root Cause Fix

**Objective**: Implement targeted fix based on diagnostic findings.

**Tasks:**

1. Fix identified issue (session config, timing, query, etc.)
2. Add defensive logging throughout flow
3. Add database query debugging

### Phase 3: Integration Testing

**Objective**: Validate end-to-end flow with automated and manual tests.

**Tasks:**

1. Create E2E integration test
2. Manual testing with WebUI
3. Regression testing

### Phase 4: Validation and Documentation

**Objective**: Confirm fix resolves Issue #45 and document findings.

**Tasks:**

1. Reproduce Issue #45 scenario
2. Validate all validation commands pass
3. Document root cause and resolution

---

## STEP-BY-STEP TASKS

IMPORTANT: Execute every task in order, top to bottom. Each task is atomic and independently testable.

### CREATE scripts/diagnose_sse_feed.py

**IMPLEMENT**: Comprehensive diagnostic script to identify breaking point

```python
"""
SSE Feed Diagnostic Script

Run with: uv run python scripts/diagnose_sse_feed.py <project_id>

This script checks:
1. Database records exist for ScarCommandExecution
2. SSE feed service queries work
3. SSE endpoint streams events correctly
4. Session isolation is configured properly
"""

import asyncio
import sys
from uuid import UUID

from sqlalchemy import select

from src.database.connection import async_session_maker
from src.database.models import Project, ScarCommandExecution
from src.services.scar_feed_service import get_recent_scar_activity, stream_scar_activity


async def diagnose(project_id: UUID):
    """Run diagnostic checks"""
    print(f"🔍 Diagnosing SSE feed for project: {project_id}")
    print("=" * 60)

    async with async_session_maker() as session:
        # Check 1: Project exists
        print("\n✓ Check 1: Project exists")
        result = await session.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()

        if not project:
            print(f"❌ FAIL: Project {project_id} not found")
            return

        print(f"✓ PASS: Found project '{project.name}'")

        # Check 2: ScarCommandExecution records exist
        print("\n✓ Check 2: ScarCommandExecution records exist")
        result = await session.execute(
            select(ScarCommandExecution)
            .where(ScarCommandExecution.project_id == project_id)
            .order_by(ScarCommandExecution.started_at.desc())
        )
        executions = result.scalars().all()

        if not executions:
            print(f"❌ FAIL: No ScarCommandExecution records found for project {project_id}")
            print("   This means execute_scar_command() is NOT creating database records!")
            return

        print(f"✓ PASS: Found {len(executions)} execution records")
        for i, exec in enumerate(executions[:5]):
            print(f"   [{i+1}] {exec.command_type.value} - {exec.status.value} - {exec.started_at}")

        # Check 3: SSE feed service can query activities
        print("\n✓ Check 3: SSE feed service query works")
        activities = await get_recent_scar_activity(session, project_id, limit=10, verbosity_level=2)

        if not activities:
            print(f"❌ FAIL: get_recent_scar_activity() returned empty list")
            print("   Database has records but SSE service query failed!")
            return

        print(f"✓ PASS: get_recent_scar_activity() returned {len(activities)} activities")
        for i, activity in enumerate(activities[:3]):
            print(f"   [{i+1}] {activity['source']} - {activity['message']}")

        # Check 4: SSE streaming works
        print("\n✓ Check 4: SSE streaming generator works")
        stream = stream_scar_activity(session, project_id, verbosity_level=2)

        count = 0
        async for activity in stream:
            count += 1
            print(f"   Streamed: {activity['source']} - {activity['message']}")
            if count >= 3:
                break

        if count == 0:
            print("❌ FAIL: stream_scar_activity() yielded no events")
            return

        print(f"✓ PASS: stream_scar_activity() streamed {count} initial activities")

        # Check 5: Session configuration
        print("\n✓ Check 5: Session configuration")
        print(f"   expire_on_commit: {session.expire_on_commit}")

        if session.expire_on_commit:
            print("   ⚠️  WARNING: expire_on_commit=True may cause session isolation issues")
            print("   Recommend setting expire_on_commit=False in async_session_maker()")

        print("\n" + "=" * 60)
        print("✅ DIAGNOSTIC COMPLETE")
        print("\nNext steps:")
        print("1. If Check 2 failed → Issue is in execute_scar_command() or agent tool invocation")
        print("2. If Check 3 failed → Issue is in SSE feed service query logic")
        print("3. If Check 4 failed → Issue is in SSE streaming generator")
        print("4. If Check 5 warning → Fix session configuration")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: uv run python scripts/diagnose_sse_feed.py <project_id>")
        sys.exit(1)

    project_id = UUID(sys.argv[1])
    asyncio.run(diagnose(project_id))
```

**VALIDATE**:
```bash
# Get project ID from database first
uv run python -c "import asyncio; from src.database.connection import async_session_maker; from src.database.models import Project; from sqlalchemy import select; async def get_id(): async with async_session_maker() as s: r = await s.execute(select(Project).limit(1)); p = r.scalar_one_or_none(); print(p.id if p else 'No projects found'); asyncio.run(get_id())"

# Then run diagnostic (replace with actual project_id)
uv run python scripts/diagnose_sse_feed.py <project_id>
```

---

### UPDATE src/database/connection.py

**IMPLEMENT**: Ensure session configuration allows cross-session data visibility

**PATTERN**: Session factory configuration (lines 32-38)

**CHANGE**: Set `expire_on_commit=False` to prevent session isolation issues

```python
# Before (if expire_on_commit=True or not set):
async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=True  # or default
)

# After (ensure expire_on_commit=False):
async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False  # Critical for SSE visibility
)
```

**GOTCHA**: If `expire_on_commit=True`, objects from one session become detached after commit, causing SSE queries in a different session to miss them.

**VALIDATE**:
```bash
# Check session config
uv run python -c "from src.database.connection import async_session_maker; print(f'expire_on_commit={async_session_maker.kw.get(\"expire_on_commit\", \"default=True\")}')"
```

---

### UPDATE src/services/scar_executor.py

**IMPLEMENT**: Add explicit session refresh and diagnostic logging after database commit

**PATTERN**: Database commit pattern (lines 93-95, 139)

**ADD**: Logging after commit to confirm record persistence

```python
# Around line 94 (after initial commit)
session.add(execution)
await session.commit()
await session.refresh(execution)

# ADD LOGGING:
logger.info(
    f"ScarCommandExecution record created and committed",
    extra={
        "execution_id": str(execution.id),
        "project_id": str(project_id),
        "command": command.value,
        "status": execution.status.value,
    }
)

# Around line 139 (after final commit)
await session.commit()

# ADD LOGGING:
logger.info(
    f"ScarCommandExecution record updated to COMPLETED",
    extra={
        "execution_id": str(execution.id),
        "project_id": str(project_id),
        "status": execution.status.value,
        "duration": duration,
    }
)
```

**VALIDATE**:
```bash
# Check logs for diagnostic messages when SCAR command runs
docker logs project-manager-backend 2>&1 | grep "ScarCommandExecution record"
```

---

### UPDATE src/services/scar_feed_service.py

**IMPLEMENT**: Add diagnostic logging to SSE polling query

**PATTERN**: SSE polling query (lines 110-119)

**ADD**: Logging before and after database query

```python
# Around line 109 (before query execution)
if last_timestamp:
    last_dt = datetime.fromisoformat(last_timestamp)

    # ADD LOGGING:
    logger.debug(
        f"SSE polling for new activities since {last_timestamp}",
        extra={"project_id": str(project_id), "last_timestamp": last_timestamp}
    )

    query = (
        select(ScarCommandExecution)
        .where(
            ScarCommandExecution.project_id == project_id,
            ScarCommandExecution.started_at > last_dt,
        )
        .order_by(ScarCommandExecution.started_at.asc())
    )

# After line 129 (after query execution)
result = await session.execute(query)
new_activities = result.scalars().all()

# ADD LOGGING:
logger.debug(
    f"SSE poll found {len(new_activities)} new activities",
    extra={"project_id": str(project_id), "count": len(new_activities)}
)
```

**VALIDATE**:
```bash
# Check SSE polling logs
docker logs project-manager-backend 2>&1 | grep "SSE poll"
```

---

### UPDATE src/api/sse.py

**IMPLEMENT**: Add logging for SSE connection lifecycle and event streaming

**PATTERN**: SSE endpoint (lines 52-103)

**ADD**: Connection start/end logging, event streaming logging

```python
# Around line 53 (event_generator function start)
async def event_generator():
    """Generate Server-Sent Events for SCAR activity."""

    # ADD LOGGING:
    logger.info(
        f"SSE event generator starting",
        extra={"project_id": str(project_id), "verbosity": verbosity}
    )

    try:
        async with async_session_maker() as session:
            # ... existing code ...

# Around line 69 (after yielding activity event)
yield {"event": "activity", "data": json.dumps(activity)}

# ADD LOGGING (but rate-limit to avoid log spam):
if count % 10 == 0:  # Log every 10th event
    logger.debug(
        f"SSE streamed {count} activities so far",
        extra={"project_id": str(project_id)}
    )
```

**VALIDATE**:
```bash
# Monitor SSE logs while WebUI is open
docker logs -f project-manager-backend 2>&1 | grep "SSE"
```

---

### CREATE tests/integration/test_sse_feed_e2e.py

**IMPLEMENT**: End-to-end integration test for SSE feed flow

**PATTERN**: Test pattern from `test_scar_executor.py`

```python
"""
End-to-end integration test for SSE feed.

Tests the complete flow:
User Message → PM Agent → execute_scar → Database → SSE Stream → Frontend
"""

import asyncio
import pytest
from uuid import uuid4

from src.database.models import Project, ProjectStatus, ScarCommandExecution, ExecutionStatus
from src.services.scar_executor import ScarCommand, execute_scar_command
from src.services.scar_feed_service import get_recent_scar_activity, stream_scar_activity


@pytest.mark.asyncio
async def test_sse_feed_e2e_flow(db_session):
    """Test complete SSE feed flow from SCAR execution to SSE streaming"""

    # Step 1: Create project
    project = Project(
        name="Test SSE Feed",
        status=ProjectStatus.PLANNING,
        github_repo_url="https://github.com/test/repo",
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Step 2: Execute SCAR command (simulates PM agent calling execute_scar tool)
    result = await execute_scar_command(
        db_session, project.id, ScarCommand.PRIME
    )

    assert result.success is True, "SCAR command should succeed"

    # Step 3: Verify database record exists (simulates what SSE will query)
    from sqlalchemy import select
    exec_result = await db_session.execute(
        select(ScarCommandExecution).where(ScarCommandExecution.project_id == project.id)
    )
    executions = exec_result.scalars().all()

    assert len(executions) == 1, "Should have 1 execution record in database"
    assert executions[0].status == ExecutionStatus.COMPLETED, "Execution should be completed"

    # Step 4: Test SSE feed service query (simulates SSE polling)
    activities = await get_recent_scar_activity(db_session, project.id, limit=10)

    assert len(activities) == 1, "SSE feed service should find 1 activity"
    assert activities[0]["source"] == "scar", "Activity source should be 'scar'"
    assert "PRIME" in activities[0]["message"], "Activity message should contain command type"

    # Step 5: Test SSE streaming (simulates SSE endpoint streaming to frontend)
    stream = stream_scar_activity(db_session, project.id, verbosity_level=2)

    streamed_activities = []
    async for activity in stream:
        streamed_activities.append(activity)
        break  # Get first activity from stream

    assert len(streamed_activities) == 1, "SSE stream should yield initial activity"
    assert streamed_activities[0]["id"] == activities[0]["id"], "Streamed activity should match query result"


@pytest.mark.asyncio
async def test_sse_feed_multiple_executions(db_session):
    """Test SSE feed with multiple SCAR executions"""

    # Create project
    project = Project(
        name="Multi Execution Test",
        status=ProjectStatus.IN_PROGRESS,
        github_repo_url="https://github.com/test/multi",
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Execute multiple SCAR commands
    await execute_scar_command(db_session, project.id, ScarCommand.PRIME)
    await execute_scar_command(db_session, project.id, ScarCommand.PLAN_FEATURE_GITHUB, args=["Test Feature"])

    # Verify SSE feed shows all executions
    activities = await get_recent_scar_activity(db_session, project.id, limit=10)

    assert len(activities) == 2, "Should have 2 activities"
    assert activities[0]["message"] != activities[1]["message"], "Activities should be different"
```

**VALIDATE**:
```bash
uv run pytest tests/integration/test_sse_feed_e2e.py -v
```

---

### MANUAL TEST: SSE Endpoint with curl

**IMPLEMENT**: Manual test to verify SSE endpoint streams events correctly

**COMMANDS**:
```bash
# 1. Get a project ID from the database
PROJECT_ID=$(uv run python -c "import asyncio; from src.database.connection import async_session_maker; from src.database.models import Project; from sqlalchemy import select; async def get_id(): async with async_session_maker() as s: r = await s.execute(select(Project).limit(1)); p = r.scalar_one_or_none(); print(p.id if p else ''); asyncio.run(get_id())")

# 2. Start SSE connection in background
echo "Connecting to SSE endpoint for project $PROJECT_ID..."
curl -N "http://localhost:8000/api/sse/scar/${PROJECT_ID}?verbosity=2" &
CURL_PID=$!

# 3. Wait a few seconds to establish connection
sleep 3

# 4. Trigger a SCAR command via API (in another terminal)
# This would be done through WebUI normally, but can test with:
# Send a chat message that triggers execute_scar('prime')

# 5. Observe SSE output
# Should see:
# event: activity
# data: {"id": "...", "timestamp": "...", "source": "scar", "message": "PRIME: COMPLETED", ...}

# 6. Stop curl
kill $CURL_PID
```

**EXPECTED OUTPUT**:
```
event: activity
data: {"id":"...","timestamp":"2026-01-06T...","source":"scar","message":"PRIME: COMPLETED","phase":null}

event: heartbeat
data: {"status":"alive","timestamp":"2026-01-06T..."}
```

**VALIDATE**: If no activity events appear, SSE endpoint is not streaming correctly.

---

### MANUAL TEST: Reproduce Issue #45 Scenario

**IMPLEMENT**: Exact reproduction of Issue #45 to verify fix

**STEPS**:
1. Open WebUI in browser
2. Open browser DevTools → Network tab → Filter by "sse"
3. Verify SSE connection established: `GET /api/sse/scar/<project_id>` status 200
4. Open Console tab
5. Send message: "analyze the codebase"
6. Observe:
   - Console should show: `SSE connected`
   - Console should show activity events (if fix works)
   - Right pane should populate with SCAR activity
7. Check backend logs: `docker logs project-manager-backend | tail -50`
   - Should see "Executing SCAR command: prime"
   - Should see "ScarCommandExecution record created"
   - Should see "SSE poll found X new activities"

**PASS CRITERIA**:
- ✅ SSE connection established
- ✅ Activity events logged in browser console
- ✅ Right pane displays "PRIME: RUNNING" then "PRIME: COMPLETED"
- ✅ Backend logs confirm database record created
- ✅ Backend logs confirm SSE polled and found new activity

**FAIL CRITERIA**:
- ❌ SSE connected but no activity events
- ❌ Right pane remains empty
- ❌ Backend logs show "SSE poll found 0 new activities" despite records existing

---

## TESTING STRATEGY

### Unit Tests

**Scope**: Test individual components in isolation

- ✅ `test_scar_executor.py` - Already exists, covers execute_scar_command()
- ✅ New: `test_sse_feed_e2e.py` - Integration test for full flow

### Integration Tests

**Scope**: Test end-to-end data flow

- Test SCAR execution → Database → SSE query → SSE stream
- Test multiple executions appear in correct order
- Test SSE polling detects new records added after connection established

### Manual Tests

**Scope**: Validate WebUI and real-world scenarios

- Reproduce Issue #45 exact scenario
- Test with SCAR actually running (not mocked)
- Test SSE connection stability over time
- Test with multiple concurrent users

---

## VALIDATION COMMANDS

Execute every command to ensure zero regressions and 100% feature correctness.

### Level 1: Import Validation (CRITICAL)

**Verify all imports resolve:**

```bash
uv run python -c "from src.main import app; print('✓ All imports valid')"
```

**Expected:** "✓ All imports valid"

**Why:** Catches import errors from new files or changed imports.

### Level 2: Diagnostic Script Validation

**Run diagnostic script:**

```bash
# Get project ID
PROJECT_ID=$(uv run python -c "import asyncio; from src.database.connection import async_session_maker; from src.database.models import Project; from sqlalchemy import select; async def get_id(): async with async_session_maker() as s: r = await s.execute(select(Project).limit(1)); p = r.scalar_one_or_none(); print(p.id if p else ''); asyncio.run(get_id())")

# Run diagnostic
uv run python scripts/diagnose_sse_feed.py $PROJECT_ID
```

**Expected:** All checks pass (✓ PASS)

**Why:** Identifies exact breaking point if SSE feed still doesn't work.

### Level 3: Unit Tests

**Run all unit tests:**

```bash
uv run pytest tests/services/test_scar_executor.py -v
```

**Expected:** All tests pass

**Why:** Ensures SCAR executor still works correctly.

### Level 4: Integration Tests

**Run SSE feed E2E tests:**

```bash
uv run pytest tests/integration/test_sse_feed_e2e.py -v
```

**Expected:** Both test cases pass

**Why:** Validates complete SSE feed flow works end-to-end.

### Level 5: Linting and Formatting

**Run linters:**

```bash
uv run ruff check src/ tests/ scripts/
uv run ruff format src/ tests/ scripts/ --check
```

**Expected:** No errors

**Why:** Code quality and consistency.

### Level 6: Manual SSE Endpoint Test

**Test SSE endpoint manually:**

```bash
# Terminal 1: Start backend
docker-compose up backend

# Terminal 2: Connect to SSE
curl -N "http://localhost:8000/api/sse/scar/<project_id>?verbosity=2"

# Terminal 3: Trigger SCAR command via WebUI
# Open browser, send "analyze the codebase"

# Observe Terminal 2: Should see activity events streaming
```

**Expected:** Activity events appear in curl output

**Why:** Confirms SSE endpoint streams events correctly.

### Level 7: Full E2E WebUI Test

**Reproduce Issue #45 scenario:**

1. Open WebUI in browser
2. Open DevTools → Console and Network tabs
3. Send message: "analyze the codebase"
4. Verify right pane populates with SCAR activity

**Expected:**
- SSE connection established (Network tab shows GET /api/sse/scar/...)
- Activity events in console
- Right pane shows "PRIME: RUNNING" → "PRIME: COMPLETED"

**Why:** Real-world validation that fix resolves Issue #45.

---

## ACCEPTANCE CRITERIA

- [ ] Diagnostic script runs successfully and all checks pass
- [ ] ScarCommandExecution records are created when execute_scar tool is called
- [ ] SSE feed service queries find records created by scar_executor
- [ ] SSE endpoint streams activity events to connected clients
- [ ] Frontend displays SCAR activity in real-time
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Manual WebUI test reproduces and confirms fix for Issue #45
- [ ] No linting or formatting errors
- [ ] Session configuration allows cross-session data visibility
- [ ] Comprehensive logging added for debugging future issues

---

## COMPLETION CHECKLIST

- [ ] Diagnostic script created and validated
- [ ] Session configuration verified (expire_on_commit=False)
- [ ] Diagnostic logging added to scar_executor
- [ ] Diagnostic logging added to scar_feed_service
- [ ] Diagnostic logging added to SSE endpoint
- [ ] Integration tests created and passing
- [ ] Manual SSE endpoint test successful
- [ ] Full E2E WebUI test successful (Issue #45 resolved)
- [ ] All validation commands executed and passed
- [ ] Code reviewed for quality
- [ ] Root cause documented

---

## NOTES

### Root Cause Analysis Findings

**Update this section after running diagnostics:**

After running `scripts/diagnose_sse_feed.py`, document findings here:

- [ ] Check 1 (Project exists): PASS / FAIL
- [ ] Check 2 (Records exist): PASS / FAIL
- [ ] Check 3 (SSE query works): PASS / FAIL
- [ ] Check 4 (SSE streaming works): PASS / FAIL
- [ ] Check 5 (Session config): expire_on_commit = ?

**Root Cause**: [To be determined by diagnostics]

**Fix Applied**: [Document the specific fix based on findings]

### Design Decisions

1. **Why diagnostic script first?**
   - Previous fixes (PR #46, #48) were speculative
   - This ensures we fix the ACTUAL problem, not symptoms

2. **Why session configuration check?**
   - `expire_on_commit=True` can cause objects to be detached after commit
   - SSE queries in different session might not see committed data

3. **Why comprehensive logging?**
   - Future debugging will be easier
   - Confirms each step of data flow is working

### Performance Considerations

- SSE polling every 2 seconds is acceptable for MVP
- Consider Redis pub/sub for production scale
- Database query uses indexed column (started_at)

### Security Considerations

- SSE endpoint requires project_id in URL
- Should add authentication check (future enhancement)
- Rate limiting already handled by slowapi middleware
