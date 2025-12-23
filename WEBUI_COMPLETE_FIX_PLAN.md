# WebUI Complete Fix Plan - Issue #19

**Date:** December 23, 2024
**Status:** Comprehensive Plan to Fix All WebUI Issues
**Goal:** Get WebUI working as intended per original vision (Issue #2)

---

## Executive Summary

After reviewing:
1. ✅ Original vision document from issue #2
2. ✅ Current codebase implementation
3. ✅ Previous fix plans (WEBUI_FIX_PLAN.md, IMPLEMENTATION-PLAN-FIX-WEBUI.md)
4. ✅ Docker/Playwright tooling availability
5. ✅ Live site status

**Finding:** The WebUI architecture is solid (3-panel design, WebSocket chat, SSE feed, Docker setup), but several integration issues prevent it from working as intended.

---

## Problems Reported by User

### 1. **Projects Not Loading All** ❌
**What user sees:**
- Only "scar" and "po" showing
- Missing "health-agent", "openhorizon", and potentially others

**Root Cause:**
- `.scar/projects.json` exists and is properly configured with 4 projects
- **BUT** the auto-import service needs to actually run and load these into the database
- Backend containers not currently running (docker compose ps shows empty)

### 2. **No Issues Loading** ❌
**What user sees:**
- No open issues displayed
- No closed issues displayed

**Root Cause:**
- GitHub API integration code exists (`src/api/github_issues.py`)
- **BUT** either:
  - Backend not running, OR
  - GitHub token authentication failing (401), OR
  - Frontend not properly calling the endpoint

### 3. **No Chat History from SCAR** ❌
**What user sees:**
- "SCAR disconnected" status
- No conversation history loading

**Root Cause:**
- Anthropic API authentication likely failing
- Database enum mismatch for message roles (already fixed in code based on WEBUI_FIX_PLAN.md)
- Backend containers not running

### 4. **No Contact with PO** ❌
**What user sees:**
- Have to refresh page to see previous messages
- Messages not persisting

**Root Cause:**
- WebSocket connection fails or messages don't persist
- Database not saving messages due to auth/connection issues
- Backend containers not running

---

## Analysis: Vision vs. Current State

### Original Vision Requirements (from `.agents/visions/project-orchestrator.md`)

| Feature | Vision | Current Status | Gap |
|---------|--------|----------------|-----|
| **Conversational brainstorming** | Natural language chat interface | ✅ WebSocket chat implemented | ❌ Not working (backend down) |
| **Vision doc generation** | Auto-generate readable vision docs | ✅ Code exists (`vision_generator.py`) | ❌ Never tested |
| **Approval gates** | User approval at key decision points | ✅ Code exists (`approval_gate.py`) | ❌ Never integrated with UI |
| **Automated workflow** | PIV loop (Prime→Plan→Execute→Validate) | ✅ SCAR executor exists | ❌ Not connected to UI |
| **Natural language interface** | No command memorization | ✅ Orchestrator agent processes NL | ❌ Backend not running |
| **Progress tracking** | Clear status updates | ✅ SCAR activity feed (SSE) | ❌ Not working |
| **Smart phase management** | Handles PIV automatically | ✅ Workflow orchestrator exists | ❌ Never tested end-to-end |
| **GitHub integration** | Repos, issues, PRs | ⚠️ Partial (issues API exists) | ❌ Token auth failing |
| **Telegram notifications** | Phase completion alerts | ✅ Telegram bot exists | ⚠️ Not connected to UI workflow |
| **Multi-project management** | Track multiple projects | ✅ Database schema supports it | ❌ Only importing 4 projects |

### Summary
**Architecture: 90% complete**
**Implementation: 75% complete**
**Integration & Testing: 10% complete**
**Current Status: NOT FUNCTIONAL**

The code is mostly there, but it's **never been properly deployed, tested, and debugged end-to-end**.

---

## Comprehensive Fix Plan

### Phase 0: Environment & Deployment Setup 🔧
**Priority:** P0 (CRITICAL - Nothing works without this)
**Time:** 2-3 hours

#### Task 0.1: Verify and Fix Environment Variables
**Current state:**
- `.env` file exists
- `.env.example` has all required variables defined

**Actions:**
1. **Audit `.env` file** (securely - don't expose in logs)
   ```bash
   # Check which keys are configured
   grep -E "^[A-Z_]+=" .env | cut -d= -f1 | sort
   ```

2. **Required for basic functionality:**
   - `ANTHROPIC_API_KEY` - For PO agent chat
   - `GITHUB_ACCESS_TOKEN` - For fetching issues/repos
   - `SECRET_KEY` - For session management
   - `DATABASE_URL` - Auto-configured in docker-compose
   - `REDIS_URL` - Auto-configured in docker-compose

3. **Verify API keys are valid:**
   ```bash
   # Test Anthropic API
   curl -H "x-api-key: $ANTHROPIC_API_KEY" \
        -H "anthropic-version: 2023-06-01" \
        https://api.anthropic.com/v1/messages

   # Test GitHub API
   curl -H "Authorization: Bearer $GITHUB_ACCESS_TOKEN" \
        https://api.github.com/user
   ```

4. **Fix any invalid/missing keys**

**Success Criteria:**
- ✅ All required env vars present
- ✅ API keys authenticate successfully
- ✅ No placeholder values like "your-key-here"

#### Task 0.2: Start Docker Services
**Actions:**
1. **Start all services:**
   ```bash
   docker compose up -d
   ```

2. **Verify all containers running:**
   ```bash
   docker compose ps
   # Expected: postgres (healthy), redis (healthy), app (running), frontend (running)
   ```

3. **Check logs for errors:**
   ```bash
   docker compose logs backend | grep -i error
   docker compose logs frontend | grep -i error
   ```

4. **Run database migrations:**
   ```bash
   docker compose exec backend alembic upgrade head
   ```

**Success Criteria:**
- ✅ All 4 containers running
- ✅ Backend accessible at http://localhost:8001
- ✅ Frontend accessible at http://localhost:3002
- ✅ Database migrations applied
- ✅ No critical errors in logs

#### Task 0.3: Test Basic Connectivity
**Actions:**
1. **Test backend API:**
   ```bash
   curl http://localhost:8001/health
   curl http://localhost:8001/api/projects
   ```

2. **Test frontend loads:**
   ```bash
   curl -I http://localhost:3002
   ```

3. **Test database connection:**
   ```bash
   docker compose exec backend python -c "from src.database.connection import async_session_maker; import asyncio; asyncio.run(async_session_maker().__aenter__())"
   ```

**Success Criteria:**
- ✅ Backend returns 200 OK
- ✅ Frontend serves HTML
- ✅ Database connection succeeds

---

### Phase 1: Fix Project Loading 📂
**Priority:** P0 (User-visible, core functionality)
**Time:** 2-3 hours

#### Task 1.1: Run Project Auto-Import
**Current state:**
- `.scar/projects.json` has 4 projects configured
- Auto-import code exists in `src/services/project_import_service.py`

**Actions:**
1. **Check if auto-import runs on startup:**
   ```bash
   docker compose logs backend | grep -i import
   ```

2. **If not running automatically, trigger manually:**
   ```bash
   docker compose exec backend python -m src.scripts.import_github_projects
   ```

3. **Verify projects in database:**
   ```bash
   docker compose exec postgres psql -U orchestrator -d project_orchestrator -c "SELECT name, github_repo_url FROM projects;"
   ```

4. **Check project count via API:**
   ```bash
   curl http://localhost:8001/api/projects | jq length
   # Expected: 4 or more
   ```

**Expected Output:**
```json
[
  {"name": "SCAR", "github_repo": "gpt153/scar", ...},
  {"name": "Platform Orchestrator", "github_repo": "gpt153/platform-orchestrator", ...},
  {"name": "Health Agent", "github_repo": "gpt153/health-agent", ...},
  {"name": "OpenHorizon", "github_repo": "gpt153/openhorizon", ...}
]
```

**Success Criteria:**
- ✅ All 4 projects in database
- ✅ API returns all projects
- ✅ Auto-import runs on container startup

#### Task 1.2: Verify Frontend Displays All Projects
**Actions:**
1. **Open WebUI:** http://localhost:3002

2. **Check browser console:**
   - Open DevTools → Console
   - Look for errors fetching projects

3. **Check Network tab:**
   - Look for GET `/api/projects` request
   - Verify response contains all 4 projects

4. **Verify left panel:**
   - Should see all 4 project names
   - Click each to verify selection works

**If projects don't appear:**
- Check CORS configuration in backend
- Check frontend API base URL configuration
- Check nginx proxy settings in frontend container

**Success Criteria:**
- ✅ All 4 projects visible in left panel
- ✅ Can select each project
- ✅ No console errors

---

### Phase 2: Fix GitHub Issues Integration 🔧
**Priority:** P1 (User-visible, important for usability)
**Time:** 3-4 hours

#### Task 2.1: Verify GitHub Issues API Endpoint
**Current state:**
- Endpoint exists: `GET /api/projects/{project_id}/issues`
- Code in `src/api/github_issues.py`

**Actions:**
1. **Test endpoint directly:**
   ```bash
   # Get a project ID first
   PROJECT_ID=$(curl -s http://localhost:8001/api/projects | jq -r '.[0].id')

   # Test issues endpoint
   curl "http://localhost:8001/api/projects/$PROJECT_ID/issues?state=all"
   ```

2. **Check for authentication errors:**
   - If 401 Unauthorized → GitHub token invalid
   - If 403 Forbidden → Token lacks required scopes
   - If 404 Not Found → Repo doesn't exist or is private

3. **Verify GitHub token scopes:**
   ```bash
   curl -H "Authorization: Bearer $GITHUB_ACCESS_TOKEN" \
        https://api.github.com/repos/gpt153/scar/issues?state=all
   ```

   **Required scopes:**
   - `repo` (for private repos)
   - `public_repo` (for public repos)

4. **If token invalid, create new one:**
   - Go to https://github.com/settings/tokens
   - Generate new token (classic)
   - Select scopes: `repo`, `read:org`, `read:user`
   - Update `.env` file
   - Restart backend: `docker compose restart backend`

**Success Criteria:**
- ✅ GitHub API returns issues (or empty array)
- ✅ No 401/403 errors
- ✅ API endpoint returns properly formatted JSON

#### Task 2.2: Add Issue Counts to Projects API
**Current state:**
- Project model has fields for issue counts
- Not currently populated

**Actions:**
1. **Check if `get_project_issue_counts()` exists:**
   ```bash
   grep -r "get_project_issue_counts" src/services/
   ```

2. **If missing, implement it** (as per IMPLEMENTATION-PLAN-FIX-WEBUI.md, lines 202-235)

3. **Integrate into `get_all_projects()` endpoint**

4. **Test:**
   ```bash
   curl http://localhost:8001/api/projects | jq '.[0] | {name, open_issues_count, closed_issues_count}'
   ```

**Success Criteria:**
- ✅ Projects API returns `open_issues_count` and `closed_issues_count`
- ✅ Counts are accurate (or 0 if no issues)

#### Task 2.3: Frontend Issues Display
**Current state:**
- Frontend has placeholder UI for issues
- Code in `frontend/src/components/LeftPanel/ProjectNavigator.tsx`

**Actions:**
1. **Check if `getProjectIssues()` API call exists:**
   ```bash
   grep -r "getProjectIssues" frontend/src/
   ```

2. **If missing, add to `frontend/src/services/api.ts`:**
   ```typescript
   getProjectIssues: async (projectId: string, state: string = "all"): Promise<Issue[]> => {
     const response = await fetch(`${API_BASE_URL}/projects/${projectId}/issues?state=${state}`);
     if (!response.ok) throw new Error('Failed to fetch issues');
     return response.json();
   }
   ```

3. **Update ProjectNavigator component** to fetch and display issues when project expands

4. **Test in browser:**
   - Open WebUI
   - Expand a project
   - Should see "Open Issues (N)" and "Closed Issues (M)"
   - Issues should be clickable links to GitHub

**Success Criteria:**
- ✅ Expanding project fetches issues
- ✅ Open and closed issue counts displayed
- ✅ Individual issues listed
- ✅ Clicking issue opens GitHub in new tab

---

### Phase 3: Fix Chat & WebSocket 💬
**Priority:** P0 (Core feature, critical for user interaction)
**Time:** 3-4 hours

#### Task 3.1: Fix Anthropic API Authentication
**Current state:**
- WebSocket endpoint exists: `/ws/chat/{project_id}`
- Orchestrator agent uses Anthropic API
- Likely failing with 401 Unauthorized

**Actions:**
1. **Verify Anthropic API key:**
   ```bash
   # Test authentication
   curl -X POST https://api.anthropic.com/v1/messages \
     -H "x-api-key: $ANTHROPIC_API_KEY" \
     -H "anthropic-version: 2023-06-01" \
     -H "content-type: application/json" \
     -d '{"model":"claude-3-5-sonnet-20241022","max_tokens":100,"messages":[{"role":"user","content":"test"}]}'
   ```

2. **If invalid, get new key:**
   - Visit https://console.anthropic.com/
   - Create new API key
   - Update `.env` file
   - Restart backend

3. **Check backend logs for auth errors:**
   ```bash
   docker compose logs backend | grep -i "anthropic\|401\|unauthorized"
   ```

**Success Criteria:**
- ✅ Anthropic API key authenticates successfully
- ✅ No 401 errors in backend logs

#### Task 3.2: Fix Message Role Enum Mismatch
**Current state:**
- Database enum: `MessageRole.USER`, `MessageRole.ASSISTANT`, `MessageRole.SYSTEM`
- Code might be using lowercase strings: `'user'`, `'assistant'`

**Actions:**
1. **Search for incorrect role usage:**
   ```bash
   grep -rn "role\s*=\s*['\"]user['\"]" src/
   grep -rn "role\s*=\s*['\"]assistant['\"]" src/
   ```

2. **Fix all occurrences to use enum:**
   ```python
   # WRONG
   role = 'assistant'

   # CORRECT
   from src.database.models import MessageRole
   role = MessageRole.ASSISTANT
   ```

3. **Key files to check:**
   - `src/api/websocket.py`
   - `src/agent/orchestrator_agent.py`
   - `src/services/project_service.py`

**Success Criteria:**
- ✅ No string literals for roles
- ✅ All use `MessageRole` enum
- ✅ Messages save to database without errors

#### Task 3.3: Test WebSocket Chat End-to-End
**Actions:**
1. **Manual test using browser:**
   - Open WebUI: http://localhost:3002
   - Select a project
   - Open DevTools → Network → WS tab
   - Send a chat message
   - Watch WebSocket traffic

2. **Check for WebSocket connection:**
   - Should see: `ws://localhost:8001/api/ws/chat/{project_id}`
   - Status: "connected"

3. **Verify message flow:**
   - User message sent → Backend receives
   - Backend processes with PO agent
   - Agent response sent back
   - Message appears in chat UI

4. **Test persistence:**
   - Send message
   - Refresh page
   - Message should still be visible

5. **Check database:**
   ```bash
   docker compose exec postgres psql -U orchestrator -d project_orchestrator -c \
     "SELECT role, content, timestamp FROM conversation_messages ORDER BY timestamp DESC LIMIT 10;"
   ```

**If WebSocket fails:**
- Check browser console for errors
- Check backend logs: `docker compose logs backend -f`
- Verify CORS settings in FastAPI
- Check nginx proxy settings

**Success Criteria:**
- ✅ WebSocket connects successfully
- ✅ Can send messages
- ✅ Receive responses from PO agent
- ✅ Messages persist in database
- ✅ Messages visible after refresh

---

### Phase 4: Fix SCAR Activity Feed 📊
**Priority:** P1 (Important for monitoring, but not blocking)
**Time:** 2-3 hours

#### Task 4.1: Fix SSE Endpoint Bug
**Current state:**
- SSE endpoint exists: `/api/sse/scar/{project_id}`
- Bug in query (from IMPLEMENTATION-PLAN-FIX-WEBUI.md):
  - Uses `created_at` (doesn't exist)
  - Should use `started_at`
  - Filters by `verbosity_level` @property (can't query on @property)

**Actions:**
1. **Apply fix from IMPLEMENTATION-PLAN-FIX-WEBUI.md** (already documented in lines 28-48)

2. **File:** `src/services/scar_feed_service.py`, lines 99-117

3. **Changes:**
   - Remove `verbosity_level` from WHERE clause
   - Change `created_at` to `started_at`

4. **Test SSE endpoint:**
   ```bash
   PROJECT_ID=$(curl -s http://localhost:8001/api/projects | jq -r '.[0].id')
   curl -N "http://localhost:8001/api/sse/scar/$PROJECT_ID"
   # Should stream events, not error
   ```

**Success Criteria:**
- ✅ SSE connection stays open
- ✅ No 500 errors
- ✅ Events stream when SCAR commands run

#### Task 4.2: Generate Test SCAR Activity
**Current state:**
- SCAR feed works, but no activity to display

**Actions:**
1. **Create seed data** for testing:
   ```bash
   docker compose exec backend python -m src.scripts.seed_data
   ```

2. **Or trigger real SCAR command:**
   - Send chat message: "Prime this project"
   - PO agent should execute SCAR prime command
   - Activity should appear in feed

3. **Verify in database:**
   ```bash
   docker compose exec postgres psql -U orchestrator -d project_orchestrator -c \
     "SELECT command_type, status, started_at FROM scar_command_executions ORDER BY started_at DESC LIMIT 5;"
   ```

**Success Criteria:**
- ✅ SCAR activity appears in database
- ✅ SSE endpoint streams the activity
- ✅ Frontend displays in SCAR Activity Feed panel

#### Task 4.3: Frontend SCAR Feed Integration
**Current state:**
- Frontend has `useScarFeed` hook
- SSE connection implemented

**Actions:**
1. **Test SSE connection in browser:**
   - Open WebUI
   - Check DevTools → Network → EventSource
   - Should see connection to `/api/sse/scar/{project_id}`

2. **Verify events received:**
   - Watch console for SSE events
   - Should log incoming activity

3. **Check right panel display:**
   - Should show "● Live" when connected
   - Should display activity items
   - Should be color-coded by source (po, scar, claude)

**If not working:**
- Check `frontend/src/hooks/useScarFeed.ts`
- Verify API base URL configuration
- Check for CORS issues

**Success Criteria:**
- ✅ SSE connects and stays connected
- ✅ Activity appears in right panel
- ✅ "● Live" status indicator shows
- ✅ Can adjust verbosity filter

---

### Phase 5: Vision Alignment & Missing Features 🎯
**Priority:** P2 (Important for vision, but MVP can work without)
**Time:** 6-8 hours

#### Task 5.1: Vision Document Generation
**Current state:**
- Code exists: `src/services/vision_generator.py`
- Orchestrator agent can create vision docs
- Never tested end-to-end

**Actions:**
1. **Test vision generation via chat:**
   - Start new project chat
   - Brainstorm a feature idea
   - Agent should create vision document

2. **Verify document saved:**
   ```bash
   ls -la .agents/visions/
   # Should see new markdown file
   ```

3. **Test viewing in WebUI:**
   - Left panel → Select project → Documents section
   - Should show vision document
   - Click to view in DocumentViewer

4. **If not working:**
   - Check `src/agent/orchestrator_agent.py` for vision doc workflow
   - Verify file system permissions
   - Check database `project_documents` table

**Success Criteria:**
- ✅ Can brainstorm idea in chat
- ✅ Agent creates vision document
- ✅ Document viewable in WebUI
- ✅ Document properly formatted markdown

#### Task 5.2: Approval Gates UI
**Current state:**
- Backend code exists: `src/services/approval_gate.py`
- Database models exist: `ApprovalGate` table
- **No frontend UI implemented**

**Actions:**
1. **Design approval gate UI:**
   - Modal dialog or inline component?
   - Show: gate type, description, approve/reject buttons

2. **Implement in ChatInterface:**
   - When agent sends approval request
   - Display UI for user to approve/reject
   - Send response back via WebSocket

3. **Test workflow:**
   - Vision doc created → Approval gate triggered
   - UI shows: "Review vision document. Approve to continue?"
   - User clicks "Approve"
   - Workflow continues

**Success Criteria:**
- ✅ Approval gates display in UI
- ✅ User can approve/reject
- ✅ Workflow respects user decision

#### Task 5.3: Automated PIV Loop
**Current state:**
- SCAR executor exists: `src/services/scar_executor.py`
- Workflow orchestrator exists: `src/services/workflow_orchestrator.py`
- Never integrated with agent workflow

**Actions:**
1. **Test PIV commands via chat:**
   - "Prime this project" → Agent runs `/command-invoke prime`
   - "Plan this feature" → Agent runs `/command-invoke plan-feature`
   - "Execute the plan" → Agent runs `/command-invoke execute`
   - "Validate the work" → Agent runs `/command-invoke validate`

2. **Verify SCAR activity feed shows progress**

3. **Test phase transitions:**
   - After prime → Agent suggests planning
   - After plan → Agent asks to execute
   - After execute → Agent suggests validation

4. **Integration points:**
   - Chat message → PO agent decides action
   - Agent uses SCAR executor to run commands
   - SCAR executor emits activity to feed
   - Agent responds with results in chat

**Success Criteria:**
- ✅ Can trigger SCAR commands via natural language
- ✅ Agent executes PIV loop automatically
- ✅ Activity appears in SCAR feed
- ✅ Results appear in chat

#### Task 5.4: Telegram Notifications
**Current state:**
- Telegram bot exists: `src/integrations/telegram_bot.py`
- Not integrated with WebUI workflow

**Actions:**
1. **Connect approval gates to Telegram:**
   - When approval gate created → Send Telegram notification
   - User can approve via Telegram or WebUI

2. **Connect phase completion to Telegram:**
   - When phase completes → Send notification
   - Include link to WebUI
   - Show next steps

3. **Test:**
   - Start workflow in WebUI
   - Receive Telegram notification
   - Approve via Telegram
   - Workflow continues in WebUI

**Success Criteria:**
- ✅ Notifications sent at key points
- ✅ Can approve via Telegram
- ✅ WebUI and Telegram stay in sync

---

### Phase 6: Testing & Validation ✅
**Priority:** P0 (Critical to verify everything works)
**Time:** 4-6 hours

#### Task 6.1: Manual End-to-End Testing
**Test Scenarios:**

**Scenario 1: New User Onboarding**
1. Open WebUI fresh
2. See all projects in left panel ✓
3. Select a project ✓
4. See issues (if any) ✓
5. See documents (if any) ✓
6. SCAR feed shows "● Live" ✓

**Scenario 2: Chat with PO Agent**
1. Select project
2. Send message: "Hello, what can you help me with?"
3. Receive response ✓
4. Messages persist after refresh ✓

**Scenario 3: Project Brainstorming**
1. Send: "I want to build a meal planner app"
2. Agent asks clarifying questions ✓
3. Back-and-forth conversation ✓
4. Agent creates vision document ✓
5. Vision doc viewable in Documents section ✓

**Scenario 4: Approval Gate**
1. Agent asks for approval ✓
2. UI shows approval dialog ✓
3. Approve ✓
4. Workflow continues ✓

**Scenario 5: SCAR Workflow Execution**
1. Send: "Prime this project"
2. SCAR feed shows activity ✓
3. Agent reports completion in chat ✓
4. Can continue to next phase ✓

**Scenario 6: GitHub Integration**
1. Expand project in navigator
2. See issue counts ✓
3. Click issue → Opens GitHub ✓

**Checklist:**
- [ ] All projects load
- [ ] Can select projects
- [ ] Issues display correctly
- [ ] Chat sends/receives messages
- [ ] Messages persist
- [ ] SCAR feed shows live status
- [ ] SCAR commands execute
- [ ] Vision docs generate
- [ ] Approval gates work
- [ ] No console errors
- [ ] No API errors in logs

#### Task 6.2: Automated Testing with Playwright
**Actions:**

1. **Install Playwright:**
   ```bash
   npm install -D @playwright/test
   npx playwright install
   ```

2. **Create test suite:**
   ```typescript
   // tests/e2e/webui.spec.ts
   import { test, expect } from '@playwright/test';

   test('WebUI loads all projects', async ({ page }) => {
     await page.goto('http://localhost:3002');

     // Wait for projects to load
     await page.waitForSelector('.project-navigator');

     // Check project count
     const projects = await page.locator('.project-item').count();
     expect(projects).toBeGreaterThanOrEqual(4);
   });

   test('Chat sends and receives messages', async ({ page }) => {
     await page.goto('http://localhost:3002');

     // Select first project
     await page.locator('.project-item').first().click();

     // Send message
     await page.fill('textarea[placeholder="Type a message..."]', 'Hello');
     await page.press('textarea', 'Enter');

     // Wait for response
     await page.waitForSelector('.message.assistant', { timeout: 10000 });

     // Verify message persists after reload
     await page.reload();
     await page.waitForSelector('.message.user');
     const userMessage = await page.locator('.message.user').first().textContent();
     expect(userMessage).toContain('Hello');
   });

   test('SCAR feed connects and shows live status', async ({ page }) => {
     await page.goto('http://localhost:3002');

     // Select project
     await page.locator('.project-item').first().click();

     // Check SCAR feed status
     await page.waitForSelector('.feed-status:has-text("Live")', { timeout: 5000 });
   });

   test('Issues load when project expanded', async ({ page }) => {
     await page.goto('http://localhost:3002');

     // Expand first project
     await page.locator('.project-item').first().click();

     // Wait for issues to load
     await page.waitForSelector('.issue-list', { timeout: 5000 });

     // Verify issue counts shown
     const openIssues = await page.locator('.issue-group:has-text("Open Issues")').textContent();
     expect(openIssues).toMatch(/Open Issues \(\d+\)/);
   });
   ```

3. **Run tests:**
   ```bash
   npx playwright test
   ```

**Success Criteria:**
- ✅ All tests pass
- ✅ No flaky tests
- ✅ Tests run in CI/CD pipeline

#### Task 6.3: Performance & Load Testing
**Actions:**

1. **Test with many projects:**
   - Import 20+ projects
   - Verify UI remains responsive

2. **Test with long chat history:**
   - Send 100+ messages
   - Verify scrolling works
   - Verify load time acceptable

3. **Test concurrent users:**
   - Multiple browser tabs/windows
   - Different projects
   - Verify no conflicts

4. **Monitor resource usage:**
   ```bash
   docker stats
   ```

**Success Criteria:**
- ✅ UI responsive with 20+ projects
- ✅ Chat loads 100+ messages quickly
- ✅ No memory leaks
- ✅ Backend CPU/memory reasonable

---

### Phase 7: Production Deployment 🚀
**Priority:** P1 (Get it live at po.153.se)
**Time:** 2-3 hours

#### Task 7.1: Review Deployment Configuration
**Current state:**
- Deployment docs exist: `DEPLOYMENT.md`, `WEBUI_DEPLOYMENT.md`
- Docker Compose configured
- Nginx reverse proxy needed for production

**Actions:**

1. **Review `DEPLOYMENT.md`**

2. **Verify production environment variables:**
   ```bash
   # On production server
   cd /opt/project-orchestrator
   cat .env | grep -v "^#" | grep -v "^$"
   ```

3. **Check critical settings:**
   - `APP_ENV=production`
   - `DEBUG=false`
   - Valid API keys
   - Correct database URL
   - HTTPS URLs (not http)

4. **Verify DNS:**
   - `po.153.se` points to server IP
   - SSL certificate valid

**Success Criteria:**
- ✅ Environment configured for production
- ✅ DNS resolves correctly
- ✅ SSL certificate valid

#### Task 7.2: Deploy to Production
**Actions:**

1. **Pull latest code:**
   ```bash
   cd /opt/project-orchestrator
   git pull origin main
   ```

2. **Build and restart services:**
   ```bash
   docker compose down
   docker compose build --no-cache
   docker compose up -d
   ```

3. **Run migrations:**
   ```bash
   docker compose exec backend alembic upgrade head
   ```

4. **Import projects:**
   ```bash
   docker compose exec backend python -m src.scripts.import_github_projects
   ```

5. **Verify services:**
   ```bash
   docker compose ps
   docker compose logs backend --tail 100
   docker compose logs frontend --tail 50
   ```

6. **Test from outside:**
   ```bash
   curl https://po.153.se/api/health
   curl https://po.153.se
   ```

**Success Criteria:**
- ✅ Services running on production
- ✅ HTTPS works
- ✅ No critical errors in logs
- ✅ Can access WebUI from internet

#### Task 7.3: Production Smoke Testing
**Actions:**

1. **Open https://po.153.se in browser**

2. **Run through manual test scenarios** (from Task 6.1)

3. **Check production logs:**
   ```bash
   docker compose logs -f
   ```

4. **Monitor for errors over 24 hours**

**Success Criteria:**
- ✅ All features work in production
- ✅ No errors in logs
- ✅ Performance acceptable
- ✅ SSL/HTTPS working

---

## Timeline & Effort Estimate

| Phase | Priority | Time | Can Start |
|-------|----------|------|-----------|
| Phase 0: Environment Setup | P0 | 2-3h | Immediately |
| Phase 1: Project Loading | P0 | 2-3h | After Phase 0 |
| Phase 2: GitHub Issues | P1 | 3-4h | After Phase 0 |
| Phase 3: Chat & WebSocket | P0 | 3-4h | After Phase 0 |
| Phase 4: SCAR Activity Feed | P1 | 2-3h | After Phase 0 |
| Phase 5: Vision Alignment | P2 | 6-8h | After Phase 3 |
| Phase 6: Testing | P0 | 4-6h | After Phase 1-4 |
| Phase 7: Production Deploy | P1 | 2-3h | After Phase 6 |
| **TOTAL** | | **24-34h** | **3-5 days** |

### Recommended Execution Order

**Day 1: Get Basic Functionality Working (8-10 hours)**
- Phase 0: Environment Setup (2-3h)
- Phase 1: Project Loading (2-3h)
- Phase 3: Chat & WebSocket (3-4h)

**Day 2: Complete Core Features (8-10 hours)**
- Phase 2: GitHub Issues (3-4h)
- Phase 4: SCAR Activity Feed (2-3h)
- Phase 6: Basic Testing (3-4h)

**Day 3: Vision Features & Production (6-8 hours)**
- Phase 5: Vision Alignment (6-8h) [Optional - can defer]
- OR proceed directly to:
- Phase 6: Full Testing (2-3h)
- Phase 7: Production Deploy (2-3h)

**Alternative: MVP-First Approach (16-20 hours / 2 days)**
- Skip Phase 5 initially
- Get Phases 0-4 + 6 + 7 working
- Deploy to production
- Add Phase 5 features later as enhancements

---

## Success Criteria

### Immediate Success (After Phases 0-4, 6, 7)
- ✅ All projects load in WebUI (4+ projects visible)
- ✅ All issues (open & closed) display for each project
- ✅ Chat works: send message → get PO agent response → persists after refresh
- ✅ SCAR feed shows "● Live" status
- ✅ Can expand projects to see issues
- ✅ No console errors in browser
- ✅ No critical errors in backend logs
- ✅ Production site accessible at https://po.153.se

### Vision Alignment (After Phase 5)
- ✅ Can brainstorm new project idea via chat
- ✅ Vision document auto-generates
- ✅ Approval gates work (UI + Telegram)
- ✅ Can trigger SCAR PIV loop via natural language
- ✅ Phase transitions automatic with approval gates
- ✅ Telegram notifications sent at key points

### Ultimate Success (Vision from Issue #2)
> "Non-technical user opens po.153.se, chats about their idea,
> approves the vision, and watches their app get built phase-by-phase
> with clear updates and approval gates. They feel in control and
> empowered throughout the process."

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Invalid API keys** | High | Critical | Pre-validate all keys before starting |
| **Docker networking issues** | Medium | High | Test container-to-container communication |
| **Database migration failures** | Low | High | Backup database before migrations |
| **CORS configuration** | Medium | Medium | Test from real browser early |
| **WebSocket connection drops** | Medium | Medium | Implement reconnection logic |
| **GitHub rate limits** | Medium | Low | Cache aggressively, use authenticated requests |
| **Anthropic API costs** | Low | Medium | Monitor usage, set spending limits |
| **Production deployment issues** | Medium | High | Test in staging environment first |

---

## Tools & Resources

### Available Tools
- ✅ Docker / Docker Compose
- ✅ Playwright (for E2E testing)
- ✅ PostgreSQL (database)
- ✅ Redis (caching)
- ✅ Anthropic Claude API
- ✅ GitHub API
- ✅ Telegram Bot API

### Documentation References
- Original Vision: `.agents/visions/project-orchestrator.md`
- Previous Fix Plan: `WEBUI_FIX_PLAN.md`
- Implementation Plan: `IMPLEMENTATION-PLAN-FIX-WEBUI.md`
- Deployment Guide: `DEPLOYMENT.md`
- README: `README.md`

### Key Files to Modify
**Backend:**
- `src/services/scar_feed_service.py` (fix SSE bug)
- `src/api/websocket.py` (ensure role enum usage)
- `src/agent/orchestrator_agent.py` (verify role enum)
- `src/services/project_service.py` (add issue counts)
- `.env` (update API keys)

**Frontend:**
- `frontend/src/services/api.ts` (add getProjectIssues)
- `frontend/src/components/LeftPanel/ProjectNavigator.tsx` (display issues)
- `frontend/src/components/MiddlePanel/ChatInterface.tsx` (approval gates UI)

**Configuration:**
- `.env` (API keys and configuration)
- `docker-compose.yml` (already correct)
- `.scar/projects.json` (already correct)

---

## Questions Before Proceeding

To ensure smooth execution, please confirm:

1. **API Keys - Do you have access to:**
   - ✅ Valid Anthropic API key? (starts with `sk-ant-`)
   - ✅ Valid GitHub personal access token? (starts with `ghp_` or `github_pat_`)
   - ✅ Telegram bot token? (if using Telegram integration)

2. **Scope - What should we prioritize:**
   - Option A: **MVP-first** (Phases 0-4, 6, 7) = Get basic WebUI working ASAP
   - Option B: **Full vision** (All phases) = Implement everything from vision doc
   - Option C: **Custom** - Specify which features are must-haves

3. **Testing Approach:**
   - Manual testing sufficient for MVP?
   - Want Playwright E2E tests?
   - Need performance/load testing?

4. **Timeline:**
   - Need this working immediately?
   - Can spread over 3-5 days?
   - Okay to deploy MVP then iterate?

5. **Production:**
   - Deploy to po.153.se after MVP?
   - Or test locally first?
   - Staging environment available?

---

## Next Steps

Once confirmed, I will:

1. ✅ **Start with Phase 0** - Get environment and services running
2. ✅ **Execute phases sequentially** - Test each before moving on
3. ✅ **Document issues** - Track any new problems discovered
4. ✅ **Report progress** - Update after each phase
5. ✅ **Deploy to production** - When tests pass

**Ready to proceed?** 🚀
