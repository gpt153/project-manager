# Project Orchestrator - Deployment Guide

Complete guide for deploying the Project Orchestrator in production or staging environments.

## Prerequisites

Before deployment, ensure you have:

- [x] Python 3.11 or higher installed
- [x] PostgreSQL 14+ database server
- [x] Docker and Docker Compose (optional, but recommended)
- [x] API keys and tokens (see Configuration section)
- [x] Server with public internet access (for webhooks)

## Configuration

### 1. Environment Variables Setup

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit the `.env` file with your actual values:

```bash
# Application Configuration
APP_NAME="Project Orchestrator"
APP_ENV=production  # Change to 'production' for prod
LOG_LEVEL=INFO
SECRET_KEY=your-super-secret-key-change-me  # Generate with: openssl rand -hex 32

# Database Configuration
DATABASE_URL=postgresql+asyncpg://orchestrator:YOUR_DB_PASSWORD@localhost:5432/project_orchestrator
DATABASE_ECHO=false  # Set to true for SQL query logging
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Anthropic API (for PydanticAI / Claude Sonnet 4)
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxx  # Get from https://console.anthropic.com/

# Telegram Bot
TELEGRAM_BOT_TOKEN=1234567890:xxxxxxxxxxxxxxxxxxxxx  # Get from @BotFather on Telegram

# GitHub Integration
GITHUB_ACCESS_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxx  # Personal access token from GitHub
GITHUB_WEBHOOK_SECRET=your-webhook-secret  # Choose a random string

# Optional: Redis (for caching - future feature)
REDIS_URL=redis://localhost:6379/0

# Optional: Monitoring
SENTRY_DSN=https://xxxxx@sentry.io/xxxxx  # For error tracking

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=false  # Set to true only in development
```

### 2. Obtain Required API Keys

#### Anthropic API Key
1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to API Keys
4. Create a new key
5. Copy the key (starts with `sk-ant-`)

#### Telegram Bot Token
1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow the prompts to create your bot
4. Copy the token provided
5. Send `/setdescription` to add a bot description
6. Send `/setcommands` and add:
```
start - Start a new project
help - Show available commands
status - Check current workflow status
continue - Advance to next workflow phase
```

#### GitHub Personal Access Token
1. Go to GitHub Settings > Developer settings > Personal access tokens > Tokens (classic)
2. Click "Generate new token (classic)"
3. Give it a descriptive name: "Project Orchestrator Bot"
4. Select scopes:
   - `repo` (all sub-scopes)
   - `admin:repo_hook` (for webhook management)
5. Click "Generate token"
6. Copy the token immediately (starts with `ghp_`)

## Deployment Methods

### Method 1: Docker Compose (Recommended)

This is the easiest method for deployment.

#### Step 1: Ensure Docker is Installed

```bash
docker --version
docker-compose --version
```

#### Step 2: Configure Environment

```bash
# Copy and edit .env file
cp .env.example .env
nano .env  # or use your preferred editor
```

#### Step 3: Start Services

```bash
# Pull and build images
docker-compose build

# Start all services in background
docker-compose up -d

# Check service status
docker-compose ps
```

Expected output:
```
NAME                  STATUS              PORTS
orchestrator-app-1    Up (healthy)        0.0.0.0:8000->8000/tcp
orchestrator-db-1     Up (healthy)        0.0.0.0:5432->5432/tcp
orchestrator-redis-1  Up (healthy)        0.0.0.0:6379->6379/tcp
```

#### Step 4: View Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f app
```

#### Step 5: Run Database Migrations

```bash
docker-compose exec app alembic upgrade head
```

#### Step 6: Start Telegram Bot

```bash
docker-compose exec -d app python -m src.bot_main
```

#### Step 7: Verify Deployment

```bash
# Check API health
curl http://localhost:8000/health

# Check API documentation
open http://localhost:8000/docs
```

### Method 2: Manual Deployment (without Docker)

Use this if you don't have Docker or prefer manual control.

#### Step 1: Install Python Dependencies

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -e .
pip install -e ".[dev]"  # Optional: for development tools
```

#### Step 2: Set Up PostgreSQL Database

```bash
# Create database user
sudo -u postgres createuser orchestrator -P  # Enter password when prompted

# Create database
sudo -u postgres createdb project_orchestrator -O orchestrator

# Verify connection
psql -U orchestrator -h localhost -d project_orchestrator -c "SELECT version();"
```

#### Step 3: Configure Environment

```bash
cp .env.example .env
nano .env  # Update DATABASE_URL and other settings
```

#### Step 4: Run Database Migrations

```bash
alembic upgrade head
```

#### Step 5: Start the Application

```bash
# Option A: Run API server
python -m src.main

# Option B: Run with uvicorn (for production)
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Step 6: Start Telegram Bot (in separate terminal)

```bash
source venv/bin/activate
python -m src.bot_main
```

### Method 3: Production Deployment with systemd

For production Linux servers, use systemd to manage services.

#### Step 1: Create systemd Service Files

Create `/etc/systemd/system/project-orchestrator-api.service`:

```ini
[Unit]
Description=Project Orchestrator FastAPI Application
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/project-orchestrator
Environment="PATH=/opt/project-orchestrator/venv/bin"
EnvironmentFile=/opt/project-orchestrator/.env
ExecStart=/opt/project-orchestrator/venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/project-orchestrator-bot.service`:

```ini
[Unit]
Description=Project Orchestrator Telegram Bot
After=network.target project-orchestrator-api.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/project-orchestrator
Environment="PATH=/opt/project-orchestrator/venv/bin"
EnvironmentFile=/opt/project-orchestrator/.env
ExecStart=/opt/project-orchestrator/venv/bin/python -m src.bot_main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Step 2: Enable and Start Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services to start on boot
sudo systemctl enable project-orchestrator-api
sudo systemctl enable project-orchestrator-bot

