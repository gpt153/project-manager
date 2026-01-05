# CI/CD Pipeline Implementation Plan

## Project Context

**Repository**: `gpt153/project-manager`
**Current State**: Production-ready orchestrator (75% complete) with Docker support
**Goal**: Complete CI/CD pipeline for automatic deployment when main branch is updated/merged

## Current Infrastructure Analysis

### Existing Components
1. **Dockerfile** - Python 3.11 slim-based, runs migrations + FastAPI app
2. **docker-compose.yml** - Multi-service setup (app, postgres, redis)
3. **Testing Suite** - 67+ passing tests with pytest, 68%+ coverage
4. **Documentation** - Comprehensive deployment and testing guides
5. **Python Stack** - FastAPI, SQLAlchemy, PydanticAI, Telegram Bot, GitHub Integration

### Missing Components
1. ❌ GitHub Actions workflows
2. ❌ Container registry configuration
3. ❌ Production deployment automation
4. ❌ Environment-specific configurations

## CI/CD Pipeline Architecture

### Pipeline Stages

```
┌──────────────────────────────────────────────────────────────┐
│                     TRIGGER: Push to main                     │
│                  or Pull Request to main                       │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│  STAGE 1: CI - Continuous Integration                         │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 1. Checkout code                                        │  │
│  │ 2. Set up Python 3.11                                   │  │
│  │ 3. Install dependencies (with cache)                    │  │
│  │ 4. Run linters (ruff, black --check)                    │  │
│  │ 5. Run type checks (mypy)                               │  │
│  │ 6. Run tests (pytest with coverage)                     │  │
│  │ 7. Upload coverage reports                              │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
                              │
                     (Only on main branch)
                              ▼
┌──────────────────────────────────────────────────────────────┐
│  STAGE 2: Build - Docker Image Creation                       │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 1. Set up Docker Buildx                                 │  │
│  │ 2. Login to GitHub Container Registry (ghcr.io)         │  │
│  │ 3. Extract metadata (tags, labels)                      │  │
│  │ 4. Build and push Docker image                          │  │
│  │    - Tag: ghcr.io/gpt153/project-manager:latest    │  │
│  │    - Tag: ghcr.io/gpt153/project-manager:SHA       │  │
│  │    - Tag: ghcr.io/gpt153/project-manager:vX.Y.Z    │  │
│  │ 5. Cache Docker layers for faster builds                │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│  STAGE 3: Deploy - Production Container Update                │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ OPTION A: Self-hosted deployment                        │  │
│  │ 1. SSH to production server                             │  │
│  │ 2. Pull latest image from GHCR                          │  │
│  │ 3. Run database migrations                              │  │
│  │ 4. Restart containers (zero-downtime)                   │  │
│  │ 5. Health check verification                            │  │
│  │                                                          │  │
│  │ OPTION B: Container platform (future)                   │  │
│  │ - Deploy to Railway, Render, Fly.io, etc.               │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│  STAGE 4: Verify - Post-Deployment Checks                     │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 1. Wait for service startup (30s)                       │  │
│  │ 2. Check /health endpoint                               │  │
│  │ 3. Verify database connectivity                         │  │
│  │ 4. Send Telegram notification (optional)                │  │
│  │ 5. Create GitHub deployment status                      │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

## Implementation Steps

### Step 1: Create GitHub Actions Workflow Structure

**Files to create:**
```
.github/
├── workflows/
│   ├── ci.yml                 # CI pipeline (tests, linting)
│   ├── build-and-push.yml     # Build Docker image, push to GHCR
│   └── deploy.yml             # Deploy to production
└── dependabot.yml             # Automated dependency updates
```

### Step 2: CI Workflow (ci.yml)

**Purpose**: Run on every PR and push to ensure code quality

**Triggers**:
- Push to any branch
- Pull requests to main

**Jobs**:
1. **lint-and-format**:
   - Run ruff linter
   - Run black formatter check
   - Run mypy type checker

2. **test**:
   - Matrix strategy: Python 3.11
   - Set up PostgreSQL service container
   - Set up Redis service container
   - Install dependencies
   - Run pytest with coverage
   - Upload coverage to Codecov (optional)
   - Fail if coverage < 60%

3. **docker-build-test**:
   - Test that Dockerfile builds successfully
   - Don't push (just verify build works)

**Exit Criteria**: All jobs must pass for PR to be mergeable

### Step 3: Build and Push Workflow (build-and-push.yml)

**Purpose**: Build production Docker image and push to registry

**Triggers**:
- Push to main branch (after merge)
- Manual trigger (workflow_dispatch)
- Version tags (v*.*.*)

**Jobs**:
1. **build-and-push**:
   - Checkout code
   - Set up Docker Buildx (for multi-platform builds)
   - Login to GitHub Container Registry
   - Extract Docker metadata:
     - `latest` tag for main branch
     - `sha-<commit>` tag for traceability
     - `v1.2.3` tag for version releases
   - Build and push with cache layers
   - Output image digest for deployment

**Image naming**:
```
ghcr.io/gpt153/project-manager:latest
ghcr.io/gpt153/project-manager:sha-abc1234
ghcr.io/gpt153/project-manager:v0.1.0
```

### Step 4: Production Deployment Workflow (deploy.yml)

**Purpose**: Deploy the built image to production server

**Triggers**:
- Completion of build-and-push workflow (workflow_run)
- Manual trigger with environment selection

**Prerequisites** (User must set up):
1. Production server with Docker installed
2. SSH access configured
3. GitHub secrets configured (see below)

**Jobs**:
1. **deploy-to-production**:
   - Download deployment artifacts
   - SSH to production server
   - Create deployment directory if not exists
   - Pull latest docker-compose production config
   - Pull latest Docker image from GHCR
   - Run database migrations (if needed)
   - Perform rolling restart:
     - Start new container
     - Wait for health check
     - Stop old container
   - Verify deployment
   - Create GitHub deployment event

**Deployment Strategy** (Zero-downtime):
```bash
# Pull new image
docker pull ghcr.io/gpt153/project-manager:latest

