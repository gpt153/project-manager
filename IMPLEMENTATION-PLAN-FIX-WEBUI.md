# Implementation Plan: Fix WebUI Issues

**Based on**: RCA-WEBUI-ISSUE-13.md
**Goal**: Transform "three empty windows" into fully functional WebUI
**Estimated Time**: 8-12 hours
**Priority**: P0 bugs → P1 data → P2 features

---

## Phase 1: Fix Critical Bugs (P0)
**Time**: 1-2 hours
**Blockers**: Prevents any usage of WebUI

### Task 1.1: Fix SCAR Activity Feed SSE Bug
**File**: `src/services/scar_feed_service.py`
**Lines**: 98-117

**Changes**:
1. Remove verbosity_level filter from SQLAlchemy query (line 103, 113)
   - Reason: Can't compare @property in WHERE clause
   - Alternative: Filter in Python after query if needed

2. Change `created_at` to `started_at` (line 106, 115)
   - Reason: `ScarCommandExecution` has `started_at` column, not `created_at`
   - The `created_at` @property returns `started_at`

**Code Change**:
```python
# Line 99-107 (if branch)
query = (
    select(ScarCommandExecution)
    .where(
        ScarCommandExecution.project_id == project_id,
        ScarCommandExecution.id > UUID(last_id)
    )
    .order_by(ScarCommandExecution.started_at.asc())
)

# Line 108-117 (else branch)
query = (
    select(ScarCommandExecution)
    .where(
        ScarCommandExecution.project_id == project_id
    )
    .order_by(desc(ScarCommandExecution.started_at))
    .limit(1)
)
```

**Validation**:
```bash
curl -N https://po.153.se/api/sse/scar/<project-id>
# Should stream events, not error
```

---

### Task 1.2: Fix Chat Messages API
**File**: `src/services/project_service.py` (needs investigation)
**Issue**: `/api/projects/{id}/messages` returns HTTP 500

**Investigation Steps**:
1. Check server logs for exact error traceback
2. Find `get_conversation_history` function
3. Identify query or relationship issue

**Likely Fixes**:
- Add proper error handling
- Fix relationship loading (`.options(selectinload(...))`)
- Handle empty results gracefully
- Fix column name mismatch

**Validation**:
```bash
curl https://po.153.se/api/projects/<project-id>/messages
# Should return [] or message list, not error
```

---

## Phase 2: GitHub Issues Integration (P1)
**Time**: 4-6 hours
**Impact**: Makes projects navigator useful

### Task 2.1: Create GitHub Issues API Endpoint
**New File**: `src/api/github_issues.py`

**Endpoint**: `GET /api/projects/{project_id}/issues`

**Query Parameters**:
- `state`: "open" | "closed" | "all" (default: "all")
- `limit`: int (default: 100)

**Implementation**:
```python
from fastapi import APIRouter, Depends, HTTPException, Query
from src.integrations.github_client import GitHubClient, GitHubRepo
from src.database.models import Project
from src.database.connection import get_session

router = APIRouter()

@router.get("/projects/{project_id}/issues")
async def get_project_issues(
    project_id: UUID,
    state: str = Query(default="all", regex="^(open|closed|all)$"),
    limit: int = Query(default=100, le=100),
    session: AsyncSession = Depends(get_session)
):
    """
    Fetch GitHub issues for a project.

    Returns issues directly from GitHub API (no database caching in MVP).
    """
    # 1. Get project
    result = await session.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(404, "Project not found")

    if not project.github_repo_url:
        return []  # No GitHub repo, return empty

    # 2. Parse repo from URL
    try:
        repo = GitHubRepo.from_url(project.github_repo_url)
    except ValueError:
        logger.warning(f"Invalid GitHub URL: {project.github_repo_url}")
        return []

    # 3. Fetch issues from GitHub
    github = GitHubClient()
    issues = await github.get_issues(repo, state=state, limit=limit)

    # 4. Format response
    return [
        {
            "number": issue["number"],
            "title": issue["title"],
            "state": issue["state"],
            "created_at": issue["created_at"],
            "updated_at": issue["updated_at"],
            "url": issue["html_url"],
        }
        for issue in issues
    ]
```

---

