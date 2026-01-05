# Testing Guide for Project Manager

Complete guide for testing all components of the Project Manager after deployment.

## Overview

This guide covers:
- ✅ Application health checks
- ✅ Database connectivity tests
- ✅ Telegram bot functionality tests
- ✅ GitHub integration tests
- ✅ End-to-end workflow tests

## Prerequisites

Before testing, ensure:
- Application is deployed and running
- Database is initialized with migrations
- All API keys are configured in `.env`
- Services are accessible

## 1. Application Health Checks

### Check API Server

```bash
# Test if API is running
curl http://localhost:8000/health

# Expected response:
# {"status": "healthy"}

# Test API documentation
curl http://localhost:8000/docs

# Should return HTML content (Swagger UI)

# Test OpenAPI schema
curl http://localhost:8000/openapi.json | jq .
```

### Check Database Connection

```bash
# Test database is reachable
psql -U orchestrator -h localhost -d project_orchestrator -c "SELECT COUNT(*) FROM projects;"

# Expected: A number (0 if no projects, or count of existing projects)

# Test alembic migrations
alembic current

# Expected: Current revision ID
```

### Check Docker Services (if using Docker)

```bash
# Check all containers are running
docker-compose ps

# Expected output (all "Up" and healthy):
# NAME                  STATUS              PORTS
# orchestrator-app-1    Up (healthy)        0.0.0.0:8000->8000/tcp
# orchestrator-db-1     Up (healthy)        0.0.0.0:5432->5432/tcp
# orchestrator-redis-1  Up (healthy)        0.0.0.0:6379->6379/tcp

# Check container logs
docker-compose logs --tail=50 app

# Should not show errors
```

## 2. Database Tests

### Test Database Schema

```bash
# Connect to database
psql -U orchestrator -d project_orchestrator

# List all tables
\dt

# Expected tables:
# - projects
# - conversation_messages
# - workflow_phases
# - approval_gates
# - scar_command_executions
# - alembic_version

# Describe projects table
\d projects

# Exit
\q
```

### Create Test Project

```sql
-- Create a test project
INSERT INTO projects (name, status, github_repo_url, telegram_chat_id)
VALUES (
    'Test Project',
    'brainstorming',
    'https://github.com/test/repo',
    999999999
)
RETURNING id;

-- Save the returned ID for later tests

-- Verify project was created
SELECT id, name, status FROM projects WHERE name = 'Test Project';

-- Clean up (optional)
DELETE FROM projects WHERE name = 'Test Project';
```

## 3. Telegram Bot Tests

### Step 1: Find Your Bot on Telegram

1. Open Telegram app
2. Search for your bot username (from @BotFather)
3. Start a chat with the bot

### Step 2: Test Bot Commands

#### Test `/start` Command

```
/start
```

**Expected Response**:
```
👋 Welcome to Project Manager!

I help non-technical people build software projects through conversation.

Let's start by discussing your project idea. What would you like to build?

Commands:
/start - Start a new project
/help - Show available commands
/status - Check workflow status
/continue - Advance to next phase
```

**Verify in Database**:
```sql
-- Check that a new project was created
SELECT id, name, telegram_chat_id, status
FROM projects
WHERE telegram_chat_id = <your-telegram-chat-id>
ORDER BY created_at DESC
LIMIT 1;
```

#### Test `/help` Command

```
/help
```

**Expected Response**:
- List of available commands
- Explanation of how the bot works

#### Test Natural Language Message

```
I want to build a task manager for students
```

**Expected Response**:
- Bot should acknowledge the message
- Ask follow-up questions
- Message should be saved to database

**Verify in Database**:
```sql
-- Check conversation was saved
SELECT role, content, created_at
FROM conversation_messages
WHERE project_id = '<project-id-from-start>'
ORDER BY created_at DESC
LIMIT 5;
```

#### Test `/status` Command

```
/status
```

**Expected Response**:
```
📊 Project Status

Current Phase: Vision Document Review
Status: Pending

You're currently in the brainstorming phase. Keep chatting about your project idea!
```

### Step 3: Test Vision Document Generation Flow

Continue chatting with the bot about your project:

```
User: I want to build a task manager
Bot: Great! Tell me more...

User: It's for students managing coursework
Bot: What features are most important?

User: Creating tasks, setting reminders, and priorities
Bot: Any specific platforms?

User: Web application
```

**Expected**: After sufficient conversation, bot should offer to generate vision document:

```
🎉 I have enough information to create a vision document!

Would you like me to generate it now?

[Yes, Generate Vision] [No, Keep Brainstorming]
```

Click "Yes, Generate Vision" button.

**Expected**:
- Bot generates a vision document
- Shows the document in formatted markdown
- Offers approval options

### Step 4: Test Approval Flow

**Expected Response**:
```
Here's your vision document:

# Task Manager - Project Vision

[... formatted vision document ...]

[Approve] [Needs Changes]
```

Click "Approve" button.

**Expected**:
- Bot confirms approval
- Workflow advances to next phase

**Verify in Database**:
```sql
-- Check approval gate was created and approved
SELECT gate_type, status, approved_at
FROM approval_gates
WHERE project_id = '<project-id>'
ORDER BY created_at DESC
LIMIT 1;

-- Check workflow phase advanced
SELECT phase_number, name, status
FROM workflow_phases
WHERE project_id = '<project-id>'
ORDER BY phase_number;
```

### Step 5: Test `/continue` Command

```
/continue
```

**Expected Response**:
- Bot advances workflow to next phase
- Executes appropriate SCAR command
- Updates status

### Telegram Bot Troubleshooting

If bot doesn't respond:

```bash
# 1. Check bot process is running
ps aux | grep bot_main
# Or for Docker:
docker-compose ps | grep app

# 2. Check bot logs
docker-compose logs -f app | grep telegram
# Or:
sudo journalctl -u project-manager-bot -f

# 3. Verify bot token
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"
# Should return bot information

# 4. Check environment variable
docker-compose exec app python -c "from src.config import get_settings; print(get_settings().telegram_bot_token)"
```

## 4. GitHub Integration Tests

### Step 1: Verify Webhook is Configured

1. Go to your GitHub repository
2. Navigate to Settings > Webhooks
3. Verify webhook exists with:
   - Payload URL: `https://your-domain.com/webhooks/github/`
   - Content type: `application/json`
   - Secret: (configured)
   - Events: Issue comments, Issues checked

### Step 2: Test Webhook Health Endpoint

```bash
# Test health endpoint
curl https://your-domain.com/webhooks/github/health

# Expected response:
# {"status": "healthy", "service": "github_webhook"}
```

### Step 3: Create Test Project in Database

```sql
-- Create project linked to your GitHub repo
INSERT INTO projects (name, status, github_repo_url)
VALUES (
    'GitHub Test Project',
    'brainstorming',
    'https://github.com/yourusername/your-repo'  -- Use your actual repo URL
)
RETURNING id;
```

### Step 4: Test GitHub @Mention

1. Go to your GitHub repository
2. Create a new issue or open existing one
3. Add a comment mentioning the bot:
   ```
   @po please help with this feature
   ```

**Expected Behavior**:
1. GitHub sends webhook to your server
2. Application receives webhook
3. Bot processes the @mention
4. (Future: Bot posts response comment)

**Verify in Logs**:

```bash
# Check application logs
docker-compose logs -f app | grep github

# Expected logs:
# INFO: Received GitHub webhook: issue_comment
# INFO: Comment contains @mention: @po
# INFO: Processing comment from user: yourusername
# INFO: Looking up project by repo URL: https://github.com/yourusername/your-repo
```

**Verify in GitHub**:

1. Go to repo Settings > Webhooks
2. Click on the webhook
3. Scroll to "Recent Deliveries"
4. Click the most recent delivery
5. Check Response tab:
   - Should show 200 OK status
   - Response body: `{"message": "Webhook received", "event": "issue_comment"}`

### Step 5: Test Webhook Signature Verification

Test that invalid signatures are rejected:

```bash
# Send webhook without signature (should fail)
curl -X POST https://your-domain.com/webhooks/github/ \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: ping" \
  -d '{"zen": "test"}'

# Expected: 403 Forbidden (signature missing or invalid)
```

### GitHub Integration Troubleshooting

```bash
# 1. Check webhook deliveries in GitHub
# Go to Settings > Webhooks > Recent Deliveries
# Look for red X (failed) or green checkmark (success)

# 2. If getting 403 errors, verify secret
docker-compose exec app python -c "from src.config import get_settings; print(get_settings().github_webhook_secret)"
# Should match GitHub webhook secret

# 3. Check webhook logs
docker-compose logs app | grep -A 10 "Received GitHub webhook"

# 4. Test GitHub API token
curl -H "Authorization: Bearer <YOUR_GITHUB_TOKEN>" https://api.github.com/user
# Should return your user information
```