# Run migrations (in separate container)
docker run --rm --env-file .env \
  ghcr.io/gpt153/project-manager:latest \
  alembic upgrade head

# Update and restart (docker-compose handles gracefully)
docker-compose pull
docker-compose up -d --no-deps --build app

# Health check
timeout 60 bash -c 'until curl -f http://localhost:8000/health; do sleep 5; done'
```

### Step 5: Production Configuration

**New file**: `docker-compose.prod.yml`

Extends base `docker-compose.yml` with production overrides:
```yaml
version: '3.8'

services:
  app:
    image: ghcr.io/gpt153/project-manager:latest
    restart: always
    environment:
      - APP_ENV=production
      - DATABASE_URL=${DATABASE_URL}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - GITHUB_ACCESS_TOKEN=${GITHUB_ACCESS_TOKEN}
      - GITHUB_WEBHOOK_SECRET=${GITHUB_WEBHOOK_SECRET}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  postgres:
    restart: always
    volumes:
      - /var/lib/project-manager/postgres:/var/lib/postgresql/data
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  redis:
    restart: always
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Step 6: Required GitHub Secrets

**Repository Secrets** (Settings > Secrets and variables > Actions):

1. **Container Registry**:
   - `GHCR_TOKEN` - GitHub Personal Access Token with `write:packages` scope
     - Or use default `GITHUB_TOKEN` (automatically provided)

2. **Production Deployment** (if using self-hosted):
   - `PRODUCTION_HOST` - IP or hostname of production server
   - `PRODUCTION_USER` - SSH username (e.g., `deploy`)
   - `PRODUCTION_SSH_KEY` - Private SSH key for authentication
   - `PRODUCTION_ENV` - Production environment variables (entire .env file)

3. **Optional - Notifications**:
   - `SLACK_WEBHOOK_URL` - For deployment notifications
   - `TELEGRAM_NOTIFICATION_TOKEN` - For Telegram notifications

### Step 7: Deployment Script for Production Server

**New file**: `scripts/deploy.sh`

