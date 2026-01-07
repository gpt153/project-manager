# Phase 2 Implementation Summary: Topic Segmentation

## Overview

Phase 2 implements a complete topic segmentation system to prevent PM from losing context mid-conversation and hallucinating about old topics. This phase builds on Phase 1's quick wins (recency weighting and topic change detection) by introducing database-backed conversation topics.

## Implementation Date

January 7, 2026

## Changes Made

### 1. Database Schema Changes

#### New Model: `ConversationTopic`

**File:** `src/database/models.py`

Added new `ConversationTopic` model to track conversation segments:

```python
class ConversationTopic(Base):
    """Tracks conversation topic segments within a project"""

    __tablename__ = "conversation_topics"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    topic_title = Column(String(255), nullable=True)
    topic_summary = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
```

**Key Features:**
- Tracks when topics start and end
- Only one topic can be active per project at a time
- Supports optional title and summary for each topic

#### Updated Model: `ConversationMessage`

Added `topic_id` foreign key to link messages to topics:

```python
topic_id = Column(PGUUID(as_uuid=True), ForeignKey("conversation_topics.id"), nullable=True)
```

**Migration Safety:**
- `topic_id` is nullable for backward compatibility
- Existing messages without topics will continue to work

#### Updated Model: `Project`

Added relationship to topics:

```python
conversation_topics = relationship(
    "ConversationTopic", back_populates="project", cascade="all, delete-orphan"
)
```

### 2. Database Migration

**File:** `src/database/migrations/versions/20260107_1131_add_conversation_topics.py`

Created Alembic migration to:
- Create `conversation_topics` table
- Add `topic_id` column to `conversation_messages`
- Create foreign key constraints
- Add performance indexes

**Indexes Created:**
- `ix_conversation_topics_project_id_active` - Fast lookup of active topics
- `ix_conversation_messages_topic_id` - Fast filtering by topic

**Rollback Support:**
- Full `downgrade()` function implemented
- Can safely roll back if issues arise

### 3. Topic Manager Service

**File:** `src/services/topic_manager.py` (NEW)

Implemented comprehensive topic management service with the following functions:

#### `get_active_topic(session, project_id)`
- Returns the currently active topic for a project
- Returns None if no active topic exists

#### `create_new_topic(session, project_id, title=None, summary=None)`
- Creates a new conversation topic
- Automatically ends the previous active topic
- Sets timestamps appropriately

#### `should_create_new_topic(session, project_id, user_message)`
- Detects when a new topic should be created
- Checks for explicit topic switch phrases:
  - "new topic"
  - "let's discuss"
  - "but we weren't discussing"
  - "we were talking about"
  - And more...
- Checks for time gaps (>1 hour since last message)

#### `generate_topic_title(session, topic_id)`
- Generates a descriptive title based on the first user message
- Fallback to "Untitled Topic" if no messages

**Detection Logic:**

1. **Explicit Phrases:** Detects when user explicitly switches topics
2. **Time Gaps:** Creates new topic if >1 hour since last message
3. **User Corrections:** Recognizes when user corrects PM's context

### 4. Updated Conversation Tools

**File:** `src/agent/tools.py`

#### `save_conversation_message()`

Updated to automatically manage topics:

**For User Messages:**
1. Check if topic switch is needed
2. If yes, create new topic
3. If no, use active topic or create first topic

**For Assistant Messages:**
- Always use the current active topic
- Ensures responses stay in the right context

**New Parameters:**
- `topic_id` (optional): Manually specify topic
- Auto-detects if not provided

#### `get_conversation_history()`

Enhanced with topic filtering:

**New Parameters:**
- `topic_id`: Filter by specific topic
- `active_topic_only`: Only return messages from active topic

**Behavior:**
- When `active_topic_only=True`, only returns current topic messages
- Prevents context bleeding from old topics
- Returns empty list if no active topic

### 5. Updated Orchestrator Agent

**File:** `src/agent/orchestrator_agent.py`

#### `run_orchestrator()`

Updated to use topic-based context:

**Before:**
```python
history_messages = await get_conversation_history(session, project_id, limit=50)
```

**After:**
```python
history_messages = await get_conversation_history(
    session,
    project_id,
    limit=50,
    active_topic_only=True  # Only get current topic
)
```

