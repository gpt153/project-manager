# Rename PM to PM Throughout Project

## Overview

This plan systematically renames the project from "Project Manager" (PM) to "Project Manager" (PM) throughout the entire codebase, documentation, and deployment configuration.

## Renaming Rules

### What to Change

1. **Project Manager** → **Project Manager**
2. **@po** → **@pm** (bot mentions)
3. **po.153.se** → **pm.153.se** (domain - if applicable)
4. **project-manager** → **project-manager** (repository name, already done)
5. **/home/samuel/po** → **/home/samuel/pm** (deployment directory)
6. **'po'** (as source identifier in code) → **'pm'**

### What NOT to Change

- **po** in URLs like `po.153.se` (domain already purchased/configured - DNS change required separately)
- **po** in historical commit messages or changelogs
- **po** as part of variable names that make sense (like `repo`, `response`, etc.)
- Comments referencing old system IF they provide historical context

## Implementation Strategy

### Phase 1: Configuration & Environment Files
Low risk, high impact files that define the project identity.

#### 1.1 Python Configuration
**File:** `src/config.py`
```python
# CHANGE:
app_name: str = "Project Manager"
# TO:
app_name: str = "Project Manager"
```

#### 1.2 Environment Examples
**File:** `.env.example`
```bash
# CHANGE:
APP_NAME="Project Manager"
# TO:
APP_NAME="Project Manager"
```

#### 1.3 Package Metadata
**File:** `frontend/package.json`
```json
// CHANGE:
"name": "project-manager-frontend"
// TO:
"name": "project-manager-frontend"
```

**File:** `frontend/index.html`
```html
<!-- CHANGE: -->
<title>Project Manager</title>
<!-- TO: -->
<title>Project Manager</title>
```

### Phase 2: Source Code (Runtime Strings)
User-facing strings in the application.

#### 2.1 Bot Welcome Messages
**File:** `src/integrations/telegram_bot.py`
- Line 99: "Welcome to the Project Manager!" → "Welcome to the Project Manager!"
- Line 118: "**Project Manager Help**" → "**Project Manager Help**"
- Bot description field (if present)

#### 2.2 Main Application
**File:** `src/main.py`
```python
# CHANGE docstring:
"""Main FastAPI application for the Project Manager."""
# TO:
"""Main FastAPI application for the Project Manager."""
```

**File:** `src/bot_main.py`
- Line 21: "Starting Project Manager Telegram Bot..." → "Starting Project Manager Telegram Bot..."

#### 2.3 Database Models
**File:** `src/database/models.py`
```python
# CHANGE docstring:
"""Database models for the Project Manager."""
# TO:
"""Database models for the Project Manager."""
```

