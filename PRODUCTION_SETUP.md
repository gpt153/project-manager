#!/bin/bash
# Production Setup Guide for Project Manager
# Deployment to /home/samuel/po on VM

This guide walks you through setting up the Project Manager in production on your VM.

## Quick Start (TL;DR)

```bash
# 1. Clone and run deployment script
cd /home/samuel
git clone https://github.com/gpt153/project-manager.git po
cd po
chmod +x deploy.sh
./deploy.sh

# 2. Edit configuration
nano .env  # Add your API keys

# 3. Test deployment
chmod +x test_deployment.sh
./test_deployment.sh

# 4. Access the application
curl http://localhost:8000/health
open http://localhost:5173  # WebUI
```

## Detailed Setup Instructions

### Prerequisites

Before starting, ensure your VM has:

1. **Operating System**: Ubuntu 20.04+ or Debian 11+
2. **Python**: Version 3.11 or higher
3. **PostgreSQL**: Version 14 or higher
4. **Node.js**: Version 20 or higher (for WebUI)
5. **Git**: For cloning the repository
6. **Minimum Resources**:
   - 2 GB RAM
   - 10 GB disk space
   - Stable internet connection

### Step-by-Step Installation

#### 1. Install System Dependencies

```bash
# Update package list
sudo apt update

# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3-pip

# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Install Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Install Git
sudo apt install -y git

# Install build tools
sudo apt install -y build-essential libpq-dev
```

#### 2. Set Up PostgreSQL Database

```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL shell:
CREATE USER orchestrator WITH PASSWORD 'choose_a_secure_password';
CREATE DATABASE project_orchestrator OWNER orchestrator;
GRANT ALL PRIVILEGES ON DATABASE project_orchestrator TO orchestrator;
\q

# Test connection
psql -U orchestrator -h localhost -d project_orchestrator -c "SELECT version();"
```

#### 3. Clone Repository to Production Location

```bash
# Navigate to deployment directory
cd /home/samuel

# Clone repository
git clone https://github.com/gpt153/project-manager.git po

# Enter directory
cd po
```

#### 4. Run Automated Deployment Script

```bash
# Make script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

The script will:
- ✅ Check all prerequisites
- ✅ Create Python virtual environment
- ✅ Install all dependencies
- ✅ Set up database migrations
- ✅ Build frontend
- ✅ Create systemd service files
- ✅ Optionally start services

#### 5. Configure Environment Variables

Edit the `.env` file with your actual credentials:

```bash
nano .env
```

**Required Configuration**:

```bash
# Application
APP_ENV=production
SECRET_KEY=<generate with: openssl rand -hex 32>

# Database
DATABASE_URL=postgresql+asyncpg://orchestrator:YOUR_DB_PASSWORD@localhost:5432/project_orchestrator

# Anthropic (Claude AI)
ANTHROPIC_API_KEY=sk-ant-xxxxx  # Get from https://console.anthropic.com/

# Telegram
TELEGRAM_BOT_TOKEN=xxxxx:xxxxx  # Get from @BotFather on Telegram

# GitHub
GITHUB_ACCESS_TOKEN=ghp_xxxxx  # Personal access token
GITHUB_WEBHOOK_SECRET=<random string>
```

**To get API keys**:

**Anthropic API Key**:
1. Visit https://console.anthropic.com/
2. Sign up or log in
3. Go to API Keys section
4. Create new key
5. Copy the key (starts with `sk-ant-`)

**Telegram Bot Token**:
1. Open Telegram
2. Search for `@BotFather`
3. Send `/newbot`
4. Follow prompts
5. Copy the token provided

**GitHub Token**:
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Select scopes: `repo`, `admin:repo_hook`
4. Copy the token (starts with `ghp_`)

#### 6. Install and Start Systemd Services

```bash
# Copy service files
sudo cp /tmp/project-manager-*.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable services (start on boot)
sudo systemctl enable project-manager-api
sudo systemctl enable project-manager-bot

# Start services
sudo systemctl start project-manager-api
sudo systemctl start project-manager-bot

# Check status
sudo systemctl status project-manager-api
sudo systemctl status project-manager-bot
```

#### 7. Verify Deployment

Run the comprehensive test suite:

```bash
chmod +x test_deployment.sh
./test_deployment.sh
```

The test script checks:
- ✅ Directory structure
- ✅ Python dependencies
- ✅ Database connection and migrations
- ✅ API server (port 8000)
- ✅ Telegram bot
- ✅ GitHub integration
- ✅ Frontend build
- ✅ Security configuration
- ✅ Automated test suite (67+ tests)

**Manual verification**:

```bash
# Test API
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","app_name":"Project Manager","environment":"production"}

