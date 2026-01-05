# Database Setup and Management Guide

Complete guide for setting up, initializing, and managing the Project Manager database.

## Overview

The Project Manager uses PostgreSQL with async SQLAlchemy for data persistence:

- **Database**: PostgreSQL 14+
- **ORM**: SQLAlchemy 2.0+ (async)
- **Migrations**: Alembic
- **Driver**: asyncpg

## Database Schema

### Tables

#### 1. **projects**
Stores project information and metadata.

```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,  -- 'brainstorming', 'planning', 'implementing', etc.
    vision_document TEXT,
    github_repo_url VARCHAR(512),
    telegram_chat_id BIGINT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

**Indexes**:
- `idx_projects_telegram_chat_id` on `telegram_chat_id`
- `idx_projects_github_repo_url` on `github_repo_url`

#### 2. **conversation_messages**
Stores all conversation history between users and the orchestrator agent.

```sql
CREATE TABLE conversation_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,  -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    message_metadata JSONB,  -- Additional metadata (timestamp, source, etc.)
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

**Indexes**:
- `idx_conversation_messages_project_id` on `project_id`
- `idx_conversation_messages_created_at` on `created_at`

#### 3. **workflow_phases**
Tracks workflow progress through different phases.

```sql
CREATE TABLE workflow_phases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    phase_number INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,  -- 'vision_review', 'prime_context', etc.
    status VARCHAR(50) NOT NULL,  -- 'pending', 'in_progress', 'completed', 'blocked'
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

**Indexes**:
- `idx_workflow_phases_project_id` on `project_id`
- `idx_workflow_phases_status` on `status`

**Phases**:
1. Vision Document Review
2. Prime Context
3. Plan Feature
4. Execute Implementation
5. Validate & Test

#### 4. **approval_gates**
Manages user approval points in the workflow.

```sql
CREATE TABLE approval_gates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    gate_type VARCHAR(50) NOT NULL,  -- 'vision_document', 'implementation_plan', 'validation'
    status VARCHAR(50) NOT NULL,  -- 'pending', 'approved', 'rejected'
    request_data JSONB,  -- The data being approved (vision doc, plan, etc.)
    response TEXT,  -- User's feedback/reason
    approved_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

**Indexes**:
- `idx_approval_gates_project_id` on `project_id`
- `idx_approval_gates_status` on `status`

#### 5. **scar_command_executions**
Logs all SCAR command executions.

```sql
CREATE TABLE scar_command_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    command_type VARCHAR(50) NOT NULL,  -- 'PRIME', 'PLAN-FEATURE-GITHUB', etc.
    command_args JSONB,  -- Command arguments
    status VARCHAR(50) NOT NULL,  -- 'queued', 'running', 'success', 'failed'
    output TEXT,  -- Command output
    error TEXT,  -- Error message if failed
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

**Indexes**:
- `idx_scar_executions_project_id` on `project_id`
- `idx_scar_executions_command_type` on `command_type`
- `idx_scar_executions_status` on `status`

## Installation Steps

### Option 1: Using Docker Compose (Easiest)

The database is automatically created and initialized:

```bash
# Start PostgreSQL container
docker-compose up -d postgres

# Wait for database to be ready
docker-compose logs -f postgres | grep "database system is ready"

# Database is ready!
```

Connection details:
- **Host**: `localhost` (or `postgres` from other containers)
- **Port**: `5432`
- **Database**: `project_orchestrator`
- **User**: `orchestrator`
- **Password**: `dev_password` (change in production!)

### Option 2: Manual PostgreSQL Installation

#### Ubuntu/Debian

```bash
# Install PostgreSQL
sudo apt-get update
sudo apt-get install -y postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create user and database
sudo -u postgres psql <<EOF
CREATE USER orchestrator WITH PASSWORD 'your_secure_password';
CREATE DATABASE project_orchestrator OWNER orchestrator;
GRANT ALL PRIVILEGES ON DATABASE project_orchestrator TO orchestrator;
ALTER USER orchestrator CREATEDB;  -- Needed for running tests
EOF
```

#### macOS

```bash
# Install PostgreSQL
brew install postgresql@15

# Start PostgreSQL service
brew services start postgresql@15

# Create user and database
createuser orchestrator -P  # Enter password when prompted
createdb project_orchestrator -O orchestrator
```

#### Verify Installation

```bash
# Test connection
psql -U orchestrator -h localhost -d project_orchestrator -c "SELECT version();"

# Expected output: PostgreSQL version information
```

## Running Migrations

### Initialize Alembic (First Time Only)

Alembic is already initialized in this project. If you need to start fresh:

```bash
# ONLY if starting from scratch (not needed for this project)
alembic init database/migrations
```

### Apply Migrations

```bash
# Check current migration version
alembic current

