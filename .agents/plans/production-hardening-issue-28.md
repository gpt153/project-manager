# Production Hardening Plan - Issue #28

**Issue**: https://github.com/gpt153/project-manager/issues/28
**Goal**: Fix all production readiness gaps from system review
**Effort**: 17 hours estimated
**Success**: 100% test pass rate + security baseline + operational readiness

---

## Phase 1: Test Infrastructure & Fixes (4 hours)

### 1.1 Create Async Test Database Fixtures (1 hour)

**File**: `tests/conftest.py`

**Add**:
```python
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from src.database.models import Base
import os

# Test database URL
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/project_orchestrator_test"
)

@pytest_asyncio.fixture
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

@pytest_asyncio.fixture
async def test_session(test_engine):
    """Create test database session"""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()
```

### 1.2 Create PydanticAI Mocking Utilities (1 hour)

**File**: `tests/mocks/pydantic_ai_mocks.py`

**Create**:
```python
from unittest.mock import AsyncMock, MagicMock
from typing import Any, Dict
from pydantic import BaseModel

class MockAgentResult:
    """Mock PydanticAI agent result"""
    def __init__(self, data: Any):
        self.data = data

class MockAgent:
    """Mock PydanticAI agent for testing"""
    def __init__(self, response_data: Any = None):
        self.response_data = response_data or {"message": "Mock response"}

    async def run(self, prompt: str, deps: Any = None, result_type: type = None) -> MockAgentResult:
        """Mock agent run method"""
        if result_type and issubclass(result_type, BaseModel):
            # Return instance of result_type with mock data
            if hasattr(result_type, 'model_validate'):
                data = result_type.model_validate(self.response_data)
            else:
                data = result_type(**self.response_data)
            return MockAgentResult(data)
        return MockAgentResult(self.response_data)

def create_mock_agent(response: Dict[str, Any] = None) -> MockAgent:
    """Create a mock PydanticAI agent"""
    return MockAgent(response)
```

### 1.3 Fix Failing Tests (2 hours)

**Strategy**: Go through each failing test, determine root cause, fix or remove

**File**: Run test suite and fix systematically:

```bash
# 1. Run tests to identify failures
pytest -v tests/ --tb=short

# 2. For each failing test:
#    - If missing fixtures: Add proper fixtures
#    - If mocking issue: Use new mocking utilities
#    - If invalid test: Remove or rewrite
#    - If actual bug: Fix the code

# 3. Specific fixes needed:

# Vision generator tests - add AI mocking
# tests/services/test_vision_generator.py
# - Mock PydanticAI agent calls
# - Use MockAgent from mocking utilities

# Telegram bot tests - add proper session mocking
# tests/integrations/test_telegram_bot.py
# - Mock telegram library
# - Use test_session fixture

# GitHub webhook tests - add signature mocking
# tests/integrations/test_github_webhook.py
# - Mock request signatures
# - Use test_session for database
```

**Validation**:
```bash
pytest tests/ -v
# Target: 98/98 passing (100%)
```

---

## Phase 2: Security Hardening (4 hours)

### 2.1 Add Rate Limiting (1.5 hours)

**Install dependency**:
```bash
cd /home/samuel/.archon/workspaces/project-manager
pip install slowapi
# Add to pyproject.toml dependencies
```

**File**: `src/middleware/rate_limit.py`

**Create**:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request

# Create limiter instance
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

# Custom rate limit error handler
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return {
        "error": "Rate limit exceeded",
        "detail": "Too many requests. Please try again later.",
        "retry_after": exc.detail
    }
```

**File**: `src/main.py`

**Update**:
```python
from src.middleware.rate_limit import limiter, rate_limit_handler
from slowapi.errors import RateLimitExceeded

# Add to app initialization
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# Add to webhook endpoint
from slowapi import Limiter

@app.post("/webhooks/github/")
@limiter.limit("10/minute")  # Restrict webhook calls
async def github_webhook(request: Request):
    # ... existing code
```

### 2.2 Implement Audit Logging (1.5 hours)

**File**: `src/services/audit_logger.py`

**Create**:
```python
import logging
import json
from datetime import datetime, UTC
from typing import Dict, Any, Optional
from uuid import UUID

