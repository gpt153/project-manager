# Quick Decision Tree

**Fast reference for choosing the right command**

---

## User Says: "Fix this bug..."

```
Do you know what's causing it?
│
├─ No, it's mysterious
│  └─ /exp-piv-loop:rca "<symptom>"
│     [Deep investigation with 5 Whys]
│     [Output: RCA report with root cause]
│     └─ Then: /exp-piv-loop:fix-rca <rca-file>
│
└─ Yes, cause is obvious
   └─ /exp-piv-loop:fix-issue "<description>"
      [Quick fix with tests]
      [Creates PR automatically]
```

---

## User Says: "Add feature..."

```
Is this complex or simple?
│
├─ Complex / unclear requirements
│  └─ Need to understand codebase first?
│     ├─ Yes → Start with /core_piv_loop:prime
│     └─ No → Start with /exp-piv-loop:plan
│        [Creates comprehensive plan]
│        └─ Then: /core_piv_loop:execute <plan>
│           [With Archon task tracking]
│
└─ Simple / straightforward
   └─ /exp-piv-loop:plan "<description>"
      [Quick planning]
      └─ /exp-piv-loop:implement <plan>
         [Autonomous execution]
```

---

## User Says: "@remote-agent" (GitHub)

```
Let router decide:
/exp-piv-loop:router <issue/comment text>
│
├─ Detects: "not working" / "broken"
│  └─ Routes to: /exp-piv-loop:rca
│
├─ Detects: "fix this" / explicit fix request
│  └─ Routes to: /exp-piv-loop:fix-issue
│
├─ Detects: "add X" / "implement Y"
│  └─ Routes to: /exp-piv-loop:plan
│
├─ Detects: "review" / PR context
│  └─ Routes to: /exp-piv-loop:review-pr
│
└─ Unclear intent
   └─ Ask user for clarification
```

---

## Before Committing Code

```
Are changes significant?
│
├─ Yes (feature, refactor, multiple files)
│  └─ /validation:code-review
│     [Technical review for bugs/quality]
│     └─ Issues found?
│        ├─ Yes → /validation:code-review-fix <review-file>
│        └─ No → /exp-piv-loop:commit <files>
│
└─ No (typo, small fix, single file)
   └─ /exp-piv-loop:commit <files>
      [Quick commit with conventional message]
```

---

## Before Merging PR

```
/exp-piv-loop:review-pr <number>
[Comprehensive review]
│
└─ All checks pass?
   ├─ Yes → /exp-piv-loop:merge-pr <number>
   └─ No → Request changes
      [Developer fixes]
      └─ Re-review when updated
```

---

## Starting New Project/Topic

```
Always start with context:
/core_piv_loop:prime
[Understand codebase deeply]
│
└─ For each feature in project:
   /core_piv_loop:plan-feature <description>
   [Create plan]
   └─ /core_piv_loop:execute <plan>
      [Implement with tracking]
```

---

## Emergency Production Issue

```
Production broken! Need fast fix!
│
└─ /exp-piv-loop:rca "<symptom>" quick
   [Quick mode for speed]
   └─ /exp-piv-loop:fix-rca <rca-file>
      [Minimal fix for stability]
      └─ /validation:code-review
         [Quick safety check]
         └─ /exp-piv-loop:create-pr
            [Fast-track review]
            └─ /exp-piv-loop:merge-pr <number>
               [Deploy immediately]
```

---

## "I want to..."

| Intent | Command | Notes |
|--------|---------|-------|
| Understand codebase | `/core_piv_loop:prime` | Start here for new projects |
| Plan a feature | `/core_piv_loop:plan-feature` | Comprehensive planning |
| Plan quickly | `/exp-piv-loop:plan` | Enhanced with web research |
| Implement a plan | `/core_piv_loop:execute` | With Archon tracking |
| Implement autonomously | `/exp-piv-loop:implement` | Adaptive, self-sufficient |
| Investigate bug | `/exp-piv-loop:rca` | Deep root cause analysis |
| Fix a bug | `/exp-piv-loop:fix-issue` | Quick bug fix |
| Fix from RCA | `/exp-piv-loop:fix-rca` | After investigation |
| Commit changes | `/exp-piv-loop:commit` | Conventional commits |
| Create PR | `/exp-piv-loop:create-pr` | From current branch |
| Review PR | `/exp-piv-loop:review-pr` | Comprehensive review |
| Merge PR | `/exp-piv-loop:merge-pr` | Safe merge |
| Review code quality | `/validation:code-review` | Pre-commit review |
| Fix review issues | `/validation:code-review-fix` | Systematic fixes |
| Full validation | `/validation:validate` | End-to-end testing |
| Create PRD | `/exp-piv-loop:prd` | Problem-focused spec |
| Work in parallel | `/exp-piv-loop:worktree` | Isolated environments |
| Clean up worktree | `/exp-piv-loop:worktree-cleanup` | After merge |
| Add changelog entry | `/exp-piv-loop:changelog-entry` | Track changes |
| Create release | `/exp-piv-loop:release` | Version management |
| Route automatically | `/exp-piv-loop:router` | GitHub @mentions |

---

## Complexity Decision Matrix

| Task Type | Complexity | Recommended Workflow |
|-----------|-----------|---------------------|
| Bug fix | Known cause | `/fix-issue` |
| Bug fix | Unknown cause | `/rca` → `/fix-rca` |
| Bug fix | Production critical | `/rca quick` → `/fix-rca` (fast mode) |
| Feature | Trivial (< 10 lines) | `/plan` → `/implement` |
| Feature | Simple (< 100 lines) | `/plan` → `/implement` |
| Feature | Medium (< 500 lines) | `/prime` → `/plan-feature` → `/execute` |
| Feature | Complex (500+ lines) | `/prime` → `/prd` → `/plan-feature` → `/execute` |
| Feature | Exploratory | `/prd` → [discuss] → `/plan` → `/execute` |
| Refactor | Small (1-2 files) | `/plan` → `/implement` |
| Refactor | Large (3+ files) | `/prime` → `/plan` → `/execute` |
| Refactor | Architectural | `/prime` → `/prd` → `/plan` → `/execute` |

---

## Platform-Specific Workflows

### Telegram Topics

```
New topic started
│
└─ /new-topic <name>
   [Creates project workspace]
   └─ /core_piv_loop:prime
      [Load context for this project]
      └─ Continue with feature development
```

### GitHub Issues

```
Issue created + @remote-agent mentioned
│
└─ Webhook triggers
   └─ /exp-piv-loop:router
      [Auto-routes based on intent]
      [Posts responses as issue comments]
```

### GitHub Pull Requests

```
PR opened or @remote-agent mentioned in PR
│
└─ /exp-piv-loop:review-pr <number>
   [Reviews code, runs validation]
   [Posts review as PR comment]
```

---

## Quick Reference: When to Use What

### Use `/core_piv_loop:*` when:
- ✅ Starting new project or topic
- ✅ Need comprehensive planning
- ✅ Want Archon task tracking
- ✅ Learning unfamiliar codebase
- ✅ Complex features with many unknowns

### Use `/exp-piv-loop:*` when:
- ✅ Quick iterations
- ✅ Autonomous execution preferred
- ✅ Enhanced web research needed
- ✅ GitHub automation (router, review-pr)
- ✅ Git operations (commit, create-pr, merge-pr)

### Use `/validation:*` when:
- ✅ Quality assurance needed
- ✅ Pre-commit code review
- ✅ End-to-end testing
- ✅ Process improvement (system-review)

---

**Next**: Read `04-subagent-patterns.md` for using Task tool and specialized agents.
