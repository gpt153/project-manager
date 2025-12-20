# Project Orchestrator - Quick Start Guide

Get the Project Orchestrator up and running in 15 minutes.

## What You'll Accomplish

By the end of this guide, you'll have:
- ✅ Application running locally or in production
- ✅ Database initialized and migrated
- ✅ Telegram bot responding to messages
- ✅ GitHub webhooks configured
- ✅ First test project created

## Prerequisites

Make sure you have these before starting:

1. **For Docker Deployment (Recommended)**:
   - Docker and Docker Compose installed
   - Internet connection for pulling images

2. **For Manual Deployment**:
   - Python 3.11+
   - PostgreSQL 14+
   - Git

3. **API Keys** (get these first):
   - Anthropic API key (for Claude)
   - Telegram bot token (from @BotFather)
   - GitHub personal access token
   - GitHub webhook secret (make one up)

## Step-by-Step Setup

### 1. Get API Keys (5 minutes)

#### Anthropic API Key
1. Visit https://console.anthropic.com/
2. Sign up/login
3. Go to API Keys → Create Key
4. Copy the key (starts with `sk-ant-`)

#### Telegram Bot Token
1. Open Telegram, search `@BotFather`
2. Send `/newbot`
3. Follow prompts (choose name and username)
4. Copy the token
5. Set commands:
   ```
   /setcommands

   start - Start a new project
   help - Show available commands
   status - Check workflow status
   continue - Advance to next phase
   ```

#### GitHub Token
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Select scopes: `repo`, `admin:repo_hook`
4. Copy token (starts with `ghp_`)

#### Webhook Secret
```bash
# Generate a random secret
openssl rand -hex 32
# Copy this for later
```

### 2. Clone and Configure (2 minutes)

```bash
# Clone repository
git clone https://github.com/gpt153/project-orchestrator.git
cd project-orchestrator

# Create .env file
cp .env.example .env

# Edit .env file (use your favorite editor)
nano .env
```

**Update these values** in `.env`:

```bash
# Anthropic API
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Telegram Bot
TELEGRAM_BOT_TOKEN=1234567890:your-token-here

# GitHub
GITHUB_ACCESS_TOKEN=ghp_your-token-here
GITHUB_WEBHOOK_SECRET=your-generated-secret

# Database (leave as-is for Docker, or update for manual install)
DATABASE_URL=postgresql+asyncpg://orchestrator:dev_password@postgres:5432/project_orchestrator
```

**Important**: Save the file!

### 3. Start the Application (3 minutes)

#### Option A: Docker (Recommended)

```bash
# Build and start all services
docker-compose up -d

# Wait for services to be ready (about 30 seconds)
docker-compose ps

# Expected output:
# NAME                  STATUS
# orchestrator-app-1    Up (healthy)
# orchestrator-db-1     Up (healthy)
# orchestrator-redis-1  Up (healthy)

# Check logs (should see no errors)
docker-compose logs -f
# Press Ctrl+C to exit
```

**Skip to Step 4** if using Docker.

#### Option B: Manual Installation

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -e .

# Create database
createdb project_orchestrator -O orchestrator

# Run migrations
alembic upgrade head

# Start API server (in one terminal)
python -m src.main

# Start Telegram bot (in another terminal)
source venv/bin/activate
python -m src.bot_main
```

### 4. Verify Installation (2 minutes)

```bash
# Test API health
curl http://localhost:8000/health

# Expected: {"status":"healthy"}

# Test API docs
open http://localhost:8000/docs
# Or visit in browser

# Test database
psql -U orchestrator -d project_orchestrator -c "SELECT COUNT(*) FROM projects;"

# Expected: count (probably 0)
```

✅ **If all tests pass, your application is running!**

### 5. Test Telegram Bot (3 minutes)

1. Open Telegram app
2. Search for your bot (@your-bot-username)
3. Start a chat, send:
   ```
   /start
   ```

**Expected Response**:
```
👋 Welcome to Project Orchestrator!

I help non-technical people build software projects through conversation.

Let's start by discussing your project idea. What would you like to build?
```

4. Try chatting:
   ```
   I want to build a simple blog
   ```

**Expected**: Bot asks follow-up questions.

5. Check database:
```bash
# Verify project was created
psql -U orchestrator -d project_orchestrator -c "SELECT id, name, telegram_chat_id FROM projects ORDER BY created_at DESC LIMIT 1;"

# Should show your new project
```

✅ **If bot responds, Telegram integration works!**

### 6. Configure GitHub Webhook (Optional, 5 minutes)

> **Note**: Only needed if you want GitHub integration.

#### For Local Development (using ngrok)

```bash
# Install ngrok (if not already installed)
brew install ngrok  # macOS
# or download from https://ngrok.com/download

# Start ngrok tunnel
ngrok http 8000

# Note the HTTPS URL (e.g., https://abc123.ngrok.io)
```

#### For Production

Use your domain: `https://your-domain.com`

#### Add Webhook to GitHub

1. Go to your GitHub repository
2. Settings → Webhooks → Add webhook
3. Configure:
   - **Payload URL**: `https://your-domain.com/webhooks/github/` (or ngrok URL)
   - **Content type**: `application/json`
   - **Secret**: (paste your `GITHUB_WEBHOOK_SECRET` from .env)
   - **Events**: Select "Issue comments" and "Issues"
   - **Active**: ✅ Checked