class AuditLogger:
    """Audit logger for tracking state-changing operations"""

    def __init__(self):
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)

        # Add file handler for audit logs
        handler = logging.FileHandler("logs/audit.log")
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)

    def log(
        self,
        action: str,
        user_id: Optional[str] = None,
        project_id: Optional[UUID] = None,
        details: Optional[Dict[str, Any]] = None,
        result: str = "success"
    ):
        """Log an audit event"""
        event = {
            "timestamp": datetime.now(UTC).isoformat(),
            "action": action,
            "user_id": user_id,
            "project_id": str(project_id) if project_id else None,
            "details": details or {},
            "result": result
        }
        self.logger.info(json.dumps(event))

# Global instance
audit_logger = AuditLogger()
```

**File**: Update services to use audit logging

```python
# Example in src/services/workflow_orchestrator.py
from src.services.audit_logger import audit_logger

async def create_project(name: str, user_id: str):
    # ... create project
    audit_logger.log(
        action="project_created",
        user_id=user_id,
        project_id=project.id,
        details={"name": name}
    )
```

### 2.3 Add IP Allowlisting for Webhooks (30 min)

**File**: `src/config/settings.py`

**Add**:
```python
import os

# GitHub webhook IP ranges (official GitHub IPs)
GITHUB_WEBHOOK_IPS = os.getenv(
    "GITHUB_WEBHOOK_IPS",
    "140.82.112.0/20,143.55.64.0/20,192.30.252.0/22,185.199.108.0/22"
).split(",")

WEBHOOK_IP_FILTERING_ENABLED = os.getenv("WEBHOOK_IP_FILTERING_ENABLED", "true").lower() == "true"
```

**File**: `src/middleware/ip_filter.py`

**Create**:
```python
from fastapi import Request, HTTPException
from ipaddress import ip_address, ip_network
from src.config.settings import GITHUB_WEBHOOK_IPS, WEBHOOK_IP_FILTERING_ENABLED

async def verify_webhook_ip(request: Request):
    """Verify webhook request comes from allowed IP"""
    if not WEBHOOK_IP_FILTERING_ENABLED:
        return True

    client_ip = request.client.host

    # Check if IP is in allowed ranges
    for ip_range in GITHUB_WEBHOOK_IPS:
        if ip_address(client_ip) in ip_network(ip_range):
            return True

    raise HTTPException(
        status_code=403,
        detail="Webhook source IP not allowed"
    )
```

### 2.4 Token Rotation Support (30 min)

**File**: `src/config/settings.py`

**Add**:
```python
# Token rotation configuration
TOKEN_ROTATION_ENABLED = os.getenv("TOKEN_ROTATION_ENABLED", "false").lower() == "true"
TOKEN_MAX_AGE_DAYS = int(os.getenv("TOKEN_MAX_AGE_DAYS", "90"))

# Support multiple active tokens during rotation
ANTHROPIC_API_KEYS = os.getenv("ANTHROPIC_API_KEY", "").split(",")
GITHUB_ACCESS_TOKENS = os.getenv("GITHUB_ACCESS_TOKEN", "").split(",")
```

**File**: `src/services/token_manager.py`

**Create**:
```python
from typing import List
import os

class TokenManager:
    """Manage API token rotation"""

    def __init__(self):
        self.anthropic_tokens = self._load_tokens("ANTHROPIC_API_KEY")
        self.github_tokens = self._load_tokens("GITHUB_ACCESS_TOKEN")
        self.current_index = 0

    def _load_tokens(self, env_var: str) -> List[str]:
        """Load tokens from environment variable"""
        tokens = os.getenv(env_var, "").split(",")
        return [t.strip() for t in tokens if t.strip()]

    def get_token(self, service: str) -> str:
        """Get current active token"""
        if service == "anthropic":
            return self.anthropic_tokens[0] if self.anthropic_tokens else ""
        elif service == "github":
            return self.github_tokens[0] if self.github_tokens else ""
        return ""

    def rotate_token(self, service: str):
        """Rotate to next token in list"""
        # Implementation for automatic rotation
        pass
