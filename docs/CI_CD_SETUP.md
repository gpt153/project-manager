# CI/CD Setup Guide

Automated deployment pipeline for Project Orchestrator - builds Docker images and deploys to production on every push to `main`.

## Overview

Two deployment options available:

1. **Self-Hosted Runner** (Recommended - Simpler)
   - Runs directly on production server
   - No SSH configuration needed
   - Faster builds (local)
   - Uses `.github/workflows/deploy-local.yml`

2. **Remote SSH Deployment**
   - Deploys from GitHub Actions to remote server
   - Requires SSH key setup
   - Uses `.github/workflows/deploy.yml`

---

## Option 1: Self-Hosted Runner (Recommended)

### Prerequisites

- Production server: `/home/samuel/po`
- Docker and Docker Compose installed
- GitHub account with admin access to repository

### Setup Steps

#### 1. Create GitHub Repository

```bash
cd /home/samuel/po

# Add GitHub remote (replace with your repository)
git remote add origin https://github.com/YOUR_USERNAME/project-orchestrator.git

# Push initial commit
git push -u origin main
```

#### 2. Install GitHub Self-Hosted Runner

On your production server:

1. Go to your GitHub repository
2. Navigate to: Settings → Actions → Runners → New self-hosted runner
3. Follow the instructions to download and configure the runner:

```bash
# Example commands (GitHub will provide exact commands)
mkdir -p ~/actions-runner && cd ~/actions-runner

# Download
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz

# Extract
tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz

# Configure (use token from GitHub)
./config.sh --url https://github.com/YOUR_USERNAME/project-orchestrator --token YOUR_TOKEN

# Install as service
sudo ./svc.sh install
sudo ./svc.sh start
```

4. Verify runner appears as "Idle" in GitHub Settings → Actions → Runners

#### 3. Configure Environment Variables

```bash
cd /home/samuel/po

# Copy production template
cp .env.production .env

# Edit with your actual values
nano .env
```

Required variables:
- `POSTGRES_PASSWORD` - Secure database password
- `ANTHROPIC_API_KEY` - Claude API key
- `TELEGRAM_BOT_TOKEN` - Bot token from @BotFather
- `GITHUB_ACCESS_TOKEN` - GitHub personal access token
- `GITHUB_WEBHOOK_SECRET` - Webhook secret

#### 4. Test Deployment

Manual deployment test:

```bash
cd /home/samuel/po
./scripts/deploy.sh
```

Verify services:

```bash
docker compose ps
curl http://localhost:8001/health
```

#### 5. Trigger Automatic Deployment

Now every push to `main` will trigger automatic deployment:

```bash
cd /home/samuel/po

# Make a change
echo "Test" >> README.md

# Commit and push
git add .
git commit -m "Test CI/CD pipeline"
git push origin main
```

Watch the deployment:
- GitHub: Actions tab shows workflow progress
- Server logs: `docker compose logs -f app`

---

## Option 2: Remote SSH Deployment

Use this if you want to deploy from GitHub Actions to a remote server.

### Setup Steps

#### 1. Generate SSH Key (on your local machine)

```bash
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_deploy
```

#### 2. Add Public Key to Production Server

```bash
# Copy public key
cat ~/.ssh/github_deploy.pub

# On production server, add to authorized_keys
ssh samuel@your-server
echo "YOUR_PUBLIC_KEY" >> ~/.ssh/authorized_keys
```

#### 3. Configure GitHub Secrets

Go to GitHub repository → Settings → Secrets and variables → Actions → New repository secret

Add these secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `PROD_HOST` | `your-server-ip` | Production server IP or hostname |
| `PROD_USER` | `samuel` | SSH username |
| `PROD_SSH_KEY` | `<contents of ~/.ssh/github_deploy>` | Private SSH key (entire file) |
| `GITHUB_TOKEN` | Auto-provided by GitHub | Used for container registry |

#### 4. Update Workflow

The repository is set up to use `.github/workflows/deploy.yml` for remote deployment.

#### 5. Enable Container Registry

GitHub Container Registry is automatically enabled. Images will be pushed to:
```
ghcr.io/YOUR_USERNAME/project-orchestrator:latest
```

#### 6. Test Deployment

Push to main branch:

```bash
git add .
git commit -m "Test remote deployment"
git push origin main
```

Monitor in GitHub Actions tab.

---

## Manual Deployment

You can always deploy manually using the script:

```bash
cd /home/samuel/po
./scripts/deploy.sh
```

Or use Docker Compose directly:

```bash
cd /home/samuel/po

# Production deployment
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# Development deployment
docker compose up -d
```

---

## Troubleshooting

### Deployment fails with permission error

```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### Health check fails

```bash
# Check logs
docker compose logs app

# Check if services are running
docker compose ps

# Test database connection
docker compose exec postgres psql -U orchestrator -d project_orchestrator -c "SELECT 1"
```

### Self-hosted runner not starting

```bash
cd ~/actions-runner
sudo ./svc.sh status
sudo ./svc.sh start
```

### Docker build fails

```bash
# Clean Docker cache
docker system prune -a -f

# Rebuild without cache
docker compose build --no-cache
```

---

## Monitoring

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f app
docker compose logs -f postgres
```

### Service Status

```bash
docker compose ps
```

### Health Check

```bash
curl http://localhost:8001/health
```

---

## Rollback

If deployment fails, rollback to previous version:

```bash
cd /home/samuel/po

# Checkout previous commit
git log --oneline
git checkout PREVIOUS_COMMIT_HASH

# Redeploy
./scripts/deploy.sh

# Or return to main
git checkout main
```

---

## Production Checklist

Before going live:

- [ ] Environment variables configured in `.env`
- [ ] Database password is secure (not default)
- [ ] GitHub runner is installed and active (if using self-hosted)
- [ ] SSH keys configured (if using remote deployment)
- [ ] Health check endpoint responds: `http://localhost:8001/health`
- [ ] Docker containers restart policy: `unless-stopped`
- [ ] Logs are being written: `docker compose logs`
- [ ] Disk space monitored (Docker images can grow)
- [ ] Backup strategy for PostgreSQL data

---

## Workflow Files

- `.github/workflows/deploy-local.yml` - Self-hosted runner deployment
- `.github/workflows/deploy.yml` - Remote SSH deployment
- `scripts/deploy.sh` - Manual deployment script
- `docker-compose.yml` - Development configuration
- `docker-compose.prod.yml` - Production configuration
