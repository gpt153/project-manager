# Root Cause Analysis: WebUI Issue #13
**Date**: 2025-12-21
**Issue**: WebUI deployed but missing data and broken functionality
**Status**: Investigation Complete

## Executive Summary

The WebUI is successfully deployed at po.153.se with a working 3-panel layout, but three critical issues prevent it from functioning as intended:

1. **SCAR Activity Feed is broken** - Server error due to code bug
2. **Chat with PM fails** - API error prevents loading conversation history
3. **Missing GitHub Issues integration** - No issues displayed in project navigator
4. **Missing Historical Data** - Only 1 demo project exists, no real project history

## Current State Assessment

### ✅ What Works
- Frontend deployed and accessible at po.153.se
- 3-panel resizable layout renders correctly
- Project Navigator displays projects from database
- WebSocket infrastructure in place
- UI components are implemented

### ❌ What's Broken
- **SCAR feed**: Server error `'<=' not supported between instances of 'property' and 'int'`
- **Chat**: API returns `{"detail":"Failed to retrieve messages"}`
- **Issues**: No issues shown (0 open, 0 closed for all projects)
- **Data**: Only 1 demo project in database, no real projects/history

## Detailed Investigation Findings

### Issue 1: SCAR Activity Feed Crash

**Symptom**: Right panel shows "disconnected", SSE connection fails with error

**Root Cause**: Bug in `/src/services/scar_feed_service.py` line 103

```python
# Line 103 - BROKEN CODE
ScarCommandExecution.verbosity_level <= verbosity_level
```

**Problem**: `verbosity_level` is a `@property` that returns `int`, but SQLAlchemy is trying to use it in a WHERE clause comparison. SQLAlchemy can't translate a Python property into SQL.

**Additional Issue**: Line 106 references `.created_at.asc()` but `ScarCommandExecution` doesn't have a `created_at` column - it has a `@property` that returns `started_at`.

**Fix Required**:
1. Remove `verbosity_level` column filter from query (line 103)
2. Change `created_at` to `started_at` (line 106, 115)
3. Filter verbosity in Python after query if needed

---

### Issue 2: Chat Message Loading Failure

**Symptom**: `/api/projects/{id}/messages` returns HTTP 500 error

**Root Cause**: Unknown - need to check server logs, but likely:
- Database query failure
- Missing conversation_messages records
- Foreign key or relationship issue

**Investigation needed**:
- Check backend logs at deployment
- Test with local database
- Verify `get_conversation_history` function in `project_service.py`

---

### Issue 3: Missing GitHub Issues

**Symptom**: All projects show "Open Issues (0)" and "Closed Issues (0)"

**Root Cause**: No integration between GitHub issues and database

**What's missing**:
1. No GitHub API call to fetch issues for projects with `github_repo_url`
2. No database table to store GitHub issues
3. No sync mechanism to keep issues updated
4. `open_issues_count` and `closed_issues_count` are hardcoded to 0 in service

**Current Implementation**: Projects have `github_repo_url` and `github_issue_number` fields, but:
- No code fetches issues from GitHub
- No code populates issue counts
- Project service returns `0` for all counts

---

### Issue 4: Missing Historical Data

**Symptom**: Only 1 project in database ("WebUI Demo Project")

**Root Cause**: No data migration from existing projects

**What's missing**:
1. Real projects created via Telegram/GitHub aren't in database
2. Historical conversations not migrated
3. SCAR execution history not present
4. Workflow phases not tracked

**Implication**: Even if bugs are fixed, WebUI will appear empty

---

## Gap Analysis: Current vs. Vision

### From Vision Document Analysis

The vision describes a system where:
> "Users can manage multiple projects, communicate with the AI assistant, and observe real-time development activity without juggling multiple tools"

**Current Reality vs. Vision:**

| Vision Feature | Current Status | Gap |
|---------------|----------------|-----|
| Browse ALL projects | ❌ Only 1 demo project | Missing data sync from GitHub/Telegram |
| See open/closed issues | ❌ Always shows 0 | No GitHub issues integration |
| View conversation history | ❌ Crashes | API bug |
| Chat with @po | ⚠️ Infrastructure exists | Messages API broken |
| See SCAR activity feed | ❌ Disconnected | SSE streaming bug |
| View vision docs | ✅ Works | **Complete** |
| View implementation plans | ✅ Works | **Complete** |
| 3-panel layout | ✅ Works | **Complete** |

### Critical Missing Features

From plan document review, these were planned but **not implemented or broken**:

1. **GitHub Issues Integration** (Phase 5 of plan)
   - No API endpoint to fetch issues from GitHub
   - No sync mechanism
   - No database storage for issues

2. **Real Project Data** (Implied in vision)
   - Existing projects from GitHub should be visible
   - Telegram conversations should be synced
   - SCAR activity should be populated

3. **Working Chat** (Phase 6 of plan)
   - WebSocket works but message history fails
   - Orchestrator agent integration appears correct
   - Database query or relationship issue

4. **Working SCAR Feed** (Phase 7 of plan)
   - SSE infrastructure exists
   - Code bugs prevent it from working
   - Even if fixed, no activity to show (empty database)

---

## Root Cause Summary

### Technical Bugs
1. **SSE Bug**: Property vs column confusion in SQLAlchemy query
2. **API Bug**: Message retrieval crashes (needs server log analysis)

### Architecture Gaps
3. **No GitHub Sync**: Missing integration to pull issues from repositories
4. **No Data Migration**: Existing projects not imported into WebUI database

### Design Issues
5. **Decoupled Systems**: Telegram bot and GitHub webhook create data that WebUI can't see
6. **No Unified State**: Three data sources (Telegram, GitHub, Database) not synchronized

---

