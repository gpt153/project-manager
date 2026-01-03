# Project Orchestrator - Operations Runbook

## Health Monitoring

### Health Check Endpoints

**Basic Health**:
```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy", "service": "project-orchestrator"}
```

**Database Health**:
```bash
curl http://localhost:8000/health/db
# Expected: {"status": "healthy", "database": "connected"}
# Error: 503 with {"status": "unhealthy", "database": "disconnected", "error": "..."}
```

**AI Service Health**:
```bash
curl http://localhost:8000/health/ai
# Expected: {"status": "healthy", "ai_service": "reachable"}
# Degraded: {"status": "degraded", "ai_service": "unreachable"}
```

**Readiness Probe**:
```bash
curl http://localhost:8000/health/ready
# Ready: 200 with {"status": "ready", "database": "ok", "ai_service": "ok"}
# Not Ready: 503 with {"status": "not ready", ...}
```

---

## Metrics (When Prometheus Enabled)

### Metrics Endpoint
```bash
curl http://localhost:8000/metrics
```

### Key Metrics

**Conversation Metrics**:
- `orchestrator_conversations_total` - Total conversations started
- `orchestrator_active_projects` - Number of projects in active workflow

**Performance Metrics**:
- `scar_command_duration_seconds` - SCAR command execution time (histogram)
- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request latency

**Workflow Metrics**:
- `approval_gates_pending` - Number of pending approval gates
- `vision_documents_generated_total` - Total vision documents created

---

## Logging

### Application Logs

**Location**: stdout (structured JSON in production)

**Format**:
```json
{
  "timestamp": "2026-01-02T12:00:00Z",
  "level": "INFO",
  "logger": "orchestrator",
  "message": "Agent started conversation",
  "project_id": "...",
  "user_id": "..."
}
```

**Log Levels**:
- `DEBUG` - Detailed debugging information
- `INFO` - Normal operational events
- `WARNING` - Warning messages
- `ERROR` - Error events

### Audit Logs

**Location**: `logs/audit.log`

**Format**: JSON per line
```json
{
  "timestamp": "2026-01-02T12:00:00Z",
  "action": "project_created",
  "user_id": "telegram:123456",
  "project_id": "...",
  "details": {"name": "My Project"},
  "result": "success",
  "ip_address": "192.168.1.1"
}
```

**Actions Logged**:
- `project_created` - New project creation
- `workflow_started` - Workflow phase started
- `approval_granted` - Approval gate approved
- `scar_command_executed` - SCAR command executed

---

## Troubleshooting

### High Response Times

**Symptoms**:
- Slow API responses
- Timeouts
- User complaints about lag

**Investigation**:
1. Check metrics for bottlenecks:
   ```bash
   curl http://localhost:8000/metrics | grep duration
   ```

2. Review `scar_command_duration_seconds` histogram

3. Check database connection pool:
   - Look for connection pool exhaustion
   - Review slow query logs

4. Check external service latency:
   - Anthropic API response times
   - GitHub API response times

**Solutions**:
- Increase database connection pool size
- Optimize slow database queries
- Add caching layer (Redis)
- Scale horizontally (add more instances)

---

### Webhook Failures

**Symptoms**:
- GitHub webhooks not processing
- 403 errors in logs
- Missing bot responses on GitHub

**Investigation**:
1. Check webhook signature verification:
   ```bash
   # Look for signature verification errors in logs
   grep "signature verification" logs/*.log
   ```

2. Verify IP filtering (if enabled):
   ```bash
   # Check WEBHOOK_IP_FILTERING_ENABLED
   echo $WEBHOOK_IP_FILTERING_ENABLED
   ```

3. Check rate limiting:
   ```bash
   # Look for rate limit errors
   grep "Rate limit exceeded" logs/*.log
   ```

**Solutions**:
- Verify `GITHUB_WEBHOOK_SECRET` matches GitHub settings
- Update `GITHUB_WEBHOOK_IPS` if GitHub changes IP ranges
- Adjust rate limits if legitimate traffic is being blocked
- Check firewall rules

---

### Database Connection Issues

**Symptoms**:
- `/health/db` returns unhealthy
- Connection errors in logs
- 500 errors on API requests

**Investigation**:
1. Check PostgreSQL status:
   ```bash
   pg_isready -h localhost -p 5432
   ```

2. Verify credentials:
   ```bash
   echo $DATABASE_URL
   ```

3. Check connection pool:
   ```bash
   # Look for pool exhaustion errors
   grep "pool" logs/*.log
   ```

**Solutions**:
- Restart PostgreSQL if needed
- Verify `DATABASE_URL` credentials
- Increase connection pool size (max setting)
- Check for connection leaks in code

