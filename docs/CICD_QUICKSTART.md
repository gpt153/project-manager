# CI/CD Quick Start Guide

Get the CI/CD pipeline up and running in under 30 minutes.

## Prerequisites

- [ ] GitHub repository with admin access
- [ ] Production VM running Ubuntu/Debian
- [ ] Docker and Docker Compose installed on VM
- [ ] SSH access to production VM

## Step 1: Enable GitHub Actions (2 minutes)

1. Go to your repository on GitHub
2. Click **Settings** → **Actions** → **General**
3. Select "Allow all actions and reusable workflows"
4. Click **Save**

✅ **Done!** GitHub Actions is now enabled.

## Step 2: Set Up Self-Hosted Runner (10 minutes)

On your production VM (`/home/samuel/po`):

```bash
# Install runner
mkdir -p ~/actions-runner && cd ~/actions-runner
curl -o actions-runner.tar.gz -L https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz
tar xzf actions-runner.tar.gz

# Get registration token:
# Go to: GitHub → Repository → Settings → Actions → Runners → New self-hosted runner
# Copy the token shown

# Configure runner (replace YOUR_TOKEN)
./config.sh --url https://github.com/gpt153/project-orchestrator --token YOUR_TOKEN

# Install as service
sudo ./svc.sh install
sudo ./svc.sh start

# Verify
sudo ./svc.sh status
```

✅ **Verify**: Go to Settings → Actions → Runners. You should see your runner as "Idle".

## Step 3: Set Up Production Environment (10 minutes)

```bash
# Create deployment directory
sudo mkdir -p /home/samuel/po
sudo chown $USER:$USER /home/samuel/po
cd /home/samuel/po

# Create .env file (IMPORTANT: Add your real credentials)
cat > .env << 'EOF'
APP_NAME=Project Orchestrator
APP_ENV=production
LOG_LEVEL=INFO
SECRET_KEY=CHANGE_THIS_TO_RANDOM_32_CHAR_STRING
DEBUG=false

DATABASE_URL=postgresql+asyncpg://orchestrator:CHANGE_DB_PASSWORD@localhost:5432/project_orchestrator
POSTGRES_USER=orchestrator
POSTGRES_PASSWORD=CHANGE_DB_PASSWORD
POSTGRES_DB=project_orchestrator

ANTHROPIC_API_KEY=sk-ant-YOUR_KEY_HERE
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
GITHUB_ACCESS_TOKEN=ghp_YOUR_GITHUB_TOKEN
GITHUB_WEBHOOK_SECRET=YOUR_WEBHOOK_SECRET

REDIS_URL=redis://redis:6379/0
API_HOST=0.0.0.0
API_PORT=8000
EOF

# Secure the file
chmod 600 .env

# Copy docker-compose production config (do this after first merge to main)
# It will be available at: /home/samuel/po/docker-compose.yml
```

✅ **Done!** Production environment is configured.

## Step 4: Enable Container Registry (2 minutes)

GitHub Container Registry (GHCR) is enabled by default. No action needed!

The pipeline will push images to:
```
ghcr.io/gpt153/project-orchestrator:latest
```

✅ **Done!** Container registry is ready.

## Step 5: Test the Pipeline (5 minutes)

### Test CI
```bash
# On your local machine
git checkout -b test-ci
echo "# Test CI" >> README.md
git add README.md
git commit -m "Test: CI pipeline"
git push origin test-ci

# Create PR on GitHub
# Watch "Actions" tab - CI should run and pass
```

### Test Build & Deploy
```bash
# Merge the PR to main
# Watch "Actions" tab
# Should see:
# 1. "Build and Push Docker Image" workflow
# 2. "Deploy to Production" workflow

# Verify on production VM
cd /home/samuel/po
docker-compose ps
curl http://localhost:8000/health
```

✅ **Done!** Full CI/CD pipeline is working!

## Step 6: Protect Main Branch (3 minutes)

1. Go to **Settings** → **Branches**
2. Click **Add rule**
3. Branch name pattern: `main`
4. Enable:
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging
   - Select: `Lint and Format Check`, `Run Tests`, `Test Docker Build`
5. Click **Create**

✅ **Done!** Main branch is protected.

## Verification Checklist

- [ ] GitHub Actions enabled
- [ ] Self-hosted runner installed and running
- [ ] Runner shows "Idle" in GitHub
- [ ] Production .env file created with real credentials
- [ ] CI workflow passes on test PR
- [ ] Docker image builds and pushes to ghcr.io
- [ ] Deployment succeeds on production VM
- [ ] Health check returns 200 OK
- [ ] Main branch protection enabled

## What Happens Now?

Every time you merge to `main`:

1. ✅ **CI runs automatically** (tests, linting, coverage)
2. ✅ **Docker image builds** and pushes to ghcr.io
3. ✅ **Production deploys automatically** with zero downtime
4. ✅ **Database migrations run** automatically
5. ✅ **Health checks verify** deployment
6. ✅ **Rollback if failure** occurs

## Troubleshooting

### Runner not showing up
```bash
# Check runner service
sudo ~/actions-runner/svc.sh status

# View runner logs
journalctl -u actions.runner.* -f
```

### Deployment fails
```bash
# Check .env file exists
ls -la /home/samuel/po/.env

# Check docker-compose.yml exists
ls -la /home/samuel/po/docker-compose.yml

# Check runner logs
sudo journalctl -u actions.runner.* -f
```

### Health check fails
```bash
# Check containers
docker-compose ps

# Check logs
docker-compose logs app

# Check environment
docker-compose exec app env
```

## Next Steps

1. Read [Full CI/CD Setup Guide](CICD_SETUP.md) for advanced configuration
2. Set up monitoring and alerts
3. Configure backup automation
4. Add staging environment (optional)

## Getting Help

- Check [CI/CD Setup Guide](CICD_SETUP.md) for detailed documentation
- View GitHub Actions logs in "Actions" tab
- Check container logs: `docker-compose logs`

---

**Total setup time: ~30 minutes**
**Ongoing maintenance: ~0 minutes** (fully automated!)
