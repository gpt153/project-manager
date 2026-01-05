# CI/CD Pipeline Setup Guide

This document explains how to set up and use the complete CI/CD pipeline for Project Manager.

## Overview

The CI/CD pipeline automatically:
1. ✅ **Tests** every code change (CI)
2. ✅ **Builds** Docker images on main branch merge
3. ✅ **Deploys** to production automatically with zero downtime

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Developer pushes to branch / Creates PR                    │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  CI Pipeline (ci.yml)                                        │
│  ├─ Lint & Format Check (ruff, black, mypy)                 │
│  ├─ Run Tests (pytest + PostgreSQL + Redis)                 │
│  ├─ Code Coverage Check (60% minimum)                       │
│  └─ Docker Build Test                                       │
└────────────────┬────────────────────────────────────────────┘
                 │
          (PR approved & merged to main)
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  Build & Push Pipeline (build-and-push.yml)                 │
│  ├─ Build production Docker image                           │
│  ├─ Tag: latest, sha-xxxxx, v1.2.3                          │
│  └─ Push to GitHub Container Registry (ghcr.io)             │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  Deploy Pipeline (deploy.yml)                               │
│  ├─ Pull latest image to production VM                      │
│  ├─ Run database migrations                                 │
│  ├─ Zero-downtime rolling restart                           │
│  ├─ Health check verification                               │
│  └─ Auto-rollback on failure                                │
└─────────────────────────────────────────────────────────────┘
```

## Setup Instructions

### 1. GitHub Repository Setup

#### Enable GitHub Actions
1. Go to repository **Settings** → **Actions** → **General**
2. Ensure "Allow all actions and reusable workflows" is selected
3. Save changes

#### Enable GitHub Container Registry
1. Go to repository **Settings** → **Packages**
2. Ensure package visibility is set appropriately (private recommended)
3. GitHub Container Registry is enabled by default

#### Configure Branch Protection (Recommended)
1. Go to **Settings** → **Branches**
2. Add rule for `main` branch:
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging
   - Select required checks:
     - `Lint and Format Check`
     - `Run Tests`
     - `Test Docker Build`
   - ✅ Do not allow bypassing the above settings
3. Save changes

### 2. Self-Hosted Runner Setup (Production VM)

Since the production server is the same VM where deployment happens, you need to set up a GitHub self-hosted runner.

#### Install GitHub Runner

On your production VM (`/home/samuel/po`):

```bash
# Create runner directory
mkdir -p ~/actions-runner && cd ~/actions-runner

# Download latest runner
curl -o actions-runner-linux-x64-2.311.0.tar.gz \
  -L https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz

# Extract
tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz

# Get registration token from GitHub
# Go to: Repository → Settings → Actions → Runners → New self-hosted runner
# Copy the registration token

# Configure runner
./config.sh --url https://github.com/gpt153/project-manager --token YOUR_TOKEN_HERE

# Install as service (runs on boot)
sudo ./svc.sh install
sudo ./svc.sh start

# Check status
sudo ./svc.sh status
```

#### Verify Runner
1. Go to **Settings** → **Actions** → **Runners**
2. You should see your runner listed as "Idle"

### 3. Production Environment Setup

#### Create Deployment Directory

```bash
# Create production directory
sudo mkdir -p /home/samuel/po
sudo chown $USER:$USER /home/samuel/po
cd /home/samuel/po
```

#### Create Production .env File

```bash
# Create .env file with production credentials
cat > /home/samuel/po/.env << 'EOF'
# Application
APP_NAME=Project Manager
APP_ENV=production
LOG_LEVEL=INFO
SECRET_KEY=your-super-secret-production-key-here
DEBUG=false

# Database
DATABASE_URL=postgresql+asyncpg://orchestrator:PROD_PASSWORD@localhost:5432/project_orchestrator
DATABASE_ECHO=false
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# PostgreSQL (for docker-compose)
POSTGRES_USER=orchestrator
POSTGRES_PASSWORD=PROD_PASSWORD
POSTGRES_DB=project_orchestrator

# Anthropic API
ANTHROPIC_API_KEY=sk-ant-your-production-key-here

# Telegram Bot
TELEGRAM_BOT_TOKEN=your-production-bot-token

# GitHub Integration
GITHUB_ACCESS_TOKEN=ghp_your-production-token
GITHUB_WEBHOOK_SECRET=your-webhook-secret

# Redis
REDIS_URL=redis://redis:6379/0

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=false
EOF

# Secure the .env file
chmod 600 /home/samuel/po/.env
```

#### Initial Setup

```bash
# Copy docker-compose production file
cp docker-compose.prod.yml /home/samuel/po/docker-compose.yml

# Start initial deployment
cd /home/samuel/po
docker-compose up -d

# Run initial migrations
docker run --rm \
  --network host \
  --env-file .env \
  ghcr.io/gpt153/project-manager:latest \
  alembic upgrade head
```

### 4. Verify Setup

#### Test CI Pipeline
```bash
# Create a test branch
git checkout -b test-ci-pipeline