4. Click "Add webhook"

5. Test webhook:
   - Create a new issue in the repo
   - Add comment: `@po hello`
   - Check application logs:
     ```bash
     docker-compose logs -f app | grep github
     # Should see "Received GitHub webhook: issue_comment"
     ```

✅ **If webhook delivers successfully (green checkmark), GitHub integration works!**

## Quick Test: Complete Workflow

Let's test the entire system with a simple project.

### 1. Start Project in Telegram

```
/start

I want to build a simple TODO app

For personal use

Add tasks, mark complete, delete tasks

React and Node.js
```

### 2. Generate Vision Document

Bot will offer: **[Generate Vision] [Keep Brainstorming]**

Click: **Generate Vision**

Wait ~10 seconds for AI to generate document.

### 3. Approve Vision

Bot shows formatted vision document with buttons:

Click: **Approve**

### 4. Watch Workflow Progress

Bot will automatically:
1. Execute PRIME command
2. Create implementation plan
3. Request approval for plan

Click **Approve** when prompted.

### 5. Verify in Database

```bash
# Check workflow phases
psql -U orchestrator -d project_orchestrator <<EOF
SELECT
    p.name,
    wp.phase_number,
    wp.name AS phase,
    wp.status
FROM workflow_phases wp
JOIN projects p ON wp.project_id = p.id
ORDER BY p.created_at DESC, wp.phase_number
LIMIT 10;
EOF
```

✅ **If you see phases progressing, the full workflow works!**

## What's Next?

Now that your Project Orchestrator is running:

### Immediate Actions

1. **Create Your First Real Project**
   - Open Telegram bot
   - Describe your actual project idea
   - Let it guide you through the workflow

2. **Connect Your GitHub Repositories**
   - Add webhook to your repos (see Step 6)
   - Create projects in database linked to repos
   - Mention `@po` in issues to interact

3. **Monitor the System**
   - Watch logs: `docker-compose logs -f`
   - Check database for new projects
   - Review SCAR command executions

### Learn More

- **Full Documentation**: See `docs/DEPLOYMENT.md`
- **Webhook Setup**: See `docs/WEBHOOK_SETUP.md`
- **Database Guide**: See `docs/DATABASE_SETUP.md`
- **Testing Guide**: See `docs/TESTING_GUIDE.md`

### Production Deployment

For production use:

1. **Set up a domain** with SSL certificate
2. **Use strong passwords** for database
3. **Configure reverse proxy** (Nginx)
4. **Set up backups** (daily database dumps)
5. **Enable monitoring** (logs, error tracking)

See `docs/DEPLOYMENT.md` for full production setup guide.

## Troubleshooting

### Application won't start

```bash
# Check Docker containers
docker-compose ps

# If services are down, check logs
docker-compose logs

# Common issues:
# - Port 8000 already in use: Change API_PORT in .env
# - Port 5432 already in use: Stop other PostgreSQL instances
# - Missing environment variables: Check .env file exists
```

### Telegram bot doesn't respond

```bash
# 1. Verify token is correct
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"
# Should return bot info

# 2. Check bot is running
docker-compose logs app | grep telegram

# 3. Restart bot
docker-compose restart app
```

### Database connection errors

```bash
# 1. Check PostgreSQL is running
docker-compose ps postgres
# Should show "Up (healthy)"

# 2. Test database connection
docker-compose exec postgres psql -U orchestrator -d project_orchestrator -c "SELECT 1;"

# 3. Check DATABASE_URL in .env matches docker-compose.yml
```

### GitHub webhooks failing

```bash
# 1. Check webhook deliveries in GitHub
# Go to repo Settings > Webhooks > Recent Deliveries

# 2. Verify webhook secret matches
echo $GITHUB_WEBHOOK_SECRET

# 3. Test webhook endpoint
curl https://your-domain.com/webhooks/github/health
# Should return {"status":"healthy"}
```

## Common Commands

### Docker Compose

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Restart specific service
docker-compose restart app

# Rebuild after code changes
docker-compose up -d --build

# Check service status
docker-compose ps
```

### Database

```bash
# Connect to database
docker-compose exec postgres psql -U orchestrator -d project_orchestrator

# Run migrations
docker-compose exec app alembic upgrade head

# Create backup
docker-compose exec postgres pg_dump -U orchestrator project_orchestrator > backup.sql
```

### Application

```bash
# View API docs
open http://localhost:8000/docs

# Check health
curl http://localhost:8000/health

# View logs
docker-compose logs -f app
```

## Getting Help

If you're stuck:

1. **Check the logs** for error messages
2. **Review documentation** in `docs/` folder
3. **Search GitHub issues** for similar problems
4. **Create new issue** with:
   - Description of problem
   - Error messages from logs
   - Steps to reproduce

## Success! 🎉

You now have a fully functional Project Orchestrator!

### What You Can Do Now

- ✅ Chat with the bot to plan projects
- ✅ Generate vision documents with AI
- ✅ Automate SCAR workflows
- ✅ Integrate with GitHub repositories
- ✅ Track project progress in database

### Share Your Experience

Built something cool? Share it!

- Star the repository ⭐
- Share on social media
- Contribute improvements
- Help other users

---

**Happy building! 🚀**