---

### AI Service Unavailable

**Symptoms**:
- `/health/ai` returns degraded
- Agent not responding
- Timeouts on conversations

**Investigation**:
1. Check Anthropic API status:
   ```bash
   curl https://api.anthropic.com
   ```

2. Verify API key:
   ```bash
   echo $ANTHROPIC_API_KEY | cut -c1-8
   # Should show first 8 chars
   ```

3. Check rate limits:
   - Review Anthropic dashboard for rate limit status

**Solutions**:
- Wait for Anthropic service restoration
- Verify API key is valid and not expired
- Implement exponential backoff
- Add retry logic with circuit breaker

---

## Deployment Procedures

### Standard Deployment

**Prerequisites**:
- [ ] Code changes merged to main branch
- [ ] All tests passing
- [ ] Database migrations prepared (if needed)
- [ ] Environment variables updated

**Steps**:
```bash
# 1. Pull latest code
git pull origin main

# 2. Install dependencies
uv sync

# 3. Run database migrations
uv run alembic upgrade head

# 4. Restart service
# (Method depends on deployment platform)
docker-compose restart app

# 5. Verify health
curl http://localhost:8000/health/ready

# 6. Monitor for 5 minutes
# Watch logs for errors
```

**Rollback Procedure**:
```bash
# 1. Revert code
git revert <commit-hash>

# 2. Rollback migrations (if needed)
uv run alembic downgrade -1

# 3. Restart service
docker-compose restart app

# 4. Verify health
curl http://localhost:8000/health/ready
```

---

### Database Migration

**Before Migration**:
1. Backup database:
   ```bash
   pg_dump -U postgres project_orchestrator > backup.sql
   ```

2. Test migration on staging first

3. Plan maintenance window (if downtime needed)

**Execute Migration**:
```bash
# 1. Stop application (if downtime needed)
docker-compose stop app

# 2. Run migration
uv run alembic upgrade head

# 3. Verify migration
uv run alembic current

# 4. Start application
docker-compose start app

# 5. Verify health
curl http://localhost:8000/health/ready
```

**Rollback Migration**:
```bash
# 1. Stop application
docker-compose stop app

# 2. Rollback migration
uv run alembic downgrade -1

# 3. Start application
docker-compose start app
```

---

## Security Incidents

### Rate Limit Abuse Detected

**Response**:
1. Identify attacker IP from audit logs:
   ```bash
   cat logs/audit.log | grep "Rate limit exceeded"
   ```

2. Add IP to blocklist (if IP filtering enabled):
   ```bash
   # Update GITHUB_WEBHOOK_IPS to exclude attacker
   ```

3. Temporarily lower rate limits:
   ```bash
   export DEFAULT_RATE_LIMIT="50/minute"
   ```

4. Restart service

5. Monitor for continued attacks

### Unauthorized Access Attempt

**Response**:
1. Review audit logs:
   ```bash
   cat logs/audit.log | grep "failed"
   ```

2. Identify compromised credentials

3. Rotate affected tokens:
   ```bash
   # Generate new token
   # Update environment variable
   # Restart service
   ```

4. Review recent actions from compromised account

5. Notify affected users if needed

---

## Maintenance Tasks

### Daily
- [ ] Check health endpoints
- [ ] Review error logs
- [ ] Monitor disk space
- [ ] Check audit logs for anomalies

### Weekly
- [ ] Review metrics trends
- [ ] Check for deprecation warnings
- [ ] Update dependencies (security patches)
- [ ] Backup database

### Monthly
- [ ] Rotate API tokens
- [ ] Review and archive old logs
- [ ] Performance optimization review
- [ ] Capacity planning review

---

## Contact Information

**On-Call Engineer**: [Configure]
**Escalation Path**: [Configure]
**Monitoring Alerts**: [Configure]

---

## Quick Reference

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db

# AI Services
ANTHROPIC_API_KEY=sk-ant-...

# Platforms
TELEGRAM_BOT_TOKEN=...
GITHUB_ACCESS_TOKEN=...
GITHUB_WEBHOOK_SECRET=...

# Security
WEBHOOK_IP_FILTERING_ENABLED=true
DEFAULT_RATE_LIMIT=100/minute

# Application
APP_ENV=production
LOG_LEVEL=INFO
```

### Common Commands
```bash
# Check application status
docker-compose ps

# View logs
docker-compose logs -f app

# Restart service
docker-compose restart app

# Run migrations
uv run alembic upgrade head

# Check database
PGPASSWORD=postgres psql -h localhost -U postgres -d project_orchestrator
```

---

**Last Updated**: January 2, 2026
**Version**: 1.0.0