# View API documentation
curl http://localhost:8000/docs  # Swagger UI

# Test Telegram bot
# Open Telegram and send /start to your bot

# Test WebUI (if running)
curl http://localhost:5173
```

#### 8. Set Up Frontend (WebUI)

```bash
cd /home/samuel/po/frontend

# Install dependencies
npm install

# Option A: Run development server
npm run dev  # Runs on http://localhost:5173

# Option B: Build for production
npm run build
# Then serve with nginx or configure FastAPI to serve static files
```

#### 9. View Logs

```bash
# API logs
sudo journalctl -u project-manager-api -f

# Bot logs
sudo journalctl -u project-manager-bot -f

# Or if running manually:
tail -f /home/samuel/po/api.log
tail -f /home/samuel/po/bot.log
```

### Deployment Methods

You have three options for running the application:

#### Option 1: Systemd Services (Recommended for Production)

Already covered in step 6 above. Services auto-start on reboot.

**Manage services**:
```bash
sudo systemctl start project-manager-api
sudo systemctl stop project-manager-api
sudo systemctl restart project-manager-api
sudo systemctl status project-manager-api
```

#### Option 2: Docker Compose

```bash
cd /home/samuel/po

# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Restart after changes
docker-compose down && docker-compose build && docker-compose up -d
```

#### Option 3: Manual Process Management

```bash
cd /home/samuel/po
source venv/bin/activate

# Terminal 1: API server
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4

# Terminal 2: Telegram bot
python -m src.bot_main

# Terminal 3: Frontend (optional)
cd frontend && npm run dev
```

## Testing the Deployment

### 1. Run Automated Tests

```bash
cd /home/samuel/po
source venv/bin/activate
pytest tests/ -v
```

Expected: 67+ tests passing

### 2. Test API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# List projects
curl http://localhost:8000/api/projects

# View Swagger docs
open http://localhost:8000/docs
```

### 3. Test Telegram Bot

1. Open Telegram
2. Search for your bot username
3. Send `/start`
4. Expected: Welcome message and project creation prompt
5. Send `/help` to see available commands
6. Send `/status` to check workflow status

### 4. Test GitHub Integration

1. Create a test issue in your GitHub repo
2. Comment with `@po hello`
3. Expected: Bot responds to the mention
4. Check webhook logs: `sudo journalctl -u project-manager-api | grep github`

### 5. Test WebUI

1. Open browser: http://localhost:5173
2. Should see 3-panel layout:
   - Left: Project Navigator
   - Middle: Chat Interface
   - Right: SCAR Activity Feed
3. Select a project
4. Send test message
5. Check WebSocket connection in browser dev tools

## Troubleshooting

### API Server Won't Start

```bash
# Check logs
sudo journalctl -u project-manager-api -n 50

# Common issues:
# 1. Port 8000 already in use
sudo lsof -i :8000
sudo kill -9 <PID>

# 2. Database connection failed
psql -U orchestrator -h localhost -d project_orchestrator

# 3. Missing environment variables
cat .env | grep -E "ANTHROPIC|TELEGRAM|GITHUB"
```

### Database Errors

```bash
# Reset database
dropdb project_orchestrator
createdb project_orchestrator -O orchestrator

# Run migrations
cd /home/samuel/po
source venv/bin/activate
alembic upgrade head

# Check migration status
alembic current
alembic history
```

### Telegram Bot Not Responding

```bash
# Check bot is running
ps aux | grep bot_main

# Test bot token
BOT_TOKEN=$(grep TELEGRAM_BOT_TOKEN .env | cut -d'=' -f2)
curl "https://api.telegram.org/bot$BOT_TOKEN/getMe"

# Check logs
sudo journalctl -u project-manager-bot -f

# Restart bot
sudo systemctl restart project-manager-bot
```

### WebUI Issues

```bash
# Reinstall dependencies
cd frontend
rm -rf node_modules package-lock.json
npm install

# Rebuild
npm run build

# Check dev server
npm run dev

# Check for errors in browser console
```

### Port Conflicts

```bash
# Find what's using port 8000
sudo lsof -i :8000
sudo netstat -tuln | grep 8000

# Kill process
sudo kill -9 <PID>

# Or change port in .env
echo "API_PORT=8080" >> .env
sudo systemctl restart project-manager-api
```

