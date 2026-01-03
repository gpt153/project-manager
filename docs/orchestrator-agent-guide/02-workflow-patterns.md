# Workflow Patterns & Best Practices

**Common workflows, decision trees, and practical guidance for Remote Coding Agent**

---

## Table of Contents

- [Standard Feature Development](#standard-feature-development)
- [Bug Investigation & Fix](#bug-investigation--fix)
- [GitHub Issue Workflows](#github-issue-workflows)
- [Code Review & Quality](#code-review--quality)
- [Release Management](#release-management)
- [Parallel Development](#parallel-development)
- [Emergency Hotfix](#emergency-hotfix)
- [Refactoring Workflows](#refactoring-workflows)

---

## Standard Feature Development

### Pattern: Full PIV Loop (Recommended)

**Use when**: Developing non-trivial features with clear requirements

```
1. /core_piv_loop:prime
   ↓ Understand codebase deeply
   
2. /core_piv_loop:plan-feature <description>
   ↓ Create comprehensive plan
   
3. /core_piv_loop:execute <plan-file>
   ↓ Implement with Archon tracking
   
4. /validation:code-review
   ↓ Quality check
   
5. /validation:code-review-fix (if needed)
   ↓ Fix any issues
   
6. /exp-piv-loop:create-pr
   ↓ Ready for review
```

**Why this workflow?**
- **Prime** ensures you understand the codebase
- **Plan** creates a blueprint for success
- **Execute** with Archon provides task tracking
- **Code Review** catches issues early
- **PR** formalizes the change

**Example Scenario**:
```
User: "Add Discord adapter to support multi-platform messaging"

Orchestrator:
1. /core_piv_loop:prime
   [Loads SCAR codebase context, identifies adapter patterns]

2. /core_piv_loop:plan-feature Add Discord adapter following IPlatformAdapter interface
   [Creates .agents/plans/discord-adapter.md with step-by-step guide]

3. /core_piv_loop:execute .agents/plans/discord-adapter.md
   [Implements adapter, tests, registers in factory]

4. /validation:code-review
   [Checks for security issues, performance, code quality]

5. /exp-piv-loop:create-pr
   [Creates PR with comprehensive description]
```

---

### Pattern: Quick Feature (Lightweight)

**Use when**: Simple features, clear patterns exist, low risk

```
1. /exp-piv-loop:plan <description>
   ↓ Quick planning with web research
   
2. /exp-piv-loop:implement <plan-file>
   ↓ Autonomous implementation
   
3. /exp-piv-loop:commit <files>
   ↓ Quick commit
   
4. /exp-piv-loop:create-pr
   ↓ Create PR
```

**Why this workflow?**
- **Faster** than full PIV loop
- **Autonomous** implementation adapts to issues
- **Good for** small features, bug fixes, refactors

**Example Scenario**:
```
User: "Add markdown support to Telegram messages"

Orchestrator:
1. /exp-piv-loop:plan Add Telegram markdown formatting using telegram-markdown library
   [Creates quick plan with pattern examples]

2. /exp-piv-loop:implement .agents/plans/telegram-markdown.md
   [Implements, tests, adapts if issues arise]

3. /exp-piv-loop:commit "telegram adapter and tests"
   [Creates conventional commit]

4. /exp-piv-loop:create-pr
   [Opens PR for review]
```

---

### Pattern: Exploratory Development

**Use when**: Requirements unclear, exploring solutions, proof-of-concept

```
1. /core_piv_loop:prime
   ↓ Load context
   
2. /exp-piv-loop:prd <topic>
   ↓ Create problem-focused PRD
   
3. [Discuss PRD with user]
   ↓ Align on approach
   
4. /core_piv_loop:plan-feature <refined description>
   ↓ Plan with clarity
   
5. /core_piv_loop:execute <plan>
   ↓ Implement
```

**Why this workflow?**
- **PRD** clarifies problem before solution
- **User alignment** prevents wasted work
- **Better planning** with clear requirements

---

## Bug Investigation & Fix

### Pattern: Deep RCA (Unknown Root Cause)

**Use when**: Bug is mysterious, cause unknown, symptoms misleading

```
1. /exp-piv-loop:rca "<symptom description>"
   ↓ Deep investigation using 5 Whys
   
2. [Review RCA report]
   ↓ Understand root cause
   
3. /exp-piv-loop:fix-rca <rca-file>
   ↓ Implement fix
   
4. /validation:code-review
   ↓ Ensure fix doesn't introduce issues
   
5. /exp-piv-loop:commit <files>
   ↓ Commit fix
   
6. /exp-piv-loop:create-pr
   ↓ PR with RCA context
```

**RCA Evidence Requirements**:
- ✅ File:line references with code snippets
- ✅ Command output you actually ran
- ✅ Tests that prove the behavior
- ❌ NO speculation without proof

**Example Scenario**:
```
User: "GitHub webhooks aren't being received after deployment"

Orchestrator:
1. /exp-piv-loop:rca "GitHub webhooks not triggering after deployment"
   
   WHY 1: Why aren't webhooks received?
   → Because webhook requests return 404
   → Evidence: ngrok inspector shows 404 responses

   WHY 2: Why does webhook endpoint return 404?
   → Because route isn't registered in Express
   → Evidence: src/index.ts:45 - webhook routes commented out

   WHY 3: Why were routes commented out?
   → Because of merge conflict resolution
   → Evidence: git blame shows conflict markers in commit abc123

   ROOT CAUSE: Webhook routes accidentally removed during merge conflict
   
2. /exp-piv-loop:fix-rca .agents/rca/github-webhook-404.md
   [Uncomments routes, adds test for route registration]

3. /exp-piv-loop:create-pr
   [PR links to RCA, explains fix]
```

---

### Pattern: Quick Fix (Known Cause)

**Use when**: Bug is straightforward, cause is obvious

```
1. /exp-piv-loop:fix-issue "<bug description>"
   ↓ Lightweight investigation + fix
   
2. /exp-piv-loop:commit <files>
   ↓ Commit
   
3. /exp-piv-loop:create-pr
   ↓ PR
```

**When to use vs RCA?**
- **fix-issue**: "The typo in validation.md breaks markdown rendering"
- **rca**: "Validation command fails but I don't know why"

---

## GitHub Issue Workflows

### Pattern: Auto-Routed GitHub Issue

**Use when**: User mentions @remote-agent on GitHub issue

```
GitHub Webhook:
@remote-agent mentioned on issue #42

↓

/exp-piv-loop:router <issue body + comment>
   ↓ Analyzes intent
   
Router Decision Tree:
   If "not working" / "broken" → /rca
   If "fix this" → /fix-issue
   If "add X" / "implement Y" → /plan
   If "review" → /review-pr
   
Selected Workflow Executes Silently
```

**Router Behavior**:
- **Silent execution**: Don't explain routing decision
- **Context-aware**: Considers issue title, labels, conversation
- **Fallback**: If unclear, asks user for clarification

**Example**:
```
GitHub Issue #42: "Login button not working on mobile"
User comment: "@remote-agent please investigate"

Router logic:
- Detects "not working" → Routes to /rca
- Executes deep investigation
- Posts RCA findings as issue comment
- Suggests /fix-rca to implement solution
```

---

### Pattern: Feature Request from GitHub

**Use when**: GitHub issue describes a new feature request

```
Issue created: "Add rate limiting to API endpoints"
@remote-agent mentioned

↓

1. /router → detects feature request → /plan
   
2. /core_piv_loop:plan-feature <extracted from issue>
   [Creates comprehensive plan]
   [Posts plan summary as issue comment]
   
3. [User approves]
   
4. /core_piv_loop:execute <plan-file>
   [Implements feature]
   [Posts progress updates to issue]
   
5. /exp-piv-loop:create-pr
   [Creates PR, links to issue: "Fixes #42"]
   [Comments on issue with PR link]
```

---

## Code Review & Quality

### Pattern: Pre-Commit Review

**Use when**: Before committing changes, quality check

```
[Implement feature]
↓

1. /validation:code-review
   ↓ Technical review for bugs/quality
   
2. If issues found:
   /validation:code-review-fix <review-file>
   ↓ Fix systematically
   
3. Re-run validation:
   npm run type-check
   npm run lint
   npm test
   ↓ Ensure green build
   
4. /exp-piv-loop:commit <files>
```

**Code Review Catches**:
- Logic errors (off-by-one, incorrect conditionals)
- Security issues (SQL injection, XSS, exposed secrets)
- Performance problems (N+1 queries, memory leaks)
- Code quality (DRY violations, complexity, naming)
- Standard violations (linting, typing, conventions)

---

### Pattern: PR Review Workflow

**Use when**: Reviewing pull requests before merge

```
PR #42 opened: "Add Discord adapter"

↓

1. /exp-piv-loop:review-pr 42
   ↓ Comprehensive review
   [Fetches PR diff]
   [Reads all changed files completely]
   [Analyzes for issues]
   [Runs validation commands]
   [Posts review comment]
   
2. If issues found:
   [Developer fixes issues]
   [Updates PR]
   
3. /exp-piv-loop:review-pr 42
   ↓ Re-review
   
4. When approved:
   /exp-piv-loop:merge-pr 42
   [Ensures up-to-date with main]
   [Merges safely]
```

---

## Release Management

### Pattern: Standard Release Process

**Use when**: Ready to create a new version

```
[Features completed on main branch]

↓

1. /exp-piv-loop:changelog-entry "Added: Discord adapter"
   /exp-piv-loop:changelog-entry "Fixed: Telegram markdown rendering"
   [Add all unreleased changes]
   
2. /exp-piv-loop:changelog-release 1.2.0
   [Promotes [Unreleased] to [1.2.0]]
   [Updates release date]
   
3. /exp-piv-loop:release 1.2.0
   [Creates git tag]
   [Generates release notes from changelog]
   [Creates GitHub Release]
   [Publishes]
   
4. /validation:validate <ngrok-url>
   [Full end-to-end validation]
   [Verify release works]
```

**Keep a Changelog Format**:
```markdown
## [Unreleased]

## [1.2.0] - 2025-12-26
### Added
- Discord adapter for multi-platform support
- Rate limiting for API endpoints

### Fixed
- Telegram markdown rendering with code blocks
- GitHub webhook signature verification

### Changed
- Updated Claude SDK to version 0.1.57
```

---

## Parallel Development

### Pattern: Worktree-Based Parallel Work

**Use when**: Working on multiple features simultaneously

```
Project: feature/auth (current)

User: "I need to work on feature/notifications too"

↓

1. /exp-piv-loop:worktree feature/notifications
   [Creates isolated worktree]
   [Separate working directory]
   
2. cd <worktree-path>
   [Work on notifications feature]
   
3. [Complete notifications feature]
   /exp-piv-loop:create-pr
   [PR for notifications]
   
4. /exp-piv-loop:merge-pr <notifications-PR>
   [Merge when ready]
   
5. /exp-piv-loop:worktree-cleanup <worktree-path> --delete-branch
   [Clean up notifications worktree]
   
6. cd <original-project>
   [Continue auth feature]
```

**Worktree Benefits**:
- No need to stash/commit before switching
- Run tests on multiple branches simultaneously
- Safe parallel development
- Preserve work-in-progress

---

## Emergency Hotfix

### Pattern: Critical Production Bug

**Use when**: Production is broken, need immediate fix

```
Production Alert: "Payment processing failing"

↓

1. /exp-piv-loop:rca "Payment processing returns 500 error"
   [Quick mode for speed]
   [Identify root cause fast]
   
2. /exp-piv-loop:fix-rca <rca-file>
   [Implement minimal fix]
   [Focus on stability, not perfection]
   
3. /validation:code-review
   [Quick security/safety check]
   
4. /exp-piv-loop:commit "hotfix payment processing"
   
5. /exp-piv-loop:create-pr
   [Fast-track review]
   
6. /exp-piv-loop:merge-pr <hotfix-PR>
   [Merge immediately after review]
   
7. Deploy to production
   
8. [Follow up with proper solution]
```

**Hotfix Principles**:
- **Speed over perfection**: Fix now, refactor later
- **Minimal changes**: Touch only what's necessary
- **Test carefully**: Even urgent fixes need validation
- **Document**: RCA explains what went wrong

---

## Refactoring Workflows

### Pattern: Safe Refactoring

**Use when**: Improving code without changing behavior

```
User: "Refactor authentication module for better testability"

↓

1. /core_piv_loop:prime
   [Understand current architecture]
   
2. /exp-piv-loop:plan Refactor authentication module
   [Plan refactoring approach]
   [Identify what stays, what changes]
   [Design new structure]
   
3. [Write tests for current behavior FIRST]
   npm test -- src/auth
   [Baseline: tests pass with current code]
   
4. /exp-piv-loop:implement <refactor-plan>
   [Refactor in small steps]
   [Run tests after each step]
   [Ensure behavior unchanged]
   
5. npm test
   [All tests still pass]
   
6. /validation:code-review
   [Check quality improved]
   
7. /exp-piv-loop:create-pr
   [PR emphasizes "no behavior change"]
```

**Refactoring Safety**:
- ✅ Tests BEFORE refactoring (baseline)
- ✅ Small incremental changes
- ✅ Tests AFTER each change (regression check)
- ✅ Verify no behavior change
- ❌ Don't refactor without tests
- ❌ Don't mix refactoring with feature changes

---

## Decision Trees

### "Should I use prime?"

```
Are you familiar with this codebase?
├─ No → YES, use /core_piv_loop:prime
└─ Yes
   └─ Have you worked on it recently (last 2 weeks)?
      ├─ No → YES, use /core_piv_loop:prime (refresh context)
      └─ Yes
         └─ Are you about to plan a complex feature?
            ├─ Yes → YES, use /core_piv_loop:prime
            └─ No → Skip prime, use lightweight workflow
```

### "Which planning command?"

```
Is this a complex feature with unclear requirements?
├─ Yes
│  └─ Need external research and web docs?
│     ├─ Yes → /exp-piv-loop:plan (enhanced research)
│     └─ No → /core_piv_loop:plan-feature (codebase-focused)
└─ No
   └─ Is it a straightforward implementation with clear patterns?
      ├─ Yes → /exp-piv-loop:plan (quick planning)
      └─ No → Maybe skip planning, go straight to /implement
```

### "Which execute command?"

```
Do you have a plan file?
├─ No → Create plan first
└─ Yes
   └─ Do you want Archon task tracking?
      ├─ Yes → /core_piv_loop:execute (full tracking)
      └─ No → /exp-piv-loop:implement (autonomous, adaptive)
```

### "Bug fix: RCA or quick fix?"

```
Do you know the root cause?
├─ No → /exp-piv-loop:rca (investigate first)
└─ Yes
   └─ Is it a simple fix (typo, obvious bug)?
      ├─ Yes → /exp-piv-loop:fix-issue (quick fix)
      └─ No → /exp-piv-loop:rca (verify your understanding)
```

---

## Best Practices

### Always Start With Context

**❌ Wrong**:
```
User: "Add feature X"
Orchestrator: [Immediately implements without understanding codebase]
```

**✅ Right**:
```
User: "Add feature X"
Orchestrator: /core_piv_loop:prime
[Understands architecture, patterns, conventions]
Then: /core_piv_loop:plan-feature X
[Creates plan matching codebase style]
```

### Validate Early and Often

**❌ Wrong**:
```
[Implement entire feature]
[Commit everything]
[Push]
[Discover it doesn't work]
```

**✅ Right**:
```
[Implement task 1]
npm test -- relevant-test
[Task 1 validated ✅]

[Implement task 2]
npm test -- relevant-test
[Task 2 validated ✅]

... continue ...
```

### Use Sessions Wisely

**Key Insight**: Plan→Execute creates NEW SESSION

**Why?**
- **Plan session**: Research-focused, builds context
- **Execute session**: Implementation-focused, follows plan

**Impact**:
- Execute doesn't "remember" planning discussions
- Plan is the ONLY contract between sessions
- Make plans COMPLETE and SELF-CONTAINED

### Match Workflow to Complexity

| Complexity | Workflow | Reason |
|------------|----------|--------|
| Trivial (typo fix) | Quick fix, no plan | Overhead not worth it |
| Simple (add logging) | /plan + /implement | Light planning sufficient |
| Medium (new feature) | Full PIV loop | Need comprehensive planning |
| Complex (architecture change) | Full PIV + PRD | Requirements clarity critical |
| Unknown (exploratory) | PRD first | Define problem before solution |

---

**Next**: Read `03-decision-tree.md` for quick decision-making guidance.
