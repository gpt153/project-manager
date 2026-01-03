# Project Orchestrator Agent - Complete Guide

**Comprehensive documentation for mastering Remote Coding Agent workflows and commands**

---

## 📚 Documentation Index

This guide provides complete expert-level knowledge for orchestrating development workflows with the Remote Coding Agent platform.

### [00 - Overview](./00-overview.md)
**Start Here**: Introduction to the Remote Coding Agent platform, core principles, and the PIV Loop mental model.

**Topics Covered**:
- What is SCAR (Remote Coding Agent)?
- Core architecture and principles
- Command categories overview
- PIV Loop workflow
- Database schema basics
- Critical concepts (sessions vs conversations, streaming modes)

**Read this first** to understand the foundation.

---

### [01 - Command Reference](./01-command-reference.md)
**Complete Catalog**: Detailed documentation of every command with usage, arguments, and examples.

**Command Categories**:
- **Core PIV Loop**: `/prime`, `/plan-feature`, `/execute`
- **Experimental PIV Loop**: `/plan`, `/implement`, `/rca`, `/fix-rca`, `/fix-issue`, `/commit`, `/create-pr`, `/review-pr`, `/merge-pr`, `/worktree`, `/router`, and more
- **Validation**: `/validate`, `/code-review`, `/code-review-fix`, `/system-review`
- **GitHub-Specific**: `/github_bug_fix:rca`, `/github_bug_fix:implement-fix`
- **General Purpose**: `/create-prd`, `/end-to-end-feature`

**Use this** as your reference when you need to know:
- What a command does
- When to use it
- What arguments it takes
- What output it produces

---

### [02 - Workflow Patterns](./02-workflow-patterns.md)
**Practical Scenarios**: Common workflows, decision trees, and best practices for real-world development.

**Workflows Covered**:
- Standard feature development (full PIV loop)
- Quick feature development (lightweight)
- Bug investigation & fix (RCA workflows)
- GitHub issue workflows (auto-routing)
- Code review & quality assurance
- Release management
- Parallel development (worktrees)
- Emergency hotfix procedures
- Safe refactoring

**Includes**:
- Decision trees for "which command should I use?"
- Best practices for each workflow type
- Common pitfalls to avoid

**Use this** when deciding which workflow to follow for a given situation.

---

### [03 - Decision Tree](./03-decision-tree.md)
**Quick Reference**: Fast lookup for choosing the right command based on user intent.

**Quick Guides**:
- "User says: Fix this bug..." → Decision tree
- "User says: Add feature..." → Decision tree
- "User says: @remote-agent" → Router logic
- Before committing code → What to run
- Before merging PR → Checklist
- Emergency production issue → Fast path

**Complexity Matrix**:
- Task type × Complexity → Recommended workflow

**Platform-Specific**:
- Telegram topics workflow
- GitHub issues workflow
- GitHub PR workflow

**Use this** for quick decision-making without reading full documentation.

---

### [04 - Subagent Patterns](./04-subagent-patterns.md)
**Advanced Coordination**: Using Task tool and specialized agents effectively.

**Topics Covered**:
- What are subagents and when to use them
- Available subagents: Explore, Plan, general-purpose, claude-code-guide
- Coordination patterns:
  - Sequential dependency
  - Parallel independent
  - Explore → Plan → Execute
  - Background processing
  - Resume for follow-up
- Best practices for task descriptions, context, model selection
- Common antipatterns to avoid

**Use this** when you need to:
- Explore large codebases
- Plan complex features
- Run parallel research
- Coordinate multi-step workflows

---

### [05 - Advanced Techniques](./05-advanced-techniques.md)
**Power User Strategies**: Optimization, error recovery, and expert patterns.

**Topics Covered**:
- Session management mastery (understanding session separation)
- Command chaining (sequential workflows, conditional branching)
- Context optimization (minimize tokens, maximize plan quality)
- Error recovery (validation failures, plan outdated, test failures)
- Performance optimization (parallel execution, caching, model selection)
- Quality assurance (multi-level validation, checklists)
- Production best practices (feature flags, migrations, canary deployments)
- Expert patterns (trust but verify, plan once execute many, fail fast recover fast)

**Use this** when you want to:
- Optimize workflows for speed and cost
- Handle complex error scenarios
- Ensure production readiness
- Master advanced patterns

---

## 🎯 Quick Start Guide

### For First-Time Users

1. **Read Overview** (`00-overview.md`)
   - Understand the PIV Loop
   - Learn core concepts
   - See the big picture

2. **Browse Command Reference** (`01-command-reference.md`)
   - Familiarize yourself with available commands
   - Understand command structure

3. **Study Workflow Patterns** (`02-workflow-patterns.md`)
   - Learn standard feature development workflow
   - Understand bug fix workflow
   - See practical examples

4. **Bookmark Decision Tree** (`03-decision-tree.md`)
   - Use for quick lookups during work