```

---

## Phase 3: Complete GitHub Integration (2 hours)

### 3.1 Enable Auto-Comments (1.5 hours)

**File**: `src/integrations/github_client.py`

**Add method**:
```python
async def post_issue_comment(
    self,
    repo_owner: str,
    repo_name: str,
    issue_number: int,
    comment_body: str
) -> Dict[str, Any]:
    """Post a comment on a GitHub issue or PR"""
    url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/issues/{issue_number}/comments"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            headers=self._get_headers(),
            json={"body": comment_body},
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()
```

**File**: `src/services/workflow_orchestrator.py`

**Update to post responses**:
```python
async def handle_phase_completion(
    self,
    project_id: UUID,
    phase_number: int,
    result: str
):
    """Handle phase completion and notify via GitHub"""
    async with self.db_session_maker() as session:
        project = await session.get(Project, project_id)

        if project.github_issue_number and project.github_repo_url:
            # Extract repo owner and name from URL
            parts = project.github_repo_url.split("/")
            repo_owner = parts[-2]
            repo_name = parts[-1].replace(".git", "")

            # Post comment
            comment = f"✅ Phase {phase_number} Complete\\n\\n{result}"
            await self.github_client.post_issue_comment(
                repo_owner,
                repo_name,
                project.github_issue_number,
                comment
            )
```

### 3.2 Test Bidirectional Flow (30 min)

**File**: `tests/integrations/test_github_bidirectional.py`

**Create**:
```python
import pytest
from unittest.mock import AsyncMock, patch
from src.integrations.github_client import GitHubClient

@pytest.mark.asyncio
async def test_post_issue_comment():
    """Test posting comment to GitHub issue"""
    client = GitHubClient("fake_token")

    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value.json.return_value = {"id": 123}

        result = await client.post_issue_comment(
            "owner",
            "repo",
            42,
            "Test comment"
        )

        assert result["id"] == 123
        mock_post.assert_called_once()

@pytest.mark.asyncio
async def test_webhook_triggers_response():
    """Test that webhook mention triggers auto-response"""
    # Test complete bidirectional flow
    # 1. Webhook received
    # 2. Agent processes
    # 3. Response posted back to issue
    pass
```

---

## Phase 4: Observability (3 hours)

### 4.1 Add Prometheus Metrics (1.5 hours)

**Install dependency**:
```bash
pip install prometheus-client prometheus-fastapi-instrumentator
```

**File**: `src/middleware/metrics.py`

**Create**:
```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_fastapi_instrumentator import Instrumentator

# Define custom metrics
conversation_counter = Counter(
    'orchestrator_conversations_total',
    'Total number of conversations started'
)

command_duration = Histogram(
    'scar_command_duration_seconds',
    'SCAR command execution time',
    buckets=[1, 5, 10, 30, 60, 120, 300]
)

active_projects = Gauge(
    'orchestrator_active_projects',
    'Number of projects in active workflow'
)

vision_generation_counter = Counter(
    'vision_documents_generated_total',
    'Total vision documents generated'
)

approval_pending = Gauge(
    'approval_gates_pending',
    'Number of pending approval gates'
)

def setup_metrics(app):
    """Setup Prometheus metrics for FastAPI app"""
    instrumentator = Instrumentator()
    instrumentator.instrument(app).expose(app, endpoint="/metrics")

    return instrumentator
```

**File**: `src/main.py`

**Add**:
```python
from src.middleware.metrics import setup_metrics

# Setup metrics
setup_metrics(app)
```

### 4.2 Enhanced Health Checks (30 min)

**File**: `src/api/health.py`

**Create**:
```python
from fastapi import APIRouter, Response
from src.database.connection import get_session
from src.services.audit_logger import audit_logger
import httpx

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/")
async def basic_health():
    """Basic health check"""
    return {"status": "healthy", "service": "project-manager"}

@router.get("/db")
async def database_health():
    """Database connectivity check"""
    try:
        async with get_session() as session:
            await session.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

@router.get("/ai")
async def ai_health():
    """AI service connectivity check"""
    try:
        # Simple ping to Anthropic API
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.anthropic.com",
                timeout=5.0
            )
        return {"status": "healthy", "ai_service": "reachable"}
    except Exception as e:
        return {"status": "degraded", "ai_service": "unreachable", "error": str(e)}

@router.get("/ready")
async def readiness():
    """Readiness probe for orchestrator systems"""
    db_ok = False
    ai_ok = False

    # Check database
    try:
        async with get_session() as session:
            await session.execute("SELECT 1")
        db_ok = True
    except:
        pass

    # Check AI service
    try:
        async with httpx.AsyncClient() as client:
            await client.get("https://api.anthropic.com", timeout=5.0)
        ai_ok = True
    except:
        pass

    if db_ok and ai_ok:
        return {"status": "ready"}
    else:
        return Response(
            content='{"status": "not ready"}',
            status_code=503,
            media_type="application/json"
        )
