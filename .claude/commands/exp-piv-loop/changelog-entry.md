---
description: Add an entry to CHANGELOG.md [Unreleased] section
argument-hint: [category] <description> or just <description>
---

# Add Changelog Entry

**Input**: $ARGUMENTS

---

## Purpose

Add a single entry to the `[Unreleased]` section of CHANGELOG.md. This command is atomic and composable - chain it with `/create-pr`, `/merge-pr`, or any other command via workflows.

---

## Phase 1: Parse Input

### 1.1 Understand the Input

Input could be:
- **Category + description**: `added New Discord adapter with thread support`
- **Just description**: `Fix rate limiting on GitHub webhooks` (infer category)
- **PR reference**: `#73` or `https://github.com/owner/repo/pull/73` (extract from PR)
- **Natural language**: `the slack changes we just merged`

### 1.2 Determine Category

**Keep a Changelog categories** (use exactly these names):
- **Added** - new features
- **Changed** - changes in existing functionality
- **Deprecated** - soon-to-be removed features
- **Removed** - removed features
- **Fixed** - bug fixes
- **Security** - vulnerability fixes

**Category inference rules:**
- `feat:` commits or "add", "new", "introduce" → **Added**
- `fix:` commits or "fix", "resolve", "correct" → **Fixed**
- `change`, "update", "modify", "improve" → **Changed**
- `deprecate`, "will be removed" → **Deprecated**
- `remove`, "delete", "drop" → **Removed**
- `security`, "vulnerability", "CVE" → **Security**

If unclear, ask: "What category should this be? (Added/Changed/Fixed/etc.)"

### 1.3 Format the Entry

**Entry format:**
```
- <Description> ([#PR](url) or commit reference if available)
```

**Examples:**
```
- Add Slack adapter with Socket Mode support (#73)
- Fix shared worktree cleanup preventing duplicate removal errors (#72)
- Change default streaming mode for GitHub to batch
```

**Rules:**
- Start with capital letter
- Use imperative mood ("Add", not "Added" or "Adds")
- Keep under 80 characters if possible
- Include PR/issue reference if known
- No period at the end

---

## Phase 2: Check CHANGELOG.md

### 2.1 Verify File Exists

```bash
ls -la CHANGELOG.md
```

**If missing**, create with template:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

### Fixed
```

### 2.2 Read Current State

```bash
cat CHANGELOG.md
```

Identify:
- Where is `## [Unreleased]` section?
- Does the category subsection exist?
- Are there existing entries?

---

## Phase 3: Add Entry

### 3.1 Locate Insert Position

Find the `### <Category>` subsection under `## [Unreleased]`.

**If category subsection doesn't exist:**
1. Create it under `## [Unreleased]`
2. Order categories: Added, Changed, Deprecated, Removed, Fixed, Security

### 3.2 Insert Entry

Add the new entry as the first item under the category (newest first within unreleased).

**Example before:**
```markdown
## [Unreleased]

### Added
- Previous feature (#70)

### Fixed
- Old bug fix (#65)
```

**Example after adding "Add Slack adapter (#73)" to Added:**
```markdown
## [Unreleased]

### Added
- Add Slack adapter with Socket Mode support (#73)
- Previous feature (#70)

### Fixed
- Old bug fix (#65)
```

### 3.3 Handle Empty Categories

If a category section exists but is empty, add the entry directly:

```markdown
### Added
- Your new entry here
```

If category section doesn't exist, create it in the correct order.

---

## Phase 4: Output

### 4.1 Show Result

```
## Changelog Updated

**Category**: [Added/Changed/Fixed/etc.]
**Entry**: [the entry text]

Added to CHANGELOG.md under [Unreleased]
```

### 4.2 Show Diff (Optional)

```bash
git diff CHANGELOG.md
```

---

## Special Cases

### If Input is a PR Number/URL

1. Fetch PR details:
   ```bash
   gh pr view [NUMBER] --json title,number,url,body,labels
   ```
2. Extract title for description
3. Infer category from:
   - PR labels (e.g., `bug` → Fixed, `enhancement` → Added)
   - PR title prefix (e.g., `fix:` → Fixed)
   - PR body content
4. Format entry with PR reference

### If Input References Recent Work

Use conversation context to understand what was just done:
- "the changes we just made" → look at recent commits/files
- "the bug fix" → find recent fix: commits
- "the new feature" → find recent feat: commits

### If Entry Already Exists

Check if a similar entry already exists (same PR number or very similar description).
- If duplicate, inform user and don't add
- If similar but different, ask for confirmation

---

## Critical Reminders

1. **Keep a Changelog format** - Use exact category names, not variations
2. **Imperative mood** - "Add", not "Added" or "Adds"
3. **Reference PRs/issues** - Include (#123) when known
4. **Atomic entries** - One feature/fix per entry
5. **User-facing language** - Write for humans reading release notes, not developers reading commits

Now parse the input, determine the category, and add the entry to CHANGELOG.md.
