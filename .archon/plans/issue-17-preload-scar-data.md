# Implementation Plan: Pre-load SCAR Projects and Issues into WebUI

**Issue**: #17
**Goal**: Automatically load existing SCAR projects, repositories, and issues into the WebUI when the container starts

## Problem Analysis

Currently:
- The WebUI starts with an empty database
- Projects must be manually created via API or seed scripts
- No automatic connection to existing SCAR projects/repos/issues
- Users must run `import_github_projects.py` manually after container start

Desired behavior:
- When container starts, SCAR project data should be pre-loaded
- This includes projects, their GitHub repos, and associated issues
- Data should persist in PostgreSQL across container restarts
- First startup should import, subsequent startups should use existing data

## Current Architecture

### Data Models
- `Project`: Stores project metadata including `github_repo_url` and `telegram_chat_id`
- Projects are linked to GitHub repos and Telegram chats
- Issue data is fetched dynamically via GitHub API (not stored in DB)

### Existing Import Mechanism
- Script: `src/scripts/import_github_projects.py`
- Supports importing from:
  - Specific repo list: `--repos "owner/repo1,owner/repo2"`
  - User repos: `--user gpt153`
  - Org repos: `--org gpt153`
- Creates `Project` records with status `IN_PROGRESS`

### Application Startup
- File: `src/main.py`
- `lifespan` function handles startup/shutdown
- In development mode: runs `init_db()` to create tables
- Dockerfile CMD: `alembic upgrade head && python -m src.main`

## Solution Design

### Approach: Startup Import Script

**Strategy**: Extend the application lifespan to run import logic on startup

### Configuration Requirements

Create a configuration file that specifies which projects to pre-load:

**Location**: `.scar/projects.json` (in repo root)

**Format**:
```json
{
  "projects": [
    {
      "name": "Project Orchestrator",
      "github_repo": "gpt153/project-orchestrator",
      "description": "AI agent for non-technical project management",
      "telegram_chat_id": null
    },
    {
      "name": "SCAR WebUI",
      "github_repo": "gpt153/scar-webui",
      "description": "Web interface for SCAR",
      "telegram_chat_id": -1001234567890
    }
  ]
}
```

Alternatively, support environment variable for dynamic import:

```env
SCAR_IMPORT_REPOS="gpt153/project-orchestrator,gpt153/scar-webui"
SCAR_IMPORT_USER="gpt153"
SCAR_IMPORT_ORG=""
```

### Implementation Steps

## Phase 1: Configuration System

### 1.1 Add Configuration to Settings
**File**: `src/config.py`

Add new settings fields:
```python
# SCAR Project Import Settings
scar_import_repos: Optional[str] = None  # Comma-separated list
scar_import_user: Optional[str] = None   # GitHub username
scar_import_org: Optional[str] = None    # GitHub org name
scar_projects_config: str = ".scar/projects.json"  # Config file path
scar_auto_import: bool = True  # Enable/disable auto-import
```

### 1.2 Create Projects Config File
**File**: `.scar/projects.json`

Create default configuration with known SCAR projects:
```json
{
  "version": "1.0",
  "projects": []
}
```

Add to `.gitignore`: `.scar/projects.json` (optional - may want to commit default)

## Phase 2: Import Service

### 2.1 Create Import Service Module
**File**: `src/services/project_import_service.py`

Functions to implement:
- `async def load_projects_config(config_path: str) -> dict`
  - Load and parse `.scar/projects.json`
  - Handle file not found gracefully

- `async def import_from_config(session: AsyncSession, config: dict) -> int`
  - Import projects from config file
  - Skip duplicates (check by `github_repo_url`)
  - Return count of imported projects

- `async def import_from_env(session: AsyncSession) -> int`
  - Import projects from environment variables
  - Use existing `import_github_projects.py` logic
  - Return count of imported projects

- `async def auto_import_projects(session: AsyncSession) -> dict`
  - Main orchestrator function
  - Try config file first, then env vars
  - Return summary: `{source: str, count: int, errors: list}`

### 2.2 Refactor Existing Import Script
**File**: `src/scripts/import_github_projects.py`

Extract core logic into reusable functions:
- Move `import_repos_from_list` logic to service
- Make script call service functions
- Keep CLI interface intact for manual usage

## Phase 3: Application Startup Integration

### 3.1 Add Startup Hook
**File**: `src/main.py`

Modify `lifespan` function:
```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    # Startup
    logger.info(f"Starting {settings.app_name} in {settings.app_env} mode")

    if settings.app_env == "development":
        logger.info("Initializing database tables (development mode)")
        await init_db()

    # NEW: Auto-import SCAR projects
    if settings.scar_auto_import:
        logger.info("Auto-importing SCAR projects...")
        async with async_session_maker() as session:
            from src.services.project_import_service import auto_import_projects
            result = await auto_import_projects(session)
            logger.info(f"Auto-import complete: {result['count']} projects from {result['source']}")
            if result['errors']:
                logger.warning(f"Import errors: {result['errors']}")

    logger.info("Application startup complete")
    yield
    # ... shutdown logic
```

### 3.2 Update Dockerfile
**File**: `Dockerfile`

Ensure `.scar/` directory is copied to container:
```dockerfile
# Copy configuration files
COPY .scar/ ./.scar/
```

Or mount as volume in `docker-compose.yml`:
```yaml
volumes:
  - ./.scar:/app/.scar:ro
```

### 3.3 Update docker-compose.yml
**File**: `docker-compose.yml`

