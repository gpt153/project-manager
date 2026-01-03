# Subagent Patterns & Coordination

**Using Task tool and specialized agents effectively**

---

## Table of Contents

- [Understanding Subagents](#understanding-subagents)
- [When to Use Subagents](#when-to-use-subagents)
- [Available Subagents](#available-subagents)
- [Coordination Patterns](#coordination-patterns)
- [Best Practices](#best-practices)

---

## Understanding Subagents

### What are Subagents?

Subagents are specialized AI agents launched via the Task tool to handle specific types of work autonomously. They operate in parallel or sequentially to decompose complex tasks.

**Key Characteristics**:
- **Specialized**: Each agent type has specific capabilities
- **Autonomous**: Operates independently with own tools
- **Context-aware**: Receives conversation history before tool call
- **Resumable**: Can be resumed with agent ID for follow-up work

### Task Tool Fundamentals

```typescript
// Launch a subagent
Task({
  description: "Short 3-5 word description",
  prompt: "Detailed task instructions",
  subagent_type: "Explore" | "Plan" | "general-purpose" | ...,
  model: "sonnet" | "opus" | "haiku",  // Optional
  run_in_background: true | false,      // Optional
  resume: "agent_id"                     // Optional: resume previous agent
})
```

**When NOT to use Task tool**:
- ❌ Reading specific file path (use Read directly)
- ❌ Searching for specific class (use Glob directly)
- ❌ Searching code within 2-3 files (use Read directly)
- ❌ Simple operations that don't need research

---

## When to Use Subagents

### Exploration & Research

**Use subagent when**:
- Searching for patterns across large codebase
- Answering "how do X work?" questions
- Finding multiple instances of similar code
- Open-ended codebase exploration

**Example**:
```
User: "How does error handling work across the adapters?"

Good: Launch Explore agent
Task({
  description: "Analyze adapter error handling",
  prompt: "Search all adapters for error handling patterns. Find common approaches, identify inconsistencies, report findings.",
  subagent_type: "Explore",
  model: "sonnet"
})

Bad: Try to search directly
[Wastes tokens, may miss patterns, less thorough]
```

### Planning Complex Features

**Use subagent when**:
- Need architectural design
- Multiple implementation approaches possible
- Critical file identification required
- Trade-off analysis needed

**Example**:
```
User: "We need to add real-time notifications"

Good: Launch Plan agent
Task({
  description: "Plan real-time notifications",
  prompt: "Design real-time notification system. Evaluate WebSocket vs SSE vs polling. Identify integration points. Consider scalability.",
  subagent_type: "Plan"
})
```

### Parallel Research

**Use subagents when**:
- Multiple independent research tasks
- Different areas of codebase to analyze
- Parallel external documentation lookup

**Example**:
```
Planning Discord adapter:

// Launch 3 agents in parallel
[
  Task({
    description: "Research Discord.js patterns",
    prompt: "Find latest Discord.js documentation, best practices for bot development, common patterns",
    subagent_type: "general-purpose"
  }),
  Task({
    description: "Analyze existing adapters",
    prompt: "Study Telegram and Slack adapters. Extract common patterns for IPlatformAdapter implementation",
    subagent_type: "Explore"
  }),
  Task({
    description: "Find integration examples",
    prompt: "Search codebase for adapter registration patterns, factory patterns, initialization sequences",
    subagent_type: "Explore"
  })
]

// Wait for all, synthesize findings
```

---

## Available Subagents

### `Explore` Agent

**Purpose**: Fast codebase exploration and pattern discovery

**Tools Available**: All tools (Read, Write, Edit, Grep, Glob, Bash, etc.)

**Use cases**:
- "Where are errors from the client handled?"
- "What is the codebase structure?"
- "How do session management work?"
- "Find all instances of database queries"

**Thoroughness Levels**:
- `"quick"` - Basic searches
- `"medium"` - Moderate exploration
- `"very thorough"` - Comprehensive analysis across multiple locations

**Example**:
```
Task({
  description: "Find session patterns",
  prompt: "Explore how sessions are created, stored, and resumed across the codebase. Find all session-related files and patterns. Level: very thorough",
  subagent_type: "Explore"
})
```

### `Plan` Agent

**Purpose**: Software architect agent for designing implementation plans

**Tools Available**: All tools

**Use cases**:
- Planning implementation strategy
- Identifying critical files
- Considering architectural trade-offs
- Creating step-by-step plans

**Returns**:
- Step-by-step plan
- File list (create vs modify)
- Pattern references
- Risk assessment

**Example**:
```
Task({
  description: "Plan caching layer",
  prompt: "Design a caching layer for API responses. Evaluate Redis vs in-memory vs file-based. Plan integration points, data structure, TTL strategy.",
  subagent_type: "Plan"
})
```

### `general-purpose` Agent

**Purpose**: Multi-step tasks, complex questions, code searches

**Tools Available**: All tools (*)

**Use cases**:
- Complex research tasks
- Multi-step workflows
- When other agents don't fit
- Autonomous problem-solving

**Use when**:
- Task requires multiple rounds of search/read
- Not confident you'll find match in first few tries
- Need adaptive approach to problem

**Example**:
```
Task({
  description: "Research authentication flows",
  prompt: "Document all authentication flows in the application. Trace from login through token generation, storage, and validation. Include diagrams if helpful.",
  subagent_type: "general-purpose"
})
```

### Specialized Agents (if configured)

**`claude-code-guide`**: Claude Code/API documentation lookup
- Use when: User asks about Claude features, SDK usage, API

**`statusline-setup`**: Configure status line
- Use when: User wants to customize terminal status line

---

## Coordination Patterns

### Pattern: Sequential Dependency

When task B depends on task A's output:

```
1. Launch Task A
   ↓
   [Wait for completion]
   ↓
   Read Task A output
   ↓
2. Launch Task B with Task A results
   ↓
   [Wait for completion]
   ↓
   Synthesize both outputs
```

**Example**:
```
// Step 1: Explore codebase patterns
const exploreResult = Task({
  description: "Find adapter patterns",
  prompt: "Search all adapters for common patterns: initialization, message handling, error handling",
  subagent_type: "Explore"
});

// Step 2: Use findings to plan new adapter
const planResult = Task({
  description: "Plan Discord adapter",
  prompt: `Based on patterns found: ${exploreResult}, create implementation plan for Discord adapter following same patterns`,
  subagent_type: "Plan"
});
```

### Pattern: Parallel Independent

When tasks are independent, launch in parallel:

```
Launch all tasks simultaneously (single message, multiple Task calls)
   ↓
   All agents work in parallel
   ↓
   Wait for all completions
   ↓
   Synthesize all outputs
```

**Example**:
```
// Launch 3 research tasks in parallel
// (send in SINGLE message with multiple Task calls)

Task 1: Search codebase for pattern X
Task 2: Research external documentation
Task 3: Analyze test patterns

[All run simultaneously]
[Combine findings when all complete]
```

### Pattern: Explore → Plan → Execute

Classic workflow using subagents:

```
1. Explore (understand current state)
   ↓
   Agent analyzes codebase, finds patterns
   ↓
2. Plan (design solution)
   ↓
   Agent creates implementation plan
   ↓
3. Execute (implement)
   ↓
   Main orchestrator implements following plan
   ↓
4. Validate (verify)
   ↓
   Run tests, checks, reviews
```

### Pattern: Background Processing

When task is long-running and you can work while it completes:

```
Task({
  description: "Long-running research",
  prompt: "Analyze entire codebase for security vulnerabilities",
  subagent_type: "general-purpose",
  run_in_background: true  // Returns immediately
})

// Continue other work
[Do other tasks...]

// Later: retrieve results
TaskOutput({
  task_id: "agent_id",
  block: true  // Wait for completion
})
```

### Pattern: Resume for Follow-up

When you need to continue previous agent's work:

```
// Initial investigation
const agent1 = Task({
  description: "Investigate bug",
  prompt: "Find why authentication fails intermittently",
  subagent_type: "general-purpose"
});

// Agent returns with agent_id

// Later: resume to dig deeper
const agent2 = Task({
  description: "Deep dive on findings",
  prompt: "Based on your previous investigation, analyze the race condition in detail",
  subagent_type: "general-purpose",
  resume: "agent_id"  // Continues with full previous context
});
```

---

## Best Practices

### 1. Clear Task Descriptions

**❌ Vague**:
```
Task({
  description: "Do research",
  prompt: "Look into stuff"
})
```

**✅ Clear**:
```
Task({
  description: "Analyze adapter patterns",
  prompt: "Search all files in src/adapters/. Extract common patterns for message handling, error handling, and streaming. Report findings with file:line references."
})
```

### 2. Right Tool for Right Job

**❌ Wrong**:
```
// Reading a specific known file
Task({
  description: "Read README",
  prompt: "Read the README.md file",
  subagent_type: "general-purpose"
})

// Should use: Read tool directly
```

**✅ Right**:
```
// Open-ended exploration
Task({
  description: "Find documentation",
  prompt: "Search for all documentation about the authentication system across README, docs/, .agents/, and code comments",
  subagent_type: "Explore"
})
```

### 3. Provide Context

**❌ No context**:
```
Task({
  description: "Find the bug",
  prompt: "Fix it"
})
```

**✅ Rich context**:
```
Task({
  description: "Investigate webhook bug",
  prompt: "GitHub webhooks return 404 after deployment. Check: 1) Route registration in src/index.ts, 2) Express middleware setup, 3) Recent commits that touched webhook code. Hypothesis: routes may be commented out.",
  subagent_type: "general-purpose"
})
```

### 4. Model Selection

Choose appropriate model for task complexity:

```
Haiku (fastest, cheapest):
- Simple searches
- Quick file reads
- Straightforward questions

Sonnet (balanced):
- Most exploration tasks
- Planning tasks
- Complex analysis

Opus (most capable):
- Architectural decisions
- Complex planning
- Critical analysis
```

**Example**:
```
// Simple search - use Haiku
Task({
  description: "Find config file",
  prompt: "Locate the main configuration file",
  subagent_type: "Explore",
  model: "haiku"
})

// Complex architecture - use Opus
Task({
  description: "Design microservices",
  prompt: "Design microservices architecture for scaling the platform",
  subagent_type: "Plan",
  model: "opus"
})
```

### 5. Parallel Execution

**When tasks are independent, run in parallel**:

```
// ✅ Correct: Single message, multiple Task calls
[Send message with 3 Task calls for parallel execution]

// ❌ Wrong: Sequential messages
Task 1 → wait → Task 2 → wait → Task 3
[Slow, wastes time]
```

### 6. Trust Agent Output

**Agents are specialized and capable**:
```
✅ Read agent output
✅ Use agent recommendations
✅ Trust agent analysis
❌ Don't second-guess without reason
❌ Don't re-do agent's work
```

---

## Common Antipatterns

### Antipattern 1: Task for Simple Operations

**Wrong**:
```
Task({
  description: "Read package.json",
  prompt: "Read the package.json file",
  subagent_type: "general-purpose"
})
```

**Right**:
```
Read({ file_path: "/path/to/package.json" })
```

### Antipattern 2: No Description

**Wrong**:
```
Task({
  description: "",  // Empty!
  prompt: "Do the thing",
  subagent_type: "general-purpose"
})
```

**Right**:
```
Task({
  description: "Analyze authentication flow",
  prompt: "Trace authentication flow from login to token validation",
  subagent_type: "Explore"
})
```

### Antipattern 3: Sequential When Parallel Possible

**Wrong**:
```
// Send 3 separate messages (slow)
Message 1: Task A
[wait]
Message 2: Task B
[wait]
Message 3: Task C
```

**Right**:
```
// Single message with 3 Task calls (fast, parallel)
[Task A, Task B, Task C in one message]
```

### Antipattern 4: Wrong Agent Type

**Wrong**:
```
// Planning task sent to Explore agent
Task({
  description: "Plan new feature",
  prompt: "Design implementation approach",
  subagent_type: "Explore"  // Wrong type!
})
```

**Right**:
```
Task({
  description: "Plan new feature",
  prompt: "Design implementation approach",
  subagent_type: "Plan"  // Correct type
})
```

---

## Advanced Coordination

### Multi-Agent Research Pipeline

```
Phase 1: Parallel Exploration
├─ Agent A: Search codebase for pattern X
├─ Agent B: Search codebase for pattern Y
└─ Agent C: Search external docs for best practices
   ↓
   [All complete]
   ↓
Phase 2: Synthesis Planning
└─ Agent D: Create plan combining A, B, C findings
   ↓
   [Plan complete]
   ↓
Phase 3: Implementation
└─ Main orchestrator: Execute plan
```

### Iterative Refinement

```
Round 1: Initial Exploration
Task({ description: "Find auth patterns", ... })
   ↓
   [Review findings]
   ↓
Round 2: Deep Dive (Resume)
Task({ description: "Analyze specific pattern", resume: "agent_1_id", ... })
   ↓
   [Review analysis]
   ↓
Round 3: Final Plan
Task({ description: "Create implementation plan", ... })
```

### Error Recovery

```
Try: Launch agent for task X
   ↓
   If agent fails or returns unclear result:
   ├─ Option 1: Relaunch with more specific prompt
   ├─ Option 2: Launch different agent type
   └─ Option 3: Perform task directly (manual)
```

---

**Next**: Read `05-advanced-techniques.md` for power user patterns and optimization strategies.
