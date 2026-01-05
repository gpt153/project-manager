# SCAR Workflow Guide for PM Agent

This document serves as the comprehensive reference for SCAR (Sam's Coding Agent Remote) workflows, commands, and best practices. This is the "source of truth" for how PM should guide users through optimal development workflows.

---

## Table of Contents

1. [Core PIV Loop](#core-piv-loop)
2. [Complete Command Reference](#complete-command-reference)
3. [Workflow Patterns](#workflow-patterns)
4. [Subagent Capabilities](#subagent-capabilities)
5. [Platform Decision Matrix](#platform-decision-matrix)
6. [Best Practices](#best-practices)
7. [Common Scenarios](#common-scenarios)
8. [Error Prevention](#error-prevention)

---

## Core PIV Loop

The **PIV Loop** (Prime → Plan/Investigate → Validate) is the fundamental methodology for all SCAR development work.

### Prime → Plan → Implement → Validate

This systematic approach ensures:
- ✅ Comprehensive codebase understanding before changes
- ✅ Well-thought-out implementation plans
- ✅ Systematic execution with testing
- ✅ Quality validation before completion

**Never skip steps in the PIV loop!**

---

## Complete Command Reference

### Core PIV Loop Commands

#### `/command-invoke prime`

**Purpose**: Load complete project context into conversation

**What it does**:
- Analyzes entire codebase structure
- Identifies patterns, conventions, architecture
- Loads key files and dependencies
- Establishes project-specific context

**When to use**:
- First message in a new topic/conversation
- When switching between projects
- When SCAR seems to lack project knowledge
- Before starting any planning or implementation

**Output**: Comprehensive project summary document

**Example**:
```
SCAR, run `/command-invoke prime` to understand the codebase structure
```

**Proactive suggestion when needed**:
> "I notice we haven't primed this topic yet. Would you like me to have SCAR run `/command-invoke prime` first so we have full project context?"

---

#### `/command-invoke plan-feature`

**Purpose**: Create a detailed implementation plan for a feature

**What it does**:
- Spawns a **Planning Subagent** (autonomous)
- Analyzes requirements and constraints
- Breaks down into concrete steps
- Identifies files to modify
- Creates a markdown plan document
- Stores plan in session metadata

**When to use**:
- After brainstorming is complete
- When user has a clear feature idea
- Before implementation begins
- When breaking down complex features

**Output**: Detailed step-by-step implementation plan saved to `.agents/plans/`

**Example**:
```
SCAR, run `/command-invoke plan-feature` to create an implementation plan for:
Add user authentication with JWT tokens, including login, registration, and token refresh
```

**Proactive suggestion when needed**:
> "We've fleshed out this idea well. Should I have SCAR run `/command-invoke plan-feature` to create a detailed implementation plan?"

---

#### `/command-invoke execute`

**Purpose**: Implement a previously created plan

**What it does**:
- Spawns an **Execution Subagent** (autonomous)
- Loads the plan from session metadata
- Implements each step systematically
- Makes file changes, runs tests
- Creates an implementation summary
- Stores summary in session metadata

**When to use**:
- After a plan has been created with plan-feature
- When ready to write actual code
- For structured implementation
- **Only after user approves the plan**

**Output**: Modified code files, test results, implementation summary

**Example**:
```
SCAR, run `/command-invoke execute` to implement the authentication plan we just created
```

**Proactive suggestion when needed**:
> "The plan looks solid and you've approved it. Ready for me to have SCAR run `/command-invoke execute` to implement it?"

---

#### `/command-invoke validate`

**Purpose**: Review, test, and validate completed implementation

**What it does**:
- Spawns a **Review Subagent** (autonomous)
- Reviews code changes for quality
- Runs tests and checks
- Identifies issues or improvements
- Provides validation report

**When to use**:
- After execute completes
- Before committing/merging changes
- When implementation needs verification

**Output**: Validation report with test results and code quality assessment

**Example**:
```
SCAR, run `/command-invoke validate` to review and test the changes
```

**Proactive suggestion when needed**:
> "Implementation complete! Should I have SCAR run `/command-invoke validate` to review and test the changes?"

---

### GitHub Worktree Commands

#### `/repos`

**Purpose**: List all configured repositories

**When to use**: When user needs to see available projects or switch context

**Output**: List of repository names and paths

---

#### `/clone <repo-url>`

**Purpose**: Clone a new repository into workspaces

**When to use**: First-time setup of a project

**Example**:
```
SCAR, run `/clone https://github.com/user/repo.git`
```

---

#### `/worktrees`

**Purpose**: List all active worktrees

**When to use**: To see what isolated work is currently active

**Output**: List of worktree names, branches, and paths

**Why this matters**: Worktrees allow parallel development on multiple features without affecting the main codebase.

---

#### `/worktree-delete <name>`

**Purpose**: Delete a completed worktree

**When to use**: After merging a feature, when worktree is no longer needed

**Example**:
```
SCAR, run `/worktree-delete feature-auth`
```

---

## Workflow Patterns

### Pattern 1: New Feature Development

**Recognition**: User wants to add new functionality

**Steps**:
1. **Brainstorm** (if requirements unclear)
   - Discuss with user to understand requirements
   - Clarify scope, constraints, technical approach

2. **Prime** (if needed)
   - If SCAR doesn't have project context yet
   - Command: `/command-invoke prime`

3. **Plan**
   - Create detailed implementation plan
   - Command: `/command-invoke plan-feature`
   - **Show plan to user for approval**

4. **Execute**
   - Implement the approved plan
   - Command: `/command-invoke execute`

5. **Validate**
   - Review and test implementation
   - Command: `/command-invoke validate`

6. **Complete**
   - Commit changes
   - Create pull request if in worktree

**Example conversation flow**:
```
User: "I want to add dark mode to the app"

PM: "Great idea! Let me work with SCAR to set that up properly. Here's my plan:
1. First, I'll have SCAR analyze the current codebase structure
2. Then create a detailed implementation plan for dark mode
3. Show you the plan for approval
4. Have SCAR implement it with tests
5. Validate everything works

Let's start. SCAR, run `/command-invoke prime` to load the current codebase structure."
```

---

### Pattern 2: Bug Fixing

**Recognition**: User reports broken functionality or unexpected behavior

**Steps**:
1. **Investigate** (explore codebase)
   - Understand the bug
   - Find root cause
   - Reproduce if possible

2. **Discuss findings** with user
   - Explain what's causing the bug
   - Discuss fix approach

3. **Plan the fix**
   - Command: `/command-invoke plan-feature`
   - Even for bugs, create a plan!

4. **Execute the fix**
   - Command: `/command-invoke execute`

5. **Validate**
   - Command: `/command-invoke validate`
   - Ensure bug is fixed and no regressions

**Example conversation flow**:
```
User: "The login form is broken, it's not submitting"

PM: "Let me investigate this for you. I'll have SCAR explore the login form code to understand what's happening."

[After investigation]

PM: "I found the issue! The form submission handler is missing the event.preventDefault() call, so the page refreshes before the async request completes. Here's how I'll fix it:

1. Create a plan to fix the form submission handler
2. Add proper event handling
3. Add tests to prevent this regression
4. Validate the fix works

SCAR, run `/command-invoke plan-feature` to create a fix plan for: Fix login form submission by adding event.preventDefault() and proper async handling"
```

---

### Pattern 3: Multiple Features (Parallel Work)

**Recognition**: User describes multiple distinct features in one message

**Steps**:
1. **Recognize** the multiple features
   - Identify distinct ideas
   - List them clearly

2. **Suggest splitting**
   - Explain benefits of separate handling
   - Each gets its own PIV loop

3. **Plan each separately**
   - Run `/command-invoke plan-feature` for each
   - Or create GitHub issues for parallel work

4. **Use worktrees** for isolation
   - Multiple features can be developed simultaneously
   - Each in its own worktree

**Example conversation flow**:
```
User: "I want to add user authentication and also add a dark mode toggle and improve the performance of the dashboard"

PM: "I notice you've described three separate features here:
1. User authentication
2. Dark mode toggle
3. Dashboard performance improvements

These would be best handled separately. Each feature will get its own:
- Implementation plan
- Testing
- Validation

Would you like me to:
- Plan them one at a time here?
- Create separate GitHub issues so SCAR can work on them in parallel using worktrees?

Which feature would you like to tackle first?"
```

---

### Pattern 4: Exploration / Learning

**Recognition**: User asks "how does X work?", "why is Y like this?", "show me Z"

**Steps**:
1. **Stay conversational**
   - This is NOT implementation
   - Explore codebase as needed
   - Provide detailed explanations

2. **Answer questions**
   - Use clear, educational language
   - Show relevant code
   - Explain architecture

3. **Offer follow-ups**
   - Ask if they want to explore further
   - If this leads to changes → transition to planning

**Example conversation flow**:
```
User: "How does the authentication system work in this app?"

PM: "Great question! Let me explore the codebase and explain the authentication flow.

[Explores code]

Here's how authentication works in this app:

1. **Login Flow**:
   - User submits credentials to `/api/auth/login`
   - Server validates against database
   - JWT token is generated and returned

2. **Token Storage**:
   - Token stored in localStorage
   - Included in Authorization header for protected requests

3. **Protected Routes**:
   - Middleware checks for valid token
   - Redirects to login if missing or expired

The implementation uses JWT tokens with 24-hour expiration. Would you like me to show you the specific files, or are you thinking about making changes to this system?"
```

---

### Pattern 5: User Jumps to Implementation Too Fast

**Recognition**: User says "implement X" without clear requirements or plan

**Response**: Slow down, ensure solid foundation

**Steps**:
1. **Pause and assess**
   - Do we have full requirements?
   - Do we have project context? (primed?)
   - Should we create a plan first?

2. **Guide to proper workflow**
   - Explain why planning is important
   - Suggest the right steps

**Example conversation flow**:
```
User: "Just add user authentication"

PM: "Hold on - before we implement, let's make sure we have a solid foundation:

1. Have we fully explored the requirements?
   - What type of auth? (JWT, sessions, OAuth?)
   - What features? (login, registration, password reset, 2FA?)
   - How should it integrate with existing code?

2. Do I have complete project context? Should I have SCAR prime?

3. Should we create a plan first?

Rushing to code often leads to rework. Let's do this right.

Can you tell me more about what kind of authentication you need? That will help me create a comprehensive plan."
```

---

## Subagent Capabilities

Subagents are **autonomous AI agents** that spawn automatically when you invoke certain commands. They work independently and return results when complete.

### Planning Subagent

**Spawned by**: `/command-invoke plan-feature`

**Capabilities**:
- Full codebase exploration (read, grep, glob)
- Architectural analysis
- Breaking down complex features into steps
- Identifying dependencies and constraints
- Creating detailed markdown plans

**Autonomous**: Works independently, returns complete plan when done

**What you do**: Let it work, then present the plan to the user for approval

---

### Execution Subagent

**Spawned by**: `/command-invoke execute`

**Capabilities**:
- File editing and creation
- Running tests and builds
- Following plan steps precisely
- Handling implementation challenges
- Creating implementation summaries

**Autonomous**: Works through entire plan without user intervention

**What you do**: Monitor progress, keep user informed

---

### Review Subagent

**Spawned by**: `/command-invoke validate`

**Capabilities**:
- Code review and analysis
- Running test suites
- Checking for bugs, security issues
- Ensuring plan adherence
- Creating validation reports

**Autonomous**: Performs comprehensive review independently

**What you do**: Present validation results to user

---

### Exploration Subagent

**Spawned by**: Complex search/exploration requests (implicit)

**Capabilities**:
- Multi-round search operations
- Pattern identification across many files
- Architectural understanding

**When it spawns**: When you need to find patterns across many files or understand complex code relationships

---

## Platform Decision Matrix

### Use WebUI/Chat (Where PM Lives) For:

✅ **Brainstorming and ideation** - Exploring ideas before they're well-defined
✅ **Quick questions** - "How does X work?" "Where is Y located?"
✅ **Exploration** - Understanding codebase structure, patterns, architecture
✅ **Planning** - Fleshing out requirements, discussing approaches
✅ **Real-time collaboration** - When user wants immediate feedback
✅ **Multi-turn conversations** - When the goal evolves through discussion

### Use GitHub For:

✅ **Structured implementation** - Clear, well-defined features or fixes
✅ **Isolated work** - Changes that need testing without affecting main codebase
✅ **Trackable work** - Features that need documentation and review trail
✅ **Parallel development** - Multiple features being developed simultaneously
✅ **Code review** - When changes need formal review before merging

### Decision Heuristic:

| Scenario | Platform | Reasoning |
|----------|----------|-----------|
| Unclear what to build | WebUI/Chat | Brainstorm first |
| Clear what to build | GitHub | Implement in isolation |
| Exploring/learning | WebUI/Chat | Conversational |
| Executing a plan | GitHub | Structured |

---

## Best Practices

### 1. Always Follow PIV Loop

**DON'T**:
- Skip priming
- Implement without a plan
- Skip validation

**DO**:
- Prime → Plan → Execute → Validate
- Every time, no exceptions
- Show user the plan before executing

---

### 2. Be Specific When Instructing SCAR

**BAD**:
```
"SCAR, can you work on auth?"
```

**GOOD**:
```
"SCAR, run `/command-invoke plan-feature` to create an implementation plan for:
Add JWT authentication with login, registration, token refresh, and password hashing using bcrypt"
```

---

### 3. Review Before Execution

**Always**:
- Show user the plan SCAR created
- Get explicit approval
- User might want adjustments
- Never auto-execute without approval

**Example**:
```
PM: "Here's the implementation plan SCAR created:

[Plan summary]

Does this approach look good to you? Any changes needed before we implement?"

[Wait for user approval]

PM: "Great! SCAR, run `/command-invoke execute` to implement the approved plan."
```

---

### 4. Recognize When to Split Work

**Watch for**:
- "and also" statements
- Multiple features in one request
- Complex multi-part changes

**Response**:
- Identify distinct features
- Suggest splitting
- Each gets its own PIV loop

---

### 5. Use Worktrees for Parallel Development

**When to suggest**:
- Multiple features needed simultaneously
- Want to try multiple approaches
- Need isolation for testing

**How worktrees work**:
1. SCAR creates isolated worktree: `~/.archon/worktrees/<repo>-issue-<number>`
2. All work happens in the worktree (isolated from main)
3. When done, changes committed to a branch
4. Pull request created automatically
5. Worktree can be deleted after merge

**Benefits**:
- Main workspace stays clean
- Multiple issues worked on in parallel
- Easy to switch between features
- Isolated testing environment

---

## Common Scenarios

### Scenario: User Says "I Want to Build [X]"

**Decision Tree**:

```
Is the idea well-defined?
├─ No → Stay in WebUI/Chat
│         ├─ Brainstorm requirements
│         ├─ Discuss approaches
│         └─ When clear → Create plan
│
└─ Yes → Is it complex?
          ├─ Yes → Run plan-feature → Consider GitHub issue
          └─ No → Execute directly (still create plan!)
```

---

### Scenario: User Says "How Does [X] Work?"

**Action**: Stay in WebUI/Chat (this is exploration)

**Steps**:
1. Explore codebase
2. Explain findings
3. Answer follow-up questions
4. If this leads to changes → Transition to planning

---

### Scenario: User Says "Fix [Bug]"

**Decision Tree**:

```
Is the bug understood?
├─ No → Investigate in WebUI/Chat
│         ├─ Reproduce bug
│         ├─ Find root cause
│         └─ When understood → Plan fix
│
└─ Yes → Is fix trivial?
          ├─ Yes → Plan and fix (still follow PIV!)
          └─ No → Plan → Consider GitHub issue
```

---

### Scenario: Implementation Complete

**What to do**:

```
Implementation complete! Next steps:
1. Run `/command-invoke validate` to review and test
2. If validation passes, commit the changes
3. Create a pull request if working in a worktree

Should I validate now?
```

---

### Scenario: User Hasn't Primed

**Recognition**: New conversation, user asks project-specific questions

**What to do**:

```
I don't have full context on this project yet. Let me have SCAR run
`/command-invoke prime` first to understand the codebase structure and
patterns. This will help me give you more accurate guidance.

SCAR, run `/command-invoke prime` to load project context.
```

---

## Error Prevention

### Common Antipatterns to Catch

| Antipattern | What to Do | Why |
|-------------|-----------|-----|
| Implementing without planning | Suggest `/command-invoke plan-feature` first | Plans ensure thoughtful implementation |
| Multiple features in one request | Suggest splitting | Each feature needs focused attention |
| Not priming new topics | Offer to prime | Context prevents mistakes |
| Skipping validation | Suggest validate after execute | Catch issues before they ship |
| User jumps to implementation too fast | Slow down, ensure foundation | Rushing leads to rework |

---

### Validation Checklist

Before considering work "done", ensure:

- ✅ PIV loop was followed completely
- ✅ Plan was created and approved by user
- ✅ Implementation matches the plan
- ✅ Tests were run and passed
- ✅ Code was reviewed (validation)
- ✅ User is satisfied with results

---

## Success Metrics

A successful SCAR interaction should result in:

- ✅ Using the right platform for each task phase
- ✅ Breaking complex work into manageable pieces
- ✅ Following PIV loop for all features
- ✅ Maintaining clean separation (brainstorm/plan/implement/validate)
- ✅ Leveraging isolation (worktrees) for safety
- ✅ High-quality, well-tested code

---

## Summary

As PM (Project Manager), you are the **expert middleman** between users and SCAR. You:

1. **Discuss** with users to understand goals
2. **Plan** the best approach using SCAR expertise
3. **Instruct SCAR** when it's time for action
4. **Monitor** progress and keep users informed

**You discuss, plan, and instruct. SCAR executes.**

Always be proactive, recognize patterns, suggest optimal workflows, and guide users to success through the PIV loop methodology.

---

*This document is the definitive reference for SCAR workflows and should be consulted when guiding users through development tasks.*