Script that runs on the production server:
```bash
#!/bin/bash
set -e

echo "🚀 Starting deployment..."

# Configuration
REPO="ghcr.io/gpt153/project-manager"
TAG="${1:-latest}"
COMPOSE_FILE="docker-compose.prod.yml"
APP_DIR="/opt/project-manager"

cd "$APP_DIR"

# Pull latest image
echo "📦 Pulling Docker image: $REPO:$TAG"
docker pull "$REPO:$TAG"

# Run migrations
echo "🗄️  Running database migrations..."
docker run --rm \
  --network project-manager_default \
  --env-file .env \
  "$REPO:$TAG" \
  alembic upgrade head

# Update services
echo "🔄 Updating services..."
docker-compose -f "$COMPOSE_FILE" pull
docker-compose -f "$COMPOSE_FILE" up -d

# Wait for health check
echo "🏥 Waiting for health check..."
timeout 60 bash -c 'until curl -f http://localhost:8000/health; do echo "Waiting..."; sleep 5; done'

echo "✅ Deployment complete!"

# Show status
docker-compose -f "$COMPOSE_FILE" ps
```

### Step 8: Frontend Build Integration (Future)

Since there's a frontend in `frontend/`:

**Additional workflow**: `.github/workflows/frontend.yml`

```yaml
name: Frontend CI/CD

on:
  push:
    branches: [main]
    paths:
      - 'frontend/**'
  pull_request:
    paths:
      - 'frontend/**'

jobs:
  build-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        working-directory: frontend
        run: npm ci

      - name: Build frontend
        working-directory: frontend
        run: npm run build

      - name: Upload build artifacts
        uses: actions/upload-artifact@v4
        with:
          name: frontend-build
          path: frontend/dist/
```

## Security Considerations

1. **Secret Management**:
   - Never commit secrets to repository
   - Use GitHub Secrets for all sensitive data
   - Use environment-specific secret scopes

2. **Container Registry**:
   - Use GitHub Container Registry (GHCR) - free and integrated
   - Make images private (default for GHCR)
   - Use SHA tags for immutable references

3. **SSH Access**:
   - Use dedicated deploy key, not personal SSH key
   - Restrict SSH user permissions (only Docker commands)
   - Consider GitHub deployment keys

4. **Database Migrations**:
   - Always run migrations before deployment
   - Use transaction-safe migrations
   - Keep backup before migration

## Testing Strategy

1. **Pre-merge (PR)**:
   - All tests must pass
   - Code coverage requirement: 60%+
   - Linting and formatting checks
   - Docker build verification

2. **Post-merge (main)**:
   - Full integration tests
   - Build production Docker image
   - Tag with commit SHA

3. **Pre-deployment**:
   - Smoke tests on staging (if available)
   - Database migration dry-run

4. **Post-deployment**:
   - Health check endpoint
   - Basic functionality test
   - Telegram bot responsiveness
   - GitHub webhook test

## Rollback Strategy

1. **Immediate Rollback**:
   ```bash
   # Revert to previous image
   docker-compose -f docker-compose.prod.yml down
   docker tag ghcr.io/gpt153/project-manager:sha-<previous> \
              ghcr.io/gpt153/project-manager:latest
   docker-compose -f docker-compose.prod.yml up -d
   ```

2. **Database Rollback**:
   ```bash
   # Rollback migrations
   docker-compose exec app alembic downgrade -1
   ```

3. **GitHub Rollback**:
   - Revert merge commit
   - Re-run pipeline with previous version

## Monitoring and Alerts

**Future enhancements**:
1. **GitHub Deployment Environments**:
   - Create "production" environment
   - Track deployment history
   - Enable manual approval gates

2. **Slack/Telegram Notifications**:
   - Deployment started
   - Deployment succeeded
   - Deployment failed
   - Health check failures

3. **Metrics Collection**:
   - Deployment frequency
   - Build duration
   - Test success rate
   - Deployment success rate

## File Changes Summary

### New Files to Create:
```
.github/
├── workflows/
│   ├── ci.yml                          # CI pipeline
│   ├── build-and-push.yml              # Docker build/push
│   ├── deploy.yml                      # Production deployment
│   └── frontend.yml                    # Frontend build (future)
└── dependabot.yml                      # Dependency updates

docker-compose.prod.yml                  # Production overrides
scripts/deploy.sh                        # Server deployment script
.dockerignore                            # Docker build optimization
```

### Files to Modify:
```
README.md                                # Add CI/CD badges and deployment docs
docs/DEPLOYMENT.md                       # Add GitHub Actions section
.env.example                             # Add production placeholders
```

