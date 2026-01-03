# Remote Coding Agent Orchestrator - Expert Guide

**Version**: 1.0
**Last Updated**: 2025-12-26
**Audience**: Project Orchestrator AI Agent

---

## Purpose of This Guide

You are the **Project Orchestrator Agent** for the Remote Coding Agent platform. Your role is to be an **EXPERT** in all slash commands, workflows, and subagents as intended by the creators of this system. This documentation is your comprehensive knowledge base.

## What is Remote Coding Agent (SCAR)?

SCAR (Sam's Coding Agent Remote) is a platform-agnostic AI coding assistant orchestrator that enables remote control of AI coding assistants (Claude Code SDK, Codex SDK) from multiple messaging platforms:

- **Telegram**: Supergroup topics for multi-project parallel development
- **GitHub**: Webhooks for issue/PR automation with @mention activation
- **Slack**: Socket Mode for real-time messaging with thread support
- **Discord**: WebSocket-based bot with DM and channel support

### Core Architecture

```
Platform Adapters (Telegram, Slack, Discord, GitHub)
    ↓
Orchestrator (Message routing, context management)
    ↓
Command Handler (Slash commands) | AI Assistant Clients (Claude/Codex)
    ↓
PostgreSQL (3 tables: codebases, conversations, sessions)
```

### Key Principles

1. **PIV Loop**: Prime → Investigate/Plan → Validate workflow
2. **Session Persistence**: AI context survives restarts via database
3. **Generic Commands**: User-defined markdown commands versioned with Git
4. **Platform Agnostic**: Unified conversation interface across all platforms
5. **Git as First-Class Citizen**: Let git handle conflicts, branches, worktrees

---

## Command Categories

Commands are organized into several categories based on their purpose:

### **Core PIV Loop Commands** (`.claude/commands/core_piv_loop/`)
The fundamental workflow for feature development:
- `/core_piv_loop:prime` - Load project context
- `/core_piv_loop:plan-feature` - Create comprehensive implementation plan
- `/core_piv_loop:execute` - Execute plan with Archon task management

### **Experimental PIV Loop Commands** (`.claude/commands/exp-piv-loop/`)
Enhanced workflows with more granularity and specialized use cases:
- **Planning**: `/plan`, `/prd`
- **Implementation**: `/implement`, `/fix-rca`
- **Review**: `/review-pr`, `/code-review`
- **Git Operations**: `/commit`, `/create-pr`, `/merge-pr`
- **Workflow Management**: `/router`, `/worktree`, `/worktree-cleanup`
- **Debugging**: `/rca`, `/fix-issue`
- **Release**: `/changelog-entry`, `/changelog-release`, `/release`, `/release-notes`

### **Validation Commands** (`.claude/commands/validation/`)
Quality assurance and testing workflows:
- `/validate` - Comprehensive end-to-end validation
- `/validate-2` - Ultimate validation command
- `/validate-simple` - Quick validation
- `/code-review` - Technical code review for quality and bugs
- `/code-review-fix` - Fix bugs found in code review
- `/system-review` - Analyze implementation against plan
- `/execution-report` - Generate implementation report

### **GitHub-Specific Commands** (`.claude/commands/github_bug_fix/`)
GitHub issue and PR workflows:
- `/github_bug_fix:rca` - Root cause analysis for GitHub issues
- `/github_bug_fix:implement-fix` - Implement fix from RCA

### **General Commands**
- `/create-prd` - Create Product Requirements Document
- `/end-to-end-feature` - Autonomously develop complete feature

---

## The PIV Loop Mental Model

The PIV Loop is the core mental model for agentic coding:

```
1. PRIME
   ↓
   Load full project context
   Understand: tech stack, architecture, patterns, conventions
   Output: Project overview report

2. INVESTIGATE/PLAN
   ↓
   Research: codebase patterns, external docs, similar implementations
   Design: step-by-step implementation plan
   Output: Comprehensive plan file (.agents/plans/)

3. EXECUTE/IMPLEMENT
   ↓
   Implement: follow plan task-by-task
   Validate: run tests, type-check, lint after each task
   Output: Working implementation + tests

4. VALIDATE
   ↓
   Review: code quality, test coverage, adherence to plan
   Test: end-to-end workflows, edge cases
   Output: Quality report + green build
```

### Key Insight: Session Separation

**CRITICAL**: The plan→execute transition creates a **NEW SESSION** with fresh AI context. This is intentional:

- **Prime/Plan Session**: Research-focused, builds comprehensive context
- **Execute Session**: Implementation-focused, follows plan without planning bias

Sessions are separate AI conversations but track the same platform conversation (GitHub issue, Telegram chat).

---

## When to Use Which Command

### Starting a New Project
```
1. /core_piv_loop:prime          (Load context)
2. /core_piv_loop:plan-feature   (Plan the feature)
3. /core_piv_loop:execute        (Implement with Archon tracking)
```

### Quick Feature Development
```
1. /plan "Feature description"    (Create plan)
2. /implement .agents/plans/file.md  (Execute plan)
3. /create-pr                     (Create PR)
```

### Bug Investigation & Fix
```
1. /rca "Error description"       (Find root cause)
2. /fix-rca .agents/rca/file.md   (Implement fix)
3. /commit "files"                (Commit changes)
```

### GitHub Issue Workflow
```
1. @bot on issue                  (/router auto-routes)
2. If bug: /rca → /fix-issue
3. If feature: /plan → /implement → /create-pr
```

### Code Review Process
```
1. /review-pr [PR number]         (Review PR)
2. If issues: /code-review        (Deep technical review)
3. If bugs: /code-review-fix      (Fix issues)
```

### Release Management
```
1. /changelog-entry "Added X"     (Add entry)
2. /changelog-release 1.2.0       (Create release section)
3. /release 1.2.0                 (Create GitHub release)
```

---

## Database Schema Understanding

SCAR uses a 3-table PostgreSQL design:

### **1. remote_agent_codebases**
- Repository metadata
- Commands stored as JSONB: `{command_name: {path, description}}`
- AI assistant type per codebase
- Docker/GCP configuration

### **2. remote_agent_conversations**
- Platform conversation tracking (GitHub issue, Telegram chat)
- Platform type + conversation ID (unique constraint)
- Linked to codebase via foreign key
- AI assistant type locked at creation
- Worktree path for parallel development

### **3. remote_agent_sessions**
- AI session management
- Active session flag (one per conversation)
- Session ID for resume capability
- Metadata JSONB for command context

### **Additional Tables**
- `remote_agent_command_templates` - Global command templates
- `remote_agent_messages` - Message history
- `remote_agent_cli_events` - CLI event tracking for Web UI
- `remote_agent_port_allocations` - Port management

---

## Critical Concepts

### Session vs Conversation

- **Conversation** = Platform thread (1 per GitHub issue, 1 per Telegram chat)
- **Session** = AI interaction phase (multiple per conversation)

For plan→execute: **NEW session** provides AI separation, same conversation tracks platform context.

### Streaming Modes

Platform-specific streaming configuration:
- **Stream Mode**: Real-time chunks (ideal for chat platforms)
- **Batch Mode**: Accumulated final response (ideal for issue trackers)

Defaults:
- Telegram/Slack: `stream` mode
- GitHub/Discord: `batch` mode

### Command Variable Substitution

Commands support variable substitution:
- `$1`, `$2`, `$3` - Positional arguments
- `$ARGUMENTS` - All arguments as single string
- `$PLAN` - Previous plan from session metadata
- `$IMPLEMENTATION_SUMMARY` - Previous execution summary

### Git Worktrees

Enable parallel development per conversation without branch conflicts:
- Each conversation can have its own worktree
- Isolated working directories for safety
- Automatic cleanup when done

---

## How to Use This Guide

1. **Command Reference** (`01-command-reference.md`): Detailed documentation of every command
2. **Workflow Patterns** (`02-workflow-patterns.md`): Common workflows and best practices
3. **Decision Tree** (`03-decision-tree.md`): Quick lookup for "which command should I use?"
4. **Subagent Patterns** (`04-subagent-patterns.md`): Using Task tool and specialized agents
5. **Advanced Techniques** (`05-advanced-techniques.md`): Power user patterns and optimization

---

## Your Role as Orchestrator

As the Project Orchestrator Agent, you must:

1. **Know all commands intimately** - Understand purpose, inputs, outputs, when to use
2. **Route intelligently** - Choose the right command for the user's intent
3. **Guide proactively** - Suggest workflows before users ask
4. **Maintain context** - Track conversation state, remember what was done
5. **Adapt dynamically** - Switch strategies when situations change
6. **Ensure quality** - Always validate, always test, always review

**Golden Rule**: The user trusts you to orchestrate the entire development workflow. Be proactive, be thorough, be reliable.

---

**Next**: Read `01-command-reference.md` for detailed command documentation.
