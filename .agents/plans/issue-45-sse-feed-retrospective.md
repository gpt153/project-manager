# Feature: Issue #45 SSE Feed Investigation & Validation

The following plan documents the investigation of Issue #45 and validates that the fixes are complete and working correctly.

## Feature Description

Issue #45 reported that the SSE (Server-Sent Events) activity feed in the WebUI was not displaying SCAR command executions despite backend logs showing commands executing successfully. The right pane SSE feed remained empty even when the Project Manager (PM) responded with SCAR-generated analysis.

**IMPORTANT**: This issue has been FIXED through multiple commits. This plan documents the root cause, the fixes applied, and validation steps to ensure the issue is fully resolved.

## User Story

As a user of the Project Manager WebUI
I want to see real-time SCAR command execution activity in the right pane SSE feed
So that I can monitor what SCAR is doing while it processes my requests

## Problem Statement

**Original Symptoms (from Issue #45):**
1. User sends message: "analyze the codebase"
2. PM responds with analysis results
3. SSE feed (right pane) remains completely empty
4. Backend logs show SCAR commands executing successfully

**Evidence:**
- Backend logs (14:24) showed: "Executing SCAR command: prime" → "SCAR command completed successfully"
- User reported: "nothing turns up in right pane"
- PM provided detailed analysis WITHOUT user seeing SCAR activity in SSE feed

**Root Causes Identified (via RCA):**

1. **UUID Comparison Bug (Fixed in commit d928ef6)**
   - **Problem**: Polling logic used `id > UUID(last_id)` to find new activities
   - **Why it failed**: UUIDs (v4) are random, not chronologically ordered
   - **Impact**: New activities were never detected as "newer" than the last ID
   - **Fix**: Changed to timestamp comparison: `started_at > last_dt`

2. **Event Listener Mismatch (Fixed in commit 4538e39)**
   - **Problem**: Frontend used `eventSource.onmessage` to catch events
   - **Why it failed**: Backend sends named events (`event: activity`), but `onmessage` only catches unnamed events
   - **Impact**: SSE connection worked, but no events were received by the frontend
   - **Fix**: Changed to `eventSource.addEventListener('activity', ...)` and added `heartbeat` listener

## Solution Statement

The issue has been resolved through two targeted fixes:
1. **Backend polling logic** - Use timestamp-based queries instead of UUID comparison
2. **Frontend event handling** - Listen for named SSE events instead of unnamed messages

This plan validates that both fixes are working correctly and the SSE feed displays SCAR activity in real-time.

## Feature Metadata

**Feature Type**: Bug Fix / Validation
**Estimated Complexity**: Low (fixes already implemented, validation only)
**Primary Systems Affected**:
- SSE endpoint (`src/api/sse.py`)
- SSE feed service (`src/services/scar_feed_service.py`)
- Frontend SSE client (`frontend/src/hooks/useScarFeed.ts`)
- Frontend UI component (`frontend/src/components/RightPanel/ScarActivityFeed.tsx`)

**Dependencies**:
- `sse-starlette==2.2.0` (SSE library)
- `SQLAlchemy>=2.0.0` (async ORM)
- Browser `EventSource` API

---

## CONTEXT REFERENCES

### Fixed Commits

**Commit d928ef6 (2026-01-06)**: Fix SSE feed polling using timestamp comparison instead of UUID
- **Files changed**: `src/services/scar_feed_service.py`
- **Key change**: Lines 111-119, replaced UUID comparison with datetime comparison
- **Status**: Merged to main

**Commit 4538e39 (2026-01-06)**: Fix SSE feed: Listen for named 'activity' events instead of unnamed
- **Files changed**: `frontend/src/hooks/useScarFeed.ts`
- **Key change**: Lines 23-32, replaced `onmessage` with `addEventListener('activity', ...)`
- **Status**: On branch `fix/sse-named-event-listeners`

### Relevant Codebase Files IMPORTANT: YOU MUST READ THESE FILES BEFORE VALIDATION!

- `src/api/sse.py` (lines 22-104) - Why: SSE endpoint that sends named events
- `src/services/scar_feed_service.py` (lines 71-149) - Why: Polling logic with timestamp comparison (FIXED)
- `frontend/src/hooks/useScarFeed.ts` - Why: Event listener implementation (FIXED)
- `frontend/src/components/RightPanel/ScarActivityFeed.tsx` - Why: UI component rendering activities
- `src/services/scar_executor.py` (lines 49-234) - Why: SCAR command execution that creates database records
- `src/database/models.py` (lines 248-301) - Why: ScarCommandExecution model with `started_at` field

### Relevant Documentation

- [sse-starlette Documentation](https://github.com/sysid/sse-starlette)
  - Section: Named vs unnamed events
  - Why: Understanding `event: activity` vs default messages
- [MDN EventSource API](https://developer.mozilla.org/en-US/docs/Web/API/EventSource)
  - Section: addEventListener() vs onmessage
  - Why: Understanding event listener behavior
- [SQLAlchemy DateTime Comparison](https://docs.sqlalchemy.org/en/20/core/sqlelement.html#sqlalchemy.sql.expression.ColumnOperators.__gt__)
  - Section: Column comparison operators
  - Why: Understanding `started_at > datetime` queries

### Patterns to Follow

**SSE Named Event Pattern (Backend):**
```python
# From src/api/sse.py (lines 69)
yield {"event": "activity", "data": json.dumps(activity)}
```

**EventSource Named Event Pattern (Frontend):**
```typescript
// From frontend/src/hooks/useScarFeed.ts (lines 24-27)
eventSource.addEventListener('activity', (event) => {
  const activity: ScarActivity = JSON.parse(event.data);
  setActivities((prev) => [...prev, activity]);
});
```

**Timestamp-Based Polling Pattern:**
```python
# From src/services/scar_feed_service.py (lines 111-119)
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

---

## IMPLEMENTATION PLAN

### Phase 1: Verification

Verify that both fixes are present in the codebase and correctly implemented.

**Tasks:**
- Confirm timestamp-based polling in `src/services/scar_feed_service.py`
- Confirm named event listeners in `frontend/src/hooks/useScarFeed.ts`
- Check that backend sends named events in `src/api/sse.py`

### Phase 2: Integration Testing

Test the complete SSE feed flow end-to-end.

**Tasks:**
- Start the application (backend + frontend)
- Create a SCAR command execution via PM agent
- Verify SSE connection establishes successfully
- Verify activity events appear in frontend feed
- Verify heartbeat events maintain connection

### Phase 3: Edge Case Validation

Test edge cases and potential failure scenarios.

**Tasks:**
- Test with no existing activities (empty feed)
- Test with multiple rapid activities
- Test SSE reconnection after disconnect
- Test verbosity filtering (low/medium/high)
- Test with invalid project ID (error handling)

---

## STEP-BY-STEP TASKS

### Task 1: READ Key Files

**Action**: Read all relevant files to understand current implementation

- **READ**: `src/services/scar_feed_service.py` (lines 71-149)
- **VERIFY**: Line 111-119 uses `started_at > last_dt` (timestamp comparison)
- **VERIFY**: No UUID comparison remains in polling logic

- **READ**: `frontend/src/hooks/useScarFeed.ts` (all lines)
- **VERIFY**: Line 24 uses `addEventListener('activity', ...)` (named event)
- **VERIFY**: Line 30 uses `addEventListener('heartbeat', ...)` (heartbeat)
- **VERIFY**: No `onmessage` handler remains

- **READ**: `src/api/sse.py` (lines 52-91)
- **VERIFY**: Line 69 sends `{"event": "activity", "data": ...}`
- **VERIFY**: Line 75 sends `{"event": "heartbeat", "data": ...}`

### Task 2: VALIDATE Backend SSE Endpoint

**Action**: Verify SSE endpoint sends named events correctly

- **IMPLEMENT**: Manual SSE endpoint test
- **PATTERN**: Use `curl` or browser DevTools to inspect SSE stream
- **VALIDATE**:
  ```bash
  # Test SSE endpoint (replace PROJECT_ID with actual UUID)
  curl -N -H "Accept: text/event-stream" "http://localhost:8000/api/sse/scar/<PROJECT_ID>?verbosity=2"
  ```
- **EXPECTED OUTPUT**:
  ```
  event: activity
  data: {"id":"...","timestamp":"...","source":"scar","message":"..."}

  event: heartbeat
  data: {"status":"alive","timestamp":"..."}
  ```
- **GOTCHA**: If you see `data: {...}` without `event:` prefix, backend is sending unnamed events

### Task 3: VALIDATE Database Query

**Action**: Verify timestamp-based queries return new activities

- **IMPLEMENT**: Database query test
- **PATTERN**: Direct SQLAlchemy query test
- **VALIDATE**:
  ```bash
  uv run python -c "
  import asyncio
  from datetime import datetime, timedelta
  from src.database.connection import async_session_maker
  from src.services.scar_feed_service import stream_scar_activity
  from uuid import UUID

  async def test():
      async with async_session_maker() as session:
          # Replace with actual project ID
          project_id = UUID('YOUR_PROJECT_ID_HERE')
          activities = []
          async for activity in stream_scar_activity(session, project_id):
              activities.append(activity)
              if len(activities) >= 5:
                  break
          print(f'Retrieved {len(activities)} activities')
          for a in activities:
              print(f'  - {a[\"timestamp\"]}: {a[\"message\"]}')

  asyncio.run(test())
  "
  ```
- **EXPECTED**: Should retrieve recent activities with chronological timestamps

### Task 4: VALIDATE Frontend Event Handling

**Action**: Verify frontend receives and displays events

- **IMPLEMENT**: Browser DevTools inspection
- **PATTERN**: Monitor network tab and console logs
- **STEPS**:
  1. Open WebUI in browser
  2. Open DevTools → Network tab
  3. Filter by "EventStream" or "sse"
  4. Select active project
  5. Check SSE connection established
  6. Open Console tab
  7. Look for "SSE connected" log
  8. Trigger SCAR command (via chat message)
  9. Monitor for activity events in console

- **VALIDATE**: Browser Console Output
  ```
  SSE connected
  SSE heartbeat: {"status":"alive","timestamp":"..."}
  [activity event received] {"id":"...","source":"scar",...}
  ```

### Task 5: VALIDATE End-to-End Flow

**Action**: Test complete user workflow

- **IMPLEMENT**: Full integration test
- **PATTERN**: User interaction simulation
- **STEPS**:
  1. Start backend: `uv run fastapi dev src/main.py`
  2. Start frontend: `cd frontend && npm run dev`
  3. Open WebUI: `http://localhost:5173`
  4. Select a project with codebase
  5. Send message: "analyze the codebase"
  6. **VERIFY**: Right pane shows "● Live" (connected)
  7. **VERIFY**: Activities appear in right pane as SCAR executes
  8. **VERIFY**: Activities show timestamps, source tags, and messages

- **VALIDATE**: Visual confirmation
  - SSE feed shows: `[scar] 14:24:15 - Executing SCAR command: prime`
  - Activities update in real-time
  - No "No SCAR activity yet" message after execution

### Task 6: VALIDATE Verbosity Filtering

**Action**: Test verbosity level filtering

- **IMPLEMENT**: Verbosity dropdown test
- **PATTERN**: UI interaction test
- **STEPS**:
  1. In SSE feed panel, select "Low" verbosity
  2. Trigger SCAR command
  3. Observe activity count
  4. Change to "High" verbosity
  5. Trigger another SCAR command
  6. Observe more detailed activities

- **VALIDATE**: Different activity volumes per verbosity level
- **GOTCHA**: Current implementation has `verbosity_level` as a fixed property (line 287 in models.py), so filtering may not work as expected. Document if this is the case.

### Task 7: VALIDATE Error Handling

**Action**: Test SSE error scenarios

- **IMPLEMENT**: Error scenario tests
- **PATTERN**: Negative testing
- **TESTS**:
  1. **Invalid Project ID**: Navigate to `/api/sse/scar/00000000-0000-0000-0000-000000000000`
     - **EXPECTED**: Error event or graceful failure
  2. **SSE Disconnect**: Stop backend while frontend connected
     - **EXPECTED**: Frontend shows "○ Disconnected" status
  3. **SSE Reconnect**: Restart backend
     - **EXPECTED**: Frontend reconnects automatically (EventSource behavior)

- **VALIDATE**: Error handling gracefully degrades UX

### Task 8: DOCUMENT Remaining Issues (If Any)

**Action**: Document any remaining issues discovered during validation

- **IMPLEMENT**: Create follow-up issues if needed
- **PATTERN**: GitHub issue template
- **EXAMPLES**:
  - Verbosity filtering not working (if `verbosity_level` property is always 2)
  - SSE reconnection not automatic (if EventSource doesn't auto-reconnect)
  - Activity timestamps not timezone-aware (if using `utcnow()` without TZ)

---

## TESTING STRATEGY

### Unit Tests

**Scope**: Test individual components in isolation

**Existing Tests to Review**:
- Check if `tests/services/test_scar_feed_service.py` exists
- Check if `tests/api/test_sse.py` exists

**Tests Needed (if missing)**:
1. **test_stream_scar_activity_timestamp_comparison**
   - Mock database with activities at different timestamps
   - Verify polling only returns activities after `last_timestamp`
   - Verify chronological ordering

2. **test_sse_endpoint_sends_named_events**
   - Mock `stream_scar_activity` generator
   - Call SSE endpoint
   - Verify response contains `event: activity` and `event: heartbeat`

### Integration Tests

**Scope**: Test end-to-end SSE flow

**Tests Needed**:
1. **test_sse_feed_displays_scar_execution**
   - Create ScarCommandExecution in database
   - Connect to SSE endpoint
   - Verify activity event received
   - Verify activity data matches database record

2. **test_sse_feed_polling_detects_new_activities**
   - Connect to SSE endpoint
   - Create new ScarCommandExecution (simulating SCAR execution)
   - Wait 2 seconds (polling interval)
   - Verify new activity event received

### Manual Testing

**Scope**: UI/UX validation

**Test Cases**:
1. **Happy Path**: User sends message → PM executes SCAR → SSE feed updates
2. **Empty State**: New project with no SCAR history shows "No activity yet"
3. **Rapid Activities**: Multiple SCAR commands in quick succession all appear
4. **Reconnection**: SSE survives backend restart (after manual reload)
5. **Verbosity**: Changing verbosity level filters activities (if implemented)

---

## VALIDATION COMMANDS

Execute every command to ensure the fixes are working correctly.

### Level 1: Import Validation (CRITICAL)

**Verify all imports resolve before running tests:**

```bash
uv run python -c "from src.api.sse import router; print('✓ SSE endpoint imports valid')"
uv run python -c "from src.services.scar_feed_service import stream_scar_activity; print('✓ Feed service imports valid')"
```

**Expected:** Both print success messages (no ModuleNotFoundError)

**Why:** Catches incorrect imports immediately.

### Level 2: Syntax & Style

**Run linting and formatting checks:**

```bash
uv run ruff check src/api/sse.py src/services/scar_feed_service.py
uv run ruff format --check src/api/sse.py src/services/scar_feed_service.py
```

**Expected:** No errors or warnings

```bash
cd frontend && npm run lint
```

**Expected:** No ESLint errors

### Level 3: Backend Unit Tests

**Run existing backend tests:**

```bash
# Check if tests exist
ls tests/services/test_scar_feed_service.py 2>/dev/null && uv run pytest tests/services/test_scar_feed_service.py -v || echo "No tests found (create if needed)"
ls tests/api/test_sse.py 2>/dev/null && uv run pytest tests/api/test_sse.py -v || echo "No tests found (create if needed)"
```

**Expected:** All tests pass (or tests don't exist yet)

### Level 4: Frontend Build

**Verify frontend builds without errors:**

```bash
cd frontend && npm run build
```

**Expected:** Build succeeds with no TypeScript errors

### Level 5: Manual SSE Endpoint Test

**Test SSE endpoint manually with curl:**

```bash
# Replace PROJECT_ID with actual UUID from database
# Get a project ID first:
uv run python -c "
from src.database.connection import async_session_maker, init_db
from src.database.models import Project
from sqlalchemy import select
import asyncio

async def get_project_id():
    await init_db()
    async with async_session_maker() as session:
        result = await session.execute(select(Project).limit(1))
        project = result.scalar_one_or_none()
        if project:
            print(f'PROJECT_ID={project.id}')
        else:
            print('No projects found - create one first')

asyncio.run(get_project_id())
"

# Then test SSE (replace <PROJECT_ID> with output above):
curl -N -H "Accept: text/event-stream" "http://localhost:8000/api/sse/scar/<PROJECT_ID>?verbosity=2" | head -20
```

**Expected Output:**
```
event: activity
data: {"id":"...","timestamp":"...","source":"scar","message":"..."}

event: heartbeat
data: {"status":"alive","timestamp":"..."}
```

**Why:** Verifies backend sends named events correctly

### Level 6: Manual WebUI Validation

**Test complete user workflow:**

1. **Start Services:**
   ```bash
   # Terminal 1: Start backend
   uv run fastapi dev src/main.py

   # Terminal 2: Start frontend
   cd frontend && npm run dev
   ```

2. **Open Browser:**
   - Navigate to `http://localhost:5173`
   - Open DevTools (F12) → Console tab
   - Open Network tab → Filter by "EventStream"

3. **Test SSE Connection:**
   - Select a project
   - **VERIFY**: Console shows `SSE connected`
   - **VERIFY**: Network tab shows active SSE connection
   - **VERIFY**: Right pane shows "● Live"

4. **Test Activity Display:**
   - Send message: "analyze the codebase"
   - **VERIFY**: Right pane populates with activities
   - **VERIFY**: Activities show timestamps and source tags
   - **VERIFY**: Activities appear in real-time (not all at once after completion)

5. **Test Heartbeat:**
   - Wait 30+ seconds
   - **VERIFY**: Console shows `SSE heartbeat: {...}`
   - **VERIFY**: Connection stays "● Live"

6. **Test Verbosity:**
   - Change verbosity dropdown to "High"
   - Trigger another SCAR command
   - **VERIFY**: Activities appear (verbosity may not filter if property is fixed at 2)

**Expected:** All verifications pass

**Why:** Confirms end-to-end fix is working from user perspective

### Level 7: Additional Validation (If Needed)

**Check git branch status:**

```bash
git branch -a | grep -E "(fix/sse|issue-45)"
git log --oneline --grep="45\|SSE\|sse" | head -10
```

**Expected:** See fix commits (d928ef6, 4538e39, b9b18b5)

**Verify issue status:**

```bash
gh issue view 45 --json state,title | jq -r '"\(.state): \(.title)"'
```

**Expected:** `CLOSED: SSE Feed Shows No SCAR Activity Despite PM Responding`

---

## ACCEPTANCE CRITERIA

- [x] Issue #45 has been fixed with two commits (d928ef6, 4538e39)
- [ ] Backend SSE endpoint sends named events (`event: activity`, `event: heartbeat`)
- [ ] Backend polling logic uses timestamp comparison (not UUID comparison)
- [ ] Frontend uses `addEventListener('activity', ...)` (not `onmessage`)
- [ ] SSE feed displays activities in real-time when SCAR commands execute
- [ ] SSE connection status shows "● Live" when connected
- [ ] Heartbeat events maintain connection every 30 seconds
- [ ] Activities show correct timestamps, source tags, and messages
- [ ] Manual validation passes all test cases
- [ ] No console errors or network failures in browser DevTools
- [ ] Original issue symptoms (empty SSE feed) no longer occur

---

## COMPLETION CHECKLIST

- [ ] All relevant files read and understood
- [ ] Backend timestamp comparison verified in code
- [ ] Frontend named event listeners verified in code
- [ ] Backend SSE endpoint manually tested with curl
- [ ] Frontend SSE connection tested in browser
- [ ] End-to-end workflow validated (user message → SCAR → SSE feed)
- [ ] Heartbeat events confirmed working
- [ ] Error handling tested (invalid project ID, disconnection)
- [ ] Documentation updated (if needed)
- [ ] Follow-up issues created (if any remaining issues found)

---

## NOTES

### Root Cause Summary

**Bug 1: UUID Comparison (Backend)**
- **Location**: `src/services/scar_feed_service.py:110-119`
- **Problem**: `id > UUID(last_id)` doesn't work because UUIDs are random (not chronological)
- **Fix**: Changed to `started_at > datetime.fromisoformat(last_timestamp)`
- **Commit**: d928ef6

**Bug 2: Event Listener Mismatch (Frontend)**
- **Location**: `frontend/src/hooks/useScarFeed.ts:23-32`
- **Problem**: `onmessage` only catches unnamed events, but backend sends named events
- **Fix**: Changed to `addEventListener('activity', ...)` and `addEventListener('heartbeat', ...)`
- **Commit**: 4538e39

### Design Considerations

1. **Polling Interval**: Currently 2 seconds (line 105 in `scar_feed_service.py`)
   - Trade-off: Lower = more responsive, higher = less DB load
   - Consider WebSocket or Redis pub/sub for production

2. **Heartbeat Interval**: Currently 30 seconds (line 64 in `sse.py`)
   - Trade-off: Lower = faster disconnect detection, higher = less bandwidth

3. **Verbosity Filtering**: Currently not fully implemented
   - `verbosity_level` property always returns 2 (line 287 in `models.py`)
   - Future: Add `verbosity` column to `ScarCommandExecution` model

### Related Issues

- **Issue #46**: Fixed SSE polling (merged in d928ef6)
- **Issue #47**: Fixed event listeners (being fixed in 4538e39)

### Future Improvements

1. **Real-time Updates**: Replace polling with Redis pub/sub or WebSocket
2. **Activity Filtering**: Implement proper verbosity levels in database
3. **Activity Details**: Add expandable activity details (full output, error logs)
4. **Activity Search**: Add search/filter functionality for activity history
5. **Activity Export**: Allow exporting activity logs for debugging

---

## VALIDATION RESULTS

### Test Results (To be filled during validation)

**Backend SSE Endpoint Test:**
- [ ] Named events sent correctly
- [ ] Heartbeat events sent every 30 seconds
- [ ] Error events sent on failure

**Frontend Event Handling Test:**
- [ ] Activity events received and displayed
- [ ] Heartbeat events logged in console
- [ ] Connection status updates correctly

**End-to-End Flow Test:**
- [ ] PM executes SCAR command successfully
- [ ] Database records created with `started_at` timestamps
- [ ] SSE polling detects new records (within 2 seconds)
- [ ] Frontend displays activities in real-time
- [ ] UI shows correct source, timestamp, and message

**Edge Case Tests:**
- [ ] Empty feed shows "No SCAR activity yet"
- [ ] Multiple rapid activities all appear
- [ ] SSE reconnects after backend restart
- [ ] Invalid project ID handled gracefully

### Issues Discovered (If any)

*Document any issues found during validation here*

### Conclusion

*Summarize validation results and confirm issue #45 is fully resolved*