### Task 2.2: Add GitHub Issues Method to GitHubClient
**File**: `src/integrations/github_client.py`

**Add Method**:
```python
async def get_issues(
    self,
    repo: GitHubRepo,
    state: str = "all",
    limit: int = 100
) -> list[dict]:
    """
    Get issues for a repository.

    Args:
        repo: Repository information
        state: Issue state filter (open, closed, all)
        limit: Maximum issues to return

    Returns:
        List of issue dictionaries from GitHub API
    """
    url = f"{self.base_url}/repos/{repo.full_name}/issues"
    params = {
        "state": state,
        "per_page": min(limit, 100),
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers=self._get_headers(),
            params=params,
            timeout=10.0
        )
        response.raise_for_status()
        return response.json()
```

---

### Task 2.3: Update Project Service to Include Issue Counts
**File**: `src/services/project_service.py`

**Modify**: `get_all_projects` function

**Add**:
```python
async def get_project_issue_counts(project: Project) -> dict:
    """
    Get issue counts from GitHub API.

    Returns dict with open_issues_count and closed_issues_count.
    Caches result for 5 minutes to avoid API rate limits.
    """
    if not project.github_repo_url:
        return {"open_issues_count": 0, "closed_issues_count": 0}

    try:
        repo = GitHubRepo.from_url(project.github_repo_url)
        github = GitHubClient()

        # Fetch just counts (use search API for efficiency)
        # Or fetch issues and count (simpler but slower)
        open_issues = await github.get_issues(repo, state="open", limit=1)
        closed_issues = await github.get_issues(repo, state="closed", limit=1)

        # GitHub API returns total count in headers
        # For MVP, can fetch all and count
        return {
            "open_issues_count": len(open_issues) if isinstance(open_issues, list) else 0,
            "closed_issues_count": len(closed_issues) if isinstance(closed_issues, list) else 0,
        }
    except Exception as e:
        logger.warning(f"Failed to fetch issue counts for {project.id}: {e}")
        return {"open_issues_count": 0, "closed_issues_count": 0}

# In get_all_projects, for each project:
issue_counts = await get_project_issue_counts(project)
project_dict["open_issues_count"] = issue_counts["open_issues_count"]
project_dict["closed_issues_count"] = issue_counts["closed_issues_count"]
```

**Note**: For MVP, this fetches counts real-time. For production, add caching (Redis) to avoid GitHub API rate limits.

---

### Task 2.4: Register New Router
**File**: `src/main.py`

**Add**:
```python
from src.api.github_issues import router as github_issues_router

app.include_router(github_issues_router, prefix="/api", tags=["GitHub Issues"])
```

---

### Task 2.5: Update Frontend to Fetch and Display Issues
**File**: `frontend/src/components/LeftPanel/ProjectNavigator.tsx`

**Changes**:
1. Add state for issues: `const [projectIssues, setProjectIssues] = useState<Map<string, Issue[]>>(new Map())`

2. When project expands, fetch issues:
```typescript
const toggleProject = async (projectId: string) => {
  if (!expandedProjects.has(projectId) && !projectIssues.has(projectId)) {
    // Fetch issues when expanding
    try {
      const issues = await api.getProjectIssues(projectId);
      setProjectIssues(prev => new Map(prev).set(projectId, issues));
    } catch (error) {
      console.error('Failed to fetch issues:', error);
    }
  }

  setExpandedProjects((prev) => {
    const next = new Set(prev);
    if (next.has(projectId)) {
      next.delete(projectId);
    } else {
      next.add(projectId);
    }
    return next;
  });
};
```

3. Render actual issues:
```typescript
{expandedProjects.has(project.id) && (
  <ul className="issue-list">
    <li className="issue-group">
      <span>Open Issues ({project.open_issues_count || 0})</span>
      {projectIssues.get(project.id)
        ?.filter(i => i.state === 'open')
        .map(issue => (
          <div key={issue.number} className="issue-item">
            <a href={issue.url} target="_blank" rel="noopener noreferrer">
              #{issue.number}: {issue.title}
            </a>
          </div>
        ))}
    </li>
    <li className="issue-group">
      <span>Closed Issues ({project.closed_issues_count || 0})</span>
      {/* Similar for closed */}
    </li>
    {/* Documents section */}
  </ul>
)}
```

