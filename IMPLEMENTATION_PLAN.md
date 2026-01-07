# Implementation Plan: Fix PM Context Loss and Add /reset Command

## Executive Summary

This plan addresses issue #56 where PM loses conversation context mid-chat and hallucinates about old topics. The root cause is inadequate context management in `orchestrator_agent.py`, which treats all recent messages equally without detecting topic changes, user corrections, or recency importance.

## Problem Analysis

### Root Causes Identified

1. **No Recency Weighting** (Line 378 in `orchestrator_agent.py`)
   - Current: `history_messages[:-1][-10:]` treats all 10 messages equally
   - Messages from days ago weighted same as messages from seconds ago
   - No exponential decay based on time or message position

2. **No Topic Boundary Detection**
   - PM doesn't recognize topic switches
   - No detection of explicit user corrections ("but we weren't discussing...")
   - Time gaps between messages ignored

3. **SCAR History Contamination**
   - `get_scar_history` tool provides old, irrelevant executions
   - Auto-triggered PRIME reinforces wrong context
   - Tool outputs bleed into conversation context

4. **Flat Message Storage**
   - No concept of "conversation segments" or "topics"
   - All messages stored in single chronological list
   - No metadata about context switches

### Evidence from Issue

**Timeline:**
- Jan 6 16:25-16:47: Discussion about SSE feed (issue #52)
- Jan 7 10:08-10:34: Discussion about chat UI features
- **Context Loss**: After only 8 messages about chat UI, PM hallucinates back to SSE feed
- **Ignores Correction**: User says "but we weren't discussing the sse feed now" - PM doubles down

**Database Query Results:**
```
10:08:20 USER: "lets discuss a change in the webui..."
10:08:31 PM: "That's a great UX improvement..." ✅
10:29:48 USER: "good. also i always looks like pm is about to reply..."
10:30:01 PM: "Looking at this UI issue..." ✅
10:32:34 USER: "tell me which /commands you would tell scar to use..."
10:32:46 PM: "Based on the conversation context about issue 52..." ❌ HALLUCINATION
10:34:09 USER: "but we werent discussing the sse feed now..."
10:34:31 PM: "Great! Now I can see the detailed SCAR execution..." ❌ IGNORES CORRECTION
```

## Solution Architecture

### Phase 1: Quick Wins (Context Weighting)
**Goal:** Fix immediate context loss without schema changes
**Timeline:** 1-2 days

### Phase 2: Topic Segmentation (Database Schema)
**Goal:** Long-term solution with conversation topic tracking
**Timeline:** 3-5 days

### Phase 3: /reset Command
**Goal:** Allow users to manually clear context
**Timeline:** 1-2 days

## Phase 1: Quick Wins - Context Weighting

### 1.1 Implement Recency Weighting

**File:** `src/agent/orchestrator_agent.py`
**Lines:** 372-387

**Current Code:**
```python
history_context = ""
if len(history_messages) > 1:
    history_context = "\n\n## Recent Conversation History:\n\n"
    for msg in history_messages[:-1][-10:]:  # Last 10 messages
        role_name = "User" if msg.role == MessageRole.USER else "You (PM)"
        history_context += f"**{role_name}**: {msg.content}\n\n"
```

**New Code:**
```python
history_context = ""
if len(history_messages) > 1:
    # Prioritize the most recent 3 turns (6 messages: user + assistant)
    recent_messages = history_messages[-7:-1]  # Last 6 messages before current
    older_messages = history_messages[-21:-7] if len(history_messages) > 7 else []

    history_context = "\n\n## CURRENT CONVERSATION (Most Important):\n\n"
    for msg in recent_messages:
        role_name = "User" if msg.role == MessageRole.USER else "You (PM)"
        history_context += f"**{role_name}**: {msg.content}\n\n"

    if older_messages:
        history_context += "\n\n## Earlier Context (Only If Relevant):\n\n"
        for msg in older_messages[-5:]:  # Max 5 older messages
            role_name = "User" if msg.role == MessageRole.USER else "You (PM)"
            history_context += f"**{role_name}**: {msg.content}\n\n"
```

**Rationale:**
- Last 6 messages (3 turns) get priority section
- Older messages in separate "Only If Relevant" section
- Clear visual hierarchy signals importance to LLM

### 1.2 Add Topic Change Detection

**File:** `src/agent/orchestrator_agent.py`
**New Function:** `detect_topic_change()`

**Location:** Before `run_orchestrator` function (around line 319)

```python
def detect_topic_change(messages: list, current_message: str) -> bool:
    """
    Detect if conversation topic has changed based on explicit signals.

    Args:
        messages: Recent conversation history
        current_message: Current user message to analyze

    Returns:
        True if topic change detected, False otherwise
    """
    # Check for explicit topic corrections
    correction_phrases = [
        "but we weren't discussing",
        "but we werent discussing",
        "we were talking about",
        "not about that",
        "different topic",
        "let's discuss",
        "lets discuss",
        "switching topics",
        "new topic",
        "back to",
    ]

    current_lower = current_message.lower()
    for phrase in correction_phrases:
        if phrase in current_lower:
            return True

    # Check for time gaps (>1 hour between messages)
    if len(messages) >= 2:
        from datetime import datetime, timezone
        last_msg = messages[-1]
        prev_msg = messages[-2]

        # Ensure timestamps are timezone-aware
        if last_msg.timestamp.tzinfo is None:
            last_time = last_msg.timestamp.replace(tzinfo=timezone.utc)
        else:
            last_time = last_msg.timestamp

        if prev_msg.timestamp.tzinfo is None:
            prev_time = prev_msg.timestamp.replace(tzinfo=timezone.utc)
        else:
            prev_time = prev_msg.timestamp

        time_gap = (last_time - prev_time).total_seconds()
        if time_gap > 3600:  # 1 hour
            return True

    return False
```

**Integration into `run_orchestrator`:**

```python
async def run_orchestrator(
    project_id: UUID,
    user_message: str,
    session,
) -> str:
    """Run the orchestrator agent with a user message."""
    deps = AgentDependencies(session=session, project_id=project_id)

    # Save user message first
    await save_conversation_message(session, project_id, MessageRole.USER, user_message)

    # Get conversation history
    history_messages = await get_conversation_history(session, project_id, limit=50)

    # Detect topic change
    topic_changed = detect_topic_change(history_messages, user_message)

    # Build conversation context
    history_context = ""
    if len(history_messages) > 1:
        if topic_changed:
            # Topic changed - only use recent messages, add warning
            history_context = "\n\n⚠️ **IMPORTANT: The user has switched topics or corrected you.**\n\n"
            history_context += "## CURRENT TOPIC (Focus on this):\n\n"
            # Only last 4 messages (2 turns)
            for msg in history_messages[-5:-1][-4:]:
                role_name = "User" if msg.role == MessageRole.USER else "You (PM)"
                history_context += f"**{role_name}**: {msg.content}\n\n"
        else:
            # Normal flow - use weighted context
            recent_messages = history_messages[-7:-1]
            older_messages = history_messages[-21:-7] if len(history_messages) > 7 else []

            history_context = "\n\n## CURRENT CONVERSATION (Most Important):\n\n"
            for msg in recent_messages:
                role_name = "User" if msg.role == MessageRole.USER else "You (PM)"
                history_context += f"**{role_name}**: {msg.content}\n\n"

            if older_messages:
                history_context += "\n\n## Earlier Context (Only If Relevant):\n\n"
                for msg in older_messages[-5:]:
                    role_name = "User" if msg.role == MessageRole.USER else "You (PM)"
                    history_context += f"**{role_name}**: {msg.content}\n\n"

    # Add current message
    history_context += f"\n---\n\n**Current User Message**: {user_message}\n\n"
    history_context += "Please respond considering the conversation context above."

    # Run agent
    result = await orchestrator_agent.run(
        history_context if history_context else user_message, deps=deps
    )

    # Save assistant response
    await save_conversation_message(session, project_id, MessageRole.ASSISTANT, result.output)

    return result.output
```

### 1.3 Filter SCAR History by Relevance

**File:** `src/agent/orchestrator_agent.py`
**Function:** `get_scar_history` (lines 238-267)

**Current Implementation:**
```python
@orchestrator_agent.tool
async def get_scar_history(ctx: RunContext[AgentDependencies], limit: int = 5) -> list[dict]:
    """Get recent SCAR command execution history."""
    # Returns ALL recent executions
```

**Enhanced Implementation:**
```python
@orchestrator_agent.tool
async def get_scar_history(
    ctx: RunContext[AgentDependencies],
    limit: int = 5,
    only_recent: bool = True
) -> list[dict]:
    """
    Get SCAR command execution history.

    Args:
        ctx: Agent context
        limit: Maximum number of executions
        only_recent: If True, only return executions from last 30 minutes

    Returns:
        List of command executions
    """
    if not ctx.deps.project_id:
        return [{"error": "No active project"}]

    history = await get_command_history(ctx.deps.session, ctx.deps.project_id, limit)

    # Filter by recency if requested
    if only_recent:
        from datetime import datetime, timedelta, timezone
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=30)

        history = [
            exec for exec in history
            if exec.started_at and exec.started_at.replace(tzinfo=timezone.utc) > cutoff_time
        ]

    return [
        {
            "command_type": exec.command_type.value,
            "command_args": exec.command_args,
            "status": exec.status.value,
            "started_at": exec.started_at.isoformat() if exec.started_at else None,
            "completed_at": exec.completed_at.isoformat() if exec.completed_at else None,
            "output": exec.output[:200] if exec.output else None,
            "error": exec.error,
        }
        for exec in history
    ]
```

**Update Tool Description in Docstring:**
```python
"""
Get recent SCAR command execution history.

⚠️ IMPORTANT: Only call this when:
- User explicitly asks about SCAR status
- User asks "what has SCAR done?"
- You need to check if a command completed

DO NOT call this automatically for context. It may contain old, irrelevant information.

Args:
    ctx: Agent context with dependencies
    limit: Maximum number of executions to return
    only_recent: Only return executions from last 30 minutes (default: True)

Returns:
    list[dict]: Recent command executions
"""
```

### 1.4 Update System Prompt

**File:** `src/agent/prompts.py`
**Section:** Add to `ORCHESTRATOR_SYSTEM_PROMPT` after line 20

**Addition:**
```python
## Context Management

**CRITICAL - Maintain Conversation Focus:**

1. **Prioritize Recent Messages:**
   - The most recent 3 turns (6 messages) are CURRENT CONVERSATION
   - Older messages are "Earlier Context" - only relevant if connected to current topic
   - If user corrects you ("but we weren't discussing..."), IMMEDIATELY focus on their correction

2. **Detect Topic Changes:**
   - User says "let's discuss X" → New topic, forget old context
   - Time gap >1 hour → Treat as new conversation
   - User corrects you → You misunderstood, refocus on their actual topic

3. **Don't Call get_scar_history Automatically:**
   - Only call when user asks "what did SCAR do?" or similar
   - SCAR history may contain old, unrelated work
   - Don't let old SCAR commands contaminate current conversation

4. **If You Lose Context:**
   - Ask the user to clarify
   - Don't hallucinate about old topics
   - Better to admit "I'm not sure what you're referring to" than to guess wrong
```

## Phase 2: Topic Segmentation (Long-term Solution)

### 2.1 Database Schema Changes

**Goal:** Store conversation in topical segments rather than flat list

**New Table:** `conversation_topics`

**File:** `src/database/models.py`
**Location:** After `ConversationMessage` class (around line 163)

```python
class ConversationTopic(Base):
    """Tracks conversation topic segments within a project"""

    __tablename__ = "conversation_topics"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    topic_title = Column(String(255), nullable=True)  # Auto-generated or user-defined
    topic_summary = Column(Text, nullable=True)  # Brief summary of topic
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    # Relationships
    project = relationship("Project", back_populates="conversation_topics")
    messages = relationship("ConversationMessage", back_populates="topic", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ConversationTopic(id={self.id}, title={self.topic_title}, active={self.is_active})>"
```

**Update:** `ConversationMessage` model

```python
class ConversationMessage(Base):
    """Stores conversation history for projects"""

    __tablename__ = "conversation_messages"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    topic_id = Column(PGUUID(as_uuid=True), ForeignKey("conversation_topics.id"), nullable=True)  # NEW
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    message_metadata = Column(JSONB, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="conversation_messages")
    topic = relationship("ConversationTopic", back_populates="messages")  # NEW
```

**Update:** `Project` model

```python
class Project(Base):
    """Main project entity tracking the software development project"""

    # ... existing fields ...

    # Relationships
    conversation_messages = relationship(
        "ConversationMessage", back_populates="project", cascade="all, delete-orphan"
    )
    conversation_topics = relationship(  # NEW
        "ConversationTopic", back_populates="project", cascade="all, delete-orphan"
    )
    workflow_phases = relationship(
        "WorkflowPhase", back_populates="project", cascade="all, delete-orphan"
    )
    # ... rest of relationships ...
```

### 2.2 Alembic Migration

**File:** `src/database/migrations/versions/XXXXX_add_conversation_topics.py`

```python
"""add conversation topics

Revision ID: XXXXX
Revises: YYYYY
Create Date: 2026-01-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'XXXXX'
down_revision = 'YYYYY'  # Update with actual previous revision
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create conversation_topics table
    op.create_table('conversation_topics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('topic_title', sa.String(length=255), nullable=True),
        sa.Column('topic_summary', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Add topic_id column to conversation_messages
    op.add_column('conversation_messages',
        sa.Column('topic_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        'conversation_messages_topic_id_fkey',
        'conversation_messages', 'conversation_topics',
        ['topic_id'], ['id']
    )

    # Create indexes for performance
    op.create_index(
        'ix_conversation_topics_project_id_active',
        'conversation_topics',
        ['project_id', 'is_active']
    )
    op.create_index(
        'ix_conversation_messages_topic_id',
        'conversation_messages',
        ['topic_id']
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_conversation_messages_topic_id', table_name='conversation_messages')
    op.drop_index('ix_conversation_topics_project_id_active', table_name='conversation_topics')

    # Drop foreign key and column
    op.drop_constraint('conversation_messages_topic_id_fkey', 'conversation_messages', type_='foreignkey')
    op.drop_column('conversation_messages', 'topic_id')

    # Drop table
    op.drop_table('conversation_topics')
```

### 2.3 Topic Management Service

**File:** `src/services/topic_manager.py` (NEW)

```python
"""
Conversation Topic Management Service.

Handles automatic topic segmentation based on conversation flow.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import ConversationTopic, ConversationMessage, MessageRole

logger = logging.getLogger(__name__)


async def get_active_topic(session: AsyncSession, project_id: UUID) -> Optional[ConversationTopic]:
    """
    Get the currently active topic for a project.

    Args:
        session: Database session
        project_id: Project UUID

    Returns:
        Active ConversationTopic or None
    """
    stmt = (
        select(ConversationTopic)
        .where(
            and_(
                ConversationTopic.project_id == project_id,
                ConversationTopic.is_active == True
            )
        )
        .order_by(desc(ConversationTopic.started_at))
        .limit(1)
    )

    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_new_topic(
    session: AsyncSession,
    project_id: UUID,
    title: Optional[str] = None,
    summary: Optional[str] = None
) -> ConversationTopic:
    """
    Create a new conversation topic.

    Args:
        session: Database session
        project_id: Project UUID
        title: Optional topic title
        summary: Optional topic summary

    Returns:
        New ConversationTopic
    """
    # End previous active topic
    active_topic = await get_active_topic(session, project_id)
    if active_topic:
        active_topic.is_active = False
        active_topic.ended_at = datetime.utcnow()
        logger.info(f"Ended topic {active_topic.id}: {active_topic.topic_title}")

    # Create new topic
    new_topic = ConversationTopic(
        project_id=project_id,
        topic_title=title or f"Topic {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
        topic_summary=summary,
        started_at=datetime.utcnow(),
        is_active=True
    )
    session.add(new_topic)
    await session.flush()  # Get ID

    logger.info(f"Created new topic {new_topic.id}: {new_topic.topic_title}")
    return new_topic


async def should_create_new_topic(
    session: AsyncSession,
    project_id: UUID,
    user_message: str
) -> bool:
    """
    Determine if a new topic should be created based on conversation signals.

    Args:
        session: Database session
        project_id: Project UUID
        user_message: Current user message

    Returns:
        True if new topic should be created
    """
    # Check for explicit topic switch phrases
    topic_switch_phrases = [
        "new topic",
        "different topic",
        "let's discuss",
        "lets discuss",
        "switching to",
        "moving on to",
        "but we weren't discussing",
        "but we werent discussing",
        "we were talking about",
    ]

    user_lower = user_message.lower()
    for phrase in topic_switch_phrases:
        if phrase in user_lower:
            logger.info(f"Topic switch detected: '{phrase}' in message")
            return True

    # Check for time gap since last message
    active_topic = await get_active_topic(session, project_id)
    if active_topic:
        # Get last message in topic
        stmt = (
            select(ConversationMessage)
            .where(ConversationMessage.topic_id == active_topic.id)
            .order_by(desc(ConversationMessage.timestamp))
            .limit(1)
        )
        result = await session.execute(stmt)
        last_message = result.scalar_one_or_none()

        if last_message:
            # Ensure timezone-aware comparison
            if last_message.timestamp.tzinfo is None:
                last_time = last_message.timestamp.replace(tzinfo=timezone.utc)
            else:
                last_time = last_message.timestamp

            now = datetime.now(timezone.utc)
            time_gap = (now - last_time).total_seconds()

            # Create new topic if >1 hour gap
            if time_gap > 3600:
                logger.info(f"Time gap detected: {time_gap/60:.1f} minutes since last message")
                return True

    return False


async def generate_topic_title(
    session: AsyncSession,
    topic_id: UUID
) -> str:
    """
    Generate a descriptive title for a topic based on its messages.

    This is a simplified version - could be enhanced with LLM summarization.

    Args:
        session: Database session
        topic_id: Topic UUID

    Returns:
        Generated topic title
    """
    # Get first few messages
    stmt = (
        select(ConversationMessage)
        .where(ConversationMessage.topic_id == topic_id)
        .order_by(ConversationMessage.timestamp)
        .limit(3)
    )

    result = await session.execute(stmt)
    messages = result.scalars().all()

    if not messages:
        return "Untitled Topic"

    # Extract keywords from first user message
    first_user_msg = None
    for msg in messages:
        if msg.role == MessageRole.USER:
            first_user_msg = msg
            break

    if not first_user_msg:
        return "Untitled Topic"

    # Simple title generation: first 5 words
    words = first_user_msg.content.split()[:5]
    title = " ".join(words)
    if len(words) == 5:
        title += "..."

    return title
```

### 2.4 Update Conversation Tools

**File:** `src/agent/tools.py`

**Update:** `save_conversation_message` function

```python
async def save_conversation_message(
    session: AsyncSession,
    project_id: UUID,
    role: MessageRole,
    content: str,
    topic_id: Optional[UUID] = None
) -> ConversationMessage:
    """
    Save a conversation message to the database.

    Args:
        session: Database session
        project_id: Project UUID
        role: Message role
        content: Message content
        topic_id: Optional topic ID (will auto-detect if not provided)

    Returns:
        Saved ConversationMessage
    """
    from src.services.topic_manager import (
        get_active_topic,
        create_new_topic,
        should_create_new_topic
    )

    # Auto-detect topic if not provided
    if topic_id is None:
        # Check if we should create new topic (only for user messages)
        if role == MessageRole.USER:
            should_create = await should_create_new_topic(session, project_id, content)
            if should_create:
                new_topic = await create_new_topic(session, project_id)
                topic_id = new_topic.id
            else:
                # Use active topic or create one if none exists
                active_topic = await get_active_topic(session, project_id)
                if active_topic:
                    topic_id = active_topic.id
                else:
                    # No active topic - create first one
                    new_topic = await create_new_topic(session, project_id, title="Initial Conversation")
                    topic_id = new_topic.id
        else:
            # Assistant messages - always use active topic
            active_topic = await get_active_topic(session, project_id)
            if active_topic:
                topic_id = active_topic.id

    # Create message
    message = ConversationMessage(
        project_id=project_id,
        topic_id=topic_id,
        role=role,
        content=content,
        timestamp=datetime.utcnow()
    )

    session.add(message)
    await session.flush()

    return message
```

**Update:** `get_conversation_history` function

```python
async def get_conversation_history(
    session: AsyncSession,
    project_id: UUID,
    limit: int = 50,
    topic_id: Optional[UUID] = None,
    active_topic_only: bool = False
) -> list[ConversationMessage]:
    """
    Get conversation history for a project.

    Args:
        session: Database session
        project_id: Project UUID
        limit: Maximum messages to return
        topic_id: Optional specific topic ID
        active_topic_only: If True, only return messages from active topic

    Returns:
        List of ConversationMessage objects
    """
    from src.services.topic_manager import get_active_topic

    # Build query
    query = select(ConversationMessage).where(ConversationMessage.project_id == project_id)

    # Filter by topic if requested
    if topic_id:
        query = query.where(ConversationMessage.topic_id == topic_id)
    elif active_topic_only:
        active_topic = await get_active_topic(session, project_id)
        if active_topic:
            query = query.where(ConversationMessage.topic_id == active_topic.id)
        else:
            # No active topic - return empty
            return []

    # Order and limit
    query = query.order_by(ConversationMessage.timestamp).limit(limit)

    result = await session.execute(query)
    return list(result.scalars().all())
```

### 2.5 Update Orchestrator Agent

**File:** `src/agent/orchestrator_agent.py`

**Update:** `run_orchestrator` function to use active topic only

```python
async def run_orchestrator(
    project_id: UUID,
    user_message: str,
    session,
) -> str:
    """Run the orchestrator agent with a user message."""
    deps = AgentDependencies(session=session, project_id=project_id)

    # Save user message first (this handles topic detection)
    await save_conversation_message(session, project_id, MessageRole.USER, user_message)

    # Get conversation history - ONLY from active topic
    history_messages = await get_conversation_history(
        session,
        project_id,
        limit=50,
        active_topic_only=True  # NEW: Only get current topic
    )

    # Build conversation context (with existing weighted logic)
    # ... rest of function remains the same ...
```

## Phase 3: /reset Command

### 3.1 Backend API Endpoint

**File:** `src/api/projects.py`

**New Endpoint:**

```python
@router.post("/projects/{project_id}/reset", response_model=dict)
async def reset_project_conversation(
    project_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    """
    Reset conversation context for a project.

    This creates a new conversation topic, effectively clearing the context
    while preserving message history.

    Args:
        project_id: Project UUID
        session: Database session

    Returns:
        Success message with new topic ID

    Raises:
        404: Project not found
    """
    from src.services.topic_manager import create_new_topic, get_active_topic

    # Verify project exists
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )

    # Create new topic (this automatically ends the previous one)
    new_topic = await create_new_topic(
        session,
        project_id,
        title="Reset - New Conversation",
        summary="User requested context reset"
    )

    await session.commit()

    return {
        "success": True,
        "message": "Conversation context reset successfully",
        "new_topic_id": str(new_topic.id),
        "previous_messages_preserved": True
    }
```

### 3.2 WebSocket Reset Handler

**File:** `src/api/websocket.py`

**Update:** Protocol to support reset command

```python
@router.websocket("/ws/chat/{project_id}")
async def websocket_chat_endpoint(websocket: WebSocket, project_id: UUID):
    """
    WebSocket endpoint for real-time chat communication.

    Protocol:
        Client -> Server: {"content": "user message"}
        Client -> Server: {"action": "reset"}  # NEW
        Server -> Client: {"type": "chat", "data": {...}}
        Server -> Client: {"type": "status", "data": {...}}
        Server -> Client: {"type": "reset", "data": {"success": true, "message": "..."}}  # NEW
        Server -> Client: {"type": "error", "data": {...}}
    """
    connection_id = str(uuid4())

    try:
        await ws_manager.connect(connection_id, websocket)
        await ws_manager.send_status_update(
            connection_id, "connected", "Connected to Project Manager"
        )

        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received message on connection {connection_id}: {data[:100]}")

            try:
                message_data = json.loads(data)

                # Handle reset action
                if message_data.get("action") == "reset":
                    from src.services.topic_manager import create_new_topic

                    async with async_session_maker() as session:
                        new_topic = await create_new_topic(
                            session,
                            project_id,
                            title="Reset - New Conversation",
                            summary="User requested context reset"
                        )
                        await session.commit()

                        await ws_manager.send_personal_message(
                            {
                                "type": "reset",
                                "data": {
                                    "success": True,
                                    "message": "✅ Conversation context has been reset. Starting fresh!",
                                    "new_topic_id": str(new_topic.id)
                                }
                            },
                            connection_id
                        )
                    continue

                # Handle regular chat message
                user_content = message_data.get("content", "").strip()

                if not user_content:
                    await ws_manager.send_error(
                        connection_id, "EMPTY_MESSAGE", "Message content cannot be empty"
                    )
                    continue

                # ... rest of existing message handling ...
```

### 3.3 Frontend Integration

**File:** `frontend/src/components/MiddlePanel/ChatInterface.tsx`

**Update:** Add reset button

```tsx
import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { useWebSocket } from '@/hooks/useWebSocket';
import { getMessageDisplayName } from '@/utils/messageUtils';
import { ProjectColor } from '@/types/project';

interface ChatInterfaceProps {
  projectId: string;
  projectName: string;
  theme?: ProjectColor;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ projectId, projectName, theme }) => {
  const { messages, isConnected, sendMessage, resetContext, isLoadingHistory, isTyping } = useWebSocket(projectId);
  const [input, setInput] = useState('');
  const [showResetConfirm, setShowResetConfirm] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    if (input.trim()) {
      sendMessage(input);
      setInput('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleReset = () => {
    resetContext();
    setShowResetConfirm(false);
  };

  return (
    <div
      className="chat-interface"
      style={{ backgroundColor: theme?.veryLight || '#ffffff' }}
    >
      <div className="chat-header">
        <h2>Chat with {projectName}</h2>
        <div className="header-actions">
          <span className={`status ${isConnected ? 'connected' : 'disconnected'}`}>
            {isConnected ? '● Connected' : '○ Disconnected'}
          </span>
          <button
            className="reset-button"
            onClick={() => setShowResetConfirm(true)}
            title="Reset conversation context"
          >
            🔄 Reset
          </button>
        </div>
      </div>

      {showResetConfirm && (
        <div className="reset-confirmation">
          <p>⚠️ Reset conversation context? This will start a new topic but preserve message history.</p>
          <button onClick={handleReset}>Confirm Reset</button>
          <button onClick={() => setShowResetConfirm(false)}>Cancel</button>
        </div>
      )}

      <div className="messages">
        {isLoadingHistory ? (
          <div className="loading-state">Loading conversation history...</div>
        ) : messages.length === 0 ? (
          <div className="empty-state">No messages yet. Start a conversation!</div>
        ) : (
          <>
            {messages.map((msg) => (
              <div key={msg.id} className={`message ${msg.role}`}>
                <div className="message-header">
                  <span className="role">{getMessageDisplayName(msg)}</span>
                  <span className="timestamp">{new Date(msg.timestamp).toLocaleTimeString()}</span>
                </div>
                <div className="content">
                  <ReactMarkdown
                    components={{
                      code({ node, inline, className, children, ...props }: any) {
                        const match = /language-(\w+)/.exec(className || '');
                        return !inline && match ? (
                          <SyntaxHighlighter
                            style={vscDarkPlus as any}
                            language={match[1]}
                            PreTag="div"
                            {...props}
                          >
                            {String(children).replace(/\n$/, '')}
                          </SyntaxHighlighter>
                        ) : (
                          <code className={className} {...props}>
                            {children}
                          </code>
                        );
                      },
                    }}
                  >
                    {msg.content}
                  </ReactMarkdown>
                </div>
              </div>
            ))}
            {isTyping && (
              <div className="message assistant typing">
                <div className="message-header">
                  <span className="role">PM</span>
                </div>
                <div className="content">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>
      <div className="input-area">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Message PM..."
          rows={3}
        />
        <button onClick={handleSend} disabled={!isConnected}>Send</button>
      </div>
    </div>
  );
};
```

**File:** `frontend/src/hooks/useWebSocket.ts`

**Update:** Add `resetContext` function

```typescript
export const useWebSocket = (projectId: string) => {
  // ... existing state ...

  const resetContext = () => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: 'reset' }));

      // Optionally clear local messages to show fresh start
      setMessages([]);
    }
  };

  useEffect(() => {
    // ... existing connection logic ...

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'chat') {
        setMessages((prev) => [...prev, data.data]);
        setIsTyping(false);
      } else if (data.type === 'status') {
        setIsConnected(data.data.status === 'connected');
      } else if (data.type === 'reset') {
        // Handle reset confirmation
        console.log('Context reset:', data.data.message);
        // Could show a toast notification here
      } else if (data.type === 'error') {
        console.error('WebSocket error:', data.data);
      }
    };

    // ... rest of connection logic ...
  }, [projectId]);

  return {
    messages,
    isConnected,
    sendMessage,
    resetContext,  // NEW
    isLoadingHistory,
    isTyping
  };
};
```

### 3.4 Telegram Bot Reset Command

**File:** `src/integrations/telegram_bot.py`

**Add Handler:**

```python
self.application.add_handler(CommandHandler("reset", self.reset_command))
```

**Add Method:**

```python
async def reset_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /reset command - reset conversation context.

    Args:
        update: Telegram update
        context: Handler context
    """
    project_id_str = context.chat_data.get("project_id")

    if not project_id_str:
        await update.message.reply_text("No active project. Use /start to begin a new project.")
        return

    project_id = UUID(project_id_str)

    async with self.db_session_maker() as session:
        from src.services.topic_manager import create_new_topic

        # Create new topic (ends previous one)
        new_topic = await create_new_topic(
            session,
            project_id,
            title="Reset - New Conversation",
            summary="User requested context reset via Telegram"
        )
        await session.commit()

        reset_message = (
            "✅ **Conversation Reset**\n\n"
            "🔄 Your conversation context has been cleared.\n"
            "📝 Previous messages are preserved but won't affect future responses.\n"
            "💬 Starting fresh - what would you like to discuss?"
        )

        await update.message.reply_text(reset_message, parse_mode="Markdown")
```

**Update Help:**

```python
async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    help_text = (
        "**Project Manager Help**\n\n"
        "**Commands:**\n"
        "/start - Start a new project\n"
        "/status - Check current project status\n"
        "/continue - Continue to next workflow phase\n"
        "/reset - Reset conversation context\n"  # NEW
        "/help - Show this help message\n\n"
        "**How it works:**\n"
        "1. 💭 **Brainstorm** - Tell me your idea\n"
        "2. 📝 **Vision** - I'll create a clear vision document\n"
        "3. 🎯 **Plan** - We'll create an implementation plan\n"
        "4. 💻 **Build** - I'll implement the features\n"
        "5. ✅ **Validate** - We'll test everything\n\n"
        "💡 **Tip:** Use /reset if I seem confused or off-topic!\n\n"  # NEW
        "Just chat with me naturally, and I'll guide you through each step!"
    )

    await update.message.reply_text(help_text, parse_mode="Markdown")
```

## Testing Plan

### Phase 1 Tests

1. **Context Weighting Test**
   - Start conversation about Feature A
   - Have 8-10 messages about Feature A
   - Switch to Feature B ("let's discuss Feature B")
   - Verify PM focuses on Feature B, not Feature A

2. **Topic Change Detection Test**
   - Test explicit corrections: "but we weren't discussing X"
   - Verify PM acknowledges correction
   - Test time gap: wait >1 hour, send message
   - Verify new context window

3. **SCAR History Filtering Test**
   - Run SCAR command for Feature A
   - Discuss Feature B (different topic)
   - Verify PM doesn't mention Feature A SCAR results

### Phase 2 Tests

1. **Topic Segmentation Test**
   - Create project
   - Discuss Topic A (5 messages)
   - Switch to Topic B ("new topic: Feature B")
   - Verify new topic created in database
   - Verify context only includes Topic B messages

2. **Topic History Test**
   - Create multiple topics
   - Query conversation history with `active_topic_only=True`
   - Verify only current topic messages returned

3. **Migration Test**
   - Run migration on test database
   - Verify schema changes applied
   - Test backward migration (downgrade)

### Phase 3 Tests

1. **REST API Reset Test**
   - POST to `/projects/{id}/reset`
   - Verify new topic created
   - Verify previous topic ended
   - Verify response includes new topic ID

2. **WebSocket Reset Test**
   - Connect to WebSocket
   - Send `{"action": "reset"}`
   - Verify reset confirmation received
   - Send message, verify fresh context

3. **Telegram Reset Test**
   - Send `/reset` command
   - Verify confirmation message
   - Send message, verify PM doesn't reference old topics

4. **Frontend Reset Test**
   - Click reset button
   - Confirm reset dialog
   - Verify UI updates
   - Send message, verify fresh conversation

## Rollout Plan

### Phase 1: Quick Wins (Week 1)
**Day 1-2:**
- Implement context weighting (1.1)
- Implement topic change detection (1.2)
- Update system prompt (1.4)
- Unit tests for detection logic

**Day 3:**
- Implement SCAR history filtering (1.3)
- Integration tests
- Deploy to staging

**Day 4:**
- User testing on staging
- Bug fixes
- Deploy to production

### Phase 2: Topic Segmentation (Week 2)
**Day 1:**
- Create database models (2.1)
- Create Alembic migration (2.2)
- Test migration on dev database

**Day 2:**
- Implement topic manager service (2.3)
- Update conversation tools (2.4)
- Unit tests

**Day 3:**
- Update orchestrator agent (2.5)
- Integration tests
- Deploy to staging

**Day 4-5:**
- User testing on staging
- Data migration for existing projects
- Deploy to production

### Phase 3: /reset Command (Week 3)
**Day 1:**
- Backend API endpoint (3.1)
- WebSocket handler (3.2)
- API tests

**Day 2:**
- Frontend integration (3.3)
- Telegram bot command (3.4)
- E2E tests

**Day 3:**
- User testing
- Bug fixes
- Deploy to production

## Acceptance Criteria

### Phase 1
- [ ] PM maintains context across 8+ message turns on same topic
- [ ] PM correctly handles user corrections ("but we weren't discussing...")
- [ ] PM doesn't auto-execute SCAR commands based on context confusion
- [ ] Recent messages (last 2-3 turns) dominate context over older messages
- [ ] Time gaps >1 hour trigger context reset
- [ ] SCAR history only injected when explicitly relevant

### Phase 2
- [ ] Database schema includes `conversation_topics` table
- [ ] Messages automatically assigned to topics
- [ ] Topic switches create new topic entries
- [ ] Context queries only use active topic
- [ ] Migration runs cleanly on production
- [ ] Existing projects migrated successfully

### Phase 3
- [ ] `/reset` command available in web UI
- [ ] `/reset` command available in Telegram
- [ ] REST API endpoint functional
- [ ] WebSocket protocol supports reset
- [ ] Reset preserves message history
- [ ] Reset creates new topic
- [ ] User receives confirmation

## Success Metrics

1. **Context Accuracy**
   - Measure: User doesn't have to correct PM about topic
   - Target: >95% of conversations stay on-topic

2. **Hallucination Reduction**
   - Measure: PM references wrong/old topics
   - Target: <5% of responses reference wrong context

3. **User Satisfaction**
   - Measure: User survey "PM understands me"
   - Target: 4.5/5 stars

4. **Reset Usage**
   - Measure: How often users use /reset
   - Target: <10% of sessions (if working well, shouldn't need it often)

## Risk Mitigation

### Risk: Breaking Existing Conversations
- **Mitigation:** Phase 1 doesn't change schema, can roll back easily
- **Mitigation:** Phase 2 migration preserves all existing data
- **Mitigation:** Backward-compatible: `topic_id` nullable

### Risk: Performance Impact
- **Mitigation:** Add database indexes on `topic_id` and `is_active`
- **Mitigation:** Limit context query to 50 messages max
- **Mitigation:** Monitor query performance in staging

### Risk: Topic Detection Too Sensitive
- **Mitigation:** Make topic switch phrases specific
- **Mitigation:** Require clear signals, not vague keywords
- **Mitigation:** Allow users to manually reset if needed

## Future Enhancements

1. **LLM-Based Topic Titles**
   - Use LLM to generate descriptive topic titles from conversation

2. **Topic Navigation UI**
   - Show list of topics in sidebar
   - Allow users to switch between topics
   - "Back to previous topic" button

3. **Topic Merging**
   - If user returns to old topic, detect and merge

4. **Topic Summaries**
   - Automatically summarize each topic when ended
   - Show summaries in topic list

5. **Cross-Topic References**
   - Allow PM to reference related topics when relevant
   - "This is similar to what we discussed in Topic X"

## Conclusion

This implementation plan systematically addresses the PM context loss issue through three phases:

1. **Quick wins** (context weighting) - immediate relief
2. **Long-term solution** (topic segmentation) - architectural fix
3. **User control** (/reset command) - escape hatch

The plan is incremental, testable, and rollback-safe. Each phase delivers value independently while building toward the complete solution.

**Estimated Timeline:** 3 weeks
**Risk Level:** Low (incremental, backward-compatible)
**Impact:** High (fixes fundamental UX issue)