## 5. End-to-End Workflow Test

Complete workflow from start to finish.

### Scenario: Build a Simple TODO App

#### Phase 1: Brainstorming (Telegram)

1. Open Telegram bot
2. Send `/start`
3. Describe project:
   ```
   User: I want to build a simple TODO application
   Bot: Great! Tell me more...

   User: For personal use, web-based
   Bot: What features?

   User: Add tasks, mark complete, delete tasks
   Bot: Tech stack preference?

   User: React frontend, Node.js backend
   ```

4. Bot offers vision document generation
5. Approve vision document

**Verify**:
```sql
SELECT name, status, vision_document
FROM projects
WHERE name LIKE '%TODO%'
ORDER BY created_at DESC
LIMIT 1;
```

#### Phase 2: Prime Context

Bot executes SCAR PRIME command.

**Verify**:
```sql
SELECT command_type, status, output
FROM scar_command_executions
WHERE command_type = 'PRIME'
ORDER BY created_at DESC
LIMIT 1;
```

#### Phase 3: Plan Feature

Bot executes SCAR PLAN-FEATURE-GITHUB.

**Verify**:
```sql
-- Check command execution
SELECT command_type, status, output
FROM scar_command_executions
WHERE command_type = 'PLAN-FEATURE-GITHUB'
ORDER BY created_at DESC
LIMIT 1;

-- Check approval gate created
SELECT gate_type, status
FROM approval_gates
WHERE gate_type = 'implementation_plan'
ORDER BY created_at DESC
LIMIT 1;
```

Approve the plan in Telegram.

#### Phase 4: Execute Implementation

Bot executes SCAR EXECUTE-GITHUB.

**Verify**:
```sql
SELECT command_type, status, started_at, completed_at
FROM scar_command_executions
WHERE command_type = 'EXECUTE-GITHUB'
ORDER BY created_at DESC
LIMIT 1;
```

#### Phase 5: Validate

Bot executes SCAR VALIDATE.

**Verify**:
```sql
SELECT command_type, status, output
FROM scar_command_executions
WHERE command_type = 'VALIDATE'
ORDER BY created_at DESC
LIMIT 1;
```

Approve final validation.

#### Final Verification

```sql
-- Check all workflow phases completed
SELECT phase_number, name, status, completed_at
FROM workflow_phases
WHERE project_id = '<project-id>'
ORDER BY phase_number;

-- Expected: All phases should have status 'completed'

-- Check all approval gates approved
SELECT gate_type, status, approved_at
FROM approval_gates
WHERE project_id = '<project-id>'
ORDER BY created_at;

-- Expected: All should be 'approved'

-- Check project status
SELECT name, status, updated_at
FROM projects
WHERE id = '<project-id>';

-- Expected: status should reflect completion
```

## 6. Performance Tests

### API Response Time

```bash
# Test API response time
time curl -s http://localhost:8000/health > /dev/null

# Should complete in < 100ms

# Test database query performance
time psql -U orchestrator -d project_orchestrator -c "SELECT COUNT(*) FROM projects;" > /dev/null

# Should complete in < 50ms
```

### Load Testing (Optional)

Use Apache Bench or similar tool:

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test 100 requests with 10 concurrent
ab -n 100 -c 10 http://localhost:8000/health

# Review results:
# - Requests per second
# - Time per request
# - Failed requests (should be 0)
```

## 7. Automated Test Suite

Run the project's test suite:

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/integrations/test_telegram_bot.py

# Run specific test
pytest tests/integrations/test_telegram_bot.py::test_start_command -v
```

**Expected Results**:
- 67+ tests passing
- 68%+ test coverage
- No critical failures

## 8. Security Tests

### Test Webhook Signature Verification

```bash
# Try to send unsigned webhook (should fail)
curl -X POST http://localhost:8000/webhooks/github/ \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: ping" \
  -d '{"test": "data"}'

# Expected: 403 Forbidden

# Try with wrong signature (should fail)
curl -X POST http://localhost:8000/webhooks/github/ \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: ping" \
  -H "X-Hub-Signature-256: sha256=wrong_signature" \
  -d '{"test": "data"}'

# Expected: 403 Forbidden
```

### Test SQL Injection Protection

SQLAlchemy with parameterized queries protects against SQL injection, but verify:

```python
# This should be safe (run in Python shell)
from src.database.models import Project
from src.database.connection import async_session_maker

async def test_sql_injection():
    async with async_session_maker() as session:
        # Try SQL injection in search
        malicious_input = "' OR '1'='1"
        result = await session.execute(
            select(Project).where(Project.name == malicious_input)
        )
        projects = result.scalars().all()
        print(f"Found {len(projects)} projects")  # Should be 0

# Run with: python -c "import asyncio; asyncio.run(test_sql_injection())"
```

## 9. Monitoring and Logging

### Check Application Logs

```bash
# Real-time logs
docker-compose logs -f app

# Filter for errors
docker-compose logs app | grep ERROR

# Filter for specific component
docker-compose logs app | grep telegram
docker-compose logs app | grep github
docker-compose logs app | grep scar
```

### Check Database Logs

```bash
# PostgreSQL logs (if not using Docker)
sudo tail -f /var/log/postgresql/postgresql-15-main.log

# Docker PostgreSQL logs
docker-compose logs -f postgres
```

## 10. Cleanup After Testing

```bash
# Remove test data from database
psql -U orchestrator -d project_orchestrator <<EOF
DELETE FROM conversation_messages WHERE project_id IN (
    SELECT id FROM projects WHERE name LIKE '%Test%'
);
DELETE FROM workflow_phases WHERE project_id IN (
    SELECT id FROM projects WHERE name LIKE '%Test%'
);
DELETE FROM approval_gates WHERE project_id IN (
    SELECT id FROM projects WHERE name LIKE '%Test%'
);
DELETE FROM scar_command_executions WHERE project_id IN (
    SELECT id FROM projects WHERE name LIKE '%Test%'
);
DELETE FROM projects WHERE name LIKE '%Test%';
EOF

# Close test Telegram chats (manually in Telegram app)

# Delete test GitHub issues (manually on GitHub)
```

## Test Checklist

Use this checklist to verify everything works:

### Infrastructure
- [ ] API server responds to /health
- [ ] Database connection successful
- [ ] All Docker containers running (if using Docker)
- [ ] Migrations applied successfully

### Database
- [ ] All tables created
- [ ] Can insert and query projects
- [ ] Can insert and query conversation messages
- [ ] Workflow phases created correctly

### Telegram Bot
- [ ] Bot responds to /start
- [ ] Bot responds to /help
- [ ] Bot responds to natural language messages
- [ ] Bot saves conversation to database
- [ ] Bot offers vision document generation
- [ ] Approval buttons work
- [ ] /status command shows correct information
- [ ] /continue command advances workflow

### GitHub Integration
- [ ] Webhook configured in GitHub
- [ ] Webhook health endpoint responds
- [ ] @mentions detected and processed
- [ ] Webhook signature verification works
- [ ] Project lookup by repo URL works
- [ ] Logs show webhook events

### End-to-End Workflow
- [ ] Complete brainstorming phase
- [ ] Vision document generated and approved
- [ ] PRIME command executed
- [ ] PLAN-FEATURE-GITHUB executed and approved
- [ ] EXECUTE-GITHUB executed
- [ ] VALIDATE executed and approved
- [ ] Workflow phases all completed

### Security
- [ ] Unsigned webhooks rejected
- [ ] Wrong signature webhooks rejected
- [ ] SQL injection protection verified
- [ ] Environment variables not exposed

## Troubleshooting Common Issues

### Issue: "Connection refused" errors

**Cause**: Service not running or wrong port

**Solution**:
```bash
# Check if service is running
netstat -tlnp | grep 8000

# Restart service
docker-compose restart app
```

### Issue: "Database does not exist"

**Cause**: Database not created

**Solution**:
```bash
createdb project_orchestrator -O orchestrator
alembic upgrade head
```

### Issue: Telegram bot doesn't respond

**Cause**: Wrong token or bot process not running

**Solution**:
```bash
# Verify token
curl "https://api.telegram.org/bot<TOKEN>/getMe"

# Check bot process
docker-compose logs -f app | grep bot

# Restart bot
docker-compose restart app
```

### Issue: GitHub webhooks fail with 403

**Cause**: Signature verification failure

**Solution**:
```bash
# Verify secret matches
echo $GITHUB_WEBHOOK_SECRET
# Should match GitHub webhook settings

# Check logs for signature verification
docker-compose logs app | grep signature
```

## Support

If tests fail:
1. Check logs for error messages
2. Verify all environment variables are set
3. Ensure all services are running
4. Review this guide for missed steps
5. Check GitHub issues for known problems