# Start services
sudo systemctl start project-orchestrator-api
sudo systemctl start project-orchestrator-bot

# Check status
sudo systemctl status project-orchestrator-api
sudo systemctl status project-orchestrator-bot

# View logs
sudo journalctl -u project-orchestrator-api -f
sudo journalctl -u project-orchestrator-bot -f
```

## Database Setup

### Initial Database Creation

If using Docker Compose, the database is created automatically. For manual setup:

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create user and database
CREATE USER orchestrator WITH PASSWORD 'your_password_here';
CREATE DATABASE project_orchestrator OWNER orchestrator;

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE project_orchestrator TO orchestrator;

# Exit
\q
```

### Run Migrations

```bash
# Check current migration status
alembic current

# Show migration history
alembic history

# Upgrade to latest
alembic upgrade head

# If needed, downgrade
alembic downgrade -1  # Go back one version
```

### Database Initialization Script

Run the initialization script to create initial data:

```bash
python scripts/init_db.py
```

## Production Considerations

### 1. Reverse Proxy Setup (Nginx)

For production, use Nginx as a reverse proxy:

```nginx
# /etc/nginx/sites-available/project-orchestrator
server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # GitHub webhooks
    location /webhooks/github/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API endpoints
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/project-orchestrator /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 2. SSL Certificate (Let's Encrypt)

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 3. Firewall Configuration

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
```

### 4. Database Backups

Create a backup script `/opt/project-orchestrator/scripts/backup_db.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/opt/project-orchestrator/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/db_backup_$DATE.sql"

mkdir -p $BACKUP_DIR

pg_dump -U orchestrator -h localhost project_orchestrator > $BACKUP_FILE
gzip $BACKUP_FILE

# Keep only last 30 days of backups
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE.gz"
```

Add to crontab:

```bash
# Run daily at 2 AM
0 2 * * * /opt/project-orchestrator/scripts/backup_db.sh
```

### 5. Monitoring and Logging

#### Set Up Log Rotation

Create `/etc/logrotate.d/project-orchestrator`:

```
/var/log/project-orchestrator/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
}
```

#### Health Check Monitoring

Use a service like UptimeRobot or create a cron job:

```bash
# Check health every 5 minutes
*/5 * * * * curl -f http://localhost:8000/health || echo "Health check failed" | mail -s "Project Orchestrator Down" admin@example.com
```

## Troubleshooting

### Application Won't Start

```bash
# Check logs
docker-compose logs app  # For Docker
sudo journalctl -u project-orchestrator-api -n 50  # For systemd

# Common issues:
# 1. Database connection failed
#    - Verify DATABASE_URL in .env
#    - Check if PostgreSQL is running: sudo systemctl status postgresql

# 2. Port already in use
#    - Find process: sudo lsof -i :8000
#    - Kill process: sudo kill -9 <PID>

# 3. Missing environment variables
#    - Check .env file exists and has all required vars
#    - Verify .env is being loaded
```

### Database Migration Errors

```bash
# Reset migrations (⚠️ DESTROYS DATA)
alembic downgrade base
alembic upgrade head

# Or recreate database
dropdb project_orchestrator
createdb project_orchestrator -O orchestrator
alembic upgrade head
```

### Telegram Bot Not Responding

```bash
# 1. Verify bot token
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getMe"

# 2. Check bot process is running
ps aux | grep bot_main

# 3. Check bot logs
docker-compose logs -f app | grep telegram
```

### GitHub Webhooks Not Working

```bash
# 1. Verify webhook is configured (see WEBHOOK_SETUP.md)

# 2. Test webhook endpoint
curl -X POST http://your-domain.com/webhooks/github/health

# 3. Check webhook signature verification
#    - Ensure GITHUB_WEBHOOK_SECRET matches GitHub settings
#    - Check webhook delivery logs in GitHub repo settings
```

## Updating the Application

### Docker Compose Method

```bash
# Pull latest code
git pull origin master

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d

# Run new migrations
docker-compose exec app alembic upgrade head
```

### Manual Method

```bash
# Pull latest code
git pull origin master

# Activate virtual environment
source venv/bin/activate

# Update dependencies
pip install -e .

# Run new migrations
alembic upgrade head

# Restart services
sudo systemctl restart project-orchestrator-api
sudo systemctl restart project-orchestrator-bot
```

## Security Best Practices

1. **Never commit `.env` file** - It contains secrets
2. **Use strong passwords** - For database and SECRET_KEY
3. **Enable firewall** - Only allow necessary ports
4. **Use HTTPS** - Always use SSL in production
5. **Regular updates** - Keep dependencies up to date
6. **Monitor logs** - Watch for suspicious activity
7. **Backup regularly** - Database and configuration
8. **Limit API access** - Use rate limiting (future feature)

## Next Steps

After deployment is complete:

1. ✅ Set up GitHub webhooks - See [WEBHOOK_SETUP.md](WEBHOOK_SETUP.md)
2. ✅ Create your first project in the database
3. ✅ Test Telegram bot - Send `/start` to your bot
4. ✅ Test GitHub integration - Mention bot in an issue
5. ✅ Monitor logs for errors
6. ✅ Set up backups and monitoring

## Support

For issues or questions:
- Check the [GitHub Issues](https://github.com/gpt153/project-orchestrator/issues)
- Review logs for error messages
- Consult the [README.md](../README.md) for general info
