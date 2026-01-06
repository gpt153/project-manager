# Root Cause Analysis - Issue #45

**Issue**: SSE Feed shows no SCAR activity despite PM responding to user messages
**Root Cause**: UUID comparison in SSE polling query fails because UUIDs are not chronologically sequential
**Severity**: Critical (completely breaks real-time activity feed)
**Confidence**: High (proven with database queries and UUID comparison tests)

## Evidence Chain

### The Path from Symptom to Cause

**SYMPTOM**: User sends "analyze the codebase" at 14:35, PM responds with analysis, but SSE feed (right pane) remains empty

↓ **BECAUSE**: SSE feed stream doesn't detect new SCAR activities created at 14:34

**Evidence**: Database shows activities exist but weren't streamed:
```sql
SELECT started_at, command_type, status FROM scar_executions
WHERE project_id = '4d5457c9-4cd2-4bba-9b95-5fc84d3c126d'
ORDER BY started_at DESC LIMIT 3;

         started_at         | command_type |  status
----------------------------+--------------+-----------
 2026-01-06 14:34:34.704289 | PRIME        | COMPLETED  ✅ EXISTS
 2026-01-06 14:34:28.314875 | PRIME        | COMPLETED  ✅ EXISTS
 2026-01-06 14:24:36.036443 | PRIME        | COMPLETED
```

---

**WHY**: SSE polling query doesn't find new activities after initial load

↓ **BECAUSE**: Query uses UUID comparison to detect "newer" activities

**Evidence**: `src/services/scar_feed_service.py:110-117`
```python
if last_id:
    query = (
        select(ScarCommandExecution)
        .where(
            ScarCommandExecution.project_id == project_id,
            ScarCommandExecution.id > UUID(last_id),  # ❌ UUID COMPARISON
        )
        .order_by(ScarCommandExecution.started_at.asc())
    )
```

---

**WHY**: UUID comparison fails to identify chronologically newer records

↓ **BECAUSE**: UUIDs are not sequential - lexicographic comparison != chronological order

**Evidence**: PostgreSQL UUID comparison test:
```sql
-- Activity IDs from database:
-- 14:24:36 → b7b27e8d-e5e4-45e7-8b38-b9f4f5bc60f0 (OLD, streamed initially)
-- 14:34:28 → 2e71579b-a74b-4464-92d5-cafc683ca2fa (NEW, should stream)
-- 14:34:34 → be352919-0425-47d8-9dd8-2d6ae4428834 (NEW, should stream)

SELECT
  '2e71579b-...'::uuid > 'b7b27e8d-...'::uuid AS newer_28_detected,
  'be352919-...'::uuid > 'b7b27e8d-...'::uuid AS newer_34_detected;

 newer_28_detected | newer_34_detected
-------------------+-------------------
 f                 | t                  ❌ 14:34:28 NOT DETECTED!
```

**Analysis**:
- Activity at 14:34:28 has UUID starting with `2e...`
- Previous activity at 14:24:36 has UUID starting with `b7...`
- Lexicographically: `'2' < 'b'` → comparison returns FALSE
- Activity at 14:34:28 is chronologically NEWER but lexicographically SMALLER
- SSE polling query never returns this activity

---

**ROOT CAUSE**: Line 114 of `src/services/scar_feed_service.py` uses UUID comparison instead of timestamp comparison

**Evidence**: `src/services/scar_feed_service.py:114`
```python
ScarCommandExecution.id > UUID(last_id)  # ❌ WRONG: UUIDs aren't sequential
```

**What it should be**:
```python
ScarCommandExecution.started_at > last_timestamp  # ✅ CORRECT: Timestamps are sequential
```

### Alternative Hypotheses Considered

**Hypothesis A: PM not calling execute_scar tool**
- ❌ RULED OUT: Database shows SCAR executions at 14:34:28 and 14:34:34
- Evidence: Queried `scar_executions` table, records exist with COMPLETED status

**Hypothesis B: SSE endpoint not working at all**
- ❌ RULED OUT: Backend logs show SSE connections established
- Evidence: `2026-01-06 14:24:09 - Starting SCAR activity stream for project 4d5457c9...`

**Hypothesis C: Frontend not displaying SSE data**
- ❌ RULED OUT: Problem is backend not sending data, not frontend not displaying
- Evidence: UUID comparison prevents data from ever reaching event generator

### Git History Context