Add environment variables:
```yaml
app:
  environment:
    - SCAR_AUTO_IMPORT=${SCAR_AUTO_IMPORT:-true}
    - SCAR_IMPORT_USER=${SCAR_IMPORT_USER:-}
    - SCAR_IMPORT_ORG=${SCAR_IMPORT_ORG:-}
    - SCAR_IMPORT_REPOS=${SCAR_IMPORT_REPOS:-}
```

## Phase 4: Issue Loading

### 4.1 Current Implementation Review
Issues are currently fetched dynamically via:
- API endpoint: `GET /api/projects/{id}/issues`
- Service: Uses GitHub API client in real-time
- No database storage

**Decision**: Keep current dynamic approach
- Issues change frequently on GitHub
- Real-time fetch ensures accuracy
- No need to pre-load issues (they're loaded on-demand by WebUI)

### 4.2 Enhance Issue Caching (Optional Future Enhancement)
If performance becomes an issue:
- Add Redis caching layer
- Cache issue lists with TTL (e.g., 5 minutes)
- Out of scope for this issue

## Phase 5: Testing & Validation

### 5.1 Unit Tests
**File**: `tests/services/test_project_import_service.py`

Test cases:
- `test_load_projects_config_success`
- `test_load_projects_config_file_not_found`
- `test_import_from_config_new_projects`
- `test_import_from_config_skip_duplicates`
- `test_import_from_env_repos_list`
- `test_import_from_env_user`
- `test_auto_import_config_takes_precedence`

### 5.2 Integration Tests
**File**: `tests/test_startup_import.py`

Test cases:
- `test_startup_imports_projects_in_development`
- `test_startup_skips_import_when_disabled`
- `test_startup_handles_import_errors_gracefully`

### 5.3 Manual Testing
1. Start fresh container: `docker-compose down -v && docker-compose up`
2. Verify projects appear in WebUI at http://localhost:3002
3. Check logs for import messages
4. Verify issues load when clicking on a project
5. Restart container, verify projects persist (no re-import)

## Phase 6: Documentation

### 6.1 Update README.md
Add section: "Pre-loading SCAR Projects"

Document:
- How to configure projects via `.scar/projects.json`
- How to use environment variables
- How to disable auto-import

### 6.2 Update .env.example
Add new environment variables:
```env
# SCAR Project Import
SCAR_AUTO_IMPORT=true
SCAR_IMPORT_USER=
SCAR_IMPORT_ORG=
SCAR_IMPORT_REPOS=
```

### 6.3 Create .scar/projects.json.example
Provide example configuration file

## Implementation Order

1. ✅ **Phase 1**: Configuration System (~30 min)
   - Update `config.py`
   - Create `.scar/projects.json`
   - Update `.env.example`

2. ✅ **Phase 2**: Import Service (~60 min)
   - Create `project_import_service.py`
   - Implement config loading
   - Implement import logic
   - Refactor existing script

3. ✅ **Phase 3**: Startup Integration (~30 min)
   - Modify `lifespan` in `main.py`
   - Update `Dockerfile` and `docker-compose.yml`

4. ✅ **Phase 4**: Issue Loading Review (~15 min)
   - Verify current implementation is sufficient
   - Document dynamic loading approach

5. ✅ **Phase 5**: Testing (~45 min)
   - Write unit tests
   - Write integration tests
   - Manual testing

6. ✅ **Phase 6**: Documentation (~30 min)
   - Update README
   - Update env files
   - Create example config

**Total Estimated Time**: ~3.5 hours

## Rollout Strategy

### Development
1. Implement and test locally
2. Verify with `docker-compose up`
3. Test with empty database
4. Test with existing database

### Production Considerations
- Set `SCAR_AUTO_IMPORT=false` if manual control desired
- Use `.scar/projects.json` for stable project list
- Use env vars for dynamic/CI environments
- Monitor startup time (imports may slow first boot)

## Success Criteria

✅ Container starts with SCAR projects pre-loaded
✅ WebUI displays projects immediately after startup
✅ Issues load dynamically when projects are selected
✅ Duplicate projects are not created on restart
✅ Configuration is flexible (file or env vars)
✅ Import can be disabled via env var
✅ All tests pass
✅ Documentation is updated

## Open Questions

1. **Should `.scar/projects.json` be committed to git?**
   - Recommendation: Yes, with default/example projects
   - Users can customize locally or via env vars

2. **Should we fetch and cache issue counts on import?**
   - Recommendation: No, keep dynamic
   - Current `/projects` endpoint already fetches counts

3. **Should we support importing from multiple sources simultaneously?**
   - Recommendation: Yes, merge all sources
   - Priority: config file → env repos → env user → env org

4. **How to handle GitHub API rate limits?**
   - Recommendation: Add error handling with exponential backoff
   - Log warnings, continue with partial import

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| GitHub API rate limit | Import fails | Graceful error handling, continue with partial data |
| Slow startup on first boot | Poor UX | Log progress, async import in background (future) |
| Config file syntax errors | Import fails | JSON validation, clear error messages |
| Duplicate repos across sources | Data inconsistency | Normalize URLs, check for duplicates |

## Future Enhancements

- **Background import**: Use Celery/RQ for async import
- **Import status API**: Expose import progress via WebSocket
- **Auto-sync**: Periodically refresh projects from GitHub
- **Project templates**: Pre-configured project types
- **Import history**: Track import runs and results

---

**Status**: Ready for Implementation
**Estimated Completion**: 1 day
**Complexity**: Medium
**Dependencies**: None
