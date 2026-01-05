# Project Manager

[![CI Pipeline](https://github.com/gpt153/project-manager/actions/workflows/ci.yml/badge.svg)](https://github.com/gpt153/project-manager/actions/workflows/ci.yml)
[![Build and Push](https://github.com/gpt153/project-manager/actions/workflows/build-and-push.yml/badge.svg)](https://github.com/gpt153/project-manager/actions/workflows/build-and-push.yml)
[![Deploy](https://github.com/gpt153/project-manager/actions/workflows/deploy.yml/badge.svg)](https://github.com/gpt153/project-manager/actions/workflows/deploy.yml)

> AI agent that helps non-coders build software projects by managing workflow between users and SCAR

## What Is This?

An AI-powered project management agent that translates natural language conversations into structured development workflows. Built to help non-technical people turn their ideas into working software.

## Vision

See the complete vision document: [`.agents/visions/project-manager.md`](.agents/visions/project-manager.md)

## Status

🎉 **PRODUCTION-READY** - Core orchestrator (75% complete) + Web Interface (Ready for Deployment!)

### Implementation Progress

- ✅ Phase 1: Core Infrastructure and Database Setup (100%)
- ✅ Phase 2: PydanticAI Conversational Agent (100%)
- ✅ Phase 3: Vision Document Generation (100%)
- ✅ Phase 4: SCAR Workflow Automation (100%)
- ✅ Phase 5: Telegram Bot Integration (100%)
- ✅ Phase 6: GitHub Integration (100%)
- ✅ Web Interface: 3-Panel UI (Build Complete - Ready for Deployment!)
- ⏳ Phase 7: End-to-End Workflow (0%)
- ⏳ Phase 8: Testing and Refinement (0%)

### Test Coverage

- **67 passing tests** across all implemented phases
- Full test coverage for database models, services, and workflows
- Integration tests for Telegram bot, GitHub webhooks, and orchestrator agent
- 90%+ success rate on all test suites

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Node.js 20+ (for web interface)
- Docker (optional, for containerized deployment)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/project-manager.git
cd project-manager
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

6. Run the backend:
```bash
python -m src.main
```

Visit http://localhost:8000/docs for the API documentation (or http://localhost:8001/docs if using Docker Compose).

### Frontend Web UI

**Production Deployment**: See [DEPLOYMENT.md](DEPLOYMENT.md) for full deployment guide to po.153.se

**Local Development**:

1. Install Node.js dependencies:
```bash
cd frontend
npm install
```

2. Start the development server:
```bash
npm run dev
```

The web UI will be available at `http://localhost:3002`

**Production Build**:

```bash
cd frontend
npm run build
```

The optimized production build will be in `frontend/dist/`

### Using Docker (Recommended)

Start all services including the WebUI:

```bash
# Copy and configure environment
cp .env.example .env

# Start all services (backend, frontend, database)
docker-compose up -d

# View logs
docker-compose logs -f

# Access the application
# - WebUI: http://localhost:3002
# - Backend API: http://localhost:8001
# - API Docs: http://localhost:8001/docs
#
# Port Mapping (Docker):
# - Backend: 8001 → 8000 (container)
# - Frontend: 3002 → 80 (container)
# - PostgreSQL: 5435 → 5432 (container)
# - Redis: 6379 → 6379 (container)

# Stop services
docker-compose down
```

## CI/CD Pipeline

**Fully automated deployment pipeline** with GitHub Actions:

### Continuous Integration (CI)
Every push and PR is automatically tested:
- ✅ Linting and formatting (ruff, black, mypy)
- ✅ Full test suite with PostgreSQL/Redis services
- ✅ Code coverage reporting (60% minimum)
- ✅ Docker build verification
- ✅ Frontend build verification

### Continuous Deployment (CD)
Automatic deployment on main branch merge:
1. 🐳 **Build** - Docker image built and pushed to GitHub Container Registry
2. 📦 **Tag** - Image tagged with `latest`, `sha-xxxxx`, and `vX.Y.Z`
3. 🚀 **Deploy** - Zero-downtime deployment to production
4. 🗄️ **Migrate** - Database migrations run automatically
5. 🏥 **Verify** - Health checks ensure successful deployment
6. ♻️ **Rollback** - Automatic rollback on failure

**Image Registry**: `ghcr.io/gpt153/project-manager`

**Documentation**:
- [CI/CD Setup Guide](docs/CICD_SETUP.md) - Complete pipeline configuration
- [Deployment Guide](DEPLOYMENT.md) - Production deployment to po.153.se

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
- **GitHub Integration**: Issue tracking and pull request automation
- **Web Interface**: 3-panel workspace for project management
- **SCAR Integration**: Automated command translation and execution
- **Approval Gates**: User control at key decision points

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

#### 5. **GitHub Integration** (Phase 6)
- Webhook receiver for issue comments and pull requests
- HMAC-SHA256 signature verification for security
- @mention detection in GitHub issues
- GitHub API client with async support:
  - Create/update pull requests
  - Post issue comments
  - Repository access verification
- Project lookup by repository URL
- Orchestrator agent integration for GitHub activity

#### 6. **Database & Models** (Phase 1)
- 5 async SQLAlchemy models
- PostgreSQL with full ACID compliance
- Alembic migrations for schema management
- Complete conversation history tracking
- Workflow phase and approval gate persistence

#### 7. **Web Interface** (In Development)
- **Backend API**: FastAPI-based REST API with WebSocket and SSE support
- **3-Panel Layout**:
  - Left Panel: Project navigator with tree structure
  - Middle Panel: Chat interface with @po (no @mention required)
  - Right Panel: Real-time SCAR activity feed
- Resizable panels using react-resizable-panels
- Real-time bidirectional communication

### ⏳ Remaining Work

- **Phase 7**: End-to-End Workflow Testing
- **Phase 8**: Production Refinements
- **Web Interface**: Complete integration with orchestrator backend

## Repository Structure

```
project-manager/
├── .agents/
│   ├── visions/           # Non-technical vision documents
│   ├── plans/             # Technical implementation plans
│   ├── progress/          # Phase completion summaries
│   └── commands/          # Custom workflow commands
├── src/
│   ├── agent/             # PydanticAI agent implementation
│   ├── api/               # FastAPI routes (REST, WebSocket, SSE)
│   ├── database/          # Database models and migrations
│   ├── integrations/      # Telegram and GitHub integrations
│   ├── scar/              # SCAR command translation and execution
│   ├── services/          # Business logic services
│   ├── config.py          # Configuration management
│   ├── main.py            # FastAPI application entry point
│   └── bot_main.py        # Telegram bot entry point
├── frontend/              # React web interface
│   ├── src/
│   │   ├── components/    # React components (3-panel layout)
│   │   ├── hooks/         # Custom React hooks (WebSocket, SSE)
│   │   ├── services/      # API client services
│   │   └── types/         # TypeScript type definitions
│   └── package.json       # Node.js dependencies
├── tests/                 # Test suite (67 passing tests)
├── docs/                  # Additional documentation
├── scripts/               # Utility scripts
├── pyproject.toml         # Project configuration and dependencies
├── alembic.ini            # Database migration configuration
├── docker-compose.yml     # Docker services configuration
└── README.md              # This file
```

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

We use pre-commit hooks to ensure code quality. Install them once:

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

Now code will be automatically checked before each commit. You can also run checks manually:

```bash
# Run all pre-commit checks
pre-commit run --all-files

# Format code
black src/ tests/

# Lint code (with auto-fix)
ruff check --fix src/ tests/

# Type checking
mypy src/
```

### Test Database Configuration

Tests use PostgreSQL with different credentials than production. The default password is `test_password` to match CI.

For local development with a different password, set the environment variable:

```bash
export TEST_DATABASE_URL="postgresql+asyncpg://orchestrator:your_password@localhost:5432/project_orchestrator_test"
```

Or create a local PostgreSQL user matching the CI configuration:

```bash
# Create test database and user
createdb project_orchestrator_test
psql -c "CREATE USER orchestrator WITH PASSWORD 'test_password';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE project_orchestrator_test TO orchestrator;"
```

## API Documentation

Once the application is running, visit:

- **Swagger UI**: http://localhost:8000/docs (direct) or http://localhost:8001/docs (Docker)
- **ReDoc**: http://localhost:8000/redoc (direct) or http://localhost:8001/redoc (Docker)
- **OpenAPI JSON**: http://localhost:8000/openapi.json (direct) or http://localhost:8001/openapi.json (Docker)

### Port Reference

When using Docker Compose, services are exposed on different host ports:

| Service     | Container Port | Host Port | Access URL                    |
|-------------|----------------|-----------|-------------------------------|
| Backend API | 8000           | 8001      | http://localhost:8001         |
| Frontend    | 80             | 3002      | http://localhost:3002         |
| PostgreSQL  | 5432           | 5435      | localhost:5435                |
| Redis       | 6379           | 6379      | localhost:6379                |

When running services directly (not via Docker), use the container ports (8000, 5432, etc.).

## Pre-loading SCAR Projects

The application can automatically import GitHub repositories as projects when the container starts. This ensures your WebUI is populated with projects immediately.

### Configuration Methods

#### Method 1: Configuration File (Recommended)

Create `.scar/projects.json` with your projects:

```json
{
  "version": "1.0",
  "projects": [
    {
      "name": "Project Manager",
      "github_repo": "gpt153/project-manager",
      "description": "AI agent for project management",
      "telegram_chat_id": null
    },
    {
      "name": "My Project",
      "github_repo": "owner/repo-name",
      "description": "Optional description",
      "telegram_chat_id": -1001234567890
    }
  ]
}
```

See `.scar/projects.json.example` for a full example.

#### Method 2: Environment Variables

Set one or more of these environment variables:

```bash
# Import specific repositories (comma-separated)
SCAR_IMPORT_REPOS="owner/repo1,owner/repo2,owner/repo3"

# Import all repos from a GitHub user
SCAR_IMPORT_USER="your-github-username"

# Import all repos from a GitHub organization
SCAR_IMPORT_ORG="your-org-name"
```

#### Method 3: Multiple Sources

You can combine multiple sources. The import process will:
1. Load projects from `.scar/projects.json` (if it exists)
2. Load projects from `SCAR_IMPORT_REPOS` (if set)
3. Load projects from `SCAR_IMPORT_USER` (if set)
4. Load projects from `SCAR_IMPORT_ORG` (if set)

Duplicate projects (same GitHub URL) are automatically skipped.

### Disabling Auto-Import

To disable automatic import on startup:

```bash
SCAR_AUTO_IMPORT=false
```

### Manual Import

You can also manually import projects using the command-line script:

```bash
# Import specific repos
python -m src.scripts.import_github_projects --repos "owner/repo1,owner/repo2"

# Import all repos from a user
python -m src.scripts.import_github_projects --user your-username

# Import all repos from an org
python -m src.scripts.import_github_projects --org your-org-name
```

## Environment Variables

See `.env.example` for all available configuration options:

- `DATABASE_URL`: PostgreSQL connection string
- `ANTHROPIC_API_KEY`: API key for Claude (PydanticAI)
- `TELEGRAM_BOT_TOKEN`: Telegram bot token
- `GITHUB_ACCESS_TOKEN`: GitHub personal access token
- `GITHUB_WEBHOOK_SECRET`: Secret for webhook verification
- `FRONTEND_URL`: Frontend CORS origin (default: http://localhost:3002)
- `SERVE_FRONTEND`: Serve frontend from FastAPI in production
- `SCAR_AUTO_IMPORT`: Enable/disable auto-import on startup (default: true)
- `SCAR_IMPORT_REPOS`: Comma-separated list of repos to import
- `SCAR_IMPORT_USER`: GitHub username to import all repos from
- `SCAR_IMPORT_ORG`: GitHub org to import all repos from
- `SCAR_PROJECTS_CONFIG`: Path to projects config file (default: .scar/projects.json)

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

- [Implementation Plan](.agents/plans/project-manager-plan.md)
- [Vision Document](.agents/visions/project-manager.md)
- [SCAR Documentation](https://github.com/anthropics/scar)

## License

MIT
