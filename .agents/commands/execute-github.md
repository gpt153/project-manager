---
description: Execute an implementation plan in GitHub workflow
argument-hint: [path-to-plan] [feature-branch]
---

# Execute: Implement from Plan (GitHub Workflow)

## Arguments

- **Plan Path** (`$1`): Path to the implementation plan file (e.g., `.agents/plans/add-user-auth.md`)
- **Feature Branch** (`$2`): Name of the feature branch to work on (e.g., `feature-add-user-auth`)

## Plan to Execute

Read plan file: `$1`

## Feature Branch

Checkout and work on branch: `$2`

## Execution Instructions

### 0. Setup: Checkout Feature Branch

Before starting implementation, ensure you're on the correct feature branch:

```bash
# Fetch latest changes from remote
git fetch origin

# Checkout the feature branch
git checkout $2

# Pull latest changes from the feature branch
git pull origin $2
```

**Verify you're on the correct branch:**
```bash
git branch --show-current
# Should output: $2
```

### 1. Read and Understand

- Read the ENTIRE plan carefully from `$1`
- Understand all tasks and their dependencies
- Note the validation commands to run
- Review the testing strategy
- Understand acceptance criteria

### 2. Execute Tasks in Order

For EACH task in "Step by Step Tasks":

#### a. Navigate to the task
- Identify the file and action required
- Read existing related files if modifying

#### b. Implement the task
- Follow the detailed specifications exactly
- Maintain consistency with existing code patterns
- Include proper type hints and documentation
- Add structured logging where appropriate

#### c. Verify as you go
- After each file change, check syntax
- Ensure imports are correct
- Verify types are properly defined

#### d. Commit incrementally
- Make small, focused commits as you complete tasks
- Use descriptive commit messages
- Example: `feat: implement streaming response handler`

### 3. Implement Testing Strategy

After completing implementation tasks:

**Recommended Approach:** Write failing tests first for complex logic (especially path handling, type conversions). This provides faster feedback than implementing then testing.

- Create all test files specified in the plan
- Implement all test cases mentioned
- Follow the testing approach outlined
- Ensure tests cover edge cases

### 4. Run Validation Commands

Execute ALL validation commands from the plan in order:

```bash
# Run each command exactly as specified in plan
```

If any command fails:
- Fix the issue
- Re-run the command
- Continue only when it passes

### 5. Final Verification

Before creating pull request:

- ✅ All tasks from plan completed
- ✅ All tests created and passing
- ✅ All validation commands pass
- ✅ Code follows project conventions
- ✅ Documentation added/updated as needed
- ✅ All changes committed to feature branch

### 6. Create Pull Request to Staging

Once all validation passes, create a pull request to the **staging** branch:

```bash
# Push all commits to the feature branch
git push origin $2

# Create PR to staging branch (NOT main)
gh pr create \
  --base staging \
  --head $2 \
  --title "Feature: <descriptive-title>" \
  --body "$(cat <<EOF
## Summary
<Brief description of what this PR implements>

## Implementation Plan
Implemented from plan: \`$1\`

## Changes
- <List major changes>
- <Include files created/modified>

## Testing
- ✅ All unit tests passing
- ✅ All integration tests passing
- ✅ All validation commands passed

## Validation Results
\`\`\`bash
# Output from validation commands
<Include key validation results>
\`\`\`

## Acceptance Criteria
<List acceptance criteria from plan with checkboxes>
- [ ] Criterion 1
- [ ] Criterion 2

## Ready for Review
All implementation tasks completed and validated. Ready for staging deployment and testing.
EOF
)"
```

**Important Notes:**
- PRs target **staging** branch, NOT main
- Staging branch is used for testing before production merge
- Use descriptive PR title that clearly indicates the feature
- Include comprehensive PR description with testing results

### 7. Capture PR Information

After creating the PR, capture the PR URL:

```bash
# Get the PR URL for the feature branch
gh pr view $2 --json url --jq .url
```

## Output Report

Provide a comprehensive summary that will be automatically posted as a GitHub comment (you don't have to do this yourself):

```markdown
## ✅ Implementation Complete

**Feature Branch:** `$2`
**Implementation Plan:** `$1`
**Pull Request:** <PR-URL>

### Summary
<Brief 2-3 sentence summary of what was implemented>

### Completed Tasks
<Summarize major tasks completed>

#### Files Created
- `path/to/new_file1.py` - <Purpose>
- `path/to/new_file2.py` - <Purpose>
- `tests/path/to/test_file.py` - <Test coverage>

#### Files Modified
- `path/to/modified_file1.py` - <Changes made>
- `path/to/modified_file2.py` - <Changes made>

### Tests Added
**Test Files Created:**
- `tests/path/to/test_suite.py` - <Number> test cases

**Test Coverage:**
- Unit tests: ✅ All passing
- Integration tests: ✅ All passing
- Edge cases: ✅ Covered

### Validation Results
```bash
# Linting
<Output from linting commands>

# Type Checking
<Output from type checking>

# Test Suite
<Output from test runs with pass/fail counts>
```

**All Validation:** ✅ Passed

### Acceptance Criteria
<List each criterion from plan with ✅ or ❌>
- ✅ Criterion 1 - Met
- ✅ Criterion 2 - Met
- ✅ All validation commands passed
- ✅ Tests provide adequate coverage
- ✅ Code follows project conventions

### Pull Request Details
- **Target Branch:** `staging`
- **Status:** Open and ready for review
- **Link:** <PR-URL>

### Deployment Notes
<Any important notes for staging deployment or testing>

### Next Steps
1. Review the pull request: <PR-URL>
2. Test in staging environment
3. If staging tests pass, merge to staging
4. After staging validation, create PR from staging to main for production deployment

---

**Implementation Status:** ✅ Complete
**Branch:** `$2`
**PR:** <PR-URL>
```

## Error Handling

If you encounter issues during execution:

### Plan Deviations
- Document any deviations from the plan
- Explain why deviation was necessary
- Update the implementation approach accordingly

### Validation Failures
- Never skip validation steps
- Fix all failures before creating PR
- Document any persistent issues in PR description

### Unexpected Complexity
- If tasks are more complex than planned, break them down further
- Add additional commits with clear messages
- Document complexity issues in final report

### Missing Information
- If plan lacks necessary details, research and document
- Add findings to implementation notes
- Consider creating research report for future reference

## Notes

- Always work on the specified feature branch (`$2`)
- All PRs target **staging** branch, not main
- Commit frequently with descriptive messages
- Run validation commands before creating PR
- Include comprehensive testing in PR description
- Document any deviations from the plan
- Feature branches follow naming convention: `feature-<descriptive-name>`

## Quality Checklist

Before marking as complete:

- [ ] All tasks from plan implemented
- [ ] All tests passing
- [ ] All validation commands successful
- [ ] Code follows project patterns and conventions
- [ ] Proper error handling implemented
- [ ] Documentation updated (if applicable)
- [ ] PR created with comprehensive description
- [ ] PR targets staging branch
- [ ] All commits have clear messages
- [ ] No debugging code or console.logs left behind
- [ ] Performance considerations addressed
- [ ] Security best practices followed

## Success Criteria

**Implementation Success**: All tasks completed, all tests passing, all validation commands successful

**PR Quality**: Comprehensive description, clear testing results, ready for review

**GitHub Integration**: PR created to staging, branch naming follows convention, proper commit history

**Documentation**: Final report includes all required sections with accurate information
