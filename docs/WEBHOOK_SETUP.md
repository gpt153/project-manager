# GitHub Webhook Setup Guide

This guide explains how to configure GitHub webhooks to enable the Project Orchestrator to respond to @mentions in issues and pull requests.

## Overview

GitHub webhooks allow the Project Orchestrator to:
- Receive notifications when someone mentions the bot in an issue
- Respond to pull request events
- Automatically trigger workflow actions based on GitHub activity

## Prerequisites

Before setting up webhooks, ensure:

- ✅ Project Orchestrator is deployed and accessible via public URL
- ✅ API server is running on port 8000
- ✅ You have admin access to the GitHub repository
- ✅ `GITHUB_WEBHOOK_SECRET` is configured in your `.env` file

## Step-by-Step Setup

### 1. Determine Your Webhook URL

The webhook URL depends on your deployment:

**For Production (with domain)**:
```
https://your-domain.com/webhooks/github/
```

**For Development (using ngrok)**:
```bash
# Install ngrok if not already installed
brew install ngrok  # macOS
# or download from https://ngrok.com/download

# Start ngrok tunnel
ngrok http 8000

# Use the HTTPS URL provided (e.g., https://abc123.ngrok.io/webhooks/github/)
```

**Important**: The URL must be publicly accessible from the internet.

### 2. Verify Webhook Endpoint is Working

Test the health check endpoint:

```bash
curl https://your-domain.com/webhooks/github/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "github_webhook"
}
```

If this fails, check your deployment and ensure the API server is running.

### 3. Configure Webhook in GitHub Repository

#### Step 3.1: Navigate to Repository Settings

1. Go to your GitHub repository
2. Click **Settings** (top right)
3. Click **Webhooks** (left sidebar)
4. Click **Add webhook** button

#### Step 3.2: Configure Webhook

Fill in the webhook configuration:

**Payload URL**:
```
https://your-domain.com/webhooks/github/
```

**Content type**:
- Select: `application/json`

**Secret**:
- Enter the value from `GITHUB_WEBHOOK_SECRET` in your `.env` file
- This should be a random string (e.g., generated with `openssl rand -hex 32`)

**Which events would you like to trigger this webhook?**

Select: **Let me select individual events**

Check these events:
- ✅ **Issue comments** - To receive @mentions in issue comments
- ✅ **Issues** - To track issue creation and updates
- ✅ **Pull request** - To monitor PR activity (optional)
- ✅ **Pull request reviews** - To track PR reviews (optional)
- ✅ **Pull request review comments** - To receive @mentions in PR review comments (optional)

**Active**:
- ✅ Ensure this is checked

#### Step 3.3: Save Webhook

Click **Add webhook** button.

GitHub will immediately send a test payload. You should see:
- ✅ Green checkmark if successful
- ❌ Red X if failed (check logs for details)

### 4. Verify Webhook Configuration

#### Check Recent Deliveries

1. In GitHub, go to Settings > Webhooks
2. Click on the webhook you just created
3. Scroll to **Recent Deliveries**
4. Click on the latest delivery
5. Check the **Response** tab:

**Successful Response** (200 OK):
```json
{
  "message": "Webhook received",
  "event": "ping"
}
```

**Failed Response** (500, 401, etc.):
- Check your application logs for errors
- Verify the webhook secret matches
- Ensure the URL is correct and accessible

#### Test with Real Event

Create a test by:

1. Create a new issue in your repository
2. Mention the bot: `@po please help with this`
3. Check webhook deliveries in GitHub Settings
4. Check your application logs:

```bash
# For Docker
docker-compose logs -f app | grep github

# For systemd
sudo journalctl -u project-orchestrator-api -f | grep github
```

You should see logs indicating:
```
INFO: Received GitHub webhook: issue_comment
INFO: Processing @mention from user: yourusername
INFO: Routing to orchestrator agent...
```

## Bot Mention Name

The bot responds to mentions using `@po` (short for "Project Orchestrator").

To change the mention name:

1. Edit `src/integrations/github_webhook.py`
2. Find the line: `BOT_MENTION = "@po"`
3. Change to your preferred name (e.g., `@project-orchestrator`)
4. Restart the application

## Webhook Events Explained

### Issue Comment Events