### GitHub Repository Settings to Configure:
1. Enable GitHub Actions
2. Add repository secrets (see Step 6)
3. Protect main branch:
   - Require status checks (CI tests)
   - Require PR reviews (optional)
   - No force pushes
4. Enable GitHub Container Registry
5. Create deployment environment "production" (optional)

## Implementation Order

1. ✅ **Phase 1**: CI Workflow (ci.yml)
   - Set up linting and testing
   - Verify all tests pass
   - No deployment yet

2. ✅ **Phase 2**: Build Workflow (build-and-push.yml)
   - Set up Docker build
   - Push to GHCR
   - Test image can be pulled

3. ✅ **Phase 3**: Production Configuration
   - Create docker-compose.prod.yml
   - Create deployment script
   - Document server setup

4. ✅ **Phase 4**: Deployment Workflow (deploy.yml)
   - Set up SSH deployment
   - Implement rolling restart
   - Add health checks

5. ✅ **Phase 5**: Documentation
   - Update README with badges
   - Document deployment process
   - Add troubleshooting guide

6. ⏳ **Phase 6**: Enhancements (Future)
   - Staging environment
   - Manual approval gates
   - Slack/Telegram notifications
   - Monitoring dashboards

## Success Criteria

### Must Have:
- ✅ CI tests run on every PR
- ✅ Docker image builds on main merge
- ✅ Image pushed to GitHub Container Registry
- ✅ Production container auto-updates on main merge
- ✅ Database migrations run automatically
- ✅ Zero-downtime deployments
- ✅ Health check verification

### Nice to Have:
- ⏳ Frontend build pipeline
- ⏳ Deployment notifications
- ⏳ Staging environment
- ⏳ Manual approval for production
- ⏳ Automated rollback on failure

## Estimated Effort

- **CI Workflow**: 1-2 hours
- **Build & Push Workflow**: 1-2 hours
- **Production Config**: 1 hour
- **Deployment Workflow**: 2-3 hours
- **Documentation**: 1 hour
- **Testing & Debugging**: 2-3 hours

**Total**: 8-12 hours for complete CI/CD pipeline

## Dependencies and Prerequisites

### Required:
1. Python 3.11+
2. Docker + Docker Compose
3. PostgreSQL 15
4. Redis 7
5. GitHub Personal Access Token (for GHCR)

### For Production Deployment:
1. Production server (VPS, EC2, etc.)
2. SSH access to server
3. Docker installed on server
4. Domain name (optional, for HTTPS)
5. Reverse proxy configured (Nginx/Caddy)

## Notes

- **Container Registry Choice**: Using GitHub Container Registry (ghcr.io) because:
  - Free for public and private repos
  - Integrated with GitHub Actions
  - Good for open-source projects
  - No additional account needed (unlike Docker Hub)

- **Deployment Strategy**: Supporting self-hosted deployment first, with container platforms (Railway, Render) as future option

- **Database Migrations**: Critical to run migrations before container restart to avoid schema mismatches

- **Health Checks**: Essential for zero-downtime deployments - new container must be healthy before old one stops

## Questions to Resolve

1. **Deployment Target**: Where will production run?
   - [ ] Self-hosted server (user provides)
   - [ ] Railway
   - [ ] Render.com
   - [ ] Fly.io
   - [ ] Other?

2. **Approval Gates**: Should production deployment require manual approval?
   - [ ] Auto-deploy on main merge
   - [ ] Manual approval required

3. **Environments**: Need staging environment?
   - [ ] Production only
   - [ ] Staging + Production

4. **Notifications**: Deployment notifications needed?
   - [ ] None
   - [ ] Telegram
   - [ ] Slack
   - [ ] Email

## Recommended Answer for User

Based on the issue request "complete cd/ci pipeline", I recommend:

1. **Start with**: Auto-deploy to GHCR on main merge (no production server needed yet)
2. **Include**: Full CI testing pipeline
3. **Prepare**: Deployment scripts for when user has production server
4. **Document**: Clear setup instructions for production deployment

This gives the user a complete CI/CD pipeline that:
- ✅ Tests every change
- ✅ Builds production Docker images automatically
- ✅ Is ready to deploy when production server is configured
- ✅ Can be easily extended to auto-deploy later

---

**Plan Status**: Ready for Review
**Next Step**: Implement workflows in order (CI → Build → Deploy → Docs)
