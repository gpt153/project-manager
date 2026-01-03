# Complete Command Reference

**Comprehensive documentation of all Remote Coding Agent commands**

---

## Table of Contents

- [Core PIV Loop Commands](#core-piv-loop-commands)
- [Experimental PIV Loop Commands](#experimental-piv-loop-commands)
- [Validation Commands](#validation-commands)
- [GitHub-Specific Commands](#github-specific-commands)
- [General Purpose Commands](#general-purpose-commands)

---

## Core PIV Loop Commands

These are the foundational commands for the PIV (Prime → Investigate → Validate) workflow.

### `/core_piv_loop:prime`

**Purpose**: Load comprehensive project context by analyzing structure, documentation, and key files.

**When to Use**:
- Starting work on a new codebase
- After being away from a project for a while
- Before planning a complex feature
- When you need deep understanding of architecture

**Process**:
1. List all tracked files (`git ls-files`)
2. Show directory structure (`tree`)
3. Read core documentation (PRD, CLAUDE.md, README)
4. Identify and read key files (entry points, configs, schemas)
5. Check recent git activity and current state

**Outputs**:
- Project overview (purpose, tech stack, current state)
- Architecture summary (patterns, directory structure)
- Tech stack catalog (languages, frameworks, tools)
- Core principles (code style, conventions, testing)
- Current state assessment (active branch, recent changes)

**Example**:
```
/core_piv_loop:prime
```

**Tips**:
- Run this command at the START of every new topic/issue
- Use output to inform planning decisions
- Save output for reference during implementation

**Archon Integration**:
- If Archon MCP is enabled, prime will check indexed documentation FIRST
- Lists available sources and searches for project-related docs
- Reports indexed vs missing dependencies
- Recommends docs to crawl for better AI assistance

---

### `/core_piv_loop:plan-feature`

**Purpose**: Transform a feature request into a comprehensive implementation plan through systematic codebase analysis, external research, and strategic planning.

**Arguments**: `<feature description>`

**When to Use**:
- Before implementing any non-trivial feature
- When requirements are clear but approach is undefined
- When you need to align on implementation strategy
- Before allocating significant development time

**Core Principle**: **Context is King**. The plan must contain ALL information needed for implementation - patterns, documentation, validation commands - so execution succeeds on first attempt.

**Planning Phases**:

1. **Feature Understanding**
   - Extract core problem being solved
   - Identify user value and business impact
   - Determine feature type (New/Enhancement/Refactor/Bug Fix)
   - Assess complexity (Low/Medium/High)
   - Map affected systems

2. **Codebase Intelligence Gathering**
   - Project structure analysis (languages, frameworks, directories)
   - Pattern recognition (search for similar implementations)
   - Dependency analysis (libraries, versions, integrations)
   - Testing patterns (framework, coverage, standards)
   - Integration points (files to modify, new files to create)

3. **External Research & Documentation**
   - Latest library versions and best practices
   - Official documentation with specific section anchors
   - Implementation examples and tutorials
   - Common gotchas and known issues
   - Breaking changes and migration guides
   - **Archon RAG** (if available): Search indexed docs for relevant patterns

4. **Deep Strategic Thinking**
   - Architectural fit assessment
   - Critical dependencies and order of operations
   - Edge cases, race conditions, error scenarios
   - Testing strategy
   - Performance implications
   - Security considerations
   - Maintainability assessment

5. **Plan Structure Generation**
   - Feature metadata (type, complexity, affected systems)
   - Context references (codebase files with line numbers)
   - Relevant documentation links
   - Patterns to follow (with code examples)
   - Step-by-step implementation tasks
   - Testing strategy
   - Validation commands
   - Acceptance criteria

**Output Format**:
- **Filename**: `.agents/plans/{kebab-case-name}.md`
- **Location**: Created in `.agents/plans/` directory
- **Contents**: Comprehensive plan following template structure

**Quality Criteria**:
- ✅ Context completeness (all patterns documented)
- ✅ Implementation ready (another dev could execute without context)
- ✅ Pattern consistency (follows existing codebase conventions)
- ✅ Information density (specific, actionable, no generic references)

**Example**:
```
/core_piv_loop:plan-feature Add user authentication with JWT tokens
```

**Success Metrics**:
- **One-Pass Implementation**: Execution agent completes without additional research
- **Validation Complete**: Every task has executable validation command
- **Context Rich**: Passes "No Prior Knowledge Test"
- **Confidence Score**: 8/10+ that execution will succeed first attempt

**Tips**:
- Be specific in feature description - vague requests yield vague plans
- Review plan before executing - it's your implementation blueprint
- Update plan if you discover issues during execution
- Plans are versioned with Git - track evolution over time

---

### `/core_piv_loop:execute`

**Purpose**: Execute a development plan with full Archon task management integration, ensuring systematic implementation and progress tracking.

**Arguments**: `<plan-file-path>`

**When to Use**:
- After creating a comprehensive plan with `/plan-feature`
- When you have a written implementation plan ready
- When you want task-by-task tracking with Archon

**Core Requirement**: **Continuous Archon usage throughout ENTIRE execution**. Every task from plan must be tracked in Archon from creation to completion.

**Execution Steps**:

1. **Read and Parse the Plan**
   - Load plan file from specified path
   - Extract tasks, context, validation strategy
   - Understand integration points and patterns

2. **Project Setup in Archon**
   - Check if project ID exists in CLAUDE.md
   - If no project exists, create new one in Archon
   - Store project ID for tracking throughout execution

3. **Create All Tasks in Archon**
   - Create task for EACH item in plan upfront
   - Set initial status as "todo"
   - Include detailed descriptions from plan
   - Maintain task order/priority

4. **Codebase Analysis**
   - Analyze ALL integration points mentioned in plan
   - Use Grep and Glob to understand existing patterns
   - Read all referenced files
   - Build comprehensive understanding before coding

5. **Implementation Cycle** (for each task):
   - **Start**: Move task to "doing" in Archon
   - **Implement**: Execute based on plan, patterns, best practices
   - **Complete**: Move task to "review" status
   - **Proceed**: Only ONE task in "doing" at a time

6. **Validation Phase**
   - Launch validator agent using Task tool
   - Validator creates simple, effective unit tests
   - Runs tests and reports results
   - Check integration between components
   - Ensure acceptance criteria met

7. **Finalize Tasks in Archon**
   - Move tasks with test coverage to "done"
   - Leave tasks without coverage in "review"
   - Document why tasks remain in review

8. **Final Report**
   - Total tasks created and completed
   - Tasks remaining in review and why
   - Test coverage achieved
   - Key features implemented
   - Issues encountered and resolutions

**Example**:
```
/core_piv_loop:execute .agents/plans/add-user-authentication.md
```

**Workflow Rules**:
1. **NEVER** skip Archon task management
2. **ALWAYS** create all tasks upfront before implementation
3. **MAINTAIN** one task in "doing" at a time
4. **VALIDATE** all work before marking as "done"
5. **TRACK** progress continuously through Archon
6. **ANALYZE** codebase thoroughly before implementation
7. **TEST** everything before final completion

**Error Handling**:
- If Archon operations fail, retry
- If persistent failures, document but continue tracking locally
- Never abandon Archon integration - find workarounds

**Success Indicators**:
- All planned tasks created in Archon
- Tasks transition through todo → doing → review → done
- Validation passes for all tasks
- Final report shows complete implementation

---

## Experimental PIV Loop Commands

Enhanced workflow commands with more granularity and specialized use cases.

### `/exp-piv-loop:plan`

**Purpose**: Deep implementation planning that analyzes codebase, mirrors patterns, and produces step-by-step guide.

**Arguments**: `<feature description or PRD path>`

**When to Use**:
- Similar to `/core_piv_loop:plan-feature` but with enhanced web research
- When you need external documentation lookup
- When you want pattern-mirroring emphasis
- For complex features requiring architectural decisions

**Key Differences from Core Plan**:
- **Enhanced web search** for latest docs and best practices
- **Pattern mirroring** with actual code snippets from codebase
- **More detailed external research** section
- **Explicit gotchas** documentation

**Phases**:

1. **Understand the Request**
   - Parse input (PRD file, feature sentence, GitHub issue)
   - Quick feasibility check
   - Identify blockers early

2. **External Research (REQUIRED)**
   - Web search for official documentation
   - Latest version info and breaking changes
   - Common implementation patterns
   - Known gotchas and issues
   - Similar implementations in open source

3. **Codebase Research (CRITICAL)**
   - Find similar implementations
   - Identify patterns to mirror (with code snippets)
   - Identify files to modify
   - Document anti-patterns to avoid

4. **Plan Generation**
   - Detailed task breakdown
   - Pattern references with file:line numbers
   - Validation commands per task
   - Complete testing strategy

**Output**: `.agents/plans/{name}.md` with comprehensive step-by-step guide

**Example**:
```
/exp-piv-loop:plan Add Discord adapter for multi-platform support
```

**Golden Rule**: Match codebase style so perfectly that changes are invisible except for new functionality.

---

### `/exp-piv-loop:implement`

**Purpose**: Execute an implementation plan autonomously and adaptively, end-to-end.

**Arguments**: `<path/to/plan.md>`

**When to Use**:
- After creating plan with `/exp-piv-loop:plan`
- When you want autonomous execution with adaptation
- For production-ready implementation workflows

**Steps**:

0. **Branch Setup**
   - Check current branch
   - Create feature branch if needed: `feature/[name]`
   - Checkout existing feature branch if present

1. **Read the Plan**
   - Locate all sections: Summary, Research, Patterns, Files, Tasks, Validation

2. **Validate Current State**
   - Check pattern files still exist and unchanged
   - Verify no git conflicts
   - Confirm dependencies available
   - Adapt if outdated

3. **Execute Tasks**
   - Follow plan's Tasks section top-to-bottom
   - For each task: Read Mirror reference → Make change → Verify → Continue
   - If stuck: Research, adapt, continue (don't stop)

4. **Run Validation**
   - Execute plan's Validation Strategy section
   - Write tests specified in plan
   - Execute manual validation steps
   - Test edge cases
   - Run regression checks

5. **Write Implementation Report**
   - Create report at `.agents/implementation-reports/[branch-name]-implementation-report.md`
   - Document what was built, how it works, what was tested

**Golden Rule**: **Finish the job**. Adapt when needed. Human decides merge/rollback after.

**Example**:
```
/exp-piv-loop:implement .agents/plans/discord-adapter.md
```

**Key Trait**: **Autonomous and adaptive** - overcomes blockers, researches when needed, completes end-to-end.

---

### `/exp-piv-loop:router`

**Purpose**: Route natural language requests to the appropriate workflow automatically.

**Arguments**: `<natural language request>`

**When to Use**:
- When user mentions @remote-agent with vague request
- When you need to determine workflow from intent
- GitHub webhooks with @mention
- Automatic workflow selection

**Routing Logic**:

**Investigation & Debugging** → `/rca`
- User reports "not working", "broken", "failing"
- User asks "why is X happening?"
- Error messages or stack traces provided

**Bug Fixes** → `/fix-issue`
- User asks to "fix" something
- After RCA, user wants fix implemented
- Bug clearly described with reproduction steps

**Code Review** → `/review-pr`
- User asks to "review" code/PR/changes
- User mentions PR number
- Event is on pull request (not issue)

**Feature Development** → `/plan`
- User requests new feature
- User asks "how should we implement X?"
- Change requires architectural decisions
- Scope unclear and needs planning

**Pull Request Creation** → `/create-pr`
- User says "create PR", "open PR", "submit PR"
- Work is complete and ready for review

**Decision Process**:
1. Read user's request carefully
2. Consider context (issue or PR? what's the title?)
3. Match to most appropriate workflow
4. If unclear between RCA and fix-issue, prefer RCA first
5. If no match, ask for clarification

**Execution**: Once workflow determined, execute it silently (don't explain routing decision).

**Example**:
```
User: "The login button isn't working on mobile"
Router: [Executes /rca silently]

User: "Add dark mode toggle to settings"
Router: [Executes /plan silently]
```

---

### `/exp-piv-loop:rca`

**Purpose**: Deep root cause analysis - finds the ACTUAL cause, not just symptoms.

**Arguments**: `<issue|error|stacktrace> [quick]`
**Mode**: blank = deep analysis, "quick" = surface scan

**When to Use**:
- When something is broken and you don't know why
- When error messages are vague or misleading
- When symptoms don't reveal the actual problem
- Before fixing bugs (understand FIRST, fix SECOND)

**The Test**: Ask yourself "If I changed THIS, would the issue be prevented?" If answer is "maybe" or "partially", keep digging.

**Investigation Protocol**:

1. **Classify and Parse Input**
   - **Type A - Raw Symptom**: Need to investigate, form hypotheses, test
   - **Type B - Pre-Diagnosed**: Need to validate and expand
   - Parse stack trace, error message, or vague description
   - Restate symptom in one sentence

2. **Form Hypotheses**
   - Generate 2-4 hypotheses about causes
   - For each: What must be true? What evidence confirms/refutes?
   - Rank by likelihood, start with most probable

3. **The 5 Whys**
   ```
   WHY 1: Why does [symptom] occur?
   → Because [intermediate cause A]
   → Evidence: [file:line with code snippet]

   WHY 2: Why does [intermediate cause A] happen?
   → Because [intermediate cause B]
   → Evidence: [command output or test result]

   ... continue until ROOT CAUSE ...

   WHY 5: Why does [intermediate cause D] happen?
   → Because [ROOT CAUSE - specific code/config/logic]
   → Evidence: [exact file:line reference]
   ```

   **Rules**:
   - May need more or fewer than 5 levels
   - Every "because" MUST have evidence (no speculation)
   - If evidence refutes, pivot to next hypothesis
   - If dead end, backtrack and try alternatives

4. **Validate the Root Cause**
   - **Causation test**: Does root cause logically lead to symptom?
   - **Necessity test**: If root cause didn't exist, would symptom still occur?
   - **Sufficiency test**: Is root cause alone enough, or are there co-factors?

5. **Write RCA Report**
   - Filename: `.agents/rca/{kebab-case-issue}.md`
   - Include: Problem statement, investigation chain, root cause, evidence, fix recommendations

**Evidence Standards (STRICT)**:
- ✅ VALID: `file.ts:123` with actual code snippet
- ✅ VALID: Command output you actually ran
- ✅ VALID: Test you executed
- ❌ INVALID: "likely includes...", "probably because..."
- ❌ INVALID: Logical deduction without code proof
- ❌ INVALID: General technology explanations

**Example**:
```
/exp-piv-loop:rca "GitHub webhooks not triggering after deployment"
```

**Output**: `.agents/rca/github-webhook-failure.md` with complete investigation chain and root cause

---

### `/exp-piv-loop:fix-rca`

**Purpose**: Implement a fix based on an RCA report - validates, implements, and verifies.

**Arguments**: `<path/to/rca-report.md>`

**When to Use**:
- After completing RCA with `/rca`
- When root cause is clearly identified
- When you're ready to implement the fix

**Process**:
1. Read RCA report
2. Extract root cause and recommended fix
3. Validate fix approach
4. Implement fix following codebase patterns
5. Write tests to prevent regression
6. Verify fix resolves original symptom
7. Document in implementation report

**Example**:
```
/exp-piv-loop:fix-rca .agents/rca/github-webhook-failure.md
```

---

### `/exp-piv-loop:fix-issue`

**Purpose**: Fix a bug end-to-end - investigate, fix, test, and create PR.

**When to Use**:
- User explicitly asks to "fix" something
- Bug is clearly described with reproduction steps
- Issue is straightforward (not requiring deep RCA)

**Combined Workflow**:
1. Investigate issue (lightweight RCA)
2. Identify root cause
3. Implement fix
4. Write tests
5. Validate fix
6. Create pull request

**Example**:
```
/exp-piv-loop:fix-issue "Telegram markdown formatting breaks with code blocks"
```

---

### `/exp-piv-loop:commit`

**Purpose**: Quick commit with natural language file targeting.

**Arguments**: `<files or description>`

**When to Use**:
- After completing implementation
- When you want conventional commit messages
- Quick commits without manual git commands

**Features**:
- Natural language file selection
- Conventional commit message format
- Remote Coding Agent attribution
- Co-Authored-By: Claude

**Example**:
```
/exp-piv-loop:commit "adapter files and tests"
```

---

### `/exp-piv-loop:create-pr`

**Purpose**: Create a PR from current branch with unpushed commits.

**When to Use**:
- After completing feature on branch
- When ready for code review
- After all validations pass

**Process**:
1. Check current branch and commits
2. Analyze all commits for PR summary
3. Generate PR description (Summary, Changes, Validation)
4. Push branch if needed
5. Create PR with gh CLI
6. Link to plan file if exists

**Example**:
```
/exp-piv-loop:create-pr
```

**PR Template**:
```markdown
## Summary
- Brief overview of changes

## Changes
- List of modifications

## Validation
- Tests passing
- Lint passing
- Manual testing completed

🤖 Generated with Remote Coding Agent
```

---

### `/exp-piv-loop:review-pr`

**Purpose**: Comprehensive PR code review - checks diff, patterns, runs validation, comments on PR.

**Arguments**: `[PR number]`

**When to Use**:
- Before merging PRs
- When you need thorough code review
- For quality assurance before production

**Review Process**:
1. Fetch PR diff and metadata
2. Read all changed files completely (not just diff)
3. Analyze for: logic errors, security issues, performance problems, code quality
4. Check adherence to codebase standards
5. Run validation commands
6. Post review comment with findings

**Review Categories**:
- **CRITICAL**: Security issues, data loss risks
- **HIGH**: Logic errors, broken functionality
- **MEDIUM**: Performance issues, code quality
- **LOW**: Style inconsistencies, minor improvements

**Example**:
```
/exp-piv-loop:review-pr 42
```

---

### `/exp-piv-loop:merge-pr`

**Purpose**: Merge PR after ensuring it's up-to-date with main.

**Arguments**: `[PR number]`

**When to Use**:
- After PR review passes
- After all checks pass
- When ready to merge to main

**Safety Checks**:
1. Verify all status checks pass
2. Ensure PR is up-to-date with base branch
3. Confirm no conflicts
4. Merge with merge commit or squash

**Example**:
```
/exp-piv-loop:merge-pr 42
```

---

### `/exp-piv-loop:worktree`

**Purpose**: Create git worktrees for parallel branch development with validation.

**Arguments**: `<branch-name>`

**When to Use**:
- Working on multiple features simultaneously
- Need isolated development environments
- Want to preserve current work while exploring

**Git Worktree Benefits**:
- Separate working directories per branch
- No need to stash/commit before switching
- Run tests on multiple branches simultaneously
- Safe parallel development

**Example**:
```
/exp-piv-loop:worktree feature/dark-mode
```

---

### `/exp-piv-loop:worktree-cleanup`

**Purpose**: Clean up git worktrees after PR merge - removes directory, kills ports, optionally deletes branches.

**Arguments**: `<worktree-path> [--delete-branch]`

**When to Use**:
- After PR is merged
- When feature branch is no longer needed
- Cleaning up development environment

**Example**:
```
/exp-piv-loop:worktree-cleanup /path/to/worktree --delete-branch
```

---

### `/exp-piv-loop:prd`

**Purpose**: Lean PRD - problem-first, hypothesis-driven product spec.

**When to Use**:
- Before starting new features
- When requirements are unclear
- For stakeholder alignment
- As input to `/plan` command

**PRD Structure**:
- Problem statement
- User needs and pain points
- Proposed solution
- Success metrics
- Technical considerations
- Out of scope

**Example**:
```
/exp-piv-loop:prd "User authentication system"
```

---

### `/exp-piv-loop:changelog-entry`

**Purpose**: Add an entry to CHANGELOG.md [Unreleased] section.

**Arguments**: `<entry text>`

**When to Use**:
- After completing feature
- After fixing bug
- For tracking changes before release

**Format**: Follows Keep a Changelog standard
- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for removed features
- **Fixed** for bug fixes
- **Security** for vulnerability fixes

**Example**:
```
/exp-piv-loop:changelog-entry "Added: Discord adapter for multi-platform support"
```

---

### `/exp-piv-loop:changelog-release`

**Purpose**: Promote [Unreleased] changelog entries to a new version.

**Arguments**: `<version>`

**When to Use**:
- Before creating release
- When ready to tag version
- For version history management

**Example**:
```
/exp-piv-loop:changelog-release 1.2.0
```

---

### `/exp-piv-loop:release`

**Purpose**: Create a GitHub Release with git tag and release notes.

**Arguments**: `<version>`

**When to Use**:
- After changelog release
- When ready to publish release
- For version distribution

**Process**:
1. Create git tag
2. Generate release notes from changelog
3. Create GitHub release
4. Publish

**Example**:
```
/exp-piv-loop:release 1.2.0
```

---

### `/exp-piv-loop:release-notes`

**Purpose**: Generate release notes from commits or changelog for GitHub Release.

**Arguments**: `<version>`

**When to Use**:
- Preparing release notes
- Summarizing changes for stakeholders
- Creating changelog from commits

**Example**:
```
/exp-piv-loop:release-notes 1.2.0
```

---

## Validation Commands

Quality assurance and testing workflows.

### `/validation:validate`

**Purpose**: Run comprehensive end-to-end validation with ngrok URL for GitHub webhooks.

**Arguments**: `<ngrok-url>`

**When to Use**:
- Before deploying to production
- After major changes
- For full system integration testing
- Continuous integration validation

**Validation Phases**:

1. **Foundation Validation**
   - Type checking (`npm run type-check`)
   - Linting (`npm run lint`)
   - Unit tests (`npm test`)
   - Build (`npm run build`)

2. **Test Repository Setup**
   - Clean workspace and database
   - Create minimal Next.js app
   - Push to private GitHub repository
   - Configure GitHub webhook with ngrok URL

3. **Docker Container Validation**
   - Rebuild and start container
   - Verify startup logs
   - Health check endpoints

4. **Test Adapter Validation**
   - Send clone command via HTTP API
   - Send implementation request
   - Verify responses and logs

5. **Database Validation**
   - Check codebase records
   - Check conversation records
   - Check session records

6. **GitHub Integration**
   - Create issue, add @remote-agent comment
   - Verify webhook processing
   - Check issue comment (batch mode)

7. **GitHub Pull Request Integration**
   - Find PR created by test adapter
   - Request PR review via @remote-agent
   - Verify PR review comment

8. **Concurrency Validation**
   - Send 3 concurrent requests
   - Check concurrency stats
   - Verify concurrent processing in logs

9. **Command Workflow Integration Test**
   - Copy commands to test repository
   - Test Prime command
   - Test Plan-Feature command
   - Test Execute command
   - Verify PR created

10. **Final Summary**
    - Collect all validation results
    - Generate comprehensive report
    - Identify any issues

**Example**:
```
/validation:validate https://your-url.ngrok-free.dev
```

**Output**: Comprehensive validation report with ✅/❌ for each phase

---

### `/validation:code-review`

**Purpose**: Technical code review for quality and bugs that runs pre-commit.

**When to Use**:
- Before committing changes
- After implementing features
- For pre-merge quality checks
- Identifying technical debt

**Review Criteria**:

1. **Logic Errors**
   - Off-by-one errors
   - Incorrect conditionals
   - Missing error handling
   - Race conditions

2. **Security Issues**
   - SQL injection vulnerabilities
   - XSS vulnerabilities
   - Insecure data handling
   - Exposed secrets

3. **Performance Problems**
   - N+1 queries
   - Inefficient algorithms
   - Memory leaks
   - Unnecessary computations

4. **Code Quality**
   - DRY principle violations
   - Overly complex functions
   - Poor naming
   - Missing type hints

5. **Adherence to Standards**
   - Codebase conventions
   - Linting standards
   - Logging standards
   - Testing standards

**Process**:
1. Run `git status` and `git diff`
2. Read all changed files completely
3. Analyze for issues in each category
4. Verify issues are real (run tests, check types)
5. Generate report at `.agents/code-reviews/{name}.md`

**Output Format**:
```
severity: critical|high|medium|low
file: path/to/file.py
line: 42
issue: [one-line description]
detail: [explanation]
suggestion: [how to fix]
```

**Example**:
```
/validation:code-review
```

---

### `/validation:code-review-fix`

**Purpose**: Fix bugs found in manual/AI code review.

**Arguments**: `<path/to/code-review.md>`

**When to Use**:
- After running `/code-review`
- When code review identifies issues
- For systematic bug fixing

**Process**:
1. Read code review report
2. Prioritize issues by severity (CRITICAL → HIGH → MEDIUM → LOW)
3. Fix each issue systematically
4. Verify fix doesn't introduce new issues
5. Re-run validation

**Example**:
```
/validation:code-review-fix .agents/code-reviews/auth-review.md
```

---

### `/validation:system-review`

**Purpose**: Analyze implementation against plan for process improvements.

**When to Use**:
- After completing major features
- For retrospective analysis
- Improving development process
- Learning from successes and failures

**Analysis**:
1. Compare plan to actual implementation
2. Identify deviations and reasons
3. Assess what worked well
4. Identify process improvements
5. Generate recommendations

**Output**: `.agents/system-reviews/{name}.md`

**Example**:
```
/validation:system-review
```

---

### `/validation:execution-report`

**Purpose**: Generate implementation report for system review.

**When to Use**:
- After completing execute command
- For documentation of what was built
- Input to system review process

**Report Contents**:
- What was implemented
- How it was implemented
- Deviations from plan
- Challenges encountered
- Solutions applied
- Test coverage
- Validation results

**Example**:
```
/validation:execution-report
```

---

## GitHub-Specific Commands

Commands tailored for GitHub issue and PR workflows.

### `/github_bug_fix:rca`

**Purpose**: Root cause analysis for GitHub issues.

**Arguments**: (inherits from issue context)

**When to Use**:
- When GitHub issue describes a bug
- When @remote-agent is mentioned on issue
- For systematic bug investigation

**Same as `/exp-piv-loop:rca` but:**
- Automatically extracts issue context
- Posts RCA report as issue comment
- Links to RCA file in `.agents/rca/`

**Example**: (triggered via @remote-agent on GitHub issue)

---

### `/github_bug_fix:implement-fix`

**Purpose**: Implement fix from RCA document for GitHub issue.

**Arguments**: (inherits from RCA context)

**When to Use**:
- After completing RCA
- When root cause is identified
- Ready to implement fix

**Process**:
1. Read RCA document
2. Implement fix
3. Write tests
4. Create feature branch
5. Commit changes
6. Create pull request
7. Link PR to issue

**Example**: (triggered after RCA completion)

---

## General Purpose Commands

### `/create-prd`

**Purpose**: Create a Product Requirements Document from conversation.

**When to Use**:
- Planning new features
- Documenting requirements
- Stakeholder alignment
- Before starting development

**PRD Template**:
- Overview and objectives
- User stories
- Functional requirements
- Non-functional requirements
- Success criteria
- Out of scope
- Timeline (optional)

**Example**:
```
/create-prd
```

---

### `/end-to-end-feature`

**Purpose**: Autonomously develop a complete feature from planning to commit.

**Arguments**: `<feature description>`

**When to Use**:
- For rapid feature development
- When you want fully autonomous workflow
- For straightforward features

**Workflow**:
1. Prime (load context)
2. Plan (create implementation plan)
3. Execute (implement feature)
4. Validate (run all checks)
5. Commit (create commit)

**Example**:
```
/end-to-end-feature "Add rate limiting to API endpoints"
```

---

## Command Cheat Sheet

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `/core_piv_loop:prime` | Load project context | Starting new work |
| `/core_piv_loop:plan-feature` | Create comprehensive plan | Before implementing features |
| `/core_piv_loop:execute` | Execute with Archon tracking | Systematic implementation |
| `/exp-piv-loop:plan` | Enhanced planning with web research | Complex features |
| `/exp-piv-loop:implement` | Autonomous implementation | After creating plan |
| `/exp-piv-loop:router` | Auto-route natural language | GitHub @mentions |
| `/exp-piv-loop:rca` | Deep root cause analysis | Bug investigation |
| `/exp-piv-loop:fix-rca` | Implement fix from RCA | After RCA completion |
| `/exp-piv-loop:fix-issue` | Fix bug end-to-end | Straightforward bugs |
| `/exp-piv-loop:commit` | Quick commit | After implementation |
| `/exp-piv-loop:create-pr` | Create pull request | Ready for review |
| `/exp-piv-loop:review-pr` | Comprehensive PR review | Before merging |
| `/exp-piv-loop:merge-pr` | Merge PR safely | After review passes |
| `/validation:validate` | End-to-end validation | Pre-deployment |
| `/validation:code-review` | Technical code review | Pre-commit |

---

**Next**: Read `02-workflow-patterns.md` for common workflows and when to use which commands.