**Impact:**
- PM now only sees messages from the current topic
- Old topics are isolated and won't contaminate context
- Combined with Phase 1's recency weighting for optimal results

### 6. Comprehensive Test Suite

#### Unit Tests: `tests/services/test_topic_manager.py`

**Coverage:**
- ✅ Getting active topic (exists, doesn't exist, ignores inactive)
- ✅ Creating topics (first topic, ending previous topic)
- ✅ Topic detection (explicit phrases, corrections, time gaps)
- ✅ Title generation (from messages, fallback)
- ✅ Edge cases (multiple active topics)

**Total Tests:** 11 unit tests

#### Integration Tests: `tests/integration/test_topic_switching.py`

**Coverage:**
- ✅ First message creates initial topic
- ✅ Continuing conversation stays in same topic
- ✅ Explicit topic switch creates new topic
- ✅ User correction creates new topic
- ✅ History filtering by topic
- ✅ Assistant messages use active topic
- ✅ Multiple topic switches
- ✅ Context isolation prevents bleeding

**Total Tests:** 10 integration tests

**Critical Test:**
`test_context_isolation_prevents_bleeding()` - Reproduces the exact scenario from issue #56 (SSE feed vs chat features) and verifies it's fixed

## How It Works

### Automatic Topic Management

1. **User sends first message** → Creates "Initial Conversation" topic
2. **Continuing conversation** → Messages stay in same topic
3. **User says "let's discuss X"** → Creates new topic, ends previous
4. **User corrects PM** → Creates new topic, ends previous
5. **Time gap >1 hour** → Next message creates new topic

### Context Retrieval

**Old Behavior (Pre-Phase 2):**
```
Get last 50 messages across ALL topics
↓
PM sees messages from days/weeks ago
↓
Context confusion and hallucination
```

**New Behavior (Phase 2):**
```
Get messages from ACTIVE TOPIC ONLY
↓
PM only sees current conversation
↓
No context bleeding, stays focused
```

### Topic Lifecycle

```
CREATED → ACTIVE → ENDED
   ↓         ↓         ↓
Started   Messages   Ended
  At      Added       At
```

Only one topic is `ACTIVE` at a time per project.

## Benefits

### 1. Eliminates Context Bleeding

**Problem:** PM referenced SSE feed discussion when user was talking about chat features

**Solution:** Each topic is isolated. When topic switches, old messages are no longer in context.

### 2. Maintains Long-term History

**Problem:** Need to preserve conversation history

**Solution:** Old topics are saved, just not included in active context. Can be retrieved later if needed.

### 3. Automatic Detection

**Problem:** User shouldn't have to manually reset

**Solution:** System automatically detects topic changes based on:
- Explicit phrases
- User corrections
- Time gaps

### 4. Graceful Degradation

**Problem:** What if detection fails?

**Solution:**
- Phase 1 recency weighting still helps
- User can use `/reset` command (Phase 3)
- `topic_id` is nullable, so old code still works

## Migration Path

### For Existing Projects

**Option 1: Lazy Migration (Recommended)**
- Existing messages have `topic_id = NULL`
- First new message creates "Initial Conversation" topic
- Future messages use the topic system
- No data loss, gradual migration

**Option 2: Backfill Migration**
- Run migration script to create topics from existing messages
- Group by time gaps or conversation patterns
- More work but cleaner data

### Running the Migration

```bash
# From project root
alembic upgrade head

# To rollback
alembic downgrade -1
```

**Migration ID:** `20260107_1131`

## Testing

### Running Tests

```bash
# Unit tests only
pytest tests/services/test_topic_manager.py -v

# Integration tests only
pytest tests/integration/test_topic_switching.py -v

# All topic-related tests
pytest tests/services/test_topic_manager.py tests/integration/test_topic_switching.py -v
```

### Test Database

Tests use `project_orchestrator_test` database (configurable via `TEST_DATABASE_URL` env var).

### Coverage

- **Unit Tests:** 11 tests covering all topic_manager functions
- **Integration Tests:** 10 tests covering end-to-end workflows
- **Critical Path:** Context isolation and topic switching verified

## Deployment Checklist

### Pre-Deployment

- [x] Database schema updated
- [x] Migration created and tested
- [x] Service layer implemented
- [x] Tools updated
- [x] Orchestrator updated
- [x] Unit tests written and passing
- [x] Integration tests written and passing
- [ ] Migration tested on staging database

### Deployment Steps

1. **Backup production database**
   ```bash
   pg_dump project_orchestrator > backup_before_phase2.sql
   ```

2. **Run migration**
   ```bash
   alembic upgrade head
   ```

3. **Verify migration**
   ```sql
   SELECT COUNT(*) FROM conversation_topics;
   SELECT COUNT(*) FROM conversation_messages WHERE topic_id IS NOT NULL;
   ```

4. **Deploy code**
   - Deploy updated application code
   - Restart services

5. **Monitor**
   - Watch for topic creation
   - Verify context isolation
   - Check for errors

### Rollback Plan

If issues arise:

```bash
# Rollback migration
alembic downgrade -1

# Restore backup if needed
psql project_orchestrator < backup_before_phase2.sql

# Revert code deployment
git revert <commit-hash>
```

## Metrics to Monitor

### Success Indicators

1. **Topic Creation Rate**
   - Should see new topics on topic switches
   - Shouldn't see excessive topic creation

2. **Context Accuracy**
   - User doesn't have to correct PM about topic
   - Target: >95% of conversations stay on-topic

3. **Hallucination Reduction**
   - PM doesn't reference wrong/old topics
   - Target: <5% of responses reference wrong context

### Queries for Monitoring

```sql
-- Active topics per project
SELECT project_id, COUNT(*)
FROM conversation_topics
WHERE is_active = true
GROUP BY project_id;

-- Messages per topic
SELECT topic_id, COUNT(*)
FROM conversation_messages
WHERE topic_id IS NOT NULL
GROUP BY topic_id
ORDER BY COUNT(*) DESC;

-- Topic switches per day
SELECT DATE(started_at), COUNT(*)
FROM conversation_topics
GROUP BY DATE(started_at)
ORDER BY DATE(started_at) DESC;
```

## Known Limitations

### 1. No Cross-Topic References

**Current:** Topics are completely isolated

**Future:** Could allow PM to reference related topics when relevant

### 2. Simple Title Generation

**Current:** Uses first 5 words of first message

**Future:** Use LLM to generate descriptive titles

### 3. Manual Topic Navigation Not Implemented

**Current:** Can only be in one (active) topic

**Future (Phase 3+):** UI to browse and switch between topics

## Next Steps (Phase 3)

1. **Implement `/reset` command**
   - Backend API endpoint
   - WebSocket handler
   - Telegram bot command
   - Frontend UI

2. **Enhanced topic management**
   - LLM-generated topic titles
   - Topic summaries
   - Topic navigation UI

3. **Cross-topic features**
   - Reference old topics when relevant
   - Topic merging
   - Topic search

## Files Changed

### Core Implementation
- `src/database/models.py` - Added ConversationTopic, updated ConversationMessage
- `src/services/topic_manager.py` - NEW: Topic management service
- `src/agent/tools.py` - Updated save/get conversation functions
- `src/agent/orchestrator_agent.py` - Updated to use active_topic_only

### Database
- `src/database/migrations/versions/20260107_1131_add_conversation_topics.py` - NEW: Migration

### Tests
- `tests/services/test_topic_manager.py` - NEW: Unit tests
- `tests/integration/test_topic_switching.py` - NEW: Integration tests

## Acceptance Criteria

### From IMPLEMENTATION_PLAN.md

- [x] Database schema includes `conversation_topics` table
- [x] Messages automatically assigned to topics
- [x] Topic switches create new topic entries
- [x] Context queries only use active topic
- [ ] Migration runs cleanly on production (pending deployment)
- [ ] Existing projects migrated successfully (pending deployment)

## Conclusion

Phase 2 successfully implements topic segmentation to solve the core issue of PM losing context mid-conversation. The implementation is:

- ✅ **Backward compatible** - nullable topic_id
- ✅ **Well-tested** - 21 tests covering all scenarios
- ✅ **Automatic** - no user intervention needed
- ✅ **Reversible** - full downgrade support
- ✅ **Performant** - indexed queries

Combined with Phase 1's recency weighting and topic detection, this provides a robust solution to prevent context bleeding and hallucination.

The system is ready for deployment to staging for real-world testing.