# Make a small change
echo "# Test" >> README.md

# Commit and push
git add README.md
git commit -m "Test CI pipeline"
git push origin test-ci-pipeline

# Create PR and watch Actions tab
# All checks should pass
```

#### Test Build Pipeline
```bash
# Merge PR to main (after CI passes)
# Go to Actions tab
# Watch "Build and Push Docker Image" workflow

# Verify image was pushed
docker pull ghcr.io/gpt153/project-manager:latest
```

#### Test Deployment
```bash
# After build completes, deployment should trigger automatically
# Monitor in Actions tab

# Or trigger manually:
# Go to Actions → Deploy to Production → Run workflow

# Check deployment on production VM
cd /home/samuel/po
docker-compose ps

# Check health
curl http://localhost:8000/health
```

## Workflows Explained

### CI Workflow (`ci.yml`)

**Triggers:**
- Push to any branch
- Pull request to main

**Jobs:**
1. **Lint and Format Check**
   - Runs `ruff` linter
   - Runs `black` format checker
   - Runs `mypy` type checker (advisory)

2. **Run Tests**
   - Spins up PostgreSQL and Redis services
   - Runs full test suite with pytest
   - Generates coverage report
   - Fails if coverage < 60%
   - Uploads coverage to Codecov (optional)

3. **Test Docker Build**
   - Verifies Dockerfile builds successfully
   - Uses BuildKit cache for speed
   - Does not push image

**Status:** Must pass for PR to be mergeable

### Build & Push Workflow (`build-and-push.yml`)

**Triggers:**
- Push to main branch
- Manual trigger (workflow_dispatch)

**Process:**
1. Checkout code
2. Set up Docker Buildx
3. Login to GitHub Container Registry (ghcr.io)
4. Extract metadata and create tags:
   - `latest` - latest main branch build
   - `sha-abc1234` - specific commit identifier
   - `v1.2.3` - semantic version (if tagged)
5. Build multi-platform image (linux/amd64)
6. Push to ghcr.io/gpt153/project-manager
7. Use layer caching for fast builds

**Outputs:**
- Image tags
- Image digest (SHA256)

### Deploy Workflow (`deploy.yml`)

**Triggers:**
- Successful completion of Build & Push workflow
- Manual trigger (workflow_dispatch)

**Process:**
1. **Deploy Job:**
   - Runs on self-hosted runner (production VM)
   - Checks out deployment configs
   - Logs into GitHub Container Registry
   - Pulls latest Docker image
   - Copies deployment files to `/home/samuel/po`
   - Runs database migrations
   - Performs zero-downtime rolling restart
   - Waits for health check (up to 120s)
   - Verifies deployment
   - Cleans up old images (older than 72h)

2. **Rollback Job** (on failure):
   - Automatically triggers if deployment fails
   - Identifies previous working image
   - Restarts containers with previous image
   - Notifies via GitHub Actions summary

**Zero-Downtime Strategy:**
- Uses `docker-compose up -d --no-deps app`
- Starts new container before stopping old one
- Health check ensures new container is ready
- Old container stops only after new one is healthy

## Manual Operations

### Deploy Specific Version

```bash
# Via GitHub Actions UI:
# Actions → Deploy to Production → Run workflow
# Input: sha-abc1234 (or latest, or v1.2.3)

# Via command line on production VM:
cd /home/samuel/po
./deploy.sh sha-abc1234
```

### Rollback to Previous Version

```bash
# Find previous image
docker images | grep project-manager

# Deploy specific version
cd /home/samuel/po
docker-compose down
docker pull ghcr.io/gpt153/project-manager:sha-previous
sed -i 's|:latest|:sha-previous|' docker-compose.yml
docker-compose up -d
```

### View Logs

```bash
# Real-time logs
cd /home/samuel/po
docker-compose logs -f app

# Last 100 lines
docker-compose logs --tail=100 app

# Specific time range
docker-compose logs --since 10m app
```

### Run Migrations Manually

```bash
cd /home/samuel/po
docker run --rm \
  --network host \
  --env-file .env \
  ghcr.io/gpt153/project-manager:latest \
  alembic upgrade head
```

### Check Deployment Status

```bash
cd /home/samuel/po
docker-compose ps
curl http://localhost:8000/health
docker-compose logs --tail=20 app
```

## Troubleshooting

### CI Pipeline Failures

#### Tests Failing
```bash
# Run tests locally
pytest -v

# Run specific test
pytest tests/test_main.py::test_health_endpoint -v

# Check database connection
docker-compose up -d postgres
psql -U orchestrator -h localhost -d project_orchestrator_test
```

#### Linting Failures
```bash
# Auto-fix formatting
black src/ tests/

# Check linting issues
ruff check src/ tests/

# Fix auto-fixable issues
ruff check --fix src/ tests/
```

### Build Pipeline Failures

#### Docker Build Fails
```bash
# Build locally
docker build -t test-build .