```

### 4.3 Structured Logging (1 hour)

**File**: `src/utils/logger.py`

**Create**:
```python
import logging
import json
from datetime import datetime, UTC
from typing import Any, Dict, Optional

class StructuredLogger:
    """Structured logger for machine-readable logs"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # JSON formatter
        handler = logging.StreamHandler()
        handler.setFormatter(self.JsonFormatter())
        self.logger.addHandler(handler)

    class JsonFormatter(logging.Formatter):
        """Format logs as JSON"""
        def format(self, record):
            log_data = {
                "timestamp": datetime.now(UTC).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }

            # Add extra fields if present
            if hasattr(record, 'extra'):
                log_data.update(record.extra)

            return json.dumps(log_data)

    def info(self, message: str, **kwargs):
        """Log info message with structured data"""
        self.logger.info(message, extra=kwargs)

    def error(self, message: str, **kwargs):
        """Log error message with structured data"""
        self.logger.error(message, extra=kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message with structured data"""
        self.logger.warning(message, extra=kwargs)

# Global instances
app_logger = StructuredLogger("app")
agent_logger = StructuredLogger("agent")
workflow_logger = StructuredLogger("workflow")
```

---

## Phase 5: Fix Deprecations (2 hours)

### 5.1 Replace datetime.utcnow() (1 hour)

**Find all occurrences**:
```bash
cd /home/samuel/.archon/workspaces/project-manager
grep -r "datetime.utcnow()" src/ --include="*.py"
```

**Replace pattern**:
```python
# OLD (deprecated)
from datetime import datetime
timestamp = datetime.utcnow()

