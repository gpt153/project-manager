# Project Orchestrator

> AI agent that helps non-coders build software projects by managing workflow between users and SCAR

## What Is This?

An AI-powered project management agent that translates natural language conversations into structured development workflows. Built to help non-technical people turn their ideas into working software.

## Vision

See the complete vision document: [`.agents/visions/project-orchestrator.md`](.agents/visions/project-orchestrator.md)

## Status

🎉 **62.5% Complete** - 5 of 8 Core Phases Implemented

### Implementation Progress

- ✅ Phase 1: Core Infrastructure and Database Setup (100%)
- ✅ Phase 2: PydanticAI Conversational Agent (100%)
- ✅ Phase 3: Vision Document Generation (100%)
- ✅ Phase 4: SCAR Workflow Automation (100%)
- ✅ Phase 5: Telegram Bot Integration (100%)
- ⏳ Phase 6: GitHub Integration (0%)
- ⏳ Phase 7: End-to-End Workflow (0%)
- ⏳ Phase 8: Testing and Refinement (0%)

### Test Coverage

- **37 passing tests** across all implemented phases
- Full test coverage for database models, services, and workflows
- Integration tests for Telegram bot and orchestrator agent

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Docker (optional, for containerized deployment)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/project-orchestrator.git
cd project-orchestrator
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e .
pip install -e ".[dev]"  # For development dependencies
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Set up the database:
```bash
# Create database
createdb project_orchestrator

# Run migrations
alembic upgrade head
```

6. Run the application:
```bash
python -m src.main
```

Visit http://localhost:8000/docs for the API documentation.

### Using Docker

```bash
# Copy and configure environment
cp .env.example .env

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

## Features

### ✅ Implemented

#### 1. **Conversational AI Agent** (Phase 2)
- Natural language understanding of project requirements
- Multi-turn conversation support with context persistence
- 8 specialized tools for project and workflow management
- Powered by Claude Sonnet 4 via PydanticAI

#### 2. **Vision Document Generation** (Phase 3)
- Automatic conversation completeness checking
- AI-powered feature extraction with prioritization
- Structured vision document generation
- Markdown export for documentation
- Approval gate integration for user review

#### 3. **SCAR Workflow Automation** (Phase 4)
- Automated execution of SCAR PIV loop commands:
  - PRIME: Load project context
  - PLAN-FEATURE-GITHUB: Create implementation plans
  - EXECUTE-GITHUB: Implement features
  - VALIDATE: Test and verify implementations
- Workflow state machine with 5 defined phases
- Command execution history and tracking
- Approval gates at key decision points

#### 4. **Telegram Bot Interface** (Phase 5)
- Full conversational interface via Telegram
- Commands: `/start`, `/help`, `/status`, `/continue`
- Inline keyboard buttons for approvals
- Automatic vision document offering
- Real-time workflow progress updates
- Markdown formatting for rich messages

#### 5. **Database & Models** (Phase 1)
- 5 async SQLAlchemy models
- PostgreSQL with full ACID compliance
- Alembic migrations for schema management
- Complete conversation history tracking
- Workflow phase and approval gate persistence

### ⏳ Remaining Work

- **Phase 6**: GitHub Integration (webhooks, issue tracking, PR management)
- **Phase 7**: End-to-End Workflow Testing
- **Phase 8**: Production Refinements

## How It Works

```
User (Telegram) → "I want to build a task manager"
       ↓
Orchestrator Agent → Brainstorms, asks questions
       ↓
Vision Generator → Creates clear vision document
       ↓
Workflow Orchestrator → Manages PIV loop automatically
       ↓
SCAR Commands → prime → plan-feature-github → execute-github → validate
       ↓
Working Code + Tests + Documentation
```

### Architecture

- **PydanticAI Agent**: Conversational AI brain (Claude Sonnet 4)
- **PostgreSQL**: State management for projects, conversations, workflows
- **Telegram Bot**: Natural language interface for non-technical users
- **SCAR Integration**: Automated command translation and execution
- **Approval Gates**: User control at key decision points

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_main.py
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/
```

## Repository Structure

```
project-orchestrator/
├── .agents/
│   ├── visions/           # Non-technical vision documents
│   ├── plans/             # Technical implementation plans
│   └── commands/          # Custom workflow commands
├── src/
│   ├── agent/             # PydanticAI agent implementation
│   ├── api/               # FastAPI routes and endpoints
│   ├── database/          # Database models and migrations
│   ├── integrations/      # Telegram and GitHub integrations
│   ├── scar/              # SCAR command translation and execution
│   ├── services/          # Business logic services
│   ├── config.py          # Configuration management
│   └── main.py            # FastAPI application entry point
├── tests/                 # Test suite
├── docs/                  # Additional documentation
├── scripts/               # Utility scripts
├── pyproject.toml         # Project configuration and dependencies
├── alembic.ini            # Database migration configuration
├── docker-compose.yml     # Docker services configuration
└── README.md              # This file
```

## API Documentation

Once the application is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Environment Variables

See `.env.example` for all available configuration options:

- `DATABASE_URL`: PostgreSQL connection string
- `ANTHROPIC_API_KEY`: API key for Claude (PydanticAI)
- `TELEGRAM_BOT_TOKEN`: Telegram bot token
- `GITHUB_ACCESS_TOKEN`: GitHub personal access token
- `GITHUB_WEBHOOK_SECRET`: Secret for webhook verification

## Development Workflow

1. **Vision** → `.agents/visions/` - Non-technical project description
2. **PRD** → `docs/PRD.md` - Detailed requirements
3. **Plan** → `.agents/plans/` - Technical implementation plan
4. **Execute** → Actual code implementation

## Contributing

This is a learning project built using AI-assisted development. Watch the Issues tab to see how it's built!

### Development Setup

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Resources

- [Implementation Plan](.agents/plans/project-orchestrator-plan.md)
- [Vision Document](.agents/visions/project-orchestrator.md)
- [SCAR Documentation](https://github.com/anthropics/scar)

## License

MIT