**Add to**: `frontend/src/services/api.ts`
```typescript
getProjectIssues: async (projectId: string, state: string = "all"): Promise<Issue[]> => {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/issues?state=${state}`);
  if (!response.ok) throw new Error('Failed to fetch issues');
  return response.json();
},
```

---

## Phase 3: Import Existing Projects (P1)
**Time**: 2-4 hours
**Impact**: Populates WebUI with real data

### Task 3.1: Create Data Import Script
**New File**: `src/scripts/import_github_projects.py`

**Purpose**: Import existing GitHub repositories as Projects

**Implementation**:
```python
"""
Import existing GitHub repositories as Projects.

This script scans the configured GitHub organization/user for repositories
and creates Project records in the database.
"""
import asyncio
from sqlalchemy import select
from src.database.connection import async_session_maker
from src.database.models import Project, ProjectStatus
from src.integrations.github_client import GitHubClient, GitHubRepo
from src.config import settings

async def import_github_repos():
    """Import all repos from GitHub as projects."""
    github = GitHubClient()

    # Get all repos (replace with your org/user)
    repos = await github.get_user_repos()  # Need to implement this method

    async with async_session_maker() as session:
        for repo_data in repos:
            # Check if project already exists
            repo_url = repo_data["html_url"]
            result = await session.execute(
                select(Project).where(Project.github_repo_url == repo_url)
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f"Project already exists: {repo_data['name']}")
                continue

            # Create new project
            project = Project(
                name=repo_data["name"],
                description=repo_data["description"],
                github_repo_url=repo_url,
                status=ProjectStatus.IN_PROGRESS,
            )
            session.add(project)
            print(f"Imported: {repo_data['name']}")

        await session.commit()
        print("Import complete!")

if __name__ == "__main__":
    asyncio.run(import_github_repos())
```

**Run**:
```bash
cd /worktrees/project-manager/issue-13
python -m src.scripts.import_github_projects
```

---

### Task 3.2: Implement `get_user_repos` in GitHubClient
**File**: `src/integrations/github_client.py`

**Add Method**:
```python
async def get_user_repos(self, username: Optional[str] = None) -> list[dict]:
    """
    Get repositories for a user.

    Args:
        username: GitHub username (uses authenticated user if None)

    Returns:
        List of repository dictionaries
    """
    if username:
        url = f"{self.base_url}/users/{username}/repos"
    else:
        url = f"{self.base_url}/user/repos"  # Authenticated user

    params = {"per_page": 100, "type": "all"}

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers=self._get_headers(),
            params=params,
            timeout=10.0
        )
        response.raise_for_status()
        return response.json()
```

---

### Task 3.3: Link Existing GitHub Issues to Projects
**Purpose**: If you have GitHub issues created by @scar, link them to projects

**File**: Extend `import_github_projects.py`

```python
# After creating project, check for associated issue
if "issue" in repo_data:  # If repo was created from an issue
    project.github_issue_number = repo_data["issue"]["number"]
```

---

## Phase 4: Conversation History Sync (P2)
**Time**: 2-3 hours (Optional for MVP)
**Impact**: Makes chat panel useful for existing projects

### Task 4.1: Export Telegram Conversation History
**If Telegram bot has conversation data in memory/files**:

1. Add endpoint to Telegram bot to export conversations
2. Format as JSON: `[{role, content, timestamp}, ...]`
3. Save to file or POST to API

### Task 4.2: Import Conversations into Database
**Script**: `src/scripts/import_telegram_conversations.py`

```python
async def import_conversation(project_id: UUID, messages: list[dict]):
    """Import conversation messages for a project."""
    async with async_session_maker() as session:
        for msg_data in messages:
            msg = ConversationMessage(
                project_id=project_id,
                role=MessageRole[msg_data["role"].upper()],
                content=msg_data["content"],
                timestamp=datetime.fromisoformat(msg_data["timestamp"]),
            )
            session.add(msg)
        await session.commit()
