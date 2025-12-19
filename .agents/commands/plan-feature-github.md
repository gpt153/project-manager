---
description: "Create comprehensive feature plan with GitHub workflow integration"
---

# Plan a new task (GitHub Workflow)

## Feature: $ARGUMENTS

## Mission

Transform a feature request into a **comprehensive implementation plan** through systematic codebase analysis, external research, and strategic planning. This plan will be committed to a feature branch and used for GitHub-based implementation workflow.

**Core Principle**: We do NOT write code in this phase. Our goal is to create a context-rich implementation plan that enables one-pass implementation success for AI agents working in GitHub workflows.

**Key Philosophy**: Context is King. The plan must contain ALL information needed for implementation - patterns, mandatory reading, documentation, validation commands - so the execution agent succeeds on the first attempt.

**HARD CONSTRAINT**: The final plan MUST be between 500-700 lines total. Be concise while comprehensive. Reference patterns instead of repeating them. Group related tasks. Remove redundancy.

## GitHub Workflow Integration

This command creates a feature branch and commits the plan to it, preparing for GitHub-native implementation workflow.

**Branch Naming**: Feature branches follow the pattern `feature-<descriptive-name>` (e.g., `feature-add-user-auth`, `feature-streaming-api`)

**Plan Location**: Plans are committed to `.agents/plans/{kebab-case-name}.md` within the feature branch

**GitHub Context**: You have access to GitHub CLI (`gh`) for and can use commands like:
- `gh issue view <number>` - View issue details
- `gh pr view <number>` - View pull request details
- `gh repo view` - View repository information

## Planning Process

### Phase 1: Feature Understanding

**Deep Feature Analysis:**

- Extract the core problem being solved
- Identify user value and business impact
- Determine feature type: New Capability/Enhancement/Refactor/Bug Fix
- Assess complexity: Low/Medium/High
- Map affected systems and components

**Create User Story Format Or Refine If Story Was Provided By The User:**

```
As a <type of user>
I want to <action/goal>
So that <benefit/value>
```

### Phase 2: Codebase Intelligence Gathering

**Use specialized agents and parallel analysis:**

**1. Project Structure Analysis**

- Detect primary language(s), frameworks, and runtime versions
- Map directory structure and architectural patterns
- Identify service/component boundaries and integration points
- Locate configuration files (pyproject.toml, package.json, etc.)
- Find environment setup and build processes

**2. Pattern Recognition** (Use specialized subagents when beneficial)

- Search for similar implementations in codebase
- Identify coding conventions:
  - Naming patterns (CamelCase, snake_case, kebab-case)
  - File organization and module structure
  - Error handling approaches
  - Logging patterns and standards
- Extract common patterns for the feature's domain
- Document anti-patterns to avoid
- Check CLAUDE.md for project-specific rules and conventions

**3. Dependency Analysis**

- Catalog external libraries relevant to feature
- Understand how libraries are integrated (check imports, configs)
- Find relevant documentation in docs/, ai_docs/, .agents/reference or ai-wiki if available
- Note library versions and compatibility requirements

**4. Testing Patterns**

- Identify test framework and structure (pytest, jest, etc.)
- Find similar test examples for reference
- Understand test organization (unit vs integration)
- Note coverage requirements and testing standards

**5. Integration Points**

- Identify existing files that need updates
- Determine new files that need creation and their locations
- Map router/API registration patterns
- Understand database/model patterns if applicable
- Identify authentication/authorization patterns if relevant

**Clarify Ambiguities:**

- If requirements are unclear at this point, ask the user to clarify before you continue
- Get specific implementation preferences (libraries, approaches, patterns)
- Resolve architectural decisions before proceeding

### Phase 3: External Research & Documentation

**Use specialized subagents when beneficial for external research:**

**Research Report Validation (CRITICAL FIRST STEP):**

Before conducting new research, validate existing research reports:

- Check `.agents/report/` for relevant research documents
- **Read each report thoroughly** - don't just skim
- **Validate completeness** - does it answer ALL implementation questions?
  - Are ALL mentioned components/patterns actually explained with code examples?
  - Does it cover edge cases and error handling?
  - Are there references to concepts without full implementation details?
- **Identify gaps** - what's mentioned but not fully explained?
- **Fill gaps immediately** - research missing details before proceeding
- Document which reports were validated and any gaps found