## Impact Assessment

### User Experience
- **Severity**: Critical
- **User sees**: "Three empty windows" (exactly as described in issue)
- **Can't use**: 2 of 3 panels (chat, SCAR feed) are non-functional
- **Missing data**: Projects, issues, history all absent

### Business Impact
- Vision of "unified workspace" is not realized
- WebUI cannot replace Telegram/GitHub workflow yet
- Demonstrates technical capability but not business value

---

## Recommended Fix Priority

### P0 - Critical (Blocks all usage)
1. Fix SCAR feed SSE bug (10 min fix)
2. Fix chat messages API bug (needs investigation, 30-60 min)

### P1 - High (Severely limits usefulness)
3. Import existing projects from GitHub into database (2-4 hours)
4. Implement GitHub issues fetching (4-6 hours)

### P2 - Medium (Improves experience)
5. Sync Telegram conversation history to database (2-3 hours)
6. Backfill SCAR execution history (if tracked elsewhere) (2-3 hours)

### P3 - Enhancement
7. Real-time sync between Telegram → Database → WebUI
8. Real-time sync between GitHub → Database → WebUI
9. Notifications for new activity

---

## Next Steps

### Immediate Actions (Can fix now)
1. **Fix scar_feed_service.py**:
   - Remove line 103 verbosity filter
   - Change `created_at` to `started_at` on lines 106, 115
   - Test SSE connection

2. **Investigate messages API**:
   - Check server logs for exact error
   - Test `get_conversation_history` function
   - Fix database query

### Short-term Actions (1-2 days)
3. **GitHub Integration**:
   - Add endpoint: `GET /api/projects/{id}/issues`
   - Use `GitHubClient` to fetch issues from repo
   - Cache in database or fetch real-time

4. **Data Import**:
   - Script to import existing GitHub repos as Projects
   - Link projects to their repos
   - Optionally migrate conversation history

### Medium-term Actions (1 week)
5. **Unified State Management**:
   - All project creation → saves to database
   - All messages → save to database
   - All SCAR commands → log to database
   - WebUI reads from single source of truth

---

## Code Changes Required

### File: `src/services/scar_feed_service.py`

**Lines 98-117** - Fix query bugs:

```python
# BEFORE (BROKEN)
if last_id:
    query = (
        select(ScarCommandExecution)
        .where(
            ScarCommandExecution.project_id == project_id,
            ScarCommandExecution.verbosity_level <= verbosity_level,  # ← BROKEN
            ScarCommandExecution.id > UUID(last_id)
        )
        .order_by(ScarCommandExecution.created_at.asc())  # ← BROKEN (no column)
    )
else:
    query = (
        select(ScarCommandExecution)
        .where(
            ScarCommandExecution.project_id == project_id,
            ScarCommandExecution.verbosity_level <= verbosity_level  # ← BROKEN
        )
        .order_by(desc(ScarCommandExecution.created_at))  # ← BROKEN (no column)
        .limit(1)
    )

# AFTER (FIXED)
if last_id:
    query = (
        select(ScarCommandExecution)
        .where(
            ScarCommandExecution.project_id == project_id,
            ScarCommandExecution.id > UUID(last_id)
        )
        .order_by(ScarCommandExecution.started_at.asc())  # ← Use actual column
    )
else:
    query = (
        select(ScarCommandExecution)
        .where(
            ScarCommandExecution.project_id == project_id
        )
        .order_by(desc(ScarCommandExecution.started_at))  # ← Use actual column
        .limit(1)
    )

# Note: Verbosity filtering can be done in Python after query if needed:
# activity_list = [a for a in activities if a.verbosity_level <= verbosity_level]
```

### File: `src/services/project_service.py` (needs investigation)

Need to check `get_conversation_history` function - likely needs:
- Proper error handling
- Correct query syntax
- Relationship loading

### New File Needed: `src/api/github_issues.py`

```python
@router.get("/projects/{project_id}/issues")
async def get_project_issues(
    project_id: UUID,
    state: str = "all",  # all, open, closed
    session: AsyncSession = Depends(get_session)
):
    """Fetch GitHub issues for a project."""
    # 1. Get project from database
    # 2. Extract github_repo_url
    # 3. Use GitHubClient to fetch issues
    # 4. Return formatted list
```

---

## Testing Plan

After fixes:

### Unit Tests
- [ ] Test `stream_scar_activity` without verbosity filter
- [ ] Test `get_conversation_history` with empty/populated database
- [ ] Test GitHub issues endpoint with mock data

### Integration Tests
- [ ] SSE connection stays alive for 60+ seconds
- [ ] WebSocket sends/receives messages
- [ ] Projects API returns correct issue counts

### Manual Tests
- [ ] Open po.153.se in browser
- [ ] Select project → Chat loads
- [ ] Send message → Receive response
- [ ] SCAR feed shows "● Live" status
- [ ] Issues count appears (if GitHub integration added)

---

## Conclusion

**Summary**: The WebUI infrastructure is ~80% complete, but 3 critical bugs and missing data make it appear broken:

1. **Bug**: SCAR feed crashes (easy fix)
2. **Bug**: Messages API crashes (needs investigation)
3. **Gap**: No GitHub issues integration (needs implementation)
4. **Gap**: No project data (needs migration/sync)

**Estimated Fix Time**:
- Bugs: 1-2 hours
- GitHub integration: 4-6 hours
- Data migration: 2-4 hours
- **Total: 7-12 hours** to have a fully functional WebUI

**Recommended Approach**:
1. Fix bugs first (quick wins)
2. Add GitHub issues endpoint
3. Import existing projects
4. Test end-to-end
5. Deploy fixes

This will transform the "three empty windows" into a fully functional project management interface matching the original vision.
