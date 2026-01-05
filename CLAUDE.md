# Project Manager - AI Development Guidelines

## Overview

**Project Manager** is an AI-powered project management agent that helps non-technical users build software through natural language conversation, automated vision generation, and SCAR workflow automation.

**Tech Stack**: PydanticAI + FastAPI + PostgreSQL + Telegram + GitHub

---

## Production Readiness Criteria

A system is **production-ready** when ALL of the following are met:

✅ **Functionality**: All planned features implemented and tested
✅ **Testing**: 90%+ code coverage, all tests passing, e2e tests executed
✅ **Security**: Rate limiting, authentication, audit logging in place
✅ **Operations**: Monitoring, alerting, runbooks, deployment automation
✅ **Performance**: Load tested at 2x expected traffic
✅ **Documentation**: API docs, ops docs, user guides complete

**"Works on my machine" ≠ Production Ready**

---

## Test Quality Standards

- **All tests must pass** before declaring a phase complete
- **Test failures block PR merge** - no exceptions
- Failing tests indicate either:
  1. Broken code (fix the code)
  2. Bad test (fix or remove the test)
  3. Missing infrastructure (add test fixtures)

**Never ship with failing tests.**

**Test coverage requirements**:
- Unit tests: ≥ 90% coverage
- Integration tests: All major workflows covered
- E2E tests: Critical user paths validated

---

## Security Baseline for Production

Every production deployment MUST have:

1. **Rate Limiting**: Protect against abuse (implemented via slowapi)
2. **Input Validation**: Validate all user inputs (Pydantic models)
3. **Audit Logging**: Log all state-changing operations (audit_logger)
4. **Secret Management**: Never commit secrets, use env vars
5. **HTTPS Only**: All external APIs over HTTPS
6. **Webhook Verification**: HMAC signatures for all webhooks
7. **IP Filtering**: Allowlist webhook sources (optional but recommended)

**These are not optional. Ship without them = ship with vulnerabilities.**

---

## Development Guidelines

### Code Quality

**Type Safety** (CRITICAL):
- All functions must have return type annotations
- All parameters must have type annotations
- Use strict TypeScript/mypy settings
- Avoid `any` - use `unknown` and type guards

**Async Patterns**:
- Use async/await consistently
- Never block the event loop
- Use async context managers for resources

**Error Handling**:
- Catch specific exceptions, not bare `except:`
- Log errors with context
- Return user-friendly error messages
- Never expose internal errors to users

### Testing Approach

**Test-Driven Development**:
1. Write failing test first
2. Implement minimum code to pass
3. Refactor for quality
4. Verify all tests pass

**Test Organization**:
```
tests/
├── unit/          # Fast, isolated tests
├── integration/   # Database + external services
└── e2e/           # Full user workflows
```

**Mocking Strategy**:
- Use `tests/mocks/` for shared mocks
- Mock external services (AI, GitHub, Telegram)
- Use test database for integration tests
- Never mock what you don't own

### Database Patterns

**Async SQLAlchemy**:
- Always use async session managers
- Use context managers (`async with`)
- Commit transactions explicitly
- Handle connection errors gracefully

**Migrations**:
- Use Alembic for all schema changes
- Test migrations up AND down
- Never skip migration steps

---

## Architecture Patterns

### PydanticAI Agent

**Agent Structure**:
```python
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel, ConfigDict

class Dependencies(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    session: AsyncSession
    project_id: UUID

agent = Agent(
    model="claude-sonnet-4-5-20250929",
    deps_type=Dependencies,
    system_prompt=SYSTEM_PROMPT
)

@agent.tool
async def save_message(ctx: RunContext[Dependencies], content: str) -> str:
    # Tool implementation
    pass
```

**Best Practices**:
- Keep system prompts focused and concise
- Use tools for all database operations
- Validate tool inputs with Pydantic
- Log all agent interactions

### FastAPI Application

**Router Organization**:
- One router per domain (projects, github, health)
- Use dependency injection for sessions
- Apply rate limiting to sensitive endpoints
- Document all endpoints with OpenAPI

**Middleware Stack** (in order):
1. CORS (development permissive, production strict)
2. Rate limiting (slowapi)
3. Custom middleware (logging, etc.)

### Database Schema

**Core Tables**:
- `projects` - Project metadata and vision documents
- `conversation_messages` - Chat history
- `workflow_phases` - Phase tracking
- `approval_gates` - User decision points
- `scar_executions` - Command history