```

---

## Phase 5: Testing & Validation
**Time**: 1-2 hours

### Test Checklist

#### Backend Tests
- [ ] SSE connection stays alive (no errors)
- [ ] Messages API returns data (even if empty)
- [ ] GitHub issues endpoint returns issues
- [ ] Projects API includes issue counts
- [ ] WebSocket chat works end-to-end

#### Frontend Tests
- [ ] Open https://po.153.se
- [ ] See multiple projects in left panel
- [ ] Expand project → See issues (open/closed)
- [ ] Click project → Chat loads in middle panel
- [ ] Send message → Get response
- [ ] SCAR feed shows "● Live" (right panel)
- [ ] Panels are resizable
- [ ] Documents open correctly

#### Integration Tests
- [ ] Create new project via API → Appears in navigator
- [ ] GitHub issue created → Count updates
- [ ] SCAR command executed → Appears in feed
- [ ] Chat message sent → Appears in history

---

## Deployment Plan

### Step 1: Fix Bugs (Deploy Immediately)
```bash
# Fix scar_feed_service.py
git add src/services/scar_feed_service.py
git commit -m "fix: SCAR feed SSE query bugs"

# Fix project_service.py (after investigation)
git add src/services/project_service.py
git commit -m "fix: Chat messages API error handling"

# Deploy
git push origin issue-13
# Trigger deployment workflow
```

### Step 2: Add GitHub Integration
```bash
# Add all GitHub issues code
git add src/api/github_issues.py
git add src/integrations/github_client.py
git add frontend/src/services/api.ts
git add frontend/src/components/LeftPanel/ProjectNavigator.tsx
git commit -m "feat: GitHub issues integration in WebUI"
git push origin issue-13
```

### Step 3: Import Data
```bash
# Run import script on production server
ssh production-server
cd /app
python -m src.scripts.import_github_projects
# Verify: curl https://po.153.se/api/projects | jq length
```

### Step 4: Verify & Close Issue
- [ ] Test all features at po.153.se
- [ ] Compare to vision document
- [ ] Update issue #13 with results
- [ ] Close issue if all criteria met

---

## Success Criteria

After implementation, WebUI should:

✅ Display ALL projects (not just 1 demo)
✅ Show real GitHub issues with accurate counts
✅ Chat with @po works (send/receive messages)
✅ SCAR activity feed shows "● Live" status
✅ Conversation history loads when selecting project
✅ Vision documents and plans are viewable
✅ No console errors in browser
✅ No HTTP 500 errors from API

**Goal**: "Three empty windows" becomes "Fully functional project management interface"

---

## Timeline

| Phase | Tasks | Time | Can Start |
|-------|-------|------|-----------|
| Phase 1 | Fix SSE bug, Fix messages API | 1-2h | Immediately |
| Phase 2 | GitHub issues integration | 4-6h | After Phase 1 |
| Phase 3 | Import existing projects | 2-4h | After Phase 1 |
| Phase 4 | Conversation history sync | 2-3h | Optional |
| Phase 5 | Testing & deployment | 1-2h | After Phase 2+3 |
| **Total** | | **8-15h** | |

**Recommended Order**:
1. Phase 1 (bugs) - Quick wins
2. Phase 3 (import data) - Makes WebUI look alive
3. Phase 2 (GitHub issues) - Completes core features
4. Phase 5 (test & deploy)
5. Phase 4 (conversation sync) - Nice to have

---

## Notes

### Rate Limiting Considerations
GitHub API has rate limits (5000 requests/hour authenticated). For production:
- Implement Redis caching for issue counts
- Cache project issues for 5-10 minutes
- Use GitHub webhooks to invalidate cache on changes

### Future Enhancements
After MVP is working:
- Real-time sync (webhooks)
- Issue search/filter
- Create issues from WebUI
- Inline issue editing
- Richer conversation UI (markdown rendering)
- SCAR command triggering from WebUI

### Alternatives Considered
**GitHub Issues Storage**:
- Option A: Fetch real-time from GitHub (MVP approach)
- Option B: Store in database + sync with webhooks (production approach)
- **Decision**: Start with Option A for speed, migrate to Option B for scale

**Conversation Sync**:
- Option A: Migrate historical conversations (one-time)
- Option B: Forward all new conversations to database (ongoing)
- **Decision**: Do both - migrate existing + forward new