# View migration history
alembic history --verbose

# Upgrade to latest version
alembic upgrade head

# Check which migrations were applied
alembic current
```

Expected output:
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> xxxxx, Initial migration
```

### Create New Migration

When you modify database models:

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add new feature column"

# Review the generated migration file in database/migrations/versions/

# Apply the migration
alembic upgrade head
```

### Rollback Migrations

```bash
# Rollback to previous version
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>

# Rollback all migrations
alembic downgrade base
```

## Database Initialization

### Create Sample Data

Run the initialization script to create sample projects:

```bash
python scripts/init_db.py
```

This creates:
- 1 sample project in "brainstorming" status
- Initial conversation messages
- Sample workflow phases

### Manual Data Creation

Connect to the database and insert data:

```bash
psql -U orchestrator -d project_orchestrator
```

#### Create a Project

```sql
INSERT INTO projects (name, status, github_repo_url, telegram_chat_id)
VALUES (
    'My Awesome App',
    'brainstorming',
    'https://github.com/username/my-awesome-app',
    123456789  -- Your Telegram chat ID
)
RETURNING id;
-- Copy the UUID returned
```

#### Add Conversation Messages

```sql
-- Replace <project-id> with the UUID from above
INSERT INTO conversation_messages (project_id, role, content)
VALUES
  ('<project-id>', 'user', 'I want to build a task manager'),
  ('<project-id>', 'assistant', 'Great! Tell me more about who will use it...'),
  ('<project-id>', 'user', 'It''s for busy professionals and students');
```

#### Initialize Workflow Phases

```sql
INSERT INTO workflow_phases (project_id, phase_number, name, status)
VALUES
  ('<project-id>', 1, 'vision_review', 'pending'),
  ('<project-id>', 2, 'prime_context', 'pending'),
  ('<project-id>', 3, 'plan_feature', 'pending'),
  ('<project-id>', 4, 'execute_implementation', 'pending'),
  ('<project-id>', 5, 'validate_test', 'pending');
```

## Querying Data

### Useful Queries

#### List All Projects

```sql
SELECT
    id,
    name,
    status,
    github_repo_url,
    telegram_chat_id,
    created_at
FROM projects
ORDER BY created_at DESC;
```

#### Get Project Conversation History

```sql
SELECT
    role,
    content,
    created_at
FROM conversation_messages
WHERE project_id = '<project-id>'
ORDER BY created_at ASC;
```

#### Check Workflow Progress

```sql
SELECT
    p.name AS project_name,
    wp.phase_number,
    wp.name AS phase_name,
    wp.status,
    wp.started_at,
    wp.completed_at
FROM workflow_phases wp
JOIN projects p ON wp.project_id = p.id
WHERE p.id = '<project-id>'
ORDER BY wp.phase_number;
```

#### View Pending Approval Gates

```sql
SELECT
    p.name AS project_name,
    ag.gate_type,
    ag.status,
    ag.created_at
FROM approval_gates ag
JOIN projects p ON ag.project_id = p.id
WHERE ag.status = 'pending'
ORDER BY ag.created_at ASC;
```

#### SCAR Command Execution History

```sql
SELECT
    p.name AS project_name,
    command_type,
    status,
    started_at,
    completed_at,
    EXTRACT(EPOCH FROM (completed_at - started_at)) AS duration_seconds,
    error
FROM scar_command_executions
JOIN projects p ON scar_command_executions.project_id = p.id
ORDER BY started_at DESC
LIMIT 20;
```

## Database Maintenance

### Backup Database

#### Full Backup

```bash
# Backup to file
pg_dump -U orchestrator -h localhost project_orchestrator > backup_$(date +%Y%m%d).sql

# Compressed backup
pg_dump -U orchestrator -h localhost project_orchestrator | gzip > backup_$(date +%Y%m%d).sql.gz
```

#### Restore from Backup

```bash
# Restore from plain SQL
psql -U orchestrator -h localhost project_orchestrator < backup_20241219.sql

# Restore from compressed backup
gunzip -c backup_20241219.sql.gz | psql -U orchestrator -h localhost project_orchestrator
```

### Automated Backups

Create a backup script `/opt/scripts/backup_orchestrator_db.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/orchestrator"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/orchestrator_$DATE.sql"

mkdir -p $BACKUP_DIR

# Perform backup
pg_dump -U orchestrator -h localhost project_orchestrator > "$BACKUP_FILE"

# Compress
gzip "$BACKUP_FILE"

