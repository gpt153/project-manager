# Feature: SSE Feed Complete Diagnostic Fix

The following plan should be complete, but it's important that you validate documentation and codebase patterns before implementing.

Pay special attention to naming of existing utils, types, and models. Import from the right files.

## Feature Description

Fix the persistent SSE (Server-Sent Events) activity feed issue where users cannot see real-time SCAR command execution in the WebUI, despite:
- Backend logs showing successful SCAR executions
- Database records confirming ScarCommandExecution entries
- Previous fixes for timestamp comparison (PR #46) and event listeners (PR #48)

Issue #45 reports the problem persists even after these fixes, indicating a deeper integration issue between the PM agent, SCAR executor, SSE feed service, and frontend hooks.

## User Story

As a user of the Project Manager WebUI
I want to see real-time SCAR command execution activity streaming in the right pane
So that I can monitor what SCAR is doing as it analyzes code, creates plans, and implements features

## Problem Statement

**Current State:**
- User sends message: "analyze the codebase"
- PM agent responds with analysis results
- Right pane SSE feed remains completely EMPTY (no activity shown)
- Backend logs show SCAR execution: "Executing SCAR command: prime" → "SCAR command completed successfully"
- Database has ScarCommandExecution records with COMPLETED status

**Root Cause Hypothesis:**
Based on Issue #45 evidence and RCA report, the problem likely involves:
1. **Agent Tool Invocation**: PM may not consistently invoke execute_scar tool for analysis requests
2. **Database Transaction Isolation**: ScarCommandExecution records may not be visible to SSE polling query
3. **SSE Polling Logic**: Despite timestamp fix, polling may have race conditions or session isolation issues
4. **Frontend Connection**: EventSource may connect before initial activities exist, missing them entirely

**Critical Unknown:** Which component(s) in the chain are failing?

## Solution Statement

Implement comprehensive end-to-end diagnostic logging and targeted fixes:
1. Add detailed logging at EVERY integration point (agent → executor → database → SSE → frontend)
2. Create diagnostic script to validate database visibility and SSE query correctness
3. Fix identified issues in agent prompts, database sessions, or SSE polling logic
4. Add integration test that validates complete flow from agent tool call to frontend reception

## Feature Metadata

**Feature Type**: Bug Fix / Diagnostic Enhancement
**Estimated Complexity**: Medium-High
**Primary Systems Affected**:
- Agent orchestrator (`src/agent/orchestrator_agent.py`)
- Agent prompts (`src/agent/prompts.py`)
- SCAR executor service (`src/services/scar_executor.py`)
- SSE feed service (`src/services/scar_feed_service.py`)
- SSE API endpoint (`src/api/sse.py`)
- Frontend SSE hook (`frontend/src/hooks/useScarFeed.ts`)
- Database connection (`src/database/connection.py`)

**Dependencies**:
- `sse-starlette==2.1.0`
- `sqlalchemy[asyncio]>=2.0.36`
- `pydantic-ai>=0.0.14`
- `fastapi>=0.115.0`
- `asyncpg>=0.30.0`

---

## CONTEXT REFERENCES

### Relevant Codebase Files IMPORTANT: YOU MUST READ THESE FILES BEFORE IMPLEMENTING!

**Agent Layer:**
- `src/agent/orchestrator_agent.py` (lines 269-316) - execute_scar tool definition
  - **Why**: Validates tool is registered and callable
- `src/agent/prompts.py` (lines 1-99) - ORCHESTRATOR_SYSTEM_PROMPT
  - **Why**: Check if prompt guides agent to use execute_scar for "analyze" requests
- `src/agent/tools.py` - AgentDependencies and helper functions
  - **Why**: Understand dependency injection pattern

**Execution Layer:**
- `src/services/scar_executor.py` (lines 49-233) - execute_scar_command function
  - **Why**: Creates ScarCommandExecution, commits to DB, critical integration point
- `src/scar/client.py` - ScarClient implementation
  - **Why**: Understand SCAR API communication

**SSE Streaming Layer:**
- `src/services/scar_feed_service.py` (lines 71-149) - stream_scar_activity generator
  - **Why**: Polling logic that detects new activities (FIXED timestamp comparison in PR #46)
- `src/api/sse.py` (lines 22-104) - SSE endpoint
  - **Why**: EventSourceResponse implementation, session management

**Database Layer:**
- `src/database/models.py` (lines 248-301) - ScarCommandExecution model
  - **Why**: Understand @property methods for source, message, verbosity_level
- `src/database/connection.py` - async_session_maker configuration
  - **Why**: Check expire_on_commit setting and session isolation

**Frontend Layer:**
- `frontend/src/hooks/useScarFeed.ts` - EventSource hook
  - **Why**: Verify event listener for 'activity' events (FIXED in PR #48)
- `frontend/src/components/RightPanel/ScarActivityFeed.tsx` - Display component
  - **Why**: Understand rendering logic

### Recent Fixes (Already Applied)

**PR #46 (Commit d928ef6)**: Fixed SSE polling timestamp comparison
- **Problem**: Used UUID comparison (UUIDs not chronological)
- **Solution**: Changed to `started_at > last_dt`
- **Status**: ✅ Merged

**PR #48 (Commit 8d8ceb3)**: Fixed frontend event listener
- **Problem**: Listened for unnamed message events instead of named 'activity' events
- **Solution**: Added `eventSource.addEventListener('activity', ...)`
- **Status**: ✅ Merged

**PR #41 (Commit 00f82a5)**: Added direct SCAR execution tool
- **Feature**: Added execute_scar tool to orchestrator_agent
- **Status**: ✅ Merged

### Issue #45 Evidence

**User Report**:
- User: "analyze the codebase"
- PM responds with detailed analysis
- Right pane: COMPLETELY EMPTY

**Backend Logs (14:24)**:
```
2026-01-06 14:24:15 - Executing SCAR command: prime
2026-01-06 14:24:15 - SCAR command sent successfully
2026-01-06 14:24:21 - SCAR command completed successfully
```

**Database Query Result**:
```sql
SELECT started_at, command_type, status FROM scar_executions
WHERE project_id = '4d5457c9-4cd2-4bba-9b95-5fc84d3c126d'
ORDER BY started_at DESC LIMIT 3;

         started_at         | command_type |  status
----------------------------+--------------+-----------
 2026-01-06 14:34:34.704289 | PRIME        | COMPLETED  ✅
 2026-01-06 14:34:28.314875 | PRIME        | COMPLETED  ✅
 2026-01-06 14:24:36.036443 | PRIME        | COMPLETED  ✅
```

**Conclusion**: Data exists in database but SSE feed doesn't show it to user.

### Relevant Documentation

- [MDN EventSource API](https://developer.mozilla.org/en-US/docs/Web/API/EventSource#named_events) - Named events pattern
- [sse-starlette](https://github.com/sysid/sse-starlette) - Event generator pattern
- [SQLAlchemy Async Sessions](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#asyncio-session) - Session isolation
- [PydanticAI Tools](https://ai.pydantic.dev/tools/) - Tool registration

### Patterns to Follow

**Logging**: `logger.info("msg", extra={"key": val})`
**Async Session**: `async with async_session_maker() as session: await session.commit()`
**Error Handling**: Try/except with status updates, commit on each state change

---

## IMPLEMENTATION PLAN

### Phase 1: Diagnostic Instrumentation

Add comprehensive logging to identify WHERE the chain breaks.

**Objective**: Log every step from agent tool call → database commit → SSE query → frontend reception

### Phase 2: Root Cause Identification

Run diagnostic script and analyze logs to pinpoint exact failure point.

**Objective**: Determine which component(s) are failing

### Phase 3: Targeted Fixes

Implement fixes based on Phase 2 findings.

**Objective**: Fix identified issues without breaking working components

### Phase 4: Integration Testing

Create end-to-end test that validates complete flow.

**Objective**: Prevent regression, ensure fix works for all SCAR commands

---

## STEP-BY-STEP TASKS

IMPORTANT: Execute tasks sequentially. Each task has validation commands.

### Phase 1: Diagnostic Instrumentation

#### TASK 1: ADD diagnostic logging to orchestrator_agent execute_scar tool

- **FILE**: `src/agent/orchestrator_agent.py` (lines 269-316)
- **IMPLEMENT**: Add 3 log statements: tool invoked, before service call, after service call
- **LOGS**: `🔧 DIAGNOSTIC: execute_scar tool INVOKED`, `📞 Calling execute_scar_command`, `✅ execute_scar_command returned`
- **VALIDATE**: `uv run python -c "from src.agent.orchestrator_agent import execute_scar; print('✓')"`

#### TASK 2: ADD diagnostic logging to scar_executor.execute_scar_command

- **FILE**: `src/services/scar_executor.py` (lines 49-233)
- **IMPLEMENT**: Add 4 log statements tracking DB commits
- **LOGS**: After line 93: `💾 created (NOT COMMITTED)`, after commit: `✅ COMMITTED`, after line 138: `💾 COMPLETED (NOT COMMITTED)`, after final commit: `✅ COMPLETED and COMMITTED`
- **VALIDATE**: `uv run python -c "from src.services.scar_executor import execute_scar_command; print('✓')"`

#### TASK 3: ADD diagnostic logging to SSE feed service polling

- **FILE**: `src/services/scar_feed_service.py` (lines 71-149)
- **IMPLEMENT**: Add 4 log statements: initial load, poll cycle (debug), new activities detected, yielding activity
- **LOGS**: `📊 Initial activities loaded`, `🔄 Polling` (debug), `🆕 New activities detected`, `📤 Yielding activity`
- **VALIDATE**: `uv run python -c "from src.services.scar_feed_service import stream_scar_activity; print('✓')"`

#### TASK 4: ADD diagnostic logging to SSE endpoint

- **FILE**: `src/api/sse.py` (lines 22-104)
- **IMPLEMENT**: Add 2 log statements: session created, sending event
- **LOGS**: `🔌 SSE session created`, `📡 Sending SSE event` (debug)
- **VALIDATE**: `uv run python -c "from src.api.sse import router; print('✓')"`

#### TASK 5: CREATE diagnostic script

- **FILE**: `scripts/diagnose_sse_feed.py` (NEW)
- **IMPLEMENT**: Script to validate DB queries and @property methods
- **FEATURES**: Total executions count, recent 10, simulate polling query, validate @property methods, session isolation check
- **USAGE**: `uv run python scripts/diagnose_sse_feed.py <project_id>`
- **VALIDATE**: `uv run python -c "import scripts.diagnose_sse_feed; print('✓')"`

**Script checks**: Total executions, recent 10, polling query simulation, @property validation, session settings


### Phase 2: Root Cause Identification

#### TASK 6: RUN diagnostic script

- **EXECUTE**: Get project ID from DB, run `uv run python scripts/diagnose_sse_feed.py <id>`
- **ANALYZE**: Validate DB records exist, timestamp query works, @property methods OK, session settings correct

#### TASK 7: TRIGGER SCAR execution and monitor

- **START**: Backend with `LOG_LEVEL=DEBUG`, monitor logs with `tail -f | grep DIAGNOSTIC`
- **TEST**: Send "analyze the codebase", observe all checkpoints: tool invoked, service called, created, committed, completed, SSE loaded, detected, yielding, sending
- **VALIDATE**: Every diagnostic log appears in correct order

#### TASK 8: IDENTIFY failure point

- **ANALYZE**: Missing logs indicate failure point - tool not invoked → fix prompts; not committed → fix executor; not detected → fix polling/session; not sending → fix stream; all present but frontend empty → fix EventSource
- **DOCUMENT**: Record findings in `.agents/diagnostics/sse-feed-failure-point.txt`

### Phase 3: Targeted Fixes

#### TASK 9: FIX identified issues (conditional)

**If agent not calling tool**: Update `src/agent/prompts.py` line 49 to be more explicit: "analyze/prime/load codebase → IMMEDIATELY call execute_scar('prime')"

**If session isolation**: Check `src/database/connection.py` has `expire_on_commit=False`

**If polling query**: Validate `src/services/scar_feed_service.py` line 116 uses `started_at > last_dt` (should already be fixed PR #46)

**If frontend**: Validate `frontend/src/hooks/useScarFeed.ts` line 24 uses `addEventListener('activity', ...)` (should already be fixed PR #48)

#### TASK 10: ADD flush to ensure DB visibility

- **FILE**: `src/services/scar_executor.py` line 94
- **ADD**: `await session.flush()` after commit for immediate visibility
- **VALIDATE**: `uv run python -c "from src.services.scar_executor import execute_scar_command; print('✓')"`

### Phase 4: Integration Testing

#### TASK 11: CREATE integration test

- **FILE**: `tests/integration/test_sse_feed_integration.py` (NEW)
- **IMPLEMENT**: E2E test: create project → call execute_scar tool → verify DB record → stream SSE → collect activities within 5s → validate structure
- **PATTERN**: Mirror `tests/services/test_scar_executor.py`
- **KEY ASSERTIONS**: Tool succeeds, DB has records, SSE stream yields within timeout, activity has id/timestamp/source/message
- **VALIDATE**: `uv run pytest tests/integration/test_sse_feed_integration.py -v`

#### TASK 12: RUN full test suite

- **EXECUTE**: `uv run pytest tests/ -v && uv run pytest --cov=src --cov-report=term-missing`
- **EXPECTED**: All tests pass, coverage ≥ 80% for modified files

---

## TESTING STRATEGY

**Level 1 - Imports**: `uv run python -c "from src.agent.orchestrator_agent import execute_scar; from src.services.scar_executor import execute_scar_command; from src.services.scar_feed_service import stream_scar_activity; from src.api.sse import router; print('✓')"`

**Level 2 - Unit**: `uv run pytest tests/services/test_scar_executor.py tests/agent/ -v`

**Level 3 - Integration**: `uv run pytest tests/integration/test_sse_feed_integration.py -v`

**Level 4 - Manual**: Start backend, send "analyze the codebase", verify SSE feed populates within 2s, check DIAGNOSTIC logs

**Level 5 - Diagnostic**: Get project ID, run `uv run python scripts/diagnose_sse_feed.py $PROJECT_ID`

---

## VALIDATION COMMANDS

**Level 1 - Import**: `uv run python -c "from src.agent.orchestrator_agent import execute_scar; from src.services.scar_executor import execute_scar_command; from src.services.scar_feed_service import stream_scar_activity; from src.api.sse import router; print('✓')"`

**Level 2 - Syntax**: `uv run ruff check src/ tests/ && uv run ruff format --check src/ tests/ && uv run mypy src/`

**Level 3 - Unit**: `uv run pytest tests/ -v --maxfail=1`

**Level 4 - Integration**: `uv run pytest tests/integration/test_sse_feed_integration.py -v`

**Level 5 - Diagnostic**: Get project ID, run `uv run python scripts/diagnose_sse_feed.py $PROJECT_ID`

**Level 6 - Manual**: Start backend (`export LOG_LEVEL=DEBUG; uv run uvicorn src.main:app --reload`), monitor logs (`tail -f logs/app.log | grep DIAGNOSTIC`), test in browser

---

## ACCEPTANCE CRITERIA

- [ ] Diagnostic logging captures every integration point (agent → executor → DB → SSE → frontend)
- [ ] Diagnostic script validates database queries work correctly
- [ ] Root cause identified and documented in `.agents/diagnostics/sse-feed-failure-point.txt`
- [ ] Targeted fixes implemented based on diagnostic findings
- [ ] Integration test validates complete SSE flow from tool call to stream
- [ ] All unit tests pass (no regressions)
- [ ] Manual testing shows SSE feed populates within 2 seconds of SCAR execution
- [ ] Backend logs show all DIAGNOSTIC checkpoints when user triggers SCAR command
- [ ] Frontend receives and displays activities in real-time
- [ ] Issue #45 reproduction scenario now works correctly

---

## COMPLETION CHECKLIST

- [ ] Phase 1 complete: All diagnostic logging added
- [ ] Phase 2 complete: Root cause identified via diagnostics
- [ ] Phase 3 complete: Targeted fixes implemented
- [ ] Phase 4 complete: Integration test created and passing
- [ ] All validation commands executed successfully
- [ ] Manual E2E test confirms SSE feed works
- [ ] Diagnostic script runs without errors
- [ ] Code reviewed for quality and maintainability
- [ ] No linting or type checking errors
- [ ] Backend logs show complete diagnostic flow
- [ ] Issue #45 marked as resolved

---

## NOTES

**Why Diagnostic-First Approach:**
- Issue #45 persists despite 2 targeted fixes (PR #46, #48)
- Indicates problem is NOT where we think it is
- Comprehensive logging will reveal actual failure point
- Prevents more guesswork fixes that don't solve root cause

**Why Integration Test:**
- Unit tests alone missed this issue
- Need end-to-end validation from agent tool call to SSE reception
- Test acts as regression prevention for future changes

**Potential Root Causes (to investigate):**
1. Agent prompt doesn't trigger execute_scar for "analyze" requests
2. Database session isolation prevents SSE from seeing committed records
3. Race condition: SSE connects BEFORE first execution, polls miss timing
4. Frontend EventSource reconnection resets last_timestamp incorrectly
5. SQLAlchemy session caching returns stale results

**Success Metric:** User sends "analyze the codebase" → SSE feed shows activity within 2 seconds
