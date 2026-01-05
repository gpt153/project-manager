# Advanced Techniques & Best Practices

**Power user patterns, optimization strategies, and expert tips**

---

## Table of Contents

- [Session Management Mastery](#session-management-mastery)
- [Command Chaining](#command-chaining)
- [Context Optimization](#context-optimization)
- [Error Recovery](#error-recovery)
- [Performance Optimization](#performance-optimization)
- [Quality Assurance](#quality-assurance)
- [Production Best Practices](#production-best-practices)

---

## Session Management Mastery

### Understanding Session Lifecycle

**CRITICAL CONCEPT**: Plan→Execute creates NEW SESSION

```
Conversation (GitHub Issue #42)
├─ Session 1: Prime + Plan
│  └─ Status: INACTIVE after plan complete
│
└─ Session 2: Execute
   └─ Status: ACTIVE during implementation
```

**Why separate sessions?**
- **Context isolation**: Execute doesn't carry planning biases
- **Fresh start**: Implementation follows plan objectively
- **Token efficiency**: Planning context not repeated during execution

### Leveraging Session Separation

**Pattern**: Deliberate context reset

```
1. /core_piv_loop:prime
   [Load EVERYTHING about codebase]
   [Build comprehensive understanding]
   
2. /core_piv_loop:plan-feature <description>
   [Research deeply]
   [Consider ALL options]
   [Document EVERYTHING in plan]
   
   ← SESSION ENDS (planning context released)
   
3. /core_piv_loop:execute <plan-file>
   ← NEW SESSION (fresh context)
   [Reads plan as ONLY source of truth]
   [Implements objectively]
   [No memory of planning discussions]
```

**Key Insight**: Make plans COMPLETE and SELF-CONTAINED because execute won't "remember" what you discussed during planning.

### Session Metadata Usage

Commands can store metadata in session for later retrieval:

```
Session Metadata (JSONB):
{
  "lastCommand": "plan",
  "planFile": ".agents/plans/feature-x.md",
  "featureBranch": "feature/feature-x",
  "confidence": 8
}

Later commands can access:
$PLAN → reads plan file path from metadata
$IMPLEMENTATION_SUMMARY → reads execution summary
```

**Use metadata for**:
- Tracking workflow state
- Passing context between commands
- Storing user preferences
- Workflow automation

---

## Command Chaining

### Pattern: Sequential Workflow

Chain commands for end-to-end workflows:

```
Prime → Plan → Execute → Validate → Commit → PR

Implemented as:
1. /core_piv_loop:prime
2. /core_piv_loop:plan-feature <desc>
3. /core_piv_loop:execute <plan>
4. /validation:code-review
5. /exp-piv-loop:commit <files>
6. /exp-piv-loop:create-pr
```

### Pattern: Conditional Branching

Adapt workflow based on outcomes:

```
/exp-piv-loop:rca <bug>
   ↓
   Root cause found?
   ├─ Yes → /exp-piv-loop:fix-rca <rca-file>
   └─ No → /exp-piv-loop:rca <bug> quick
           [Try again with quick mode]
           Or: Manual investigation needed
```

### Pattern: Iterative Refinement

```
Round 1: /exp-piv-loop:plan <description>
   ↓
   [Review plan]
   User: "Can we use library X instead?"
   ↓
Round 2: /exp-piv-loop:plan <refined description with library X>
   ↓
   [Plan updated]
   ↓
Execute: /exp-piv-loop:implement <final-plan>
```

---

## Context Optimization

### Minimize Token Usage

**Techniques**:

1. **Use prime strategically** - Only when needed
2. **Targeted reads** - Read specific files, not entire directories
3. **Grep before Read** - Find files first, then read
4. **Subagents for exploration** - Offload research to specialized agents

**Example**:
```
❌ Wasteful:
Read all files in src/
[Reads 100+ files, wastes tokens]

✅ Efficient:
Grep({ pattern: "IPlatformAdapter", output_mode: "files_with_matches" })
[Find 5 relevant files]
Read each file specifically
[Reads only what's needed]
```

### Maximize Plan Quality

**Plans should be information-dense**:

```
❌ Vague:
"Add error handling to API"

✅ Specific:
"Add try-catch blocks to API endpoints following pattern in src/api/users.ts:45-60. Use custom ApiError class from src/errors.ts. Log errors with Winston logger. Return 500 status with error message."
```

**Include**:
- Exact file:line references
- Code snippets to mirror
- Library versions and imports
- Validation commands
- Expected behavior
- Edge cases

### Variable Substitution Mastery

**Use variables to avoid repetition**:

```
Command file: .agents/commands/analyze.md

Analyze the following aspect: $1
Focus areas: $ARGUMENTS

Invocation:
/command-invoke analyze security authentication authorization

Result:
Analyze the following aspect: security
Focus areas: security authentication authorization
```

**Available variables**:
- `$1`, `$2`, `$3` - Positional arguments
- `$ARGUMENTS` - All arguments as string
- `$PLAN` - Plan file path from session metadata
- `$IMPLEMENTATION_SUMMARY` - Execution summary

---

## Error Recovery

### Recovery Pattern: Validation Failures

```
/exp-piv-loop:implement <plan>
   ↓
npm run type-check → FAILS
   ↓
Analyze error
   ├─ Simple fix? → Fix inline, continue
   └─ Complex issue?
      ├─ /exp-piv-loop:rca "<error>"
      │  [Investigate root cause]
      └─ /exp-piv-loop:fix-rca <rca-file>
         [Implement fix]
         └─ Re-run validation
```

### Recovery Pattern: Plan Outdated

```
/exp-piv-loop:implement <plan>
   ↓
Pattern file referenced in plan doesn't exist
   ↓
Adapt:
   ├─ Search for similar pattern: Grep
   ├─ Find replacement pattern
   └─ Continue with updated reference
   
Document deviation in implementation report
```

### Recovery Pattern: Test Failures

```
All tests passing → Deploy
   ↓
Post-deployment: tests fail
   ↓
/exp-piv-loop:rca "Tests fail after deployment but passed locally"
   ↓
Common causes:
├─ Environment differences
├─ Missing dependencies in production
├─ Configuration issues
└─ Race conditions (timing-sensitive)
```

---

## Performance Optimization

### Parallel Execution

**Maximize parallelism**:

```
✅ Parallel (fast):
Single message with:
- Task({ description: "Research library A", ... })
- Task({ description: "Research library B", ... })
- Task({ description: "Research library C", ... })

[All run simultaneously]

❌ Sequential (slow):
Message 1: Task A → wait
Message 2: Task B → wait
Message 3: Task C → wait
```

### Caching Strategies

**Leverage file reads**:
```
Pattern: Read file once, reference multiple times

Read src/index.ts
[Store content in context]

Use content for:
- Pattern extraction
- Import analysis
- Dependency identification
- Integration point mapping

Don't re-read same file multiple times
```

### Strategic Model Selection

```
Haiku (fast, cheap):
├─ Simple file searches
├─ Grep operations
└─ Straightforward questions

Sonnet (balanced):
├─ Most exploration
├─ Planning tasks
└─ Implementation

Opus (powerful, expensive):
├─ Critical architectural decisions
├─ Complex planning
└─ High-stakes code review

Use right model for right task!
```

### Background Processing

```
Long-running research:
Task({
  description: "Comprehensive security audit",
  prompt: "Analyze entire codebase for security vulnerabilities",
  subagent_type: "general-purpose",
  run_in_background: true
})

[Continue other work while agent runs]

Later: TaskOutput({ task_id, block: true })
```

---

## Quality Assurance

### Multi-Level Validation

**Level 1: Syntax & Types**
```bash
npm run type-check  # TypeScript
npm run lint        # ESLint
npm run format:check  # Prettier
```

**Level 2: Unit Tests**
```bash
npm test
npm run test:coverage
```

**Level 3: Integration Tests**
```bash
npm run test:integration
```

**Level 4: Manual Validation**
```bash
# Start application
npm run dev

# Test feature manually
curl -X POST http://localhost:3000/api/...

# Verify behavior
```

**Level 5: End-to-End**
```bash
/validation:validate <ngrok-url>
# Full system validation
```

### Pre-Commit Checklist

```
Before /exp-piv-loop:commit:

1. ✅ Code review completed: /validation:code-review
2. ✅ Tests pass: npm test
3. ✅ Types pass: npm run type-check
4. ✅ Lint passes: npm run lint
5. ✅ Format passes: npm run format:check
6. ✅ Manual testing: verified feature works
7. ✅ No secrets: checked for API keys, tokens
8. ✅ Documentation: updated if needed
```

### Pre-Merge Checklist

```
Before /exp-piv-loop:merge-pr:

1. ✅ PR review completed: /exp-piv-loop:review-pr
2. ✅ All CI checks pass
3. ✅ Approved by reviewer
4. ✅ Up-to-date with base branch
5. ✅ No merge conflicts
6. ✅ Feature tested in staging
7. ✅ Changelog updated
8. ✅ Documentation complete
```

---

## Production Best Practices

### Feature Flag Pattern

```
Instead of:
[Implement feature directly in main code]
[Deploy]
[Hope it works]

Better:
[Implement feature behind feature flag]
```typescript
if (process.env.ENABLE_NEW_FEATURE === 'true') {
  // New feature code
} else {
  // Old behavior
}
```
[Deploy with flag OFF]
[Test in production]
[Enable flag when ready]
[Remove flag once stable]
```

### Database Migration Pattern

```
Instead of:
[Change schema]
[Deploy]
[Data migration runs]
[Hope it works]

Better:
1. [Create migration script]
2. [Test migration on staging copy]
3. [Deploy migration (no app changes yet)]
4. [Verify migration successful]
5. [Deploy app code using new schema]
6. [Rollback plan ready]
```

### Canary Deployment Pattern

```
Instead of:
[Deploy to all servers]
[Monitor for errors]

Better:
1. [Deploy to 1 server]
2. [Monitor metrics closely]
3. [If stable, deploy to 10% servers]
4. [Monitor]
5. [If stable, deploy to 50% servers]
6. [Monitor]
7. [If stable, deploy to all servers]
```

### Rollback Preparedness

```
Before deployment:
✅ Document rollback procedure
✅ Test rollback in staging
✅ Know how to revert database changes
✅ Have communication plan ready

During deployment:
✅ Monitor metrics continuously
✅ Watch error rates
✅ Check logs for issues

If problems:
✅ Execute rollback immediately
✅ Investigate in staging
✅ Fix issue
✅ Re-deploy when ready
```

---

## Expert Patterns

### The "Trust but Verify" Pattern

```
1. Trust AI to implement features
   └─ Let it work autonomously
   
2. But verify at checkpoints:
   ├─ After each major task
   ├─ After validation commands
   └─ Before committing

3. Use validation commands extensively:
   ├─ /validation:code-review
   ├─ npm test
   └─ Manual testing
```

### The "Plan Once, Execute Many" Pattern

```
Create comprehensive plan:
/core_piv_loop:plan-feature <complex feature>

Then execute in stages:
Phase 1: /exp-piv-loop:implement <plan> (foundation)
[Pause, review]
Phase 2: /exp-piv-loop:implement <plan> (core)
[Pause, review]
Phase 3: /exp-piv-loop:implement <plan> (polish)
[Final review]
```

### The "Fail Fast, Recover Fast" Pattern

```
Don't be afraid of failures:
1. Try bold implementation
   ↓
2. If validation fails → analyze quickly
   ↓
3. Fix or rollback decisively
   ↓
4. Learn from failure
   ↓
5. Update plan/approach
   ↓
6. Try again with better understanding
```

### The "Document Everything" Pattern

```
Keep these documents:
├─ .agents/prd/ → Product requirements
├─ .agents/plans/ → Implementation plans
├─ .agents/rca/ → Root cause analyses
├─ .agents/code-reviews/ → Code review reports
├─ .agents/implementation-reports/ → What was built
└─ .agents/system-reviews/ → Process improvements

Benefits:
✅ Knowledge base grows
✅ Patterns emerge
✅ Future work easier
✅ Team onboarding faster
```

---

## Power User Tips

### Tip 1: Chain with Confidence

Don't overthink - trust the workflow:
```
/prime → /plan → /execute → /code-review → /commit → /create-pr

Just follow the sequence. It works.
```

### Tip 2: When Stuck, Go Back to Basics

```
Stuck on implementation?
└─ Go back to /prime
   [Re-load context]
   └─ Often reveals solution
```

### Tip 3: Use Router for Flexibility

```
Instead of:
User: "The login is broken"
You: [Manually decide what to do]

Better:
/exp-piv-loop:router "The login is broken"
[Router decides: /rca]
[Auto-executes investigation]
```

### Tip 4: Leverage Session Metadata

```
Store frequently-used values:
{
  "apiEndpoint": "https://api.example.com",
  "testUser": "test@example.com",
  "mainBranch": "main"
}

Reference in commands:
$API_ENDPOINT, $TEST_USER, $MAIN_BRANCH
```

### Tip 5: Build Command Library

```
Create domain-specific commands:
├─ /prime-auth → Prime with auth focus
├─ /plan-api → Plan API endpoint
├─ /test-auth → Test authentication flow
└─ /deploy-staging → Deploy to staging

Saves time, reduces errors
```

---

## Antipatterns to Avoid

### ❌ Planning Without Context

```
Wrong:
User: "Add feature X"
You: /plan "Add feature X"
[Plan without understanding codebase]

Right:
User: "Add feature X"
You: /prime
[Understand codebase]
Then: /plan "Add feature X"
[Informed planning]
```

### ❌ Skipping Validation

```
Wrong:
[Implement feature]
/commit
/create-pr
[Ship to production]
[Discover it's broken]

Right:
[Implement feature]
/code-review
npm test
npm run type-check
[All pass]
/commit
/create-pr
```

### ❌ Generic Plans

```
Wrong:
"Add error handling"

Right:
"Add try-catch to API routes following pattern in src/api/users.ts:45-60. Use ApiError class from src/errors.ts. Log with Winston. Return 500 with {error: message}."
```

### ❌ Ignoring Git Best Practices

```
Wrong:
git add .
git commit -m "stuff"
git push -f

Right:
/commit "API routes and error handling"
[Conventional commit]
[Proper attribution]
```

---

## Conclusion

Mastering Remote Coding Agent requires:

1. **Understanding workflows**: Know which command for which situation
2. **Trusting the system**: Let AI work autonomously
3. **Validating thoroughly**: Trust but verify
4. **Learning from failures**: Iterate and improve
5. **Building expertise**: Pattern recognition over time

**The ultimate goal**: Ship production-ready code faster and more reliably than ever before.

---

**End of Orchestrator Agent Guide**

You are now equipped to be an expert Project Manager for Remote Coding Agent. Use these docs as your comprehensive reference. Guide users proactively, choose workflows wisely, and orchestrate development with confidence.
