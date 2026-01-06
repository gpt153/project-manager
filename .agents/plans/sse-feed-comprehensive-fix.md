# Feature: SSE Feed Comprehensive Fix and Validation

The following plan should be complete, but it's important that you validate documentation and codebase patterns and task sanity before you start implementing.

Pay special attention to naming of existing utils types and models. Import from the right files etc.

## Feature Description

Comprehensive fix and validation of the Server-Sent Events (SSE) feed system that displays real-time SCAR command execution activity in the WebUI. Previous attempts (Issues #45, #47, PRs #46, #48) have addressed specific symptoms, but the user reports the issue persists. This plan ensures end-to-end functionality with comprehensive testing and validation.

## User Story

As a user of the Project Manager WebUI
I want to see real-time SCAR command execution activity in the right pane SSE feed
So that I can monitor what SCAR is doing and have transparency into system operations

## Problem Statement

**Historical Context:**
- **Issue #45**: SSE feed shows no SCAR activity despite PM responding
- **PR #46**: Fixed SSE polling timestamp comparison (UUID → timestamp)
- **Issue #47**: Frontend not listening to named events
- **PR #48**: Fixed frontend event listeners (`onmessage` → `addEventListener('activity')`)
- **Current Status**: User reports issue persists, requesting comprehensive fix

**Potential Remaining Issues:**
1. Agent may not be calling `execute_scar()` tool consistently
2. Database records may not be created/committed properly
3. SSE polling may have edge cases with timing
4. Frontend may lose connection or fail to reconnect
5. Integration between components may have gaps

## Solution Statement

Implement a comprehensive fix that addresses the complete event flow:
1. **Agent Layer**: Ensure execute_scar tool is called reliably
2. **Execution Layer**: Verify database records are created and committed
3. **SSE Layer**: Enhance polling reliability with better error handling
4. **Frontend Layer**: Add connection recovery and better state management
5. **Testing**: Add end-to-end integration tests
6. **Monitoring**: Add diagnostic endpoints for debugging

## Feature Metadata

**Feature Type**: Bug Fix / System Integration
**Estimated Complexity**: Medium
**Primary Systems Affected**:
- Agent orchestrator (`src/agent/orchestrator_agent.py`)
- SCAR executor (`src/services/scar_executor.py`)
- SSE feed service (`src/services/scar_feed_service.py`)
- SSE endpoint (`src/api/sse.py`)
- Frontend SSE hook (`frontend/src/hooks/useScarFeed.ts`)
- Frontend activity display (`frontend/src/components/RightPanel/ScarActivityFeed.tsx`)

**Dependencies**:
- `sse-starlette==2.1.0`
- `sqlalchemy[asyncio]>=2.0.36`
- `pydantic-ai>=0.0.14`
- `fastapi>=0.115.0`
- `pytest>=8.3.0`
- `pytest-asyncio>=0.24.0`

---

## CONTEXT REFERENCES

### Relevant Codebase Files IMPORTANT: YOU MUST READ THESE FILES BEFORE IMPLEMENTING!

**Agent Layer:**
- `src/agent/orchestrator_agent.py` (lines 269-316) - **Why**: execute_scar tool definition
- `src/agent/prompts.py` (lines 251-276) - **Why**: System prompt guidance for when to call execute_scar
- `src/agent/tools.py` - **Why**: Tool registration patterns

**Execution Layer:**
- `src/services/scar_executor.py` (lines 49-234) - **Why**: Creates ScarCommandExecution records, core execution logic
- `src/scar/client.py` (lines 112-290) - **Why**: SCAR HTTP client, workspace setup, command sending

**SSE Streaming Layer:**
- `src/api/sse.py` (lines 22-104) - **Why**: SSE endpoint implementation
- `src/services/scar_feed_service.py` (lines 19-149) - **Why**: Database polling and activity streaming

**Database Layer:**
- `src/database/models.py` (lines 248-301) - **Why**: ScarCommandExecution model with @property methods
- `src/database/connection.py` - **Why**: Session configuration (expire_on_commit=False)

**Frontend Layer:**
- `frontend/src/hooks/useScarFeed.ts` - **Why**: EventSource client with event listeners (FIXED in PR #48)
- `frontend/src/components/RightPanel/ScarActivityFeed.tsx` - **Why**: UI rendering of activities

**Testing Layer:**
- `tests/conftest.py` - **Why**: Test fixtures and database setup patterns
- `tests/services/test_scar_executor.py` - **Why**: Existing test patterns for SCAR execution

### Previous Fixes (Already Merged)

**PR #46 (Commit d928ef6)**:
- Fixed SSE polling timestamp comparison
- Changed from UUID comparison to `started_at > last_dt`
- File: `src/services/scar_feed_service.py`

**PR #48 (Commit 8d8ceb3)**:
- Fixed frontend event listeners
- Changed `onmessage` → `addEventListener('activity')` and `addEventListener('heartbeat')`
- File: `frontend/src/hooks/useScarFeed.ts`

### Relevant Documentation

- [Server-Sent Events (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
  - **Section**: Using server-sent events
  - **Why**: Understand EventSource API and named events
- [sse-starlette Documentation](https://github.com/sysid/sse-starlette)
  - **Section**: EventSourceResponse usage
  - **Why**: Backend SSE implementation patterns
- [SQLAlchemy Async Sessions](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
  - **Section**: AsyncSession and expire_on_commit
  - **Why**: Proper async session handling
- [Pytest Asyncio](https://pytest-asyncio.readthedocs.io/en/latest/)
  - **Section**: pytest.mark.asyncio
  - **Why**: Testing async functions

### Patterns to Follow

**Testing Pattern (from tests/services/test_scar_executor.py):**
```python
@pytest.mark.asyncio
async def test_execute_prime_command(db_session):
    """Test executing PRIME command"""
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
    assert result.output is not None
```

**Database Session Pattern (from conftest.py):**
```python
async_session_maker_test = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,  # CRITICAL: Prevents lazy-loading issues
)
```

**SSE Event Pattern (from src/api/sse.py):**
```python
yield {"event": "activity", "data": json.dumps(activity)}
yield {"event": "heartbeat", "data": json.dumps({"status": "alive"})}
```

**Frontend Event Listener Pattern (from useScarFeed.ts - ALREADY FIXED):**
```typescript
eventSource.addEventListener('activity', (event) => {
  const activity: ScarActivity = JSON.parse(event.data);
  setActivities((prev) => [...prev, activity]);
});
```

**Logging Pattern:**
```python
logger.info(
    "Message with context",
    extra={"project_id": str(project_id), "key": "value"}
)
```

---

## IMPLEMENTATION PLAN

### Phase 1: Diagnostic Enhancement

Add diagnostic capabilities to identify exactly where issues occur.

**Rationale**: Before fixing, we need visibility into what's failing.

**Tasks:**
- Add diagnostic endpoint to check SSE feed health
- Add detailed logging to track execution flow
- Add database query endpoint to verify ScarCommandExecution records

### Phase 2: Execution Layer Hardening

Ensure SCAR execution reliably creates database records.

**Rationale**: Database records are the source of truth for SSE feed.

**Tasks:**
- Review and enhance error handling in scar_executor.py
- Verify session commit happens in all code paths
- Add retry logic for transient failures
- Improve logging to track execution lifecycle

### Phase 3: SSE Streaming Enhancement

Improve SSE feed reliability and error handling.

**Rationale**: Streaming layer must handle edge cases gracefully.

**Tasks:**
- Add connection recovery in scar_feed_service.py
- Improve error handling in SSE endpoint
- Add heartbeat timeout detection
- Optimize database polling query

### Phase 4: Frontend Enhancement

Add frontend resilience and better state management.

**Rationale**: Frontend should recover from connection issues.

**Tasks:**
- Add automatic reconnection logic
- Add connection status indicators
- Add error message display
- Add manual reconnect button

### Phase 5: Integration Testing

Comprehensive end-to-end testing.

**Rationale**: Prevent regressions and validate complete flow.

**Tasks:**
- Create end-to-end SSE feed test
- Test database record creation
- Test SSE streaming
- Test frontend event handling
- Add CI test coverage

### Phase 6: Validation and Monitoring

Ensure system is working and maintainable.

**Rationale**: Long-term reliability and debuggability.

**Tasks:**
- Manual testing with real SCAR execution
- Performance testing of SSE streaming
- Documentation update
- Monitoring dashboard

---

## STEP-BY-STEP TASKS

### Phase 1: Diagnostic Enhancement

#### CREATE src/api/diagnostics.py

- **IMPLEMENT**: Diagnostic endpoint for SSE feed health check
- **PATTERN**: Follow src/api/sse.py router structure
- **IMPORTS**:
  ```python
  from fastapi import APIRouter, Depends
  from sqlalchemy.ext.asyncio import AsyncSession
  from src.database.connection import get_session
  from src.services.scar_feed_service import get_recent_scar_activity
  ```
- **GOTCHA**: Use async def with proper session dependency
- **VALIDATE**: `curl http://localhost:8001/api/diagnostics/sse/{project_id}`

**Implementation Details:**
```python
@router.get("/diagnostics/sse/{project_id}")
async def diagnose_sse_feed(
    project_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    """
    Diagnostic endpoint to check SSE feed health.

    Returns:
    - Recent activity count
    - Database record count
    - Last activity timestamp
    - Connection test result
    """
    activities = await get_recent_scar_activity(session, project_id, limit=10)

    return {
        "project_id": str(project_id),
        "activity_count": len(activities),
        "last_activity": activities[-1] if activities else None,
        "status": "healthy" if activities else "no_data",
        "database_check": "passed"
    }
```

#### UPDATE src/services/scar_executor.py

- **IMPLEMENT**: Enhanced logging at critical execution points
- **PATTERN**: Existing logger.info calls with extra context
- **IMPORTS**: None (already has logging)
- **GOTCHA**: Log BEFORE and AFTER database commit
- **VALIDATE**: Check logs during test execution

**Add logging at these points:**
1. Before execution record creation (line 85)
2. After database commit (line 94)
3. Before status update to RUNNING (line 101)
4. After status update commit (line 102)
5. Before final commit (line 139)
6. After final commit (line 140)

Example:
```python
# Before commit
logger.info("Creating ScarCommandExecution record", extra={
    "project_id": str(project_id),
    "command": command.value,
    "execution_id": str(execution.id)
})
await session.commit()
logger.info("ScarCommandExecution record committed", extra={
    "execution_id": str(execution.id)
})
```

### Phase 2: Execution Layer Hardening

#### UPDATE src/services/scar_executor.py

- **IMPLEMENT**: Add explicit session.flush() before commit to catch errors early
- **PATTERN**: SQLAlchemy flush pattern
- **IMPORTS**: None needed
- **GOTCHA**: flush() detects constraint violations before commit
- **VALIDATE**: Run test_scar_executor.py tests

**Changes:**
```python
# Line 93-94: Add flush before commit
session.add(execution)
await session.flush()  # Catch errors before commit
await session.commit()
```

#### UPDATE src/services/scar_executor.py

- **IMPLEMENT**: Add session.refresh() after commits to ensure data is loaded
- **PATTERN**: Existing refresh at line 95
- **IMPORTS**: None needed
- **GOTCHA**: With expire_on_commit=False, refresh ensures attributes are accessible
- **VALIDATE**: Verify execution.id is accessible after commit

**Changes:**
```python
# After each commit, add refresh
await session.commit()
await session.refresh(execution)
```

### Phase 3: SSE Streaming Enhancement

#### UPDATE src/services/scar_feed_service.py

- **IMPLEMENT**: Add error handling for database query failures in polling loop
- **PATTERN**: Try-except around database queries
- **IMPORTS**: None needed (logging already imported)
- **GOTCHA**: Don't break streaming loop on transient DB errors
- **VALIDATE**: Simulate DB connection issue during streaming

**Changes:**
```python
# Line 128-129: Wrap query in try-except
try:
    result = await session.execute(query)
    new_activities = result.scalars().all()
except Exception as e:
    logger.error(f"Error querying activities: {e}", extra={
        "project_id": str(project_id)
    })
    # Continue polling despite error
    continue
```

#### UPDATE src/services/scar_feed_service.py

- **IMPLEMENT**: Add query optimization - select only needed columns
- **PATTERN**: SQLAlchemy select with specific columns
- **IMPORTS**: `from sqlalchemy import select, desc` (already imported)
- **GOTCHA**: Still need to access @property methods, so load full object
- **VALIDATE**: Check query performance with `EXPLAIN ANALYZE`

**Note**: Current implementation is already optimal (selects full objects for @property access).

#### UPDATE src/api/sse.py

- **IMPLEMENT**: Add timeout detection for heartbeat
- **PATTERN**: Track heartbeat interval
- **IMPORTS**: None needed (asyncio already available)
- **GOTCHA**: Don't send heartbeat too frequently (network overhead)
- **VALIDATE**: Check browser DevTools Network tab for heartbeat events

**Current implementation (lines 63-80) is already good**. No changes needed.

### Phase 4: Frontend Enhancement

#### UPDATE frontend/src/hooks/useScarFeed.ts

- **IMPLEMENT**: Add automatic reconnection on error
- **PATTERN**: EventSource error handling with retry
- **IMPORTS**: None needed
- **GOTCHA**: Exponential backoff to avoid overwhelming server
- **VALIDATE**: Kill backend, verify frontend reconnects when backend restarts

**Changes:**
```typescript
const [reconnectAttempts, setReconnectAttempts] = useState(0);
const maxReconnectAttempts = 5;
const reconnectDelay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);

eventSource.onerror = (error) => {
  console.error('SSE error:', error);
  setIsConnected(false);

  if (reconnectAttempts < maxReconnectAttempts) {
    console.log(`Reconnecting in ${reconnectDelay}ms...`);
    setTimeout(() => {
      setReconnectAttempts(prev => prev + 1);
      // React will re-run useEffect due to dependency change
    }, reconnectDelay);
  } else {
    console.error('Max reconnection attempts reached');
  }
};
```

#### UPDATE frontend/src/components/RightPanel/ScarActivityFeed.tsx

- **IMPLEMENT**: Add connection status indicator with reconnect button
- **PATTERN**: React conditional rendering
- **IMPORTS**: None needed
- **GOTCHA**: Style indicator to be visible but not intrusive
- **VALIDATE**: Manually test connection status display

**Changes:**
```tsx
{!isConnected && (
  <div className="connection-warning">
    <span>⚠️ Disconnected from activity feed</span>
    <button onClick={() => window.location.reload()}>Reconnect</button>
  </div>
)}
```

### Phase 5: Integration Testing

#### CREATE tests/integration/test_sse_feed.py

- **IMPLEMENT**: End-to-end SSE feed integration test
- **PATTERN**: Mirror test_scar_executor.py structure
- **IMPORTS**:
  ```python
  import pytest
  import asyncio
  from httpx import AsyncClient
  from src.database.models import Project, ProjectStatus
  from src.services.scar_executor import ScarCommand, execute_scar_command
  ```
- **GOTCHA**: Test needs to handle SSE streaming (async iteration)
- **VALIDATE**: `pytest tests/integration/test_sse_feed.py -v`

**Implementation:**
```python
@pytest.mark.asyncio
async def test_sse_feed_receives_activity(db_session, client: AsyncClient):
    """Test that SSE feed streams SCAR activity after execution"""
    # Create project
    project = Project(
        name="SSE Test",
        status=ProjectStatus.PLANNING,
        github_repo_url="https://github.com/test/repo",
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Execute SCAR command (creates activity record)
    result = await execute_scar_command(db_session, project.id, ScarCommand.PRIME)
    assert result.success is True

    # Connect to SSE feed
    async with client.stream(
        "GET",
        f"/api/sse/scar/{project.id}?verbosity=2"
    ) as response:
        assert response.status_code == 200

        # Read first few events
        events = []
        async for line in response.aiter_lines():
            if line.startswith("data:"):
                data = line[5:].strip()
                events.append(data)
                if len(events) >= 1:
                    break

        # Verify we received activity event
        assert len(events) >= 1
        import json
        activity = json.loads(events[0])
        assert "id" in activity
        assert "message" in activity
        assert activity["source"] == "scar"
```

#### CREATE tests/integration/test_scar_to_sse_flow.py

- **IMPLEMENT**: Test complete flow from agent tool call to SSE stream
- **PATTERN**: Integration test with mocked SCAR client
- **IMPORTS**:
  ```python
  import pytest
  from unittest.mock import AsyncMock, patch
  from src.agent.orchestrator_agent import orchestrator_agent
  from src.agent.tools import AgentDependencies
  ```
- **GOTCHA**: Need to mock SCAR HTTP client to avoid external dependency
- **VALIDATE**: `pytest tests/integration/test_scar_to_sse_flow.py -v`

**Implementation:**
```python
@pytest.mark.asyncio
@patch('src.scar.client.httpx.AsyncClient')
async def test_agent_execute_scar_creates_sse_activity(
    mock_client, db_session, client: AsyncClient
):
    """Test that agent execute_scar tool creates SSE-streamable activity"""
    # Setup mocks
    mock_response = AsyncMock()
    mock_response.raise_for_status = AsyncMock()
    mock_response.json.return_value = {"messages": [
        {"direction": "sent", "message": "Prime complete"}
    ]}
    mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
    mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

    # Create project
    project = Project(
        name="Agent SSE Test",
        status=ProjectStatus.PLANNING,
        github_repo_url="https://github.com/test/repo",
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Call agent tool directly
    from pydantic_ai import RunContext
    deps = AgentDependencies(session=db_session, project_id=project.id)

    # This simulates agent calling execute_scar tool
    from src.agent.orchestrator_agent import execute_scar
    result = await execute_scar(
        RunContext(deps=deps, retry=0, tool_name="execute_scar"),
        command="prime",
        args=None
    )

    assert result["success"] is True

    # Verify SSE feed has the activity
    response = await client.get(f"/api/diagnostics/sse/{project.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["activity_count"] >= 1
    assert data["last_activity"] is not None
```

### Phase 6: Validation and Monitoring

#### Manual Testing Checklist

1. **Database Verification**:
```bash
# Connect to database and verify records
psql -U manager -d project_orchestrator_dev -c "SELECT id, command_type, status, started_at FROM scar_executions ORDER BY started_at DESC LIMIT 5;"
```

2. **SSE Endpoint Testing**:
```bash
# Test SSE endpoint directly
curl -N http://localhost:8001/api/sse/scar/{PROJECT_ID}
# Should see: event: activity, data: {...}
```

3. **Diagnostic Endpoint Testing**:
```bash
# Check diagnostic endpoint
curl http://localhost:8001/api/diagnostics/sse/{PROJECT_ID}
# Should return JSON with activity count
```

4. **Frontend Testing**:
- Open WebUI
- Send message: "analyze the codebase"
- Verify right pane shows activity
- Check browser console for SSE connection messages
- Verify no errors in console

5. **Reconnection Testing**:
- Open WebUI with SSE feed active
- Stop backend (Ctrl+C)
- Wait 5 seconds
- Restart backend
- Verify frontend reconnects automatically

#### UPDATE src/main.py

- **IMPLEMENT**: Register diagnostics router
- **PATTERN**: Existing router registration (lines 158-166)
- **IMPORTS**: `from src.api.diagnostics import router as diagnostics_router`
- **GOTCHA**: Add after SSE router registration
- **VALIDATE**: Check `http://localhost:8001/docs` shows diagnostic endpoint

**Changes:**
```python
# After line 165
try:
    from src.api.diagnostics import router as diagnostics_router
    app.include_router(diagnostics_router, prefix="/api", tags=["Diagnostics"])
    logger.info("Diagnostics router registered")
except ImportError as e:
    logger.warning(f"Diagnostics router not available: {e}")
```

---

## TESTING STRATEGY

### Unit Tests

**Scope**: Individual component testing
- Test scar_executor.py functions in isolation
- Test scar_feed_service.py functions with mock data
- Test frontend hooks with mock EventSource

**Pattern**:
```python
@pytest.mark.asyncio
async def test_function_name(db_session):
    # Arrange
    # Act
    # Assert
```

### Integration Tests

**Scope**: Multi-component interaction testing
- Test SCAR execution → Database record creation
- Test Database record → SSE streaming
- Test SSE endpoint → Frontend reception

**Pattern**: See Phase 5 implementation details above

### End-to-End Tests

**Scope**: Complete user workflow testing
- User message → Agent tool call → SCAR execution → SSE feed → Frontend display

**Manual Testing**: See Phase 6 validation checklist

### Edge Cases to Test

1. **Database connection lost during execution**
   - Verify retry logic works
   - Verify error is logged
   - Verify user sees error message

2. **SCAR not available**
   - Verify graceful failure
   - Verify error recorded in database
   - Verify SSE feed shows error status

3. **SSE connection interrupted**
   - Verify frontend reconnects
   - Verify no activity is lost
   - Verify heartbeat resumes

4. **Multiple concurrent SSE connections**
   - Verify each connection is independent
   - Verify no cross-talk between connections

5. **No SCAR activity for extended period**
   - Verify heartbeat keeps connection alive
   - Verify no memory leaks in polling loop

---

## VALIDATION COMMANDS

Execute every command to ensure zero regressions and 100% feature correctness.

### Level 1: Import Validation (CRITICAL)

**Verify all imports resolve:**
```bash
uv run python -c "from src.main import app; print('✓ All imports valid')"
```
**Expected**: "✓ All imports valid"
**Why**: Catches import errors immediately

### Level 2: Database Migration Check

**Verify database schema is up to date:**
```bash
uv run alembic check
```
**Expected**: "No new upgrade operations detected"
**Why**: Ensures database models match migrations

### Level 3: Syntax & Style

**Run linter:**
```bash
uv run ruff check src/ tests/
```
**Expected**: No errors

**Run formatter:**
```bash
uv run ruff format --check src/ tests/
```
**Expected**: No files would be reformatted

### Level 4: Unit Tests

**Run SCAR executor tests:**
```bash
uv run pytest tests/services/test_scar_executor.py -v
```
**Expected**: All tests pass

**Run all unit tests:**
```bash
uv run pytest tests/unit/ -v
```
**Expected**: All tests pass

### Level 5: Integration Tests

**Run SSE feed integration tests:**
```bash
uv run pytest tests/integration/test_sse_feed.py -v
uv run pytest tests/integration/test_scar_to_sse_flow.py -v
```
**Expected**: All tests pass

**Run all integration tests:**
```bash
uv run pytest tests/integration/ -v
```
**Expected**: All tests pass

### Level 6: Manual Validation

**Start backend:**
```bash
uv run python -m src.main
```
**Expected**: Server starts on port 8001

**Test diagnostic endpoint:**
```bash
# Replace {PROJECT_ID} with actual project UUID from database
curl http://localhost:8001/api/diagnostics/sse/{PROJECT_ID}
```
**Expected**: JSON response with activity data

**Test SSE endpoint:**
```bash
# Replace {PROJECT_ID} with actual project UUID
curl -N http://localhost:8001/api/sse/scar/{PROJECT_ID}
```
**Expected**: SSE events streaming (event: activity, event: heartbeat)

**Test WebUI:**
1. Open http://localhost:5173 (frontend)
2. Select a project
3. Send message: "analyze the codebase"
4. Verify right pane shows SCAR activity in real-time
5. Check browser console: should see "SSE connected" message
6. Verify no errors in console

### Level 7: Performance Validation

**Test SSE streaming performance:**
```bash
# Run load test with multiple concurrent connections
for i in {1..10}; do
  curl -N "http://localhost:8001/api/sse/scar/{PROJECT_ID}" &
done
# Wait 30 seconds
# Kill all curl processes
killall curl
```
**Expected**: All connections receive heartbeats, no server errors

**Check memory usage:**
```bash
# Monitor memory during SSE streaming
ps aux | grep "python.*src.main"
```
**Expected**: Memory usage stable over time (no memory leak)

---

## ACCEPTANCE CRITERIA

- [x] **Previous Fixes Validated**: PR #46 and PR #48 changes are present and correct
- [ ] **Diagnostic Endpoint**: `/api/diagnostics/sse/{project_id}` returns activity health status
- [ ] **Execution Logging**: Detailed logs at all critical execution points
- [ ] **Database Records**: ScarCommandExecution records created for all SCAR executions
- [ ] **SSE Streaming**: Activity events streamed to frontend in real-time
- [ ] **Frontend Display**: Activities visible in right pane with correct formatting
- [ ] **Connection Recovery**: Frontend automatically reconnects on connection loss
- [ ] **Error Handling**: Graceful degradation when SCAR unavailable or database issues
- [ ] **Integration Tests**: Complete test coverage for SSE feed flow
- [ ] **Manual Testing**: All validation checklist items pass
- [ ] **No Regressions**: All existing tests continue to pass
- [ ] **Performance**: SSE streaming handles 10+ concurrent connections without issues
- [ ] **Documentation**: All diagnostic endpoints documented in OpenAPI spec

---

## COMPLETION CHECKLIST

- [ ] Phase 1 complete: Diagnostic enhancement implemented
- [ ] Phase 2 complete: Execution layer hardened
- [ ] Phase 3 complete: SSE streaming enhanced
- [ ] Phase 4 complete: Frontend resilience added
- [ ] Phase 5 complete: Integration tests passing
- [ ] Phase 6 complete: Manual validation successful
- [ ] All validation commands executed successfully
- [ ] Full test suite passes (unit + integration)
- [ ] No linting or formatting errors
- [ ] Manual testing confirms end-to-end functionality
- [ ] Diagnostic endpoints working
- [ ] Performance testing shows no degradation
- [ ] Connection recovery tested and working
- [ ] Documentation updated
- [ ] Code reviewed for quality

---

## NOTES

### Design Decisions

1. **Diagnostics First**: Adding diagnostic endpoints before fixes allows us to identify the exact failure point rather than guessing.

2. **Logging Enhancement**: Comprehensive logging at critical points (before/after commits) provides audit trail for debugging.

3. **Frontend Reconnection**: Exponential backoff prevents overwhelming server during outages while providing good user experience.

4. **Database Query Optimization**: Current implementation loads full objects for @property access, which is appropriate given the need for computed fields like `source`.

5. **Integration Testing**: End-to-end tests ensure components work together, not just in isolation.

### Trade-offs

1. **Polling vs Push**: SSE feed uses database polling (2-second interval) rather than pub/sub. This is simpler but less real-time. For production, consider Redis pub/sub.

2. **Reconnection Limit**: Frontend stops reconnecting after 5 attempts. This prevents infinite reconnection loops but may require manual page refresh for extended outages.

3. **Heartbeat Frequency**: 30-second heartbeat interval balances connection keep-alive with network overhead.

### Future Enhancements

1. **WebSocket Alternative**: Consider WebSocket for bidirectional communication and lower latency.

2. **Redis Pub/Sub**: Replace polling with pub/sub for true real-time updates.

3. **Activity Filtering**: Allow users to filter activities by type, phase, or time range.

4. **Activity Search**: Add search functionality to find specific activities.

5. **Metrics Dashboard**: Add Prometheus/Grafana metrics for SSE connection counts, message rates, etc.

### Known Limitations

1. **SCAR Availability**: System requires SCAR to be running. When SCAR is down, users see errors but no graceful fallback.

2. **Database Dependency**: SSE feed requires database connection. If database is down, streaming fails.

3. **Browser Limits**: Browsers limit EventSource connections (typically 6 per domain). Opening many tabs may hit this limit.

4. **No Persistence**: If user refreshes page, activity history is limited to database records (no client-side persistence).
