---
description: Promote [Unreleased] changelog entries to a new version
argument-hint: [version] (optional - auto-determined based on release stage)

---

# Changelog Release

**Input**: $ARGUMENTS

---

## Release Stage Configuration

release-stage: alpha

This command uses the `release-stage` frontmatter to determine versioning behavior.

**Stages:**
- **alpha** (default): Pre-1.0, experimental. Breaking changes don't bump major. Version format: `0.x.y`
- **beta**: Pre-1.0, stabilizing. More conservative versioning. Version format: `0.x.y`
- **stable**: Post-1.0, production. Full semantic versioning. Version format: `x.y.z`

**Current stage**: Check the `release-stage` in this file.

---

## Purpose

Promote the `[Unreleased]` section of CHANGELOG.md to a new version:
1. Rename `[Unreleased]` to `[X.Y.Z] - YYYY-MM-DD`
2. Create new empty `[Unreleased]` section
3. Determine version based on changes and release stage

---

## Phase 1: Analyze Current State

### 1.1 Read CHANGELOG.md

```bash
cat CHANGELOG.md
```

Extract:
- Current `[Unreleased]` content
- Previous version number (most recent `## [X.Y.Z]` entry)
- Categories with entries under Unreleased

### 1.2 Check for Unreleased Content

**If `[Unreleased]` is empty:**
```
No unreleased changes to release.

Add entries with /changelog-entry first.
```
STOP here.

### 1.3 Get Last Version

Find the most recent version in CHANGELOG.md:
```
## [0.2.0] - 2025-12-01
```

**If no previous version**, this is the first release. Default to `0.1.0`.

---

## Phase 2: Determine Version

### 2.1 Parse User Input

If version provided (e.g., `/changelog-release 0.3.0`):
- Validate format (semver)
- Use provided version
- Skip auto-determination

If no version provided, proceed to auto-determination.

### 2.2 Analyze Changes for Version Bump

Scan the `[Unreleased]` section:

**Breaking changes indicators:**
- Entry contains "BREAKING" or "breaking change"
- Entry under "Removed" that affects public API
- Entry mentions "incompatible" or "migration required"

**Feature indicators:**
- Entries under "Added"
- Entries under "Changed" that add functionality

**Fix indicators:**
- Entries under "Fixed"
- Entries under "Security"

### 2.3 Apply Release Stage Rules

**Alpha stage (pre-1.0, experimental):**
```
Current: 0.2.3

Breaking change → 0.3.0 (bump minor, reset patch)
New feature    → 0.3.0 (bump minor, reset patch)
Bug fix only   → 0.2.4 (bump patch)

Note: Major stays at 0 until stable
```

**Beta stage (pre-1.0, stabilizing):**
```
Current: 0.9.2

Breaking change → 0.10.0 (bump minor, reset patch) + WARNING
New feature    → 0.10.0 (bump minor, reset patch)
Bug fix only   → 0.9.3 (bump patch)

Warning on breaking: "Breaking changes in beta should be minimized"
```

**Stable stage (post-1.0):**
```
Current: 1.2.3

Breaking change → 2.0.0 (bump major, reset minor/patch)
New feature    → 1.3.0 (bump minor, reset patch)
Bug fix only   → 1.2.4 (bump patch)
```

### 2.4 Show Version Decision

```
## Version Analysis

**Release stage**: alpha
**Previous version**: 0.2.0
**Changes detected**:
- Added: 3 entries (features)
- Fixed: 2 entries (bug fixes)
- Breaking: No

**Determined version**: 0.3.0
**Reason**: New features in alpha stage bump minor version

Proceeding with 0.3.0...
```

---

## Phase 3: Update CHANGELOG.md

### 3.1 Get Today's Date

```bash
date +%Y-%m-%d
```

### 3.2 Transform Unreleased Section

**Before:**
```markdown
## [Unreleased]

### Added
- Add Slack adapter with Socket Mode support (#73)
- Add Discord thread support (#71)

### Fixed
- Fix worktree cleanup duplicate removal (#72)
```

**After:**
```markdown
## [Unreleased]

### Added

### Changed

### Fixed

## [0.3.0] - 2025-12-08

### Added
- Add Slack adapter with Socket Mode support (#73)
- Add Discord thread support (#71)

### Fixed
- Fix worktree cleanup duplicate removal (#72)
```

### 3.3 Clean Up Empty Categories

In the new version section, remove any empty categories:

**Remove this:**
```markdown
### Changed

### Deprecated
```

**Keep only categories with entries.**

### 3.4 Preserve Comparison Links (If Present)

If CHANGELOG.md has comparison links at the bottom:
```markdown
[unreleased]: https://github.com/owner/repo/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/owner/repo/compare/v0.1.0...v0.2.0
```

Update them:
```markdown
[unreleased]: https://github.com/owner/repo/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/owner/repo/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/owner/repo/compare/v0.1.0...v0.2.0
```

---

## Phase 4: Output

### 4.1 Show Summary

```
## Changelog Released

**Version**: 0.3.0
**Date**: 2025-12-08
**Release stage**: alpha

### Changes included:
- **Added**: 2 entries
- **Fixed**: 1 entry

### Next steps:
1. Review: `cat CHANGELOG.md | head -50`
2. Commit: `git add CHANGELOG.md && git commit -m "chore: release 0.3.0"`
3. Tag: `/release 0.3.0` (creates git tag + GitHub release)
```

### 4.2 Show Diff

```bash
git diff CHANGELOG.md
```

---

## Special Cases

### First Release

If no previous version exists:
- Default to `0.1.0` for alpha/beta
- Default to `1.0.0` for stable
- All unreleased content becomes first release

### Pre-release Versions

For alpha/beta software that wants explicit pre-release tags:
- `0.3.0-alpha.1`
- `0.3.0-beta.2`

Only use if user explicitly requests pre-release suffix.

### Empty Categories After Release

The new `[Unreleased]` section should have empty category placeholders:
```markdown
## [Unreleased]

### Added

### Changed

### Fixed
```

This makes it easy to add entries without creating sections.

### Version Override

If user provides version that doesn't match analysis:
```
Note: Provided version 1.0.0 differs from suggested 0.3.0.
Using provided version 1.0.0 as specified.
```

Always respect explicit user input.

---

## Critical Reminders

1. **Check release stage** - Different rules for alpha/beta/stable
2. **Never lose content** - Unreleased entries must appear in new version
3. **Clean empty sections** - Don't leave empty categories in released version
4. **Preserve links** - Update comparison URLs if they exist
5. **Show what happened** - Always display summary and diff

Now read the changelog, determine the version, and promote the unreleased changes.