**Patterns**:
- Use UUIDs for all primary keys
- Store JSON as JSONB for queryability
- Use enums for finite states
- Index foreign keys and search fields

---

## Workflow Patterns

### SCAR Integration

**PIV Loop** (Prime-Implement-Validate):
1. **Prime**: Load codebase context
2. **Plan-Feature-GitHub**: Create implementation plan
3. **Execute-GitHub**: Implement and create PR
4. **Validate**: Run tests and verify

**Command Execution**:
- Track all commands in `scar_executions` table
- Log to audit log
- Handle timeouts and retries
- Parse output for status

### Approval Gates

**Pattern**:
1. Create gate with question and context
2. Pause workflow
3. Wait for user approval/rejection
4. Resume or abort workflow

**Types**:
- Vision document review
- Implementation plan approval
- Phase completion check
- Error resolution decision

---

## Operational Excellence

### Monitoring & Observability

**Health Checks** (implemented):
- `/health` - Basic liveness
- `/health/db` - Database connectivity
- `/health/ai` - AI service reachability
- `/health/ready` - Readiness probe

**Logging**:
- Structured JSON logs (production)
- Audit logs for state changes
- Request/response logging (debug)

**Metrics** (when Prometheus enabled):
- `orchestrator_conversations_total` - Total conversations
- `scar_command_duration_seconds` - Command execution time
- `orchestrator_active_projects` - Active projects
- `approval_gates_pending` - Pending approvals

### Security Practices

**Secrets Management**:
- Store in environment variables
- Never commit to git
- Rotate regularly (90 days)
- Use separate credentials per environment

**Audit Trail**:
- Log all state-changing operations
- Include user ID, timestamp, action
- Store in dedicated audit log file
- Retain for compliance period

**Rate Limiting**:
- API: 100 requests/minute (configurable)
- Webhooks: 10 requests/minute
- Stricter limits for sensitive endpoints

---

## Deployment

### Prerequisites
- PostgreSQL 18+ running
- Environment variables configured
- Database migrations applied
- Secrets properly stored

### Startup Sequence
1. Initialize database connection
2. Auto-import SCAR projects (if enabled)
3. Start FastAPI application
4. Register routes and middleware
5. Begin polling/listening

### Health Verification
```bash
curl http://localhost:8000/health        # Basic health
curl http://localhost:8000/health/db     # Database
curl http://localhost:8000/health/ready  # Full readiness
```

---

## Common Tasks

### Adding a New Feature

1. **Plan**:
   - Write PRD or vision document
   - Design database schema changes
   - Identify integration points

2. **Implement**:
   - Write failing tests first (TDD)
   - Implement minimum viable code
   - Add audit logging for state changes
   - Update API documentation

3. **Validate**:
   - All tests passing (100%)
   - No deprecation warnings
   - Security review passed
   - Documentation updated

4. **Deploy**:
   - Create migration (if DB changes)
   - Update environment variables
   - Deploy to staging first
   - Monitor for 24 hours
   - Promote to production

### Debugging Issues

1. **Check logs**:
   - Application logs (stdout)
   - Audit logs (logs/audit.log)
   - Database logs

2. **Verify health**:
   - All health endpoints green
   - Database connectivity OK
   - External services reachable

3. **Reproduce**:
   - Use test adapter for isolation
   - Check conversation history
   - Review SCAR command output

---

## Emergency Procedures

### Database Connection Lost
1. Check PostgreSQL status
2. Verify credentials in env vars
3. Check connection pool settings
4. Restart application if needed

### High Error Rate
1. Check `/health` endpoints
2. Review recent code changes
3. Check external service status (Anthropic, GitHub)
4. Enable debug logging
5. Rollback if needed

### Rate Limit Abuse
1. Check audit logs for attacker IP
2. Add IP to blocklist (if IP filtering enabled)
3. Temporarily lower rate limits
4. Investigate attack vector

---

## References

- **System Review**: `.agents/system-reviews/project-manager-review.md`
- **Operations Runbook**: `docs/OPERATIONS.md`
- **Production Checklist**: `.agents/commands/production-checklist.md`
- **Implementation Plans**: `.agents/plans/`

---

## Version History

- **v0.1.0** (Jan 2026): Production hardening complete
  - Security baseline implemented
  - Health checks added
  - Documentation updated
  - Test infrastructure improved