# Keep only last 30 days
find "$BACKUP_DIR" -name "orchestrator_*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE.gz"
```

Add to crontab:

```bash
# Daily backup at 2 AM
0 2 * * * /opt/scripts/backup_orchestrator_db.sh
```

### Vacuum and Analyze

Optimize database performance:

```bash
# Connect to database
psql -U orchestrator -d project_orchestrator

# Analyze tables (updates statistics)
ANALYZE;

# Vacuum (reclaim storage)
VACUUM;

# Full vacuum with analyze
VACUUM FULL ANALYZE;
```

### Monitor Database Size

```sql
-- Database size
SELECT pg_size_pretty(pg_database_size('project_orchestrator'));

-- Table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## Security Best Practices

### 1. Strong Password

```bash
# Generate strong password
openssl rand -base64 32

# Update password
sudo -u postgres psql -c "ALTER USER orchestrator WITH PASSWORD 'new_strong_password';"

# Update .env file with new password
```

### 2. Limit Network Access

Edit `/etc/postgresql/15/main/pg_hba.conf`:

```
# Allow only from localhost
host    project_orchestrator    orchestrator    127.0.0.1/32    scram-sha-256
host    project_orchestrator    orchestrator    ::1/128         scram-sha-256

# Deny all others
host    all                     all             0.0.0.0/0       reject
```

Restart PostgreSQL:

```bash
sudo systemctl restart postgresql
```

### 3. SSL Connections

Enable SSL in `/etc/postgresql/15/main/postgresql.conf`:

```
ssl = on
ssl_cert_file = '/etc/ssl/certs/ssl-cert-snakeoil.pem'
ssl_key_file = '/etc/ssl/private/ssl-cert-snakeoil.key'
```

Update connection string in `.env`:

```
DATABASE_URL=postgresql+asyncpg://orchestrator:password@localhost:5432/project_orchestrator?ssl=require
```

### 4. Regular Updates

```bash
# Update PostgreSQL
sudo apt-get update
sudo apt-get upgrade postgresql
```

## Troubleshooting

### Cannot Connect to Database

```bash
# 1. Check if PostgreSQL is running
sudo systemctl status postgresql

# 2. Check if port is listening
sudo netstat -tlnp | grep 5432

# 3. Test connection
psql -U orchestrator -h localhost -d project_orchestrator

# 4. Check logs
sudo tail -f /var/log/postgresql/postgresql-15-main.log
```

### Migration Errors

```bash
# 1. Check current state
alembic current

# 2. Check migration history
alembic history

# 3. If stuck, reset migrations (⚠️ DESTROYS DATA)
alembic downgrade base
alembic upgrade head

# 4. If tables exist but alembic thinks they don't
alembic stamp head  # Mark current state as up-to-date
```

### Database Locked / Connection Issues

```bash
# 1. Check active connections
psql -U postgres -c "SELECT * FROM pg_stat_activity WHERE datname = 'project_orchestrator';"

# 2. Kill hanging connections
psql -U postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'project_orchestrator' AND pid <> pg_backend_pid();"

# 3. Restart PostgreSQL
sudo systemctl restart postgresql
```

### Out of Disk Space

```bash
# 1. Check disk usage
df -h

# 2. Check database size
psql -U orchestrator -d project_orchestrator -c "SELECT pg_size_pretty(pg_database_size('project_orchestrator'));"

# 3. Vacuum to reclaim space
psql -U orchestrator -d project_orchestrator -c "VACUUM FULL;"

# 4. Remove old data
psql -U orchestrator -d project_orchestrator -c "DELETE FROM conversation_messages WHERE created_at < NOW() - INTERVAL '90 days';"
```

## Performance Optimization

### Connection Pooling

The application uses SQLAlchemy's async connection pooling. Configure in `.env`:

```bash
DATABASE_POOL_SIZE=10        # Number of persistent connections
DATABASE_MAX_OVERFLOW=20     # Maximum additional connections
```

### Indexes

All critical indexes are created by migrations. To check:

```sql
-- List all indexes
SELECT tablename, indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
```

### Query Performance

```sql
-- Enable query timing
\timing

-- Explain query plan
EXPLAIN ANALYZE
SELECT * FROM conversation_messages WHERE project_id = '<uuid>';

-- Look for slow queries
SELECT
    query,
    calls,
    total_time,
    mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

## Testing Database

For running tests with a test database:

```bash
# Create test database
createdb project_orchestrator_test -O orchestrator

# Run tests
TEST_DATABASE_URL=postgresql+asyncpg://orchestrator:password@localhost/project_orchestrator_test pytest

# Clean up
dropdb project_orchestrator_test
```

## Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLAlchemy Async Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [asyncpg Documentation](https://magicstack.github.io/asyncpg/)
