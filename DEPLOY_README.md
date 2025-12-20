# 🚀 Quick Deployment Guide for Project Orchestrator

**Deploy to `/home/samuel/po` in 5 minutes!**

## Prerequisites

Your VM needs:
- Ubuntu 20.04+ or Debian 11+
- Python 3.11+
- PostgreSQL 14+
- Node.js 20+ (for WebUI)
- 2GB RAM, 10GB disk

## Quick Deploy (Automated)

```bash
# 1. Install prerequisites (if needed)
sudo apt update
sudo apt install -y python3.11 python3.11-venv postgresql nodejs npm git

# 2. Clone to deployment directory
cd /home/samuel
git clone https://github.com/gpt153/project-orchestrator.git po
cd po

# 3. Run automated deployment
chmod +x deploy.sh
./deploy.sh

# 4. Configure API keys
nano .env
# Add your:
# - ANTHROPIC_API_KEY
# - TELEGRAM_BOT_TOKEN
# - GITHUB_ACCESS_TOKEN
# - DATABASE_URL

# 5. Run tests
chmod +x test_deployment.sh
./test_deployment.sh

# 6. Start services
sudo systemctl start project-orchestrator-api project-orchestrator-bot

# 7. Verify
curl http://localhost:8000/health
```

## What Gets Deployed

- ✅ Backend API on port 8000
- ✅ Telegram bot process
- ✅ PostgreSQL database with migrations
- ✅ Frontend WebUI (build ready)
- ✅ Systemd services for auto-restart
- ✅ Complete test suite (67+ tests)

## Testing Your Deployment

Run the comprehensive test script:

```bash
./test_deployment.sh
```

This checks:
- Directory structure
- Python dependencies
- Database connection
- API server (http://localhost:8000)
- Telegram bot
- GitHub integration
- WebUI build
- Security configuration
- Runs all 67+ automated tests

## Manual Deployment (Step by Step)

If you prefer manual control:

### 1. Set Up Database

```bash
sudo -u postgres psql
CREATE USER orchestrator WITH PASSWORD 'your_password';
CREATE DATABASE project_orchestrator OWNER orchestrator;
\q
```

### 2. Set Up Python

```bash
cd /home/samuel/po
python3.11 -m venv venv
source venv/bin/activate
pip install -e .
pip install -e ".[dev]"
```

### 3. Configure Environment

```bash
cp .env.example .env
nano .env  # Add your API keys
```

### 4. Run Migrations

```bash
alembic upgrade head
```

### 5. Start Services

```bash
# Terminal 1: API
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4

# Terminal 2: Bot
python -m src.bot_main

# Terminal 3: WebUI (optional)
cd frontend && npm run dev
```

## Docker Deployment

Prefer Docker?

```bash
cd /home/samuel/po

# Configure .env first
cp .env.example .env
nano .env

# Start with Docker Compose
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Run migrations
docker-compose exec app alembic upgrade head
```

## Getting API Keys

### Anthropic (Claude)
1. Visit https://console.anthropic.com/
2. Create account / sign in
3. Go to API Keys
4. Create new key
5. Copy key (starts with `sk-ant-`)

### Telegram
1. Open Telegram
2. Message `@BotFather`
3. Send `/newbot`
4. Follow prompts
5. Copy token

### GitHub
1. GitHub Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Scopes: `repo`, `admin:repo_hook`
4. Copy token (starts with `ghp_`)

## Verify Installation

### API Health Check
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","app_name":"Project Orchestrator",...}
```

### View API Docs
```bash
open http://localhost:8000/docs  # Swagger UI
```

### Test Telegram Bot
1. Open Telegram
2. Find your bot
3. Send `/start`
4. Expected: Welcome message

### Test WebUI
```bash
open http://localhost:5173  # If dev server running
```

## Troubleshooting

### Port 8000 Already in Use
```bash
sudo lsof -i :8000
sudo kill -9 <PID>
```

### Database Connection Failed
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -U orchestrator -h localhost -d project_orchestrator
```

### API Won't Start
```bash
# Check logs
sudo journalctl -u project-orchestrator-api -n 50

# Or if running manually
tail -f /home/samuel/po/api.log
```

### Tests Failing
```bash
# Install test dependencies
pip install -e ".[dev]"

# Run tests with verbose output
pytest tests/ -v --tb=short
```

## File Structure After Deployment

```
/home/samuel/po/
├── src/              # Backend Python code
├── frontend/         # React WebUI
├── tests/            # Test suite (67+ tests)
├── docs/             # Documentation
├── .env              # Your configuration (SECRET!)
├── venv/             # Python virtual environment
├── deploy.sh         # Automated deployment script
└── test_deployment.sh # Testing script
```

## Service Management

### Using systemd (recommended)
```bash
# Start
sudo systemctl start project-orchestrator-api project-orchestrator-bot

# Stop
sudo systemctl stop project-orchestrator-api project-orchestrator-bot

# Restart
sudo systemctl restart project-orchestrator-api project-orchestrator-bot

# Status
sudo systemctl status project-orchestrator-api

# Logs
sudo journalctl -u project-orchestrator-api -f
```

### Using Docker Compose
```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Restart
docker-compose restart

# Logs
docker-compose logs -f app
```

## Updating the Deployment

```bash
cd /home/samuel/po
git pull origin main
./deploy.sh  # Handles everything automatically
```

## CI/CD with GitHub Actions

Three workflows are configured:

### 1. **CI** (Continuous Integration)
- Runs on every PR
- Tests all code
- Checks code quality
- Builds frontend

### 2. **Docker Build**
- Runs on push to main
- Builds Docker image
- Pushes to GitHub Container Registry

### 3. **CD** (Continuous Deployment)
- Runs on push to main
- Requires self-hosted runner
- Auto-deploys to `/home/samuel/po`
- Runs migrations
- Health checks
- Rolls back on failure

To enable auto-deployment, set up a self-hosted runner (see PRODUCTION_SETUP.md).

## Security Checklist

Before going to production:

- [ ] Change all default passwords in `.env`
- [ ] Generate strong SECRET_KEY: `openssl rand -hex 32`
- [ ] Set `.env` permissions: `chmod 600 .env`
- [ ] Configure firewall: `sudo ufw enable && sudo ufw allow 22,80,443/tcp`
- [ ] Set up SSL certificate (if using domain)
- [ ] Configure GitHub webhook secret
- [ ] Set up database backups
- [ ] Review security headers in API

## Next Steps

After deployment:

1. ✅ Test Telegram bot with `/start`
2. ✅ Create first project
3. ✅ Test API endpoints
4. ✅ Configure GitHub webhooks
5. ✅ Set up monitoring
6. ✅ Configure backups
7. ✅ Set up SSL (if public)

## Support

- **Full Documentation**: `docs/DEPLOYMENT.md`
- **Production Setup**: `PRODUCTION_SETUP.md`
- **Testing Guide**: `docs/TESTING_GUIDE.md`
- **GitHub Issues**: https://github.com/gpt153/project-orchestrator/issues

## Quick Reference

```bash
# Health check
curl http://localhost:8000/health

# Run all tests
./test_deployment.sh

# View API logs
sudo journalctl -u project-orchestrator-api -f

# View Bot logs
sudo journalctl -u project-orchestrator-bot -f

# Restart services
sudo systemctl restart project-orchestrator-api project-orchestrator-bot

# Update deployment
git pull && ./deploy.sh

# Database migrations
alembic upgrade head

# Run test suite
pytest tests/ -v
```

---

**That's it!** Your Project Orchestrator should now be running at `/home/samuel/po` 🎉

Questions? Check the full documentation or open an issue on GitHub.