Triggered when someone comments on an issue.

**Payload structure**:
```json
{
  "action": "created",
  "issue": {
    "number": 123,
    "title": "Feature request",
    "body": "Description",
    "user": { "login": "username" }
  },
  "comment": {
    "body": "@po please help",
    "user": { "login": "commenter" }
  },
  "repository": {
    "full_name": "owner/repo",
    "html_url": "https://github.com/owner/repo"
  }
}
```

**Bot behavior**:
- Checks if comment contains `@po`
- If yes, routes message to orchestrator agent
- Looks up project by repository URL
- Processes the request and posts a response (future feature)

### Issue Events

Triggered when an issue is opened, edited, closed, etc.

**Actions handled**:
- `opened` - New issue created
- `edited` - Issue title or description changed
- `closed` - Issue closed
- `reopened` - Issue reopened

### Pull Request Events

Triggered when a PR is opened, merged, closed, etc.

**Future feature**: Automatically validate PRs, run tests, update status.

## Security Considerations

### Webhook Signature Verification

The Project Orchestrator verifies webhook authenticity using HMAC-SHA256:

1. GitHub signs each webhook with your secret
2. Our app receives the webhook and the signature (in `X-Hub-Signature-256` header)
3. App computes expected signature using the secret
4. If signatures match → webhook is authentic
5. If signatures don't match → webhook is rejected (403 Forbidden)

**Code reference**: `src/integrations/github_webhook.py` - `verify_github_signature()`

### Best Practices

1. **Use a strong secret** - Generate with `openssl rand -hex 32`
2. **Never commit secrets** - Keep `GITHUB_WEBHOOK_SECRET` in `.env` only
3. **Use HTTPS** - Webhooks should only be sent to HTTPS endpoints
4. **Monitor failed deliveries** - Check GitHub webhook settings regularly
5. **Rotate secrets periodically** - Update the secret every 90 days

## Troubleshooting

### Webhook Deliveries Failing (Red X)

**Problem**: GitHub shows failed deliveries with 4xx or 5xx errors.

**Solutions**:

1. **401 Unauthorized / 403 Forbidden**:
   ```bash
   # Check webhook secret matches
   cat .env | grep GITHUB_WEBHOOK_SECRET
   # Should match the secret in GitHub webhook settings
   ```

2. **404 Not Found**:
   ```bash
   # Verify URL is correct
   curl https://your-domain.com/webhooks/github/health
   # Should return {"status": "healthy"}
   ```

3. **500 Internal Server Error**:
   ```bash
   # Check application logs
   docker-compose logs app | tail -100
   # Look for Python tracebacks
   ```

4. **Timeout**:
   ```bash
   # Ensure server is running and accessible
   curl -I https://your-domain.com/webhooks/github/
   # Should return HTTP 405 (Method Not Allowed for GET) or 200
   ```

### Bot Not Responding to @Mentions

**Problem**: Commenting `@po help` but nothing happens.

**Solutions**:

1. **Check webhook is configured**:
   - Go to GitHub repo Settings > Webhooks
   - Verify webhook exists and is active
   - Check Recent Deliveries show successful (green checkmark)

2. **Check bot mention name**:
   ```bash
   # Verify the mention name in code
   grep "BOT_MENTION" src/integrations/github_webhook.py
   # Default is "@po"
   ```

3. **Check project exists in database**:
   ```bash
   # Connect to database
   psql -U orchestrator -d project_orchestrator

   # List projects
   SELECT id, name, github_repo_url FROM projects;

   # Should show your repository URL
   ```

4. **Check application logs**:
   ```bash
   docker-compose logs -f app | grep "Processing @mention"
   # Should see log when @mention is detected
   ```

### Signature Verification Failures

**Problem**: Logs show "Invalid signature" errors.

**Solutions**:

```bash
# 1. Verify secret matches
echo $GITHUB_WEBHOOK_SECRET

# 2. Check secret is loaded in application
docker-compose exec app python -c "from src.config import get_settings; print(get_settings().github_webhook_secret)"

# 3. Update secret in GitHub webhook settings to match

# 4. Restart application
docker-compose restart app
```

### Testing Webhooks Locally with ngrok

For local development and testing:

```bash
# 1. Start application locally
docker-compose up

# 2. Start ngrok tunnel
ngrok http 8000

# 3. Use ngrok HTTPS URL in GitHub webhook settings
# Example: https://abc123.ngrok.io/webhooks/github/

# 4. Test by creating issue comment with @mention

# 5. Watch logs in real-time
docker-compose logs -f app
```

## Advanced Configuration

### IP Whitelisting (Optional)

For extra security, only allow webhooks from GitHub's IP ranges:

1. Get GitHub's webhook IPs: https://api.github.com/meta
2. Configure firewall or reverse proxy to only allow those IPs
3. Example nginx config:

```nginx
location /webhooks/github/ {
    # Allow GitHub webhook IPs
    allow 140.82.112.0/20;
    allow 143.55.64.0/20;
    allow 185.199.108.0/22;
    allow 192.30.252.0/22;
    deny all;

    proxy_pass http://127.0.0.1:8000;
}
```

### Custom Webhook Handler

To add custom logic when webhooks are received:

1. Edit `src/integrations/github_webhook.py`
2. Find the `handle_webhook()` function
3. Add your custom logic for specific events

Example:

```python
@router.post("/")
async def receive_webhook(
    request: Request,
    x_hub_signature_256: str = Header(None),
    x_github_event: str = Header(None),
    session: AsyncSession = Depends(get_session),
):
    # ... existing code ...

    # Custom logic for issue opened
    if event_type == "issues" and payload.get("action") == "opened":
        issue_number = payload["issue"]["number"]
        # Do something custom
        logger.info(f"New issue #{issue_number} opened!")

    # ... rest of code ...
```

### Webhook Event Logging

All webhook events are logged. To view:

```bash
# Real-time webhook logs
docker-compose logs -f app | grep webhook

# Search for specific issue
docker-compose logs app | grep "issue #123"

# Count webhook events received today
docker-compose logs app | grep "Received GitHub webhook" | grep "$(date +%Y-%m-%d)" | wc -l
```

## Multiple Repositories

To use the Project Orchestrator with multiple repositories:

1. **Set up webhook in each repository** (repeat Steps 1-4 for each repo)
2. **Use the same webhook secret** for all repositories
3. **Create a project in database for each repository**:

```sql
-- Connect to database
psql -U orchestrator -d project_orchestrator

-- Create project for each repo
INSERT INTO projects (name, github_repo_url, status, created_at)
VALUES
  ('My First Project', 'https://github.com/owner/repo1', 'brainstorming', NOW()),
  ('My Second Project', 'https://github.com/owner/repo2', 'brainstorming', NOW());
```

The bot will automatically identify which project based on the repository URL in webhook payloads.

## Webhook Payload Examples

### Issue Comment with @Mention

```json
{
  "action": "created",
  "issue": {
    "number": 5,
    "title": "Build user authentication",
    "state": "open",
    "user": {
      "login": "gpt153"
    }
  },
  "comment": {
    "id": 123456789,
    "body": "@po please help plan this feature",
    "user": {
      "login": "gpt153"
    },
    "created_at": "2024-12-19T10:30:00Z"
  },
  "repository": {
    "full_name": "gpt153/my-app",
    "html_url": "https://github.com/gpt153/my-app"
  }
}
```

### Pull Request Opened

```json
{
  "action": "opened",
  "pull_request": {
    "number": 10,
    "title": "Add login page",
    "state": "open",
    "user": {
      "login": "gpt153"
    },
    "head": {
      "ref": "feature/login"
    },
    "base": {
      "ref": "main"
    }
  },
  "repository": {
    "full_name": "gpt153/my-app"
  }
}
```

## Resources

- [GitHub Webhooks Documentation](https://docs.github.com/en/developers/webhooks-and-events/webhooks/about-webhooks)
- [GitHub Webhook Events](https://docs.github.com/en/developers/webhooks-and-events/webhooks/webhook-events-and-payloads)
- [Securing Webhooks](https://docs.github.com/en/developers/webhooks-and-events/webhooks/securing-your-webhooks)

## Support

If you encounter issues:
1. Check Recent Deliveries in GitHub webhook settings
2. Review application logs for errors
3. Verify webhook secret matches
4. Test webhook endpoint manually with curl
5. Create an issue in the Project Orchestrator repository