- **Introduced**: Commit `5a14dc7` - "Phase B.4: SCAR Feed with Verbosity Filtering"
- **Author**: Initial implementation of SSE feed service
- **Recent changes**: Code has not changed since introduction
- **Implication**: This is an **original design bug**, not a regression
- **Impact**: SSE feed has NEVER worked reliably - only works by chance when new UUIDs happen to be lexicographically larger

## Fix Specification

### What Needs to Change

Replace UUID-based polling with timestamp-based polling in the SSE feed service.

**File**: `src/services/scar_feed_service.py:110-117`

**Current logic**:
- Tracks `last_id` (UUID)
- Queries for `id > last_id`
- Fails when new UUID is lexicographically smaller

**Required logic**:
- Track `last_timestamp` (datetime)
- Query for `started_at > last_timestamp`
- Always works because timestamps are sequential

### Implementation Guidance

**Change 1**: Track timestamp instead of ID
```python
# Current (src/services/scar_feed_service.py:92-99)
last_id = None
activities = await get_recent_scar_activity(...)
if activities:
    last_id = activities[-1]["id"]  # ❌ UUID

# Required:
last_timestamp = None
activities = await get_recent_scar_activity(...)
if activities:
    last_timestamp = activities[-1]["timestamp"]  # ✅ Timestamp string
```

**Change 2**: Query by timestamp
```python
# Current (src/services/scar_feed_service.py:110-117)
if last_id:
    query = (
        select(ScarCommandExecution)
        .where(
            ScarCommandExecution.project_id == project_id,
            ScarCommandExecution.id > UUID(last_id),  # ❌ UUID comparison
        )
        .order_by(ScarCommandExecution.started_at.asc())
    )

# Required:
if last_timestamp:
    from datetime import datetime
    last_dt = datetime.fromisoformat(last_timestamp)
    query = (
        select(ScarCommandExecution)
        .where(
            ScarCommandExecution.project_id == project_id,
            ScarCommandExecution.started_at > last_dt,  # ✅ Timestamp comparison
        )
        .order_by(ScarCommandExecution.started_at.asc())
    )
```

**Change 3**: Update tracking variable
```python
# Current (src/services/scar_feed_service.py:145)
last_id = activity_dict["id"]  # ❌ UUID

# Required:
last_timestamp = activity_dict["timestamp"]  # ✅ Timestamp
```

**Key considerations for implementation:**
- Timestamp strings are ISO format (from `activity["timestamp"]`)
- Need to convert to datetime for PostgreSQL comparison
- Handle edge case where `started_at` is NULL (fall back to `completed_at`)
- Keep the initial query unchanged (lines 95-101) - only fix the polling query
- Order by `started_at ASC` remains correct

### Files to Examine

- `src/services/scar_feed_service.py:89-147` - Main polling logic in `stream_scar_activity()`
- `src/database/models.py:ScarCommandExecution` - Confirm `started_at` column exists and is indexed

## Verification

**How to confirm the fix works:**

1. **Deploy the fix** to production

2. **Clear any existing SSE connections** (restart backend or wait for timeout)

3. **Test end-to-end flow**:
   ```
   Step 1: Open PM WebUI for Health Agent project
   Step 2: Open browser DevTools → Network tab → Filter by "eventsource"
   Step 3: Send message: "analyze the codebase"
   Step 4: Watch SSE feed in right pane
   ```

4. **Expected outcome if fixed**:
   - SSE connection establishes
   - Initial activities load (any existing ones)
   - When PM calls execute_scar("prime"), new activity appears in feed
   - Activity shows: "PRIME: COMPLETED" with timestamp
   - No missing activities regardless of UUID values

5. **Test with database query** (confirm all activities appear):
   ```sql
   -- Get activities in order
   SELECT id, started_at, command_type, status
   FROM scar_executions
   WHERE project_id = '<project-id>'
   ORDER BY started_at DESC
   LIMIT 10;

   -- Verify SSE streamed ALL of them (check browser DevTools → Network → EventStream)
   ```

6. **Reproduce original issue to compare**:
   - Before fix: Some activities missing from feed (those with "smaller" UUIDs)
   - After fix: ALL activities appear in feed in chronological order

## Summary

The SSE feed has been broken since its initial implementation. It uses UUID comparison (`id > last_id`) to detect new activities, but UUIDs are not chronologically sequential. When a new activity has a UUID that is lexicographically smaller than the previous one (e.g., `2e...` < `b7...`), it never gets streamed to the frontend.

The fix is straightforward: Replace UUID tracking with timestamp tracking, and compare `started_at > last_timestamp` instead of `id > last_id`. This ensures all chronologically newer activities are always detected and streamed, regardless of their UUID values.