# Check Dockerfile syntax
docker build --no-cache -t test-build .

# Check .dockerignore
cat .dockerignore
```

#### Push to Registry Fails
```bash
# Check authentication
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Verify package permissions
# Go to: Repository → Settings → Packages
```

### Deployment Failures

#### Health Check Fails
```bash
# Check container logs
cd /home/samuel/po
docker-compose logs app

# Check specific container
docker logs project-manager-app

# Check health endpoint manually
curl -v http://localhost:8000/health

# Check environment variables
docker-compose exec app env | grep DATABASE_URL
```

#### Database Migration Fails
```bash
# Check current migration state
docker-compose exec app alembic current

# Check migration history
docker-compose exec app alembic history

# Try migration manually
docker-compose exec app alembic upgrade head

# Rollback migration
docker-compose exec app alembic downgrade -1
```

#### Port Already in Use
```bash
# Find process using port 8000
sudo lsof -i :8000

# Stop existing containers
docker-compose down

# Restart
docker-compose up -d
```

## Security Best Practices

### Secrets Management
- ✅ Never commit `.env` files
- ✅ Use GitHub Secrets for sensitive data
- ✅ Rotate secrets regularly
- ✅ Use strong passwords (20+ characters)

### Container Security
- ✅ Images are private by default on GHCR
- ✅ Use specific image tags for production
- ✅ Scan images for vulnerabilities
- ✅ Keep base images updated

### Access Control
- ✅ Limit self-hosted runner permissions
- ✅ Use separate user for deployment
- ✅ Restrict file permissions (chmod 600 .env)
- ✅ Enable 2FA on GitHub

## Monitoring and Maintenance

### Health Checks
```bash
# Automated health check (every 30s)
docker-compose ps

# Manual health check
curl http://localhost:8000/health

# Database health
docker-compose exec postgres pg_isready
```

### Log Rotation
Logs are automatically rotated:
- Max size: 10MB per file
- Keep: 3 files
- Total: ~30MB max per container

### Disk Space Management
```bash
# Clean old images (automatic in deploy workflow)
docker image prune -a -f --filter "until=72h"

# Clean all unused resources
docker system prune -a --volumes

# Check disk usage
docker system df
```

### Backup Strategy

#### Database Backups
```bash
# Create backup
docker-compose exec postgres pg_dump -U orchestrator project_orchestrator > backup.sql

# Automated backups (add to cron)
# 0 2 * * * cd /home/samuel/po && docker-compose exec postgres pg_dump -U orchestrator project_orchestrator > backups/$(date +\%Y\%m\%d).sql
```

#### Configuration Backups
```bash
# Backup .env and docker-compose.yml
cp /home/samuel/po/.env ~/backups/.env.$(date +%Y%m%d)
cp /home/samuel/po/docker-compose.yml ~/backups/docker-compose.yml.$(date +%Y%m%d)
```

## Performance Optimization

### Docker Build Speed
- ✅ Layer caching enabled (GitHub Actions cache)
- ✅ Multi-stage builds (if needed in future)
- ✅ .dockerignore excludes unnecessary files

### Deployment Speed
- ✅ Zero-downtime deployments
- ✅ Parallel image pulls
- ✅ Health check timeout: 120s

### Database Performance
- ✅ Connection pooling (10 connections)
- ✅ Max overflow: 20 connections
- ✅ Async database operations

## Cost Analysis

### GitHub Actions
- Free tier: 2,000 minutes/month
- Typical usage:
  - CI per PR: ~3-5 minutes
  - Build: ~2-3 minutes
  - Deploy: ~1-2 minutes
- Estimate: 50-100 minutes/month (well within free tier)

### GitHub Container Registry
- Free for public repositories
- Free for private repositories with usage limits
- Typical usage: < 1GB storage

### Self-Hosted Runner
- No GitHub cost (runs on your VM)
- Minimal resource usage:
  - CPU: < 5% during idle
  - Memory: ~100MB
  - Disk: ~500MB

**Total Cost: $0/month** ✅

## Next Steps

### Phase 1: Current Implementation ✅
- CI testing pipeline
- Docker build and push
- Automated deployment
- Zero-downtime restarts
- Auto-rollback on failure

### Phase 2: Future Enhancements
- [ ] Staging environment
- [ ] Manual approval gates for production
- [ ] Slack/Telegram deployment notifications
- [ ] Performance monitoring integration
- [ ] Automated database backups
- [ ] Security scanning (Snyk, Trivy)
- [ ] Load testing before deployment

### Phase 3: Advanced Features
- [ ] Blue-green deployments
- [ ] Canary deployments
- [ ] A/B testing infrastructure
- [ ] Multi-region deployment
- [ ] Disaster recovery automation

## Support

For issues or questions:
1. Check GitHub Actions logs
2. Review container logs: `docker-compose logs`
3. Check this documentation
4. Create GitHub issue with details

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Project Deployment Guide](DEPLOYMENT.md)
- [Testing Guide](TESTING_GUIDE.md)