# NEW (correct)
from datetime import datetime, UTC
timestamp = datetime.now(UTC)
```

**Files to update**:
- `src/database/models.py`
- `src/services/*.py`
- `src/agent/*.py`
- All other files with datetime.utcnow()

### 5.2 Update Pydantic Config (30 min)

**Find all occurrences**:
```bash
grep -r "class Config:" src/ --include="*.py" -A 2
```

**Replace pattern**:
```python
# OLD (deprecated)
class MyModel(BaseModel):
    field: str

    class Config:
        arbitrary_types_allowed = True

# NEW (correct)
from pydantic import ConfigDict

class MyModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    field: str
```

### 5.3 Verify Dependencies (30 min)

**File**: `pyproject.toml`

**Update to latest stable versions**:
```toml
[project]
dependencies = [
    "fastapi>=0.115.0",
    "pydantic>=2.10.0",
    "pydantic-ai>=0.0.14",
    "anthropic>=0.42.0",
    "sqlalchemy>=2.0.36",
    "asyncpg>=0.30.0",
    "alembic>=1.14.0",
    "python-telegram-bot>=22.5.0",
    "httpx>=0.28.0",
    "slowapi>=0.1.9",
    "prometheus-client>=0.21.0",
    "prometheus-fastapi-instrumentator>=7.0.0"
]
```

---

## Phase 6: Documentation Updates (2 hours)

### 6.1 Update CLAUDE.md (1 hour)

**File**: `/home/samuel/.archon/workspaces/project-manager/CLAUDE.md`

**Add sections** (from system review recommendations):

```markdown
## Production Readiness Criteria

A system is production-ready when ALL of the following are met:

✅ **Functionality**: All planned features implemented and tested
✅ **Testing**: 90%+ code coverage, all tests passing, e2e tests executed
✅ **Security**: Rate limiting, authentication, audit logging in place
✅ **Operations**: Monitoring, alerting, runbooks, deployment automation
✅ **Performance**: Load tested at 2x expected traffic
✅ **Documentation**: API docs, ops docs, user guides complete

**"Works on my machine" ≠ Production Ready**

## Test Quality Standards

- **All tests must pass** before declaring a phase complete
- **Test failures block PR merge** - no exceptions
- Failing tests indicate either:
  1. Broken code (fix the code)
  2. Bad test (fix or remove the test)
  3. Missing infrastructure (add test fixtures)

**Never ship with failing tests.**

## Security Baseline for Production

Every production deployment MUST have:

1. **Rate Limiting**: Protect against abuse
2. **Input Validation**: Validate all user inputs
3. **Audit Logging**: Log all state-changing operations
4. **Secret Management**: Never commit secrets
5. **HTTPS Only**: All external APIs over HTTPS
6. **Webhook Verification**: HMAC signatures

**These are not optional.**
```

### 6.2 Create Production Checklist Command (30 min)

**File**: `/home/samuel/.archon/workspaces/project-manager/.agents/commands/production-checklist.md`

**Create**: (Full checklist from system review)

### 6.3 Create Operations Runbook (30 min)

**File**: `/home/samuel/.archon/workspaces/project-manager/docs/OPERATIONS.md`

**Create**:
```markdown
# Operations Runbook

## Health Checks

- `/health` - Basic health
- `/health/db` - Database connectivity
- `/health/ai` - AI service connectivity
- `/health/ready` - Readiness probe

## Metrics

- `/metrics` - Prometheus metrics endpoint

Key metrics:
- `orchestrator_conversations_total` - Total conversations
- `scar_command_duration_seconds` - Command execution time
- `orchestrator_active_projects` - Active projects
- `approval_gates_pending` - Pending approvals

## Logs

### Application Logs
- Location: `stdout` (structured JSON)
- Format: `{"timestamp": "...", "level": "...", "message": "...", ...}`

### Audit Logs
- Location: `logs/audit.log`
- Format: JSON per line
- Contains: All state-changing operations

## Troubleshooting

### High Response Times
1. Check `/metrics` for bottlenecks
2. Review `scar_command_duration_seconds`
3. Check database connection pool

### Webhook Failures
1. Verify IP allowlist
2. Check signature verification
3. Review rate limiting

### Database Issues
1. Check `/health/db`
2. Review connection pool settings
3. Check disk space

## Deployment

### Prerequisites
- Database migrations applied
- Environment variables configured
- Secrets properly stored

### Steps
1. Pull latest code
2. Run migrations: `alembic upgrade head`
3. Restart service
4. Verify health: `curl /health/ready`
5. Monitor metrics for 5 minutes

### Rollback
1. Revert code to previous version
2. Rollback migrations: `alembic downgrade -1`
3. Restart service
4. Verify health
```

---

## Validation Checklist

After implementing all phases, verify:

### Tests
- [ ] `pytest tests/ -v` shows 98/98 passing (100%)
- [ ] No test failures
- [ ] Coverage ≥ 90%

### Security
- [ ] Rate limiting working (`curl` test with >100 requests/min fails)
- [ ] Audit logs being written to `logs/audit.log`
- [ ] IP filtering active for webhooks
- [ ] No secrets in code

### Integration
- [ ] GitHub auto-comments posting correctly
- [ ] Bidirectional webhook flow tested
- [ ] Issue mentions trigger responses

### Observability
- [ ] `/metrics` endpoint responding
- [ ] `/health/*` endpoints all healthy
- [ ] Structured logs in JSON format
- [ ] Custom metrics incrementing

### Documentation
- [ ] CLAUDE.md updated with standards
- [ ] Production checklist created
- [ ] Operations runbook complete
- [ ] All deprecation warnings fixed

### Final Check
- [ ] Run full test suite: `pytest tests/`
- [ ] Check for warnings: `pytest tests/ -W error`
- [ ] Verify imports: `python -c "import src.main"`
- [ ] Test health endpoint: `curl http://localhost:8000/health`

---

## Success Criteria

✅ All 98 tests passing (100%)
✅ Rate limiting operational
✅ Audit logging implemented
✅ GitHub bidirectional integration working
✅ Prometheus metrics exposed
✅ Health checks responding
✅ Zero deprecation warnings
✅ Documentation complete

**Only then can the system be declared production-ready.**

---

## Estimated Timeline

- Phase 1: Test Infrastructure - 4 hours
- Phase 2: Security Hardening - 4 hours
- Phase 3: GitHub Integration - 2 hours
- Phase 4: Observability - 3 hours
- Phase 5: Fix Deprecations - 2 hours
- Phase 6: Documentation - 2 hours

**Total: 17 hours**

---

## Implementation Order

1. **Start**: Test infrastructure (unblocks everything else)
2. **Then**: Fix deprecations (clean code)
3. **Then**: Security features (parallel to observability)
4. **Then**: Observability (parallel to security)
5. **Then**: GitHub integration (depends on clean codebase)
6. **Finally**: Documentation (summarizes all changes)