**Example Gap Analysis:**
```markdown
Report: research-report-streaming.md
✓ Covers: Basic streaming pattern
✗ Gap Found: Mentions CallToolsNode but no handling code
✗ Gap Found: Says "first chunk includes role" but no empty chunk requirement
→ Action: Research OpenAI SSE spec for first chunk requirements
→ Action: Research Pydantic AI CallToolsNode attributes and usage
```

**Documentation Gathering:**

- Research latest library versions and best practices
- Find official documentation with specific section anchors
- Locate implementation examples and tutorials
- Identify common gotchas and known issues
- Check for breaking changes and migration guides

**Technology Trends:**

- Research current best practices for the technology stack
- Find relevant blog posts, guides, or case studies
- Identify performance optimization patterns
- Document security considerations

**Compile Research References:**

```markdown
## Relevant Documentation

- [Library Official Docs](https://example.com/docs#section)
  - Specific feature implementation guide
  - Why: Needed for X functionality
- [Framework Guide](https://example.com/guide#integration)
  - Integration patterns section
  - Why: Shows how to connect components
```

**External Package API Verification (CRITICAL for new dependencies):**

When the feature requires adding a new external Python package:

1. **Verify Package Name vs Import Name**
   - PyPI package name often differs from Python import name
   - Example: `brave-search-python-client` (package) → `brave_search_python_client` (import)
   - NEVER assume they're identical - always verify

2. **Test Actual API Before Planning**
   ```bash
   # Install package
   uv add <package-name>

   # Test import and inspect API
   uv run python -c "from package_name import ClassName; help(ClassName)" | head -50
   ```

3. **Document Verified API in Plan**
   - Correct import statements with actual class/function names
   - Actual method signatures (sync vs async, parameters)
   - Required request/response objects
   - Include code examples from package documentation

4. **Common API Verification Mistakes to Avoid**
   - ❌ Assuming class name from package name (e.g., `BraveSearchClient` vs actual `BraveSearch`)
   - ❌ Guessing method names (e.g., `.search()` vs actual `.web()`)
   - ❌ Missing required request objects (e.g., `WebSearchRequest`)
   - ❌ Wrong sync/async usage (e.g., sync when package is async-only)

**Example Research Entry with API Verification:**
```markdown
### brave-search-python-client API

**Verified Import & API:**
```python
# ✓ Verified via: uv run python -c "from brave_search_python_client import BraveSearch; help(BraveSearch.web)"
from brave_search_python_client import BraveSearch, WebSearchRequest

# Class: BraveSearch (NOT BraveSearchClient)
# Method: async web(request: WebSearchRequest) - NOT search()
# Requires: WebSearchRequest object (NOT direct parameters)
```

**Documentation:**
- [Official API Docs](https://brave-search-python-client.readthedocs.io/)
- [GitHub Examples](https://github.com/helmut-hoffer-von-ankershoffen/brave-search-python-client/tree/main/examples)

**Why This Matters:** Prevents ModuleNotFoundError and AttributeError during implementation.
```

### Phase 4: Deep Strategic Thinking

**Think Harder About:**

- How does this feature fit into the existing architecture?
- What are the critical dependencies and order of operations?
- What could go wrong? (Edge cases, race conditions, errors)
- How will this be tested comprehensively?
- What performance implications exist?
- Are there security considerations?
- How maintainable is this approach?

**Design Decisions:**

- Choose between alternative approaches with clear rationale
- Design for extensibility and future modifications
- Plan for backward compatibility if needed
- Consider scalability implications

### Phase 5: Create Feature Branch & Commit Plan

**1. Create Feature Branch:**

```bash
# Generate descriptive branch name (e.g., feature-add-streaming-api)
git checkout -b feature-<descriptive-name>
```

**Branch name should be:**
- Lowercase with hyphens
- Descriptive and concise (3-5 words max)
- Clearly indicate the feature (e.g., `feature-user-auth`, `feature-rag-pipeline`, `feature-streaming-response`)

**2. Generate Plan Structure:**

Create comprehensive plan with the following structure template:

```markdown
# Feature: <feature-name>

The following plan should be complete, but its important that you validate documentation and codebase patterns and task sanity before you start implementing.

Pay special attention to naming of existing utils types and models. Import from the right files etc.

## Feature Description

<Detailed description of the feature, its purpose, and value to users>

## User Story

As a <type of user>
I want to <action/goal>
So that <benefit/value>

## Problem Statement

<Clearly define the specific problem or opportunity this feature addresses>

## Solution Statement

<Describe the proposed solution approach and how it solves the problem>

## Feature Metadata

**Feature Type**: [New Capability/Enhancement/Refactor/Bug Fix]
**Estimated Complexity**: [Low/Medium/High]
**Primary Systems Affected**: [List of main components/services]
**Dependencies**: [External libraries or services required]

---

## CONTEXT REFERENCES

### Relevant Codebase Files IMPORTANT: YOU MUST READ THESE FILES BEFORE IMPLEMENTING!

<List files with line numbers and relevance>

- `path/to/file.py` (lines 15-45) - Why: Contains pattern for X that we'll mirror
- `path/to/model.py` (lines 100-120) - Why: Database model structure to follow
- `path/to/test.py` - Why: Test pattern example

### New Files to Create

- `path/to/new_service.py` - Service implementation for X functionality
- `path/to/new_model.py` - Data model for Y resource
- `tests/path/to/test_new_service.py` - Unit tests for new service

### Relevant Documentation YOU SHOULD READ THESE BEFORE IMPLEMENTING!

- [Documentation Link 1](https://example.com/doc1#section)
  - Specific section: Authentication setup
  - Why: Required for implementing secure endpoints
- [Documentation Link 2](https://example.com/doc2#integration)
  - Specific section: Database integration
  - Why: Shows proper async database patterns

### Patterns to Follow

<Specific patterns extracted from codebase - include actual code examples from the project>

**Naming Conventions:** (for example)

**Error Handling:** (for example)

**Logging Pattern:** (for example)

**Other Relevant Patterns:** (for example)

---

## IMPLEMENTATION PLAN

### Phase 1: Foundation

<Describe foundational work needed before main implementation>

**Tasks:**

- Set up base structures (schemas, types, interfaces)
- Configure necessary dependencies
- Create foundational utilities or helpers

### Phase 2: Core Implementation

<Describe the main implementation work>

**Tasks:**

- Implement core business logic
- Create service layer components
- Add API endpoints or interfaces
- Implement data models

### Phase 3: Integration

<Describe how feature integrates with existing functionality>

**Tasks:**

- Connect to existing routers/handlers
- Register new components ⚠️ **CRITICAL: Preserve import order for side-effect imports** (use `# ruff: noqa: I001`)
- Update configuration files
- Add middleware or interceptors if needed

### Phase 4: Testing & Validation

<Describe testing approach>

**Tasks:**

- Implement unit tests for each component
- Create integration tests for feature workflow
  - **Pattern:** Test service layer functions directly (NOT tool registration with RunContext)
  - **Example:** `await service.execute_function(vault_manager, params...)`
- Add edge case tests
- Validate against acceptance criteria

---

## STEP-BY-STEP TASKS

IMPORTANT: Execute every task in order, top to bottom. Each task is atomic and independently testable.

### Task Format Guidelines

Use information-dense keywords for clarity:

- **CREATE**: New files or components
- **UPDATE**: Modify existing files
- **ADD**: Insert new functionality into existing code
- **REMOVE**: Delete deprecated code
- **REFACTOR**: Restructure without changing behavior
- **MIRROR**: Copy pattern from elsewhere in codebase

### {ACTION} {target_file}

- **IMPLEMENT**: {Specific implementation detail}
- **PATTERN**: {Reference to existing pattern - file:line}
- **IMPORTS**: {Required imports and dependencies}
- **GOTCHA**: {Known issues or constraints to avoid}
- **VALIDATE**: `{executable validation command}`

<Continue with all tasks in dependency order...>

---

## TESTING STRATEGY

<Define testing approach based on project's test framework and patterns discovered in during research>

### Unit Tests

<Scope and requirements based on project standards>

Design unit tests with fixtures and assertions following existing testing approaches

### Integration Tests

<Scope and requirements based on project standards>

### Edge Cases

<List specific edge cases that must be tested for this feature>

---

## VALIDATION COMMANDS

<Define validation commands based on project's tools discovered in Phase 2>

Execute every command to ensure zero regressions and 100% feature correctness.

### Level 1: Import Validation (CRITICAL)

**Verify all imports resolve before running tests:**

```bash
uv run python -c "from app.main import app; print('✓ All imports valid')"
```

**Expected:** "✓ All imports valid" (no ModuleNotFoundError or ImportError)

**Why:** Catches incorrect package imports immediately. If this fails, fix imports before proceeding.

### Level 2: Syntax & Style