#### 2.4 Agent System
**File:** `src/agent/orchestrator_agent.py`
```python
# CHANGE docstring:
"""Project Manager PydanticAI Agent."""
# TO:
```"""Project Manager PydanticAI Agent."""
```

**File:** `src/agent/prompts.py`
```python
# CHANGE docstring:
"""System prompts and templates for the Project Manager agent."""
# TO:
"""System prompts and templates for the Project Manager agent."""
```

#### 2.5 API Endpoints
**File:** `src/api/websocket.py`
- Line 27: "the Project Manager agent." → "the Project Manager agent."
- Line 47: "Connected to Project Manager" → "Connected to Project Manager"

**File:** `src/api/sse.py`
- Line 32: "Project Manager → SCAR → Claude" → "Project Manager → SCAR → Claude"
- Line 45: `source: "po|scar|claude"` → `source: "pm|scar|claude"`

#### 2.6 GitHub Webhook Handler
**File:** `src/integrations/github_webhook.py`
```python
# CHANGE line 108:
bot_mention = "@po"
# TO:
bot_mention = "@pm"
```

#### 2.7 Tests
**File:** `tests/test_main.py`
```python
# CHANGE line 16:
assert data["app_name"] == "Project Manager"
# TO:
assert data["app_name"] == "Project Manager"
```

**File:** `tests/integrations/test_github_webhook.py`
```python
# CHANGE line 47:
"body": "@po please help me with authentication",
# TO:
"body": "@pm please help me with authentication",
```

#### 2.8 Frontend TypeScript
**File:** `frontend/src/hooks/useScarFeed.ts`
```typescript
// CHANGE:
source: 'po' | 'scar' | 'claude';
// TO:
source: 'pm' | 'scar' | 'claude';
```

### Phase 3: Documentation Files
Update all markdown documentation.

#### 3.1 Primary Documentation
- `README.md`: Multiple occurrences
  - Title: "# Project Manager" → "# Project Manager"
  - Deployment references: "po.153.se" → "pm.153.se" (or keep if domain doesn't change)
  - Chat references: "@po" → "@pm"

- `CLAUDE.md`:
  - Title and intro: "Project Manager" → "Project Manager"
  - Description text updates

- `DEPLOYMENT.md`:
  - Title: "Deployment Guide: Project Manager WebUI" → "Deployment Guide: Project Manager WebUI"
  - References to "@po" → "@pm"
  - **Domain references**: KEEP "po.153.se" unless domain is changing

- `PRODUCTION_SETUP.md`:
  - Title updates
  - Path references: `/home/samuel/po` → `/home/samuel/pm`
  - Bot mention: "@po" → "@pm"

#### 3.2 Agent Guide Documentation
**Directory:** `docs/orchestrator-agent-guide/`
- `README.md`: "Project Manager Agent" → "Project Manager Agent"
- `00-overview.md`: Update "Project Manager Agent" references
- `05-advanced-techniques.md`: Update references
- `DOCUMENTATION_COMPLETE.md`: Update throughout

**Note**: Consider renaming directory `orchestrator-agent-guide` → `manager-agent-guide` OR keep for historical continuity.

#### 3.3 Plans & Visions
**Directory:** `.agents/plans/`
- `project-manager-plan.md` → Consider renaming file to `project-manager-plan.md`
  - Update all internal references

**Directory:** `.agents/visions/`
- `project-manager.md` → Consider renaming to `project-manager.md`
  - Update all content references

**Directory:** `.agents/plans/`
- `webui-project-organizer.md` & `.plan.md`:
  - Update "@po" references to "@pm"
  - Update "Project Manager" to "Project Manager"

#### 3.4 Deployment & Status Documentation
- `DEPLOYMENT_STATUS.md`: Update references, keep domain as-is if not changing
- `DEPLOYMENT-STATUS.md`: Same as above
- `WEBUI_DEPLOYMENT.md`: Update references
- `DEPLOY_README.md`: Update title and references, **deployment path** change
- `CICD_IMPLEMENTATION_SUMMARY.md`: Update path references `/home/samuel/po` → `/home/samuel/pm`

#### 3.5 RCA & Implementation Documents
- `RCA-*.md` files: Update "Project Manager" → "Project Manager", "@po" → "@pm"
- `IMPLEMENTATION_*.md` files: Same updates
- `VALIDATION_REPORT.md`: Update throughout

#### 3.6 Production Checklist
**File:** `.agents/commands/production-checklist.md`
```markdown
# CHANGE:
**Project**: Project Manager
# TO:
**Project**: Project Manager
```

### Phase 4: Deployment Scripts & Configuration

#### 4.1 Deployment Scripts
**File:** `scripts/deploy.sh`
- Line 4: Comment "Project Manager - Production Deployment Script" → "Project Manager..."
- Line 18: `DEPLOY_DIR="/home/samuel/po"` → `DEPLOY_DIR="/home/samuel/pm"`
- Line 20: Echo message update

**File:** `deploy.sh`
- Similar changes to `scripts/deploy.sh`
- Update all path references

**File:** `deploy-manual.sh`
- Line 8: `DEPLOY_DIR="/home/samuel/po"` → `DEPLOY_DIR="/home/samuel/pm"`
- Line 98: Update production URL if domain changes

**File:** `test_deployment.sh`
- Line 2: Comment update
- Line 15: `DEPLOY_DIR="${DEPLOY_DIR:-/home/samuel/po}"` → `DEPLOY_DIR="${DEPLOY_DIR:-/home/samuel/pm}"`
- Line 25: Echo message update

#### 4.2 Systemd Service Files
**File:** `deploy.sh` (embedded service definitions)
- Line 233: `Description=Project Manager FastAPI Application` → `Description=Project Manager FastAPI Application`
- Line 253: `Description=Project Manager Telegram Bot` → `Description=Project Manager Telegram Bot`

#### 4.3 Example Configuration
**File:** `.scar/projects.json.example`
```json
// CHANGE:
"name": "Project Manager",
// TO:
"name": "Project Manager",
```

### Phase 5: GitHub & CI/CD Configuration

#### 5.1 GitHub Actions
**Directory:** `.github/workflows/`
- Check workflow files for "Project Manager" references
- Update job names, descriptions

#### 5.2 Self-Hosted Runner
- Runner path updates if needed
- Update runner labels if they include "po" or "project-manager"

### Phase 6: Docker Configuration

#### 6.1 Docker Compose
**File:** `docker-compose.yml`
- Service names: Consider if you want to rename services
- Environment variables: Check for hardcoded "Project Manager" strings
- Container names: Update if they include "po"

**File:** `docker-compose.prod.yml.backup`
- Similar updates if this file is still in use

#### 6.2 Dockerfiles
- Check for any labels, env vars, or comments mentioning "Project Manager"

## Domain & Deployment Path Decisions

### Option A: Change Domain (po.153.se → pm.153.se)
**Pros:**
- Complete consistency with new naming
- Fresh start

**Cons:**
- Requires DNS changes
- Requires SSL certificate for new domain
- Breaking change for any bookmarks/links
- May need to maintain redirect from old domain

**If pursuing this option:**
1. Set up DNS for pm.153.se
2. Update all documentation references
3. Update deployment scripts
4. Get SSL cert for new domain
5. Set up 301 redirect from po.153.se → pm.153.se

### Option B: Keep Domain (po.153.se)
**Pros:**
- No infrastructure changes needed
- No breaking changes
- URL still works

**Cons:**
- Inconsistency between name and URL

**Recommendation:** **Option B (Keep Domain)** - Less risky, no downtime, URL still makes sense as "pm.153.se" isn't far off.

### Deployment Path: `/home/samuel/po` → `/home/samuel/pm`

**Recommended Approach:**
1. Deploy to new path `/home/samuel/pm`
2. Update systemd services
3. Test thoroughly
4. Remove old `/home/samuel/po` once confirmed working
5. Update CI/CD to deploy to new path

## Execution Order

1. **Phase 1** (Configuration) - Lowest risk
2. **Phase 2** (Source Code) - Test locally after changes
3. **Phase 3** (Documentation) - No runtime impact
4. **Phase 4** (Deployment Scripts) - Critical, test before production use
5. **Phase 5** (CI/CD) - Test in dev first
6. **Phase 6** (Docker) - Test with local docker-compose

## Testing Checklist

After making changes:

### Local Testing
- [ ] `pytest` passes all tests
- [ ] Bot starts successfully (check log message)
- [ ] API health endpoint returns correct app_name
- [ ] Telegram bot responds to `/start` with correct welcome
- [ ] WebUI title shows "Project Manager"
- [ ] GitHub webhook recognizes `@pm` mention

### Production Testing
- [ ] Deployment script deploys to correct path
- [ ] Systemd services start correctly
- [ ] Domain (keep po.153.se or migrate to pm.153.se) resolves
- [ ] SSL certificate valid
- [ ] API returns correct app name
- [ ] Bot responds to `@pm` mentions on GitHub
- [ ] Telegram bot shows correct identity

## Risk Mitigation

1. **Backup before changes**: `git commit` before starting
2. **Test incrementally**: Don't change everything at once
3. **Keep old path temporarily**: `/home/samuel/po` until `/home/samuel/pm` proven working
4. **Gradual rollout**: Test in development first
5. **Revert plan**: Keep old deployment scripts accessible for quick rollback

## Files Requiring Manual Review

Some files have complex references that may need case-by-case decisions:

- Long markdown documents with extensive "PM" references
- Historical RCA documents (may want to keep as-is for accuracy)
- Commit messages in git history (don't change)
- Any external documentation or wikis

## Post-Rename Tasks

1. **Update GitHub repository description** if it mentions "orchestrator"
2. **Update repository topics/tags**
3. **Announce name change** to users (if any)
4. **Update any external links** pointing to documentation
5. **Search for lingering references**: `git grep -i "project manager"`, `git grep "@po"`

## Summary of Changes

- **~200+ file references** to update
- **Key runtime strings**: Bot mentions (@po → @pm), app name, API responses
- **Deployment paths**: /home/samuel/po → /home/samuel/pm
- **Domain**: RECOMMEND keeping po.153.se (low risk)
- **Estimated time**: 2-3 hours for changes + 1 hour testing

## Sources

This plan was created by analyzing:
- Grep results for "PM", "Project Manager", "@po"
- Current codebase structure
- Deployment configuration
- Documentation hierarchy