### For Experienced Users

1. **Decision Tree** (`03-decision-tree.md`) - Quick command selection
2. **Advanced Techniques** (`05-advanced-techniques.md`) - Optimization strategies
3. **Subagent Patterns** (`04-subagent-patterns.md`) - Complex coordination

---

## 🔍 How to Use This Guide

### Scenario 1: "I need to add a new feature"

**Path**:
1. Decision Tree → "User says: Add feature..."
2. Workflow Patterns → "Standard Feature Development"
3. Command Reference → Details on `/prime`, `/plan-feature`, `/execute`

### Scenario 2: "Something is broken and I don't know why"

**Path**:
1. Decision Tree → "Bug fix: RCA or quick fix?"
2. Workflow Patterns → "Bug Investigation & Fix"
3. Command Reference → Details on `/rca`, `/fix-rca`

### Scenario 3: "How do I use subagents effectively?"

**Path**:
1. Subagent Patterns → Read entire document
2. Advanced Techniques → "Multi-Agent Research Pipeline"

### Scenario 4: "I want to optimize my workflow"

**Path**:
1. Advanced Techniques → "Performance Optimization"
2. Advanced Techniques → "Context Optimization"
3. Best Practices → Review all antipatterns

---

## 🎓 Learning Path

### Beginner (Week 1)
- [ ] Read Overview completely
- [ ] Study Core PIV Loop commands in Command Reference
- [ ] Practice: Standard Feature Development workflow
- [ ] Practice: Simple bug fix workflow

### Intermediate (Week 2-3)
- [ ] Study all Experimental PIV Loop commands
- [ ] Learn Validation commands
- [ ] Practice: GitHub issue workflows
- [ ] Practice: Code review workflows
- [ ] Start using Decision Tree for daily work

### Advanced (Week 4+)
- [ ] Master Subagent Patterns
- [ ] Study Advanced Techniques thoroughly
- [ ] Implement custom workflows
- [ ] Optimize for speed and quality
- [ ] Build command library for your domain

### Expert (Ongoing)
- [ ] Contribute improvements to workflows
- [ ] Create domain-specific commands
- [ ] Share best practices with team
- [ ] Continuously refine processes

---

## 📊 Command Quick Reference

| Command | Use Case | Complexity |
|---------|----------|------------|
| `/core_piv_loop:prime` | Load project context | Any |
| `/core_piv_loop:plan-feature` | Plan comprehensive feature | Medium-High |
| `/core_piv_loop:execute` | Implement with Archon tracking | Medium-High |
| `/exp-piv-loop:plan` | Quick planning with research | Low-Medium |
| `/exp-piv-loop:implement` | Autonomous implementation | Low-Medium |
| `/exp-piv-loop:rca` | Root cause analysis | Bug investigation |
| `/exp-piv-loop:fix-issue` | Quick bug fix | Simple bugs |
| `/exp-piv-loop:commit` | Conventional commit | After implementation |
| `/exp-piv-loop:create-pr` | Create pull request | Ready for review |
| `/exp-piv-loop:review-pr` | Comprehensive review | Before merge |
| `/validation:code-review` | Quality check | Pre-commit |
| `/validation:validate` | Full E2E validation | Pre-deployment |

---

## 🚀 Best Practices Summary

1. **Always start with context** - Use `/prime` for new codebases
2. **Plan before implementing** - Use appropriate plan command
3. **Validate continuously** - Test after each major task
4. **Use the right workflow** - Match complexity to workflow
5. **Leverage subagents** - For exploration and research
6. **Trust but verify** - Let AI work, but check results
7. **Document everything** - Keep plans, RCAs, reviews
8. **Iterate and improve** - Learn from each workflow

---

## 🆘 Common Questions

**Q: Which planning command should I use?**
A: See Decision Tree → "Which planning command?" section

**Q: When do I create a new session?**
A: Only plan→execute transition creates new session. See Advanced Techniques → "Session Management Mastery"

**Q: How do I use subagents?**
A: See Subagent Patterns → Complete guide with examples

**Q: What's the fastest workflow for simple features?**
A: See Workflow Patterns → "Quick Feature (Lightweight)"

**Q: How do I handle production bugs?**
A: See Workflow Patterns → "Emergency Hotfix"

---

## 📝 Contributing

This documentation is meant to be a living guide. As you discover new patterns, optimization strategies, or best practices:

1. Document them
2. Share with the team
3. Update this guide
4. Help others learn

---

## 📖 Version

- **Version**: 1.0
- **Created**: 2025-12-26
- **Last Updated**: 2025-12-26
- **Comprehensive Coverage**: All slash commands, subagents, and workflows

---

**You are now ready to orchestrate Remote Coding Agent workflows like an expert.**

Start with **00-overview.md** and work your way through the guide. Reference the **Decision Tree** for quick lookups. Master the **Advanced Techniques** for power user capabilities.

Happy orchestrating! 🎯
