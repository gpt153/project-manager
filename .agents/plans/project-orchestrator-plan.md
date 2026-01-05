# Project Manager - AI Workflow Manager
## Comprehensive Implementation Plan

Based on my analysis of the vision document, SCAR workflow commands, and the current repository structure, here is a detailed, actionable implementation plan for building the Project Manager agent.

---

## Executive Summary

The Project Manager is an AI-powered project management agent that bridges the gap between non-technical users and the SCAR (Sam's Coding Agent Remote) development system. It will translate natural language conversations into structured development workflows, manage approval gates, generate vision documents, and orchestrate the complete software development lifecycle.

**Core Architecture**: PydanticAI-based conversational agent with PostgreSQL state management, integrated with Telegram for user interaction and GitHub for workflow execution.

**Key Innovation**: Natural language interface that shields users from technical complexity while maintaining full control through approval gates.

---

## 1. Architecture Design

### 1.1 System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         User Layer                          │
│  ┌──────────────────┐           ┌──────────────────┐       │
│  │   Telegram Bot   │           │  GitHub @mention │       │
│  │  (Natural Lang)  │           │   (Issue/PR)     │       │
│  └────────┬─────────┘           └────────┬─────────┘       │
│           │                              │                  │
└───────────┼──────────────────────────────┼──────────────────┘
            │                              │
            ▼                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Project Manager Agent Core                │
│  ┌────────────────────────────────────────────────────┐    │
│  │         PydanticAI Conversational Agent             │    │
│  │  - Brainstorming & Requirements Gathering          │    │
│  │  - Vision Document Generation                       │    │
│  │  - SCAR Command Translation                        │    │
│  │  - Approval Gate Management                        │    │
│  │  - Progress Tracking & Notifications               │    │
│  └────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌───────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │  State Mgmt   │  │  Command     │  │  Notification  │  │
│  │  PostgreSQL   │  │  Executor    │  │  Handler       │  │
│  └───────────────┘  └──────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────────┘
            │                              │
            ▼                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Integration Layer                        │
│  ┌──────────────────┐           ┌──────────────────┐       │
│  │   SCAR System    │           │   GitHub API     │       │
│  │  - prime         │           │  - Create Repo   │       │
│  │  - plan-feature  │           │  - Manage Issues │       │
│  │  - execute       │           │  - Create PRs    │       │
│  │  - validate      │           │  - Webhooks      │       │
│  └──────────────────┘           └──────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Core Components

#### 1.2.1 PydanticAI Agent (`src/agent/orchestrator_agent.py`)

**Purpose**: The conversational AI brain that understands user intent and orchestrates workflows.

**Key Capabilities**:
- Multi-turn conversation management for brainstorming
- Context-aware question generation
- Vision document generation from conversations
- SCAR command selection and parameter extraction
- Natural language to structured command translation

**Dependencies**:
```python
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel
from typing import Optional, List
```

**System Prompt Structure**:
```python
ORCHESTRATOR_SYSTEM_PROMPT = """
You are a friendly project management AI assistant helping non-technical users
build software projects. Your role is to:

1. Ask clarifying questions to understand their vision
2. Generate clear, non-technical vision documents
3. Manage the development workflow with SCAR
4. Keep users informed with simple status updates
5. Ask for approval at key decision points

IMPORTANT RULES:
- Use plain English, avoid technical jargon
- Ask one question at a time during brainstorming
- Always get approval before major actions
- Translate user requests into SCAR commands automatically
- Track progress and notify users at phase completions

SCAR WORKFLOW EXPERTISE:
You are an expert in the SCAR PIV loop:
- Prime: Load codebase understanding (read-only analysis)
- Plan-feature-github: Create implementation plan on feature branch
- Execute-github: Implement from plan and create PR
- Validate: Run tests and verify implementation

You understand worktree management, GitHub workflows, and multi-project patterns.
"""
```

#### 1.2.2 State Management (`src/database/`)

**Schema Design** (`src/database/models.py`):

```python
# Projects Table
class Project(Base):
    __tablename__ = "projects"

    id: UUID (PK)
    name: str
    description: str
    github_repo_url: Optional[str]
    telegram_chat_id: Optional[int]
    github_issue_number: Optional[int]
    status: enum (BRAINSTORMING, VISION_REVIEW, PLANNING, IN_PROGRESS, PAUSED, COMPLETED)
    created_at: datetime
    updated_at: datetime
    vision_document: Optional[JSONB]  # Stored vision doc

# Conversation History
class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id: UUID (PK)
    project_id: UUID (FK)
    role: enum (USER, ASSISTANT, SYSTEM)
    content: str
    timestamp: datetime
    metadata: Optional[JSONB]  # Tool calls, attachments, etc.

# Workflow Phases
class WorkflowPhase(Base):
    __tablename__ = "workflow_phases"

    id: UUID (PK)
    project_id: UUID (FK)
    phase_number: int
    name: str
    description: str
    status: enum (PENDING, IN_PROGRESS, COMPLETED, FAILED, BLOCKED)
    scar_command: Optional[str]  # The SCAR command executed
    branch_name: Optional[str]
    pr_url: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]

# Approval Gates
class ApprovalGate(Base):
    __tablename__ = "approval_gates"

    id: UUID (PK)
    project_id: UUID (FK)
    phase_id: Optional[UUID] (FK)
    gate_type: enum (VISION_DOC, PHASE_START, PHASE_COMPLETE, ERROR_RESOLUTION)
    question: str
    context: JSONB  # Additional context for the approval
    status: enum (PENDING, APPROVED, REJECTED, EXPIRED)
    user_response: Optional[str]
    responded_at: Optional[datetime]
    created_at: datetime

# SCAR Command Executions
class ScarCommandExecution(Base):
    __tablename__ = "scar_executions"

    id: UUID (PK)
    project_id: UUID (FK)
    phase_id: Optional[UUID] (FK)
    command_type: enum (PRIME, PLAN_FEATURE, PLAN_FEATURE_GITHUB, EXECUTE, EXECUTE_GITHUB, VALIDATE)
    command_args: str
    branch_name: Optional[str]
    status: enum (QUEUED, RUNNING, COMPLETED, FAILED)
    output: Optional[str]
    error: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
```

**Database Connection** (`src/database/connection.py`):

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/project_orchestrator"

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def get_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session
```

#### 1.2.3 Telegram Bot Integration (`src/integrations/telegram_bot.py`)

**Purpose**: Natural language interface for user interactions.

**Key Features**:
- Multi-turn conversation support
- Context preservation across messages
- Approval gate notifications
- Progress updates
- Rich message formatting (Markdown)

**Implementation**:
```python
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

class OrchestratorTelegramBot:
    def __init__(self, token: str, agent: Agent, db_session_maker):
        self.application = Application.builder().token(token).build()
        self.agent = agent
        self.db_session_maker = db_session_maker

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command - initiate new project"""

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process user messages and route to agent"""

    async def handle_approval_response(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button callbacks for approvals"""

    async def send_approval_request(self, chat_id: int, approval_gate: ApprovalGate):
        """Send approval gate with Yes/No buttons"""
        keyboard = [
            [
                InlineKeyboardButton("✅ Yes", callback_data=f"approve:{approval_gate.id}"),
                InlineKeyboardButton("❌ No", callback_data=f"reject:{approval_gate.id}")
            ]
        ]

    async def notify_phase_complete(self, chat_id: int, phase: WorkflowPhase):
        """Notify user of phase completion"""

    def run(self):
        """Start the bot"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.application.add_handler(CallbackQueryHandler(self.handle_approval_response))

        self.application.run_polling()
```

#### 1.2.4 GitHub Integration (`src/integrations/github_client.py`)

**Purpose**: Monitor GitHub issues for @mentions and post updates.

**Key Features**:
- Webhook receiver for issue mentions
- Issue comment posting
- Repository creation assistance
- Status updates on issues

**Implementation**:
```python
from fastapi import FastAPI, Request, HTTPException
from github import Github
import hmac
import hashlib

class GitHubIntegration:
    def __init__(self, access_token: str, webhook_secret: str):
        self.client = Github(access_token)
        self.webhook_secret = webhook_secret

    async def verify_webhook_signature(self, request: Request) -> bool:
        """Verify GitHub webhook signature"""
        signature = request.headers.get("X-Hub-Signature-256")
        body = await request.body()

        expected_signature = "sha256=" + hmac.new(
            self.webhook_secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, expected_signature)

    async def handle_issue_comment(self, payload: dict):
        """Handle issue comment webhook - detect @mentions"""
        comment_body = payload["comment"]["body"]
        if "@po" in comment_body:
            # Extract user request
            # Route to agent
            # Post response as comment
            pass

    async def post_issue_comment(self, repo_name: str, issue_number: int, comment: str):
        """Post a comment to a GitHub issue"""
        repo = self.client.get_repo(repo_name)
        issue = repo.get_issue(issue_number)
        issue.create_comment(comment)

    async def create_repository(self, name: str, description: str, private: bool = False):
        """Create a new GitHub repository"""
        user = self.client.get_user()
        return user.create_repo(name, description=description, private=private)
```

#### 1.2.5 SCAR Command Executor (`src/scar/command_executor.py`)

**Purpose**: Translate natural language to SCAR commands and execute them.

**SCAR Command Mapping**:

```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List

class ScarCommandType(Enum):
    PRIME = "prime"
    PLAN_FEATURE = "plan-feature"
    PLAN_FEATURE_GITHUB = "plan-feature-github"
    EXECUTE = "execute"
    EXECUTE_GITHUB = "execute-github"
    VALIDATE = "validate"

@dataclass
class ScarCommand:
    command_type: ScarCommandType
    args: str
    branch_name: Optional[str] = None
    plan_path: Optional[str] = None

class ScarCommandTranslator:
    """Translates user intent to SCAR commands"""

    def __init__(self, agent: Agent):
        self.agent = agent

    async def translate_to_command(self, user_message: str, project_context: dict) -> ScarCommand:
        """Use PydanticAI agent to understand intent and select SCAR command"""

        # Example translations:
        # "Start building the project" -> prime command
        # "Add user authentication" -> plan-feature-github "Add user authentication"
        # "Build the feature we just planned" -> execute-github {branch} {plan_path}
        # "Run tests" -> validate

    def build_prime_command(self, repo_url: str) -> str:
        """Build prime command for codebase analysis"""
        return f"@scar /command-invoke prime"

    def build_plan_feature_command(self, feature_description: str, use_github: bool = True) -> str:
        """Build plan-feature or plan-feature-github command"""
        cmd = "plan-feature-github" if use_github else "plan-feature"
        return f'@scar /command-invoke {cmd} "{feature_description}"'

    def build_execute_command(self, plan_path: str, branch_name: str, use_github: bool = True) -> str:
        """Build execute or execute-github command"""
        cmd = "execute-github" if use_github else "execute"
        return f'@scar /command-invoke {cmd} {plan_path} {branch_name}'

class ScarCommandExecutor:
    """Executes SCAR commands via GitHub issues or other mechanism"""

    def __init__(self, github_client: GitHubIntegration, db_session_maker):
        self.github = github_client
        self.db_session_maker = db_session_maker

    async def execute_command(self, project_id: UUID, command: ScarCommand) -> ScarCommandExecution:
        """Execute a SCAR command and track execution"""

        async with self.db_session_maker() as session:
            # Create execution record
            execution = ScarCommandExecution(
                project_id=project_id,
                command_type=command.command_type,
                command_args=command.args,
                status="QUEUED"
            )
            session.add(execution)
            await session.commit()

            try:
                # Post command to GitHub issue
                # Monitor for completion
                # Update execution status
                pass
            except Exception as e:
                execution.status = "FAILED"
                execution.error = str(e)
                await session.commit()

        return execution
```

#### 1.2.6 Vision Document Generator (`src/services/vision_generator.py`)

**Purpose**: Generate non-technical vision documents from conversation history.

**Implementation**:
```python
from pydantic import BaseModel
from typing import List

class VisionDocument(BaseModel):
    """Structure for vision documents"""
    title: str
    what_it_is: str
    who_its_for: List[str]
    problem_statement: str
    solution_overview: str
    key_features: List[dict]  # [{name: str, description: str}]
    user_journey: str
    success_metrics: List[str]
    out_of_scope: List[str]

class VisionDocumentGenerator:
    def __init__(self, agent: Agent):
        self.agent = agent

    async def generate_from_conversation(
        self,
        conversation_history: List[ConversationMessage]
    ) -> VisionDocument:
        """Generate vision doc from brainstorming conversation"""

        # Use PydanticAI with structured output
        result = await self.agent.run(
            f"""
            Based on this conversation about a project idea:

            {self._format_conversation(conversation_history)}

            Generate a comprehensive vision document in plain English.
            Focus on WHAT and WHY, not HOW.
            """,
            result_type=VisionDocument
        )

        return result.data

    def _format_conversation(self, messages: List[ConversationMessage]) -> str:
        """Format conversation for agent processing"""
        return "\n\n".join([
            f"{msg.role}: {msg.content}" for msg in messages
        ])

    def format_as_markdown(self, vision: VisionDocument) -> str:
        """Convert vision document to markdown format"""
        # Generate markdown following the template in vision document
```

### 1.3 Communication Flows

#### Flow 1: New Project via Telegram

```
User: "I want to build a meal planning app"
  ↓
Telegram Bot receives message
  ↓
Check DB for existing project for this chat_id
  ↓
Create new Project (status: BRAINSTORMING)
  ↓
Agent starts brainstorming (multi-turn)
  ↓
Agent asks clarifying questions
  ↓
User responds with answers
  ↓
After sufficient info gathered:
  ↓
Agent generates VisionDocument
  ↓
Create ApprovalGate (type: VISION_DOC)
  ↓
Send vision to user with Yes/No buttons
  ↓
User approves
  ↓
Update Project (status: PLANNING)
  ↓
Agent asks for GitHub repo creation or existing repo
  ↓
Create GitHub repo or link existing
  ↓
Execute SCAR prime command
  ↓
Wait for completion, update Phase status
  ↓
Agent plans phases and executes plan-feature-github
  ↓
Continue workflow...
```

#### Flow 2: @Mention in GitHub Issue

```
User creates GitHub issue and @mentions project-manager
  ↓
GitHub webhook fires
  ↓
FastAPI webhook endpoint receives payload
  ↓
Verify signature
  ↓
Extract issue content and user request
  ↓
Check DB for existing project linked to this repo
  ↓
If new: Create project, link to issue
  ↓
Route to PydanticAI agent
  ↓
Agent processes request
  ↓
Generate response
  ↓
Post response as GitHub issue comment
  ↓
If Telegram chat linked: Send notification to Telegram
```

#### Flow 3: Phase Completion Notification

```
SCAR command completes (detected via polling or webhook)
  ↓
Update ScarCommandExecution status
  ↓
Update WorkflowPhase status
  ↓
Create ApprovalGate for next phase
  ↓
Send Telegram notification with phase summary
  ↓
Send approval request for next phase
  ↓
If GitHub issue linked: Post update comment
  ↓
Wait for user approval
  ↓
On approval: Execute next SCAR command
```

---

## 2. Implementation Phases

### Phase 1: Core Infrastructure and Database Setup (Week 1)

**Objective**: Establish foundational infrastructure for the orchestrator.

**Tasks**:

1. **Project Setup**
   - Initialize Python project with `pyproject.toml`
   - Set up project structure (`src/`, `tests/`, `docs/`)
   - Configure development environment (uvicorn, pytest, ruff)
   - Set up `.env` configuration with environment variables

2. **Database Setup**
   - Install PostgreSQL locally or configure cloud instance
   - Create database schema using Alembic migrations
   - Implement all SQLAlchemy models (`models.py`)
   - Create async database connection utilities
   - Write database initialization script
   - Create seed data for testing

3. **Basic API Framework**
   - Set up FastAPI application structure
   - Configure CORS, middleware
   - Create health check endpoints
   - Set up logging infrastructure
   - Configure environment-based settings (dev/staging/prod)

4. **Testing Infrastructure**
   - Set up pytest with async support
   - Create test database fixtures
   - Implement database cleanup between tests
   - Create test utilities for mocking

**Validation**:
```bash
# Database migrations work
alembic upgrade head

# Tests pass
pytest tests/

# API starts
uvicorn src.main:app --reload

# Health check responds
curl http://localhost:8000/health
```

**Deliverables**:
- Working database with all tables
- FastAPI app skeleton
- Test infrastructure
- Configuration management

---

### Phase 2: Basic Conversational AI with PydanticAI (Week 2)

**Objective**: Build the core conversational agent that can engage in multi-turn dialogues.

**Tasks**:

1. **PydanticAI Agent Setup**
   - Install and configure PydanticAI
   - Create `OrchestratorAgent` class
   - Implement system prompt with SCAR expertise
   - Set up dependency injection for database access
   - Configure LLM provider (Anthropic Claude)

2. **Conversation Management**
   - Implement conversation history storage
   - Create session management
   - Build context retrieval from database
   - Implement conversation state machine

3. **Agent Tools**
   - Create tool for storing conversation messages
   - Create tool for retrieving project information
   - Create tool for updating project status
   - Implement structured output validation with Pydantic

4. **Testing**
   - Unit tests for agent initialization
   - Test conversation flow with mocked LLM
   - Test tool execution
   - Test structured output parsing

**Key Implementation** (`src/agent/orchestrator_agent.py`):

```python
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.anthropic import AnthropicModel

class AgentDependencies(BaseModel):
    session: AsyncSession
    project_id: Optional[UUID] = None

orchestrator_agent = Agent(
    model=AnthropicModel("claude-sonnet-4-5-20250929"),
    deps_type=AgentDependencies,
    system_prompt=ORCHESTRATOR_SYSTEM_PROMPT
)

@orchestrator_agent.tool
async def save_message(ctx: RunContext[AgentDependencies], role: str, content: str) -> str:
    """Save a conversation message to the database"""
    async with ctx.deps.session as session:
        message = ConversationMessage(
            project_id=ctx.deps.project_id,
            role=role,
            content=content,
            timestamp=datetime.utcnow()
        )
        session.add(message)
        await session.commit()
    return "Message saved"

@orchestrator_agent.tool
async def get_project_context(ctx: RunContext[AgentDependencies]) -> dict:
    """Retrieve current project context"""
    async with ctx.deps.session as session:
        project = await session.get(Project, ctx.deps.project_id)
        return {
            "name": project.name,
            "status": project.status,
            "description": project.description
        }
```

**Validation**:
```bash
# Agent can be instantiated
pytest tests/agent/test_agent_init.py

# Tools execute successfully
pytest tests/agent/test_tools.py

# Multi-turn conversation works
pytest tests/agent/test_conversation.py
```

**Deliverables**:
- Working PydanticAI agent
- Conversation storage and retrieval
- Agent tools for database interaction
- Comprehensive test coverage

---

### Phase 3: Vision Document Generation (Week 3)

**Objective**: Enable agent to generate structured vision documents from conversations.

**Tasks**:

1. **Vision Document Schema**
   - Create Pydantic models for vision document structure
   - Implement validation rules
   - Create markdown formatter

2. **Brainstorming Logic**
   - Implement intelligent question generation
   - Create conversation completeness checker
   - Build feature extraction logic
   - Implement problem/solution identification

3. **Document Generation**
   - Create vision document generator service
   - Implement template-based markdown generation
   - Add vision document storage in database
   - Create document versioning support

4. **Approval Gate System**
   - Implement approval gate creation
   - Build approval tracking
   - Create timeout handling
   - Implement revision request handling

5. **Testing**
   - Test vision document generation from various conversation types
   - Test markdown formatting
   - Test approval gate workflow
   - Test edge cases (incomplete info, conflicting requirements)

**Key Implementation** (`src/services/vision_generator.py`):

```python
class VisionDocumentService:
    def __init__(self, agent: Agent, db_session_maker):
        self.agent = agent
        self.db_session_maker = db_session_maker

    async def generate_vision_document(
        self,
        project_id: UUID
    ) -> VisionDocument:
        """Generate vision document from conversation history"""

        async with self.db_session_maker() as session:
            # Retrieve conversation
            messages = await self._get_conversation(session, project_id)

            # Use agent to generate structured vision
            result = await self.agent.run(
                self._build_vision_prompt(messages),
                deps=AgentDependencies(session=session, project_id=project_id),
                result_type=VisionDocument
            )

            # Store in project
            project = await session.get(Project, project_id)
            project.vision_document = result.data.model_dump()
            await session.commit()

            return result.data

    def _build_vision_prompt(self, messages: List[ConversationMessage]) -> str:
        """Build prompt for vision generation"""
        return f"""
        Based on this brainstorming conversation:

        {self._format_messages(messages)}

        Generate a comprehensive vision document following this structure:
        - What It Is: One paragraph overview
        - Who It's For: Primary and secondary users
        - Problem Statement: What problem does this solve?
        - Solution Overview: How does this solve it?
        - Key Features: List of features in plain English
        - User Journey: Story of how someone uses it
        - Success Metrics: Clear, measurable goals
        - Out of Scope: What we're NOT building (for MVP)

        Use plain English. No technical jargon. Focus on WHAT and WHY, not HOW.
        """
```

**Validation**:
```bash
# Vision document generation
pytest tests/services/test_vision_generator.py

# Markdown formatting
pytest tests/services/test_markdown_formatter.py

# Approval gate workflow
pytest tests/services/test_approval_gates.py
```

**Deliverables**:
- Vision document generation from conversations
- Markdown-formatted output
- Approval gate system
- Document storage and retrieval

---

### Phase 4: SCAR Workflow Automation (Week 4-5)

**Objective**: Implement SCAR command translation, execution, and monitoring.

**Tasks**:

1. **SCAR Command Translation**
   - Create command type enum
   - Implement natural language to command translator
   - Build command parameter extraction
   - Create command validation

2. **Command Executor**
   - Implement GitHub issue comment posting for commands
   - Create command execution tracking
   - Build command status polling
   - Implement execution result parsing

3. **Workflow Phase Management**
   - Create workflow phase state machine
   - Implement phase dependency tracking
   - Build phase execution orchestration
   - Create error recovery logic

4. **SCAR Expertise Integration**
   - Encode PIV loop knowledge in agent
   - Implement worktree management awareness
   - Create branch naming logic
   - Build plan file path tracking

5. **Monitoring and Polling**
   - Implement GitHub API polling for command completion
   - Create webhook receiver for command updates (if available)
   - Build execution timeout handling
   - Implement retry logic

**Key Implementation** (`src/scar/workflow_manager.py`):

```python
class WorkflowManager:
    """Manages SCAR workflow execution"""

    def __init__(self, github_client, command_executor, db_session_maker):
        self.github = github_client
        self.executor = command_executor
        self.db_session_maker = db_session_maker

    async def start_development_workflow(self, project_id: UUID):
        """Start the complete development workflow"""

        async with self.db_session_maker() as session:
            project = await session.get(Project, project_id)

            # Phase 1: Prime the codebase
            await self._execute_prime(session, project)

            # Phase 2: Plan first feature
            await self._execute_plan_feature(session, project)

            # Phase 3: Execute plan
            await self._execute_implementation(session, project)

            # Phase 4: Validate
            await self._execute_validation(session, project)

    async def _execute_prime(self, session: AsyncSession, project: Project):
        """Execute prime command"""

        # Create phase
        phase = WorkflowPhase(
            project_id=project.id,
            phase_number=1,
            name="Codebase Analysis",
            description="Load codebase understanding",
            status="IN_PROGRESS",
            scar_command="prime"
        )
        session.add(phase)
        await session.commit()

        # Build command
        command = ScarCommand(
            command_type=ScarCommandType.PRIME,
            args=""
        )

        # Execute via GitHub
        execution = await self.executor.execute_command(project.id, command)

        # Poll for completion
        await self._wait_for_completion(session, execution.id)

        # Update phase
        phase.status = "COMPLETED"
        phase.completed_at = datetime.utcnow()
        await session.commit()
```

**SCAR Command Templates**:

```python
SCAR_COMMAND_TEMPLATES = {
    "prime": "@scar /command-invoke prime",
    "plan-feature-github": '@scar /command-invoke plan-feature-github "{feature_description}"',
    "execute-github": "@scar /command-invoke execute-github {plan_path} {branch_name}",
    "validate": "@scar /command-invoke validate"
}
```

**Validation**:
```bash
# Command translation
pytest tests/scar/test_command_translator.py

# Workflow execution
pytest tests/scar/test_workflow_manager.py

# Phase state management
pytest tests/scar/test_phase_manager.py
```

**Deliverables**:
- SCAR command translation system
- Command execution and monitoring
- Workflow phase orchestration
- Integration with GitHub API

---

### Phase 5: Telegram Bot Integration (Week 6)

**Objective**: Build user-facing Telegram bot for natural language interaction.

**Tasks**:

1. **Bot Setup**
   - Create Telegram bot with BotFather
   - Configure python-telegram-bot
   - Implement async handlers
   - Set up bot commands

2. **Message Handling**
   - Implement message routing to agent
   - Create response formatting
   - Build context preservation
   - Implement typing indicators

3. **Approval Gates in Telegram**
   - Create inline keyboard buttons for approvals
   - Implement callback query handling
   - Build approval notification system
   - Create timeout reminders

4. **Notifications**
   - Implement phase completion notifications
   - Create error notifications
   - Build progress updates
   - Implement rich message formatting (Markdown)

5. **User Experience**
   - Implement /start command with onboarding
   - Create /status command for project status
   - Build /help command with examples
   - Implement /cancel for stopping workflows

**Key Implementation** (`src/integrations/telegram_bot.py`):

```python
class OrchestratorBot:
    def __init__(self, token: str, agent: Agent, workflow_manager: WorkflowManager):
        self.application = Application.builder().token(token).build()
        self.agent = agent
        self.workflow = workflow_manager

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        await update.message.reply_text(
            "👋 Hi! I'm your Project Manager.\n\n"
            "I help you build software projects without knowing how to code.\n\n"
            "Just tell me about your idea, and I'll guide you through the process!\n\n"
            "What would you like to build?"
        )

        # Create new project
        async with self.db_session_maker() as session:
            project = Project(
                telegram_chat_id=update.effective_chat.id,
                status="BRAINSTORMING"
            )
            session.add(project)
            await session.commit()

            # Store project_id in context
            context.user_data['project_id'] = str(project.id)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle user messages"""
        user_message = update.message.text
        project_id = context.user_data.get('project_id')

        if not project_id:
            await update.message.reply_text("Please use /start to begin a new project.")
            return

        # Show typing indicator
        await update.effective_chat.send_action("typing")

        # Send to agent
        async with self.db_session_maker() as session:
            result = await self.agent.run(
                user_message,
                deps=AgentDependencies(
                    session=session,
                    project_id=UUID(project_id)
                )
            )

            # Send response
            await update.message.reply_text(
                result.data,
                parse_mode="Markdown"
            )

    async def send_approval_request(self, chat_id: int, approval: ApprovalGate):
        """Send approval gate with buttons"""
        keyboard = [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"approve:{approval.id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject:{approval.id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await self.application.bot.send_message(
            chat_id=chat_id,
            text=f"🔔 **Approval Needed**\n\n{approval.question}\n\n{approval.context}",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
```

**Validation**:
```bash
# Bot initialization
pytest tests/integrations/test_telegram_bot.py

# Message handling
pytest tests/integrations/test_message_routing.py

# Approval gates
pytest tests/integrations/test_approval_ui.py
```

**Deliverables**:
- Working Telegram bot
- Multi-turn conversation support
- Approval gate UI with buttons
- Notification system

---

### Phase 6: GitHub Integration (Week 7)

**Objective**: Enable GitHub issue-based interaction and webhook handling.

**Tasks**:

1. **Webhook Receiver**
   - Create FastAPI webhook endpoint
   - Implement signature verification
   - Build payload parsing
   - Create event routing

2. **Issue Comment Handling**
   - Detect @mentions in issues
   - Extract user requests
   - Route to agent
   - Post responses as comments

3. **Repository Integration**
   - Implement repository creation helper
   - Create repository linking
   - Build issue creation
   - Implement PR status tracking

4. **Status Updates**
   - Post phase updates to issues
   - Create PR links in comments
   - Build error notifications
   - Implement completion summaries

**Key Implementation** (`src/integrations/github_webhooks.py`):

```python
from fastapi import APIRouter, Request, HTTPException

router = APIRouter()

@router.post("/webhooks/github")
async def github_webhook(request: Request):
    """Handle GitHub webhook events"""

    # Verify signature
    if not await verify_signature(request):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse payload
    payload = await request.json()
    event_type = request.headers.get("X-GitHub-Event")

    # Route events
    if event_type == "issue_comment":
        await handle_issue_comment(payload)
    elif event_type == "issues":
        await handle_issue(payload)

    return {"status": "ok"}

async def handle_issue_comment(payload: dict):
    """Process issue comment events"""
    comment = payload["comment"]["body"]

    # Check for @mention
    if "@po" not in comment:
        return

    # Extract repo and issue info
    repo_name = payload["repository"]["full_name"]
    issue_number = payload["issue"]["number"]

    # Find or create project
    async with db_session_maker() as session:
        project = await find_project_by_repo(session, repo_name)

        if not project:
            project = Project(
                github_repo_url=f"https://github.com/{repo_name}",
                github_issue_number=issue_number,
                status="BRAINSTORMING"
            )
            session.add(project)
            await session.commit()

        # Process with agent
        result = await orchestrator_agent.run(
            comment,
            deps=AgentDependencies(session=session, project_id=project.id)
        )

        # Post response
        await github_client.post_issue_comment(
            repo_name,
            issue_number,
            result.data
        )
```

**Validation**:
```bash
# Webhook verification
pytest tests/integrations/test_github_webhooks.py

# Issue comment handling
pytest tests/integrations/test_issue_comments.py

# Repository operations
pytest tests/integrations/test_github_operations.py
```

**Deliverables**:
- GitHub webhook receiver
- Issue comment @mention handling
- Status update posting
- Repository integration

---

### Phase 7: End-to-End Workflow Integration (Week 8)

**Objective**: Connect all components into a complete workflow.

**Tasks**:

1. **Workflow Orchestration**
   - Integrate all services
   - Implement end-to-end flow
   - Create state machine for project lifecycle
   - Build error recovery

2. **Notification System**
   - Implement cross-platform notifications (Telegram + GitHub)
   - Create notification templates
   - Build notification queue
   - Implement retry logic

3. **Progress Tracking**
   - Create phase progress calculator
   - Implement ETA estimation
   - Build status dashboard data
   - Create summary generation

4. **Testing**
   - End-to-end integration tests
   - Multi-user scenario tests
   - Error recovery tests
   - Performance tests

**Key Integration** (`src/services/orchestration_service.py`):

```python
class OrchestrationService:
    """Coordinates all services for end-to-end workflow"""

    def __init__(
        self,
        agent: Agent,
        vision_service: VisionDocumentService,
        workflow_manager: WorkflowManager,
        telegram_bot: OrchestratorBot,
        github_client: GitHubIntegration,
        db_session_maker
    ):
        self.agent = agent
        self.vision = vision_service
        self.workflow = workflow_manager
        self.telegram = telegram_bot
        self.github = github_client
        self.db_session_maker = db_session_maker

    async def process_user_message(
        self,
        project_id: UUID,
        message: str,
        source: str  # "telegram" or "github"
    ) -> str:
        """Central message processing"""

        async with self.db_session_maker() as session:
            project = await session.get(Project, project_id)

            # Determine project state and route appropriately
            if project.status == "BRAINSTORMING":
                return await self._handle_brainstorming(session, project, message)
            elif project.status == "VISION_REVIEW":
                return await self._handle_vision_review(session, project, message)
            elif project.status == "PLANNING":
                return await self._handle_planning(session, project, message)
            elif project.status == "IN_PROGRESS":
                return await self._handle_execution(session, project, message)

    async def _handle_brainstorming(
        self,
        session: AsyncSession,
        project: Project,
        message: str
    ) -> str:
        """Handle brainstorming phase"""

        # Use agent for conversation
        result = await self.agent.run(
            message,
            deps=AgentDependencies(session=session, project_id=project.id)
        )

        # Check if enough information gathered
        if await self._check_conversation_complete(session, project.id):
            # Generate vision document
            vision = await self.vision.generate_vision_document(project.id)

            # Create approval gate
            approval = ApprovalGate(
                project_id=project.id,
                gate_type="VISION_DOC",
                question="Here's the vision for your project. Does this look good?",
                context=self.vision.format_as_markdown(vision),
                status="PENDING"
            )
            session.add(approval)

            project.status = "VISION_REVIEW"
            await session.commit()

            # Send approval request
            if project.telegram_chat_id:
                await self.telegram.send_approval_request(
                    project.telegram_chat_id,
                    approval
                )

            return "I've created a vision document for your project. Please review!"

        return result.data
```

**Validation**:
```bash
# End-to-end workflow tests
pytest tests/integration/test_complete_workflow.py

# Cross-platform notifications
pytest tests/integration/test_notifications.py

# Error recovery
pytest tests/integration/test_error_recovery.py
```

**Deliverables**:
- Complete workflow orchestration
- Cross-platform notification system
- Progress tracking
- Comprehensive integration tests

---

### Phase 8: Testing and Refinement (Week 9-10)

**Objective**: Ensure quality, reliability, and user experience.

**Tasks**:

1. **Comprehensive Testing**
   - Write unit tests for all components (target 80% coverage)
   - Create integration tests for workflows
   - Build end-to-end user scenario tests
   - Implement load testing

2. **User Experience Refinement**
   - Test with real users (if available)
   - Refine agent prompts based on feedback
   - Improve error messages
   - Enhance notification formatting

3. **Performance Optimization**
   - Optimize database queries
   - Implement caching where appropriate
   - Reduce API latency
   - Optimize LLM token usage

4. **Documentation**
   - Write user guide
   - Create developer documentation
   - Document API endpoints
   - Create deployment guide

5. **Monitoring and Logging**
   - Set up structured logging
   - Implement error tracking (Sentry)
   - Create metrics collection
   - Build admin dashboard

**Validation**:
```bash
# Full test suite
pytest tests/ --cov=src --cov-report=html

# Linting and type checking
ruff check src/
mypy src/

# Load testing
locust -f tests/load/locustfile.py
```

**Deliverables**:
- 80%+ test coverage
- User and developer documentation
- Monitoring and logging infrastructure
- Performance benchmarks

---

## 3. Key Technical Decisions

### 3.1 PydanticAI Agent Structure

**Decision**: Use single agent with multiple tools vs. multiple specialized agents

**Choice**: Single orchestrator agent with specialized tools

**Rationale**:
- Simpler context management
- Unified conversation history
- Easier state tracking
- Tools can be modular and testable

**Implementation**:
```python
orchestrator_agent = Agent(
    model=AnthropicModel("claude-sonnet-4-5-20250929"),
    deps_type=AgentDependencies,
    system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
    retries=2
)

# Tools for different capabilities
@orchestrator_agent.tool
async def save_conversation_message(...)

@orchestrator_agent.tool
async def generate_vision_document(...)

@orchestrator_agent.tool
async def execute_scar_command(...)

@orchestrator_agent.tool
async def create_approval_gate(...)

@orchestrator_agent.tool
async def check_workflow_status(...)
```

### 3.2 Database Schema Design

**Decision**: How to store conversation history and maintain context

**Choice**: Separate tables for conversations, projects, phases, and approvals with JSONB for flexibility

**Rationale**:
- Clear separation of concerns
- Efficient querying
- Flexibility for metadata
- Easy to extend

**Schema relationships**:
```
Project (1) -----> (many) ConversationMessage
Project (1) -----> (many) WorkflowPhase
Project (1) -----> (many) ApprovalGate
WorkflowPhase (1) -> (many) ScarCommandExecution
```

### 3.3 Asynchronous Operations

**Decision**: How to handle SCAR command execution and monitoring

**Choice**: Async polling with background tasks + webhooks (when available)

**Rationale**:
- SCAR commands can take minutes to complete
- Need non-blocking execution
- Webhooks may not always be available
- Polling provides reliable fallback

**Implementation**:
```python
import asyncio
from fastapi import BackgroundTasks

async def execute_and_monitor(project_id: UUID, command: ScarCommand):
    """Execute command and poll for completion"""

    # Execute command
    execution = await executor.execute_command(project_id, command)

    # Poll for completion in background
    while True:
        await asyncio.sleep(30)  # Poll every 30 seconds

        status = await check_execution_status(execution.id)

        if status in ["COMPLETED", "FAILED"]:
            await handle_completion(execution.id)
            break

        # Timeout after 2 hours
        if (datetime.utcnow() - execution.started_at).seconds > 7200:
            await handle_timeout(execution.id)
            break

# Usage in FastAPI
@app.post("/execute-command")
async def execute_command(request: CommandRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(execute_and_monitor, request.project_id, request.command)
    return {"status": "queued"}
```

### 3.4 Error Handling and Retry Logic

**Decision**: How to handle failures in SCAR execution

**Choice**: Exponential backoff with max retries + user notification

**Implementation**:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60)
)
async def execute_scar_command_with_retry(command: ScarCommand):
    """Execute SCAR command with retry logic"""
    try:
        return await github_client.post_command(command)
    except Exception as e:
        # Log error
        logger.error(f"SCAR command failed: {e}")

        # Notify user
        await notify_user_of_error(command.project_id, str(e))

        raise  # Re-raise for retry
```

### 3.5 Security Considerations

**Decisions**:

1. **GitHub Webhook Verification**
   - Always verify webhook signatures using HMAC
   - Reject requests with invalid signatures

2. **Telegram Bot Security**
   - Store bot token in environment variables
   - Validate user permissions before executing commands
   - Rate limit user requests

3. **Database Access**
   - Use connection pooling with limits
   - Parameterized queries (SQLAlchemy ORM handles this)
   - Encrypt sensitive data at rest

4. **API Keys**
   - Store in environment variables or secret manager
   - Rotate regularly
   - Use separate keys for dev/staging/prod

**Implementation**:
```python
# Webhook verification
async def verify_github_signature(request: Request, secret: str) -> bool:
    signature = request.headers.get("X-Hub-Signature-256")
    body = await request.body()

    expected = "sha256=" + hmac.new(
        secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected)

# Rate limiting
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/message")
@limiter.limit("10/minute")
async def handle_message(request: Request):
    ...
```

---

## 4. Integration with SCAR System

### 4.1 SCAR Command Execution Flow

```python
class ScarIntegration:
    """Integration layer for SCAR workflow system"""

    PIV_LOOP = {
        "Prime": {
            "command": "prime",
            "purpose": "Load codebase understanding (read-only analysis)",
            "when": "Start of project or when switching contexts",
            "output": "Codebase summary and architecture understanding"
        },
        "Plan": {
            "command": "plan-feature-github",
            "purpose": "Create implementation plan on feature branch",
            "when": "After prime, for each new feature",
            "output": "Feature branch with plan file (.agents/plans/*.md)"
        },
        "Execute": {
            "command": "execute-github",
            "purpose": "Implement from plan and create PR",
            "when": "After plan is approved",
            "output": "Pull request with implemented feature"
        },
        "Validate": {
            "command": "validate",
            "purpose": "Run tests and verify implementation",
            "when": "After execution, before merge",
            "output": "Test results and validation status"
        }
    }

    async def execute_piv_loop(self, project_id: UUID, feature_description: str):
        """Execute complete PIV loop for a feature"""

        # 1. Prime (if needed)
        if not await self.is_primed(project_id):
            await self.execute_prime(project_id)

        # 2. Plan
        plan_result = await self.execute_plan_feature_github(
            project_id,
            feature_description
        )
        branch_name = plan_result.branch_name
        plan_path = plan_result.plan_path

        # Wait for user approval
        await self.request_plan_approval(project_id, plan_path)

        # 3. Execute
        execute_result = await self.execute_github(
            project_id,
            plan_path,
            branch_name
        )
        pr_url = execute_result.pr_url

        # 4. Validate (automatic in execute-github)
        # Tests run as part of PR creation

        # Notify user
        await self.notify_completion(project_id, pr_url)
```

### 4.2 Worktree Management

The orchestrator understands SCAR's worktree patterns:

```python
class WorktreeManager:
    """Understands SCAR worktree patterns"""

    WORKTREE_PATTERN = "/workspace/worktrees/{repo-name}/{issue-number}"

    async def get_worktree_path(self, project: Project) -> str:
        """Get the worktree path for a project"""
        repo_name = self._extract_repo_name(project.github_repo_url)
        issue_number = project.github_issue_number

        return f"/workspace/worktrees/{repo_name}/issue-{issue_number}"

    async def track_branch(self, project_id: UUID, branch_name: str):
        """Track feature branch for a project"""
        async with self.db_session_maker() as session:
            project = await session.get(Project, project_id)
            # Store branch in current phase
            current_phase = await self._get_current_phase(session, project_id)
            current_phase.branch_name = branch_name
            await session.commit()
```

### 4.3 GitHub Workflow Commands

The orchestrator knows when to use GitHub workflow commands vs. local commands:

```python
class CommandSelector:
    """Select appropriate SCAR command based on context"""

    def select_plan_command(self, has_github_repo: bool) -> str:
        """Choose between plan-feature and plan-feature-github"""
        return "plan-feature-github" if has_github_repo else "plan-feature"

    def select_execute_command(self, has_github_repo: bool) -> str:
        """Choose between execute and execute-github"""
        return "execute-github" if has_github_repo else "execute"

    def build_command(self, command_type: str, **kwargs) -> str:
        """Build SCAR command with proper syntax"""

        if command_type == "plan-feature-github":
            return f'@scar /command-invoke plan-feature-github "{kwargs["feature"]}"'

        elif command_type == "execute-github":
            return f'@scar /command-invoke execute-github {kwargs["plan_path"]} {kwargs["branch"]}'

        elif command_type == "prime":
            return "@scar /command-invoke prime"
```

### 4.4 Multi-Project Development Patterns

The orchestrator can manage multiple projects simultaneously:

```python
class MultiProjectManager:
    """Manage multiple concurrent projects"""

    async def get_active_projects(self, user_id: str) -> List[Project]:
        """Get all active projects for a user"""
        async with self.db_session_maker() as session:
            result = await session.execute(
                select(Project).where(
                    Project.telegram_chat_id == user_id,
                    Project.status.in_(["IN_PROGRESS", "PLANNING", "VISION_REVIEW"])
                )
            )
            return result.scalars().all()

    async def switch_context(self, user_id: str, project_id: UUID):
        """Switch active project context"""
        # Update conversation context
        # May trigger prime command to reload codebase understanding
        pass
```

---

## 5. Files to Create/Modify

### 5.1 New Project Structure

```
project-manager/
├── .agents/
│   ├── visions/
│   │   └── project-manager.md (existing)
│   ├── plans/
│   │   └── project-manager-plan.md (this document)
│   └── commands/ (existing)
├── src/
│   ├── __init__.py
│   ├── main.py                          # FastAPI application entry point
│   ├── config.py                        # Configuration management
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── orchestrator_agent.py        # PydanticAI agent setup
│   │   ├── prompts.py                   # System prompts and templates
│   │   └── tools.py                     # Agent tools
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py                    # SQLAlchemy models
│   │   ├── connection.py                # Async database connection
│   │   └── migrations/                  # Alembic migrations
│   │       └── versions/
│   ├── services/
│   │   ├── __init__.py
│   │   ├── vision_generator.py          # Vision document generation
│   │   ├── approval_service.py          # Approval gate management
│   │   ├── notification_service.py      # Cross-platform notifications
│   │   └── orchestration_service.py     # Main orchestration logic
│   ├── scar/
│   │   ├── __init__.py
│   │   ├── command_translator.py        # NL to SCAR command translation
│   │   ├── command_executor.py          # SCAR command execution
│   │   ├── workflow_manager.py          # PIV loop management
│   │   └── worktree_manager.py          # Worktree pattern handling
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── telegram_bot.py              # Telegram bot implementation
│   │   ├── github_client.py             # GitHub API client
│   │   └── github_webhooks.py           # Webhook handlers
│   └── api/
│       ├── __init__.py
│       ├── routes.py                    # FastAPI routes
│       └── dependencies.py              # FastAPI dependencies
├── tests/
│   ├── __init__.py
│   ├── conftest.py                      # Pytest fixtures
│   ├── agent/
│   │   ├── test_agent_init.py
│   │   ├── test_tools.py
│   │   └── test_conversation.py
│   ├── services/
│   │   ├── test_vision_generator.py
│   │   └── test_approval_service.py
│   ├── scar/
│   │   ├── test_command_translator.py
│   │   └── test_workflow_manager.py
│   ├── integrations/
│   │   ├── test_telegram_bot.py
│   │   └── test_github_webhooks.py
│   └── integration/
│       └── test_complete_workflow.py
├── docs/
│   ├── USER_GUIDE.md
│   ├── DEVELOPER_GUIDE.md
│   └── API_REFERENCE.md
├── scripts/
│   ├── init_db.py                       # Database initialization
│   └── seed_data.py                     # Test data seeding
├── alembic.ini                          # Alembic configuration
├── pyproject.toml                       # Python project configuration
├── .env.example                         # Environment variables template
├── Dockerfile                           # Container definition
├── docker-compose.yml                   # Local development setup
└── README.md                            # Project readme (update existing)
```

### 5.2 Files to Modify

1. **README.md** - Update with project status and usage instructions
2. **.gitignore** - Add Python-specific ignores (if not present)

---

## 6. Dependencies

### 6.1 Python Dependencies (`pyproject.toml`)

```toml
[project]
name = "project-manager"
version = "0.1.0"
description = "AI agent that helps non-coders build software projects"
requires-python = ">=3.11"

dependencies = [
    # Core framework
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",

    # AI Agent
    "pydantic-ai>=0.0.14",
    "anthropic>=0.42.0",  # For Claude Sonnet 4.5

    # Database
    "sqlalchemy[asyncio]>=2.0.36",
    "asyncpg>=0.30.0",  # Async PostgreSQL driver
    "alembic>=1.14.0",  # Migrations

    # Telegram Bot
    "python-telegram-bot>=22.5",

    # GitHub Integration
    "PyGithub>=2.5.0",
    "httpx>=0.28.0",  # For async GitHub API calls

    # Utilities
    "pydantic>=2.10.0",
    "pydantic-settings>=2.7.0",
    "python-dotenv>=1.0.0",
    "tenacity>=9.0.0",  # Retry logic
    "python-multipart>=0.0.20",  # For file uploads
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=6.0.0",
    "pytest-mock>=3.14.0",
    "ruff>=0.8.0",
    "mypy>=1.13.0",
    "black>=24.10.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
strict = true
```

### 6.2 System Requirements

- **Python**: 3.11 or higher
- **PostgreSQL**: 14 or higher
- **Redis**: 7.0 or higher (optional, for caching)
- **Docker**: 20.10 or higher (for containerized deployment)

### 6.3 External Services

- **Anthropic API**: For Claude Sonnet 4.5 (PydanticAI)
- **Telegram Bot API**: For bot interactions
- **GitHub API**: For repository and webhook integration

---

## 7. Testing Strategy

### 7.1 Unit Tests

**Coverage Target**: 80%+

**Areas to Test**:

1. **Agent Tools**
   - Tool execution with mocked database
   - Tool parameter validation
   - Error handling in tools

2. **Services**
   - Vision document generation from various inputs
   - Approval gate state transitions
   - Notification formatting

3. **SCAR Integration**
   - Command translation accuracy
   - Command parameter extraction
   - Workflow state machine

4. **Database Models**
   - Model creation and validation
   - Relationship queries
   - JSON field serialization

**Example Test** (`tests/services/test_vision_generator.py`):

```python
import pytest
from src.services.vision_generator import VisionDocumentService
from src.database.models import ConversationMessage

@pytest.mark.asyncio
async def test_vision_generation_from_conversation(mock_agent, db_session):
    """Test vision document generation"""

    # Create test conversation
    messages = [
        ConversationMessage(
            role="user",
            content="I want to build a meal planning app"
        ),
        ConversationMessage(
            role="assistant",
            content="Great! Who would use this app?"
        ),
        ConversationMessage(
            role="user",
            content="Busy parents who waste food"
        ),
        # ... more messages
    ]

    # Generate vision
    service = VisionDocumentService(mock_agent, db_session)
    vision = await service.generate_vision_document(project_id)

    # Assert structure
    assert vision.title is not None
    assert len(vision.key_features) > 0
    assert vision.problem_statement is not None
```

### 7.2 Integration Tests

**Focus Areas**:

1. **End-to-End Workflows**
   - Complete project lifecycle (brainstorm → vision → development → completion)
   - Multi-phase workflows
   - Error recovery scenarios

2. **Cross-Platform Integration**
   - Telegram → Agent → Database
   - GitHub → Agent → Telegram
   - Approval flow across platforms

3. **Database Transactions**
   - Concurrent project creation
   - State transition atomicity
   - Rollback on errors

**Example Test** (`tests/integration/test_complete_workflow.py`):

```python
@pytest.mark.asyncio
async def test_complete_project_workflow(app_client, db_session, mock_telegram, mock_github):
    """Test complete project lifecycle"""

    # 1. User starts conversation via Telegram
    await mock_telegram.send_message("/start")
    await mock_telegram.send_message("I want to build a meal planner")

    # 2. Agent brainstorms (multiple turns)
    # ... simulation of conversation

    # 3. Vision document generated
    # Assert vision doc created in database

    # 4. User approves vision
    await mock_telegram.click_button("approve")

    # 5. GitHub repo created
    # Assert repo creation called

    # 6. SCAR prime executed
    # Assert command posted to GitHub

    # 7. Plan-feature-github executed
    # Assert plan created

    # 8. Execute-github executed
    # Assert PR created

    # Verify final state
    project = await get_project(db_session, project_id)
    assert project.status == "COMPLETED"
```

### 7.3 End-to-End Tests

**User Scenarios**:

1. **Scenario 1: Complete MVP via Telegram**
   - New user starts bot
   - Describes project idea
   - Reviews and approves vision
   - Monitors progress via notifications
   - Receives completed project

2. **Scenario 2: Feature Addition via GitHub**
   - Existing project
   - User creates issue and @mentions orchestrator
   - Agent plans feature
   - User approves via Telegram
   - Implementation completed

3. **Scenario 3: Multi-Project Management**
   - User has 2 active projects
   - Switches between contexts
   - Both projects progress independently

### 7.4 Load and Performance Tests

**Tools**: Locust or pytest-benchmark

**Scenarios**:
- 100 concurrent users sending messages
- Database query performance under load
- LLM API rate limiting
- Webhook processing throughput

---

## 8. Deployment Considerations

### 8.1 Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Load Balancer                       │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼────────┐      ┌─────────▼────────┐
│   FastAPI App  │      │   FastAPI App    │
│   (Instance 1) │      │   (Instance 2)   │
│   + Telegram   │      │   + Telegram     │
└───────┬────────┘      └─────────┬────────┘
        │                         │
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────┐
        │  PostgreSQL Cluster     │
        │  (Primary + Replicas)   │
        └─────────────────────────┘
```

### 8.2 Environment Configuration

**Environment Variables** (`.env.example`):

```bash
# Application
APP_ENV=production
LOG_LEVEL=INFO
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Anthropic API (for PydanticAI)
ANTHROPIC_API_KEY=your-anthropic-api-key

# Telegram Bot
TELEGRAM_BOT_TOKEN=your-telegram-bot-token

# GitHub
GITHUB_ACCESS_TOKEN=your-github-token
GITHUB_WEBHOOK_SECRET=your-webhook-secret

# Redis (optional, for caching)
REDIS_URL=redis://localhost:6379/0

# Monitoring
SENTRY_DSN=your-sentry-dsn
```

### 8.3 Docker Deployment

**Dockerfile**:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install -e .

# Copy application
COPY src/ ./src/
COPY alembic.ini ./

# Run migrations and start app
CMD alembic upgrade head && \
    uvicorn src.main:app --host 0.0.0.0 --port 8000
```

**docker-compose.yml** (for local development):

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: orchestrator
      POSTGRES_PASSWORD: dev_password
      POSTGRES_DB: project_orchestrator
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://orchestrator:dev_password@postgres:5432/project_orchestrator
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - GITHUB_ACCESS_TOKEN=${GITHUB_ACCESS_TOKEN}
    depends_on:
      - postgres
      - redis
    volumes:
      - ./src:/app/src

volumes:
  postgres_data:
```

### 8.4 Monitoring and Logging

**Structured Logging** (`src/config.py`):

```python
import logging
import json
from datetime import datetime

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def log(self, level: str, message: str, **kwargs):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            **kwargs
        }
        self.logger.log(getattr(logging, level), json.dumps(log_entry))

# Usage
logger = StructuredLogger("orchestrator")
logger.log("INFO", "Agent started conversation", project_id=str(project_id), user_id=user_id)
```

**Error Tracking with Sentry**:

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,
    environment=os.getenv("APP_ENV", "production")
)
```

**Metrics Collection**:

```python
from prometheus_client import Counter, Histogram

# Define metrics
conversation_counter = Counter('orchestrator_conversations_total', 'Total conversations')
command_duration = Histogram('scar_command_duration_seconds', 'SCAR command execution time')

# Use in code
conversation_counter.inc()

with command_duration.time():
    await execute_scar_command(command)
```

### 8.5 Deployment Checklist

- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Telegram webhook set (if using webhooks instead of polling)
- [ ] GitHub webhook configured
- [ ] SSL certificates installed
- [ ] Monitoring dashboards created
- [ ] Log aggregation configured
- [ ] Backup strategy implemented
- [ ] Rate limiting configured
- [ ] Health check endpoints responding

---

## 9. Success Metrics

### 9.1 User Success Metrics

- **Completion Rate**: 90% of started projects reach VISION_REVIEW stage
- **Time to First Vision**: <10 minutes from project start to vision document
- **Approval Response Time**: <5 minutes average user response to approval gates
- **Phase Success Rate**: 85% of phases complete without manual intervention
- **User Satisfaction**: 8+/10 average rating

### 9.2 Technical Success Metrics

- **Agent Response Time**: <3 seconds for conversational responses
- **Command Execution Success**: 90% of SCAR commands complete successfully
- **Database Query Performance**: <100ms for 95th percentile
- **API Uptime**: 99.5%
- **Error Rate**: <1% of requests fail

### 9.3 Business Metrics

- **Active Projects**: Number of projects in PLANNING or IN_PROGRESS
- **Completed Projects**: Number of projects reaching COMPLETED status
- **Daily Active Users**: Unique users interacting per day
- **Conversation Volume**: Messages processed per day
- **SCAR Command Volume**: Commands executed per day

---

## 10. Risk Mitigation

### 10.1 Technical Risks

**Risk**: LLM API rate limiting or downtime
- **Mitigation**: Implement exponential backoff, queue requests, show user-friendly error messages

**Risk**: SCAR command execution failures
- **Mitigation**: Robust error handling, retry logic, manual intervention option

**Risk**: Database performance degradation
- **Mitigation**: Connection pooling, query optimization, read replicas, caching

**Risk**: Webhook delivery failures
- **Mitigation**: Signature verification, idempotent processing, retry mechanism

### 10.2 User Experience Risks

**Risk**: Agent generates poor quality vision documents
- **Mitigation**: Iterative prompt refinement, user feedback loop, revision capability

**Risk**: Users confused by approval gates
- **Mitigation**: Clear messaging, examples, help documentation

**Risk**: Long wait times for SCAR execution
- **Mitigation**: Progress updates, ETA estimation, ability to cancel

### 10.3 Security Risks

**Risk**: Unauthorized access to projects
- **Mitigation**: User authentication, project ownership validation

**Risk**: Webhook replay attacks
- **Mitigation**: Signature verification, timestamp validation, nonce tracking

**Risk**: Sensitive data exposure
- **Mitigation**: Encryption at rest, secure API key storage, access logging

---

## Appendix A: SCAR Workflow Reference

### PIV Loop Commands

1. **Prime**: `@scar /command-invoke prime`
   - Loads codebase understanding
   - Read-only analysis
   - Generates architecture summary

2. **Plan-Feature-GitHub**: `@scar /command-invoke plan-feature-github "feature description"`
   - Creates feature branch
   - Generates implementation plan
   - Commits plan to `.agents/plans/`

3. **Execute-GitHub**: `@scar /command-invoke execute-github [plan-path] [branch-name]`
   - Implements from plan
   - Creates pull request
   - Runs validations

4. **Validate**: `@scar /command-invoke validate`
   - Runs test suite
   - Checks code quality
   - Verifies implementation

### Worktree Pattern

```
/workspace/worktrees/{repo-name}/{issue-number}/
```

### Branch Naming

```
feature-{descriptive-name}
```

### Plan File Location

```
.agents/plans/{kebab-case-name}.md
```

---

## Appendix B: Example Workflows

### Example 1: New Project from Scratch

```
Day 1 - Morning (10 minutes):
User: /start (Telegram)
Bot: "Hi! What would you like to build?"

User: "A meal planning app for busy parents"
Bot: "Great! Who would use this?"
[... 10 message conversation ...]

Bot: "Here's your vision document: [vision.md]"
     "Does this look good? [Yes] [No]"
User: [Yes]

Bot: "Perfect! Should I create a GitHub repository? [Yes] [No]"
User: [Yes]

Bot: "Repository created: github.com/user/meal-planner"
     "Starting development workflow..."
     "⏳ Phase 1: Analyzing project structure (2 min)"

Day 1 - Afternoon:
Bot: "✅ Phase 1 Complete: Project analyzed"
     "✅ Phase 2 Complete: Implementation plan created"
     "Ready to build first feature: User authentication"
     "Continue? [Yes] [No]"
User: [Yes]

Bot: "⏳ Building user authentication..."
[... 30 minutes later ...]
Bot: "✅ User authentication complete!"
     "Pull request: github.com/user/meal-planner/pull/1"
     "Test it here: meal-planner-staging.app"
     "Start next feature? [Yes] [No]"
```

### Example 2: Adding Feature to Existing Project

```
User creates GitHub issue:
Title: "Add recipe import from URL"
Body: "@po can you add the ability to import recipes from URLs?"

Bot comments on issue:
"I'll help you add recipe import functionality! Let me plan this feature..."
[... 5 minutes later ...]

Bot comments:
"Implementation plan created. This will:
- Add URL parser for common recipe sites
- Extract ingredients and instructions
- Save to recipe database
- Add to user's collection

Plan: .agents/plans/recipe-url-import.md
Approve to continue? 👍 this comment to approve"

User reacts with 👍

Bot comments:
"Building recipe import feature..."
[... 20 minutes later ...]

Bot comments:
"✅ Recipe import feature complete!
PR: github.com/user/meal-planner/pull/5
Try it: meal-planner-staging.app/import

Tests passing: ✅
Ready for review!"
```

---

## Critical Files for Implementation

Based on this comprehensive plan, here are the 5 most critical files for implementing the Project Manager:

1. **src/agent/orchestrator_agent.py** - Core PydanticAI agent setup with system prompt, tools, and conversation management. This is the brain of the orchestrator and determines all intelligent behavior.

2. **src/database/models.py** - Complete SQLAlchemy model definitions for projects, conversations, workflow phases, approval gates, and SCAR executions. The schema design determines how state is tracked throughout the workflow.

3. **src/services/orchestration_service.py** - Main orchestration logic that coordinates all services, manages project lifecycle state machine, and routes messages appropriately. This is the central coordinator of all components.

4. **src/scar/workflow_manager.py** - SCAR PIV loop implementation with command execution, phase management, and GitHub integration. This encapsulates all SCAR workflow expertise.

5. **src/integrations/telegram_bot.py** - Telegram bot implementation with message handling, approval gate UI, and notifications. This is the primary user interface most users will interact with.

---

## Next Steps

1. **Immediate**: Review and approve this plan
2. **Week 1**: Set up development environment and database infrastructure
3. **Week 2-3**: Build core agent and vision generation
4. **Week 4-6**: Implement SCAR integration and Telegram bot
5. **Week 7-8**: End-to-end integration and testing
6. **Week 9-10**: Refinement, documentation, and deployment preparation

---

**Plan Version**: 1.0
**Created**: 2025-12-19
**Status**: Ready for Review