<Project-specific linting and formatting commands>

### Level 3: Unit Tests

<Project-specific unit test commands>

### Level 4: Integration Tests

<Project-specific integration test commands>

### Level 5: Manual Validation

<Feature-specific manual testing steps - API calls, UI testing, etc.>

### Level 6: Additional Validation (Optional)

<MCP servers or additional CLI tools if available>

---

## ACCEPTANCE CRITERIA

<List specific, measurable criteria that must be met for completion>

- [ ] Feature implements all specified functionality
- [ ] All validation commands pass with zero errors
- [ ] Unit test coverage meets requirements (80%+)
- [ ] Integration tests verify end-to-end workflows
- [ ] Code follows project conventions and patterns
- [ ] No regressions in existing functionality
- [ ] Documentation is updated (if applicable)
- [ ] Performance meets requirements (if applicable)
- [ ] Security considerations addressed (if applicable)

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Each task validation passed immediately
- [ ] All validation commands executed successfully
- [ ] Full test suite passes (unit + integration)
- [ ] No linting or type checking errors
- [ ] Manual testing confirms feature works
- [ ] Acceptance criteria all met
- [ ] Code reviewed for quality and maintainability

---

## NOTES

<Additional context, design decisions, trade-offs>
```

**3. Commit Plan to Feature Branch:**

```bash
# Create .agents/plans directory if it doesn't exist
mkdir -p .agents/plans

# Write plan to file
# Filename: .agents/plans/{kebab-case-descriptive-name}.md

# Commit the plan
git add .agents/plans/{plan-name}.md
git commit -m "Add implementation plan for {feature-name}"

# Push feature branch to GitHub
git push -u origin feature-<descriptive-name>
```

## Output Format

### GitHub Comment Summary

Provide a final summary that will be automatically posted as a GitHub comment (you don't need to do that yourself). This should include:

```markdown
## 📋 Implementation Plan Created

**Feature Branch:** `feature-<branch-name>`
**Plan Location:** `.agents/plans/<plan-name>.md`

### Summary
<Brief 2-3 sentence summary of what this feature does and why>

### Complexity Assessment
**Complexity**: [Low/Medium/High]
**Estimated Confidence**: [X/10] for one-pass implementation success

### Key Implementation Details
- **Primary Systems**: <List main components affected>
- **New Dependencies**: <Any new libraries required, or "None">
- **Breaking Changes**: <Yes/No and explanation if yes>

### Implementation Approach
<2-3 bullet points summarizing the approach>

### Risks & Considerations
<Key risks or things to watch out for during implementation>

### Next Steps
To implement this plan, use:
```bash
@remote-agent /command-invoke execute-github .agents/plans/<plan-name>.md feature-<branch-name>
```

**Branch Status**: Plan committed and pushed to `feature-<branch-name>`
**Ready for Implementation**: ✅
```

## Quality Criteria

### Context Completeness ✓

- [ ] All necessary patterns identified and documented
- [ ] External library usage documented with links
- [ ] Integration points clearly mapped
- [ ] Gotchas and anti-patterns captured
- [ ] Every task has executable validation command

### Implementation Ready ✓

- [ ] Another developer could execute without additional context
- [ ] Tasks ordered by dependency (can execute top-to-bottom)
- [ ] Each task is atomic and independently testable
- [ ] Pattern references include specific file:line numbers

### Pattern Consistency ✓

- [ ] Tasks follow existing codebase conventions
- [ ] New patterns justified with clear rationale
- [ ] No reinvention of existing patterns or utils
- [ ] Testing approach matches project standards

### Information Density ✓

- [ ] No generic references (all specific and actionable)
- [ ] URLs include section anchors when applicable
- [ ] Task descriptions use codebase keywords
- [ ] Validation commands are non interactive executable

### GitHub Integration ✓

- [ ] Feature branch created with proper naming convention
- [ ] Plan committed to feature branch
- [ ] Branch pushed to GitHub remote
- [ ] Final summary formatted for GitHub comment

## Success Metrics

**One-Pass Implementation**: Execution agent can complete feature without additional research or clarification

**Validation Complete**: Every task has at least one working validation command

**Context Rich**: The Plan passes "No Prior Knowledge Test" - someone unfamiliar with codebase can implement using only Plan content

**GitHub Ready**: Plan is committed to feature branch and ready for GitHub-native workflow

**Confidence Score**: X/10 that execution will succeed on first attempt
