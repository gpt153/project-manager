---
description: Generate release notes from commits or changelog for GitHub Release
argument-hint: [version|since-tag] (optional - defaults to latest unreleased)
---

# Generate Release Notes

**Input**: $ARGUMENTS

---

## Purpose

Generate polished, user-facing release notes suitable for:
- GitHub Releases
- Announcements
- Documentation

This command can work from:
1. **CHANGELOG.md** - Extract and format a specific version's notes
2. **Git commits** - Analyze commits since a tag/commit and generate notes
3. **Combination** - Use changelog as base, enhance with commit details

---

## Phase 1: Determine Source

### 1.1 Parse Input

Input could be:
- **Version number**: `0.3.0` → extract from CHANGELOG.md
- **Tag reference**: `v0.2.0` or `since v0.2.0` → commits since that tag
- **Nothing**: Use `[Unreleased]` from CHANGELOG.md or commits since last tag

### 1.2 Check Available Sources

```bash
# Check for CHANGELOG.md
ls -la CHANGELOG.md

# Get last tag
git describe --tags --abbrev=0 2>/dev/null || echo "No tags"

# List recent tags
git tag --sort=-version:refname | head -5
```

### 1.3 Decide Strategy

**If version exists in CHANGELOG.md:**
- Extract that version's content
- Format for GitHub Release

**If version doesn't exist (or using commits):**
- Analyze commits since last tag
- Generate release notes from commit history
- Optionally cross-reference with CHANGELOG.md

---

## Phase 2: Extract from CHANGELOG.md

### 2.1 Read Changelog

```bash
cat CHANGELOG.md
```

### 2.2 Extract Version Section

Find the section for the requested version:
```markdown
## [0.3.0] - 2025-12-08

### Added
- Add Slack adapter with Socket Mode support (#73)
- Add Discord thread support (#71)

### Fixed
- Fix worktree cleanup duplicate removal (#72)
```

### 2.3 Format for GitHub Release

Transform to user-friendly format:

```markdown
## What's New

### New Features
- **Slack Integration**: Full Slack adapter with Socket Mode for real-time messaging (#73)
- **Discord Threads**: Discord adapter now supports threaded conversations (#71)

### Bug Fixes
- Fixed an issue where worktree cleanup could fail with duplicate removal errors (#72)

---

**Full Changelog**: https://github.com/owner/repo/compare/v0.2.0...v0.3.0
```

---

## Phase 3: Generate from Commits

### 3.1 Get Commit Range

```bash
# Find last tag
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null)

# If no tags, use initial commit
if [ -z "$LAST_TAG" ]; then
  LAST_TAG=$(git rev-list --max-parents=0 HEAD)
fi

# Get commits since last tag
git log ${LAST_TAG}..HEAD --pretty=format:"%h %s" --no-merges
```

### 3.2 Categorize Commits

Parse commit messages using conventional commits pattern:

```
feat(slack): Add Socket Mode support (#73)  → Added
fix(worktree): Prevent duplicate cleanup (#72) → Fixed
docs: Update deployment guide → Documentation
chore(deps): Bump dependencies → (skip or Dependencies)
refactor: Simplify adapter interface → (skip internal)
```

**Categorization rules:**
| Prefix | Category | Include in Notes |
|--------|----------|------------------|
| `feat:` | New Features | Yes |
| `fix:` | Bug Fixes | Yes |
| `perf:` | Performance | Yes |
| `security:` | Security | Yes |
| `docs:` | Documentation | Maybe (significant only) |
| `refactor:` | Internal | No |
| `test:` | Internal | No |
| `chore:` | Internal | No (unless deps) |
| `ci:` | Internal | No |

### 3.3 Extract PR/Issue References

For each commit, look for:
- `(#123)` - PR number
- `Fixes #123` - Issue reference
- `Closes #123` - Issue reference

### 3.4 Enhance with PR Details (Optional)

For significant changes, fetch PR details:
```bash
gh pr view 73 --json title,body,labels
```

Use PR description for richer release notes.

---

## Phase 4: Format Release Notes

### 4.1 Standard Format

```markdown
## What's New in v0.3.0

Brief overview paragraph describing the main theme of this release.

### Highlights
- **Major Feature**: One-sentence description of the biggest addition
- **Key Improvement**: Another significant change

### New Features
- Feature description with context (#PR)
- Another feature (#PR)

### Improvements
- Enhancement description (#PR)

### Bug Fixes
- Bug fix description (#PR)

### Security
- Security fix if any (#PR)

### Breaking Changes
- Description of breaking change and migration path

---

### Contributors
Thanks to @contributor1, @contributor2 for their contributions!

**Full Changelog**: https://github.com/owner/repo/compare/v0.2.0...v0.3.0
```

### 4.2 Tone Guidelines

**Do:**
- Write for users, not developers
- Explain the benefit, not just the change
- Use active voice ("Added", "Fixed", "Improved")
- Group related changes
- Highlight breaking changes prominently

**Don't:**
- Include internal refactoring
- Use technical jargon without explanation
- List every commit (consolidate related changes)
- Include merge commits

### 4.3 Examples of Good vs Bad Entries

**Bad (too technical):**
```
- Refactor IPlatformAdapter to use async generators
```

**Good (user-focused):**
```
- Slack messages now stream in real-time instead of waiting for complete response
```

**Bad (too vague):**
```
- Fix bug
```

**Good (specific):**
```
- Fixed an issue where Discord messages over 2000 characters would fail silently
```

---

## Phase 5: Output

### 5.1 Display Release Notes

Show the formatted release notes in full.

### 5.2 Save to File (Optional)

```bash
mkdir -p .agents/releases
```

Save to: `.agents/releases/v0.3.0-notes.md`

### 5.3 Provide Copy Command

```
## Release Notes Generated

Preview above. To create the GitHub Release:

/release 0.3.0

Or manually:
gh release create v0.3.0 --title "v0.3.0" --notes-file .agents/releases/v0.3.0-notes.md
```

---

## Special Cases

### No Tags Exist

If this is the first release:
- Use all commits since initial commit
- Note this is the initial release
- Focus on what the project does, not just what changed

### Many Commits (>50)

For large releases:
- Group by theme/area instead of listing everything
- Highlight top 5-10 most important changes
- Link to full commit log for details

### Unreleased Preview

If generating notes for unreleased changes:
- Clearly mark as "preview" or "upcoming"
- Note that version number is tentative
- Show what would be in next release

### Cross-Reference with CHANGELOG.md

If both commits and CHANGELOG.md exist:
- Use CHANGELOG.md as authoritative source for entry text
- Use commits to find anything missing from changelog
- Suggest adding missing items to changelog

---

## Critical Reminders

1. **User-facing language** - Write for people reading release announcements
2. **Consolidate** - Group related commits into single entries
3. **Skip internal** - Don't include refactoring, tests, CI changes
4. **Highlight breaking** - Breaking changes need prominent warnings
5. **Include references** - Link to PRs/issues for details

Now analyze the source (changelog or commits) and generate polished release notes.