## Updating the Application

### Pull Latest Changes

```bash
cd /home/samuel/po

# Stop services
sudo systemctl stop project-manager-api project-manager-bot

# Pull updates
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Update dependencies
pip install -e .

# Run new migrations
alembic upgrade head

# Rebuild frontend
cd frontend
npm install
npm run build
cd ..

# Restart services
sudo systemctl start project-manager-api project-manager-bot
```

### Using Automated Deployment Script

```bash
cd /home/samuel/po
./deploy.sh
```

The script handles:
- Pulling latest code
- Installing new dependencies
- Running migrations
- Rebuilding frontend
- Restarting services

## GitHub Actions CI/CD Setup

For automated deployments when you push to main:

### 1. Set Up GitHub Actions Secrets

In your GitHub repository:
1. Go to Settings → Secrets and variables → Actions
2. Add repository secrets:
   - `ANTHROPIC_API_KEY`
   - `TELEGRAM_BOT_TOKEN`
   - `GITHUB_ACCESS_TOKEN`
   - `GITHUB_WEBHOOK_SECRET`
   - `SECRET_KEY`
   - `DATABASE_URL`

### 2. Set Up Self-Hosted Runner on VM

```bash
# On your VM
cd /home/samuel

# Download runner
mkdir actions-runner && cd actions-runner
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz
tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz

# Configure (get token from GitHub Settings → Actions → Runners)
./config.sh --url https://github.com/gpt153/project-manager --token YOUR_TOKEN

# Install as service
sudo ./svc.sh install
sudo ./svc.sh start
```

### 3. Trigger Deployment

```bash
# Push to main branch
git add .
git commit -m "Deploy to production"
git push origin main
```

GitHub Actions will:
1. ✅ Run tests (CI workflow)
2. ✅ Build Docker image
3. ✅ Push to GitHub Container Registry
4. ✅ Deploy to /home/samuel/po
5. ✅ Run migrations
6. ✅ Health check
7. ✅ Rollback on failure

## Security Checklist

- [ ] Change all default passwords
- [ ] Generate strong SECRET_KEY: `openssl rand -hex 32`
- [ ] Set `.env` permissions: `chmod 600 .env`
- [ ] Enable firewall: `sudo ufw enable && sudo ufw allow 22,80,443/tcp`
- [ ] Set up SSL with Let's Encrypt (if using domain)
- [ ] Configure GitHub webhook signature verification
- [ ] Regular database backups
- [ ] Keep dependencies updated
- [ ] Monitor logs for errors

## Monitoring and Maintenance

### Daily Tasks

```bash
# Check service health
curl http://localhost:8000/health

# Check logs for errors
sudo journalctl -u project-manager-api --since today | grep -i error
sudo journalctl -u project-manager-bot --since today | grep -i error
```

### Weekly Tasks

```bash
# Update dependencies
cd /home/samuel/po
source venv/bin/activate
pip list --outdated

# Run tests
pytest tests/ -v

# Check disk space
df -h
```

### Monthly Tasks

```bash
# Full system update
sudo apt update && sudo apt upgrade

# Database backup
pg_dump -U orchestrator project_orchestrator > backup_$(date +%Y%m%d).sql
gzip backup_$(date +%Y%m%d).sql

# Review logs
journalctl --disk-usage
sudo journalctl --vacuum-time=30d
```

## Support and Resources

- **Documentation**: `/home/samuel/po/docs/`
- **GitHub Issues**: https://github.com/gpt153/project-manager/issues
- **Test Suite**: `pytest tests/ -v`
- **Health Check**: `curl http://localhost:8000/health`
- **Logs**: `sudo journalctl -u project-manager-api -f`

## Quick Reference Commands

```bash
# Check status
sudo systemctl status project-manager-api project-manager-bot

# Restart services
sudo systemctl restart project-manager-api project-manager-bot

# View logs
sudo journalctl -u project-manager-api -f

# Run tests
cd /home/samuel/po && source venv/bin/activate && pytest tests/ -v

# Test API
curl http://localhost:8000/health

# Update application
cd /home/samuel/po && ./deploy.sh

# Database migrations
alembic upgrade head

# Backup database
pg_dump -U orchestrator project_orchestrator > backup.sql
```

---

**Deployment Complete!** 🎉

Your Project Manager is now running at:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- WebUI: http://localhost:5173 (if dev server running)
