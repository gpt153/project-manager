---
description: Create a GitHub Release with git tag and release notes
argument-hint: <version>
---

# Create Release

**Input**: $ARGUMENTS

---

## Purpose

Create a complete GitHub Release:
1. Verify version is ready (changelog updated, tests pass)
2. Create and push git tag
3. Create GitHub Release with release notes
4. Output release URL

---

## Phase 1: Parse and Validate

### 1.1 Parse Version

Input should be a version number: `0.3.0`

Validate format:
- Matches semver pattern: `X.Y.Z` or `X.Y.Z-prerelease`
- Examples: `0.3.0`, `1.0.0`, `0.3.0-alpha.1`

**If no version provided:**
```
Usage: /release <version>

Example: /release 0.3.0

To determine version, run /changelog-release first.
```
STOP here.

### 1.2 Check Prerequisites

```bash
# 1. Ensure we're on main branch
git branch --show-current

# 2. Ensure working directory is clean
git status --porcelain

# 3. Ensure we're up to date with remote
git fetch origin
git status -uno
```

**If not on main:**
```
Warning: Not on main branch. Releases should typically be from main.
Current branch: feature/something

Switch to main? [y/n]
```

**If uncommitted changes:**
```
Error: Uncommitted changes detected. Commit or stash before releasing.

git status
```
STOP here.

**If behind remote:**
```
Warning: Local main is behind origin/main.
Pull latest changes first: git pull origin main
```

### 1.3 Check Tag Doesn't Exist

```bash
git tag -l "v$VERSION"
```

**If tag exists:**
```
Error: Tag v0.3.0 already exists.

To see existing release: gh release view v0.3.0
To delete and recreate: gh release delete v0.3.0 && git tag -d v0.3.0 && git push origin :v0.3.0
```
STOP here.

---

## Phase 2: Verify Release Readiness

### 2.1 Check CHANGELOG.md

```bash
cat CHANGELOG.md | head -60
```

Verify:
- Version `[X.Y.Z]` section exists (not just `[Unreleased]`)
- Date is present: `## [0.3.0] - 2025-12-08`
- Content exists under the version

**If version not in changelog:**
```
Error: Version 0.3.0 not found in CHANGELOG.md.

Run /changelog-release 0.3.0 first to promote unreleased changes.
```
STOP here.

### 2.2 Run Validation Suite

```bash
# Type check
npm run type-check

# Lint
npm run lint

# Tests
npm test

# Build
npm run build
```

**If any fail:**
```
Error: Validation failed. Fix issues before releasing.

Failed: [type-check/lint/test/build]
```
STOP here with details.

### 2.3 Check Version Consistency (Optional)

If package.json exists, check version matches:
```bash
cat package.json | grep '"version"'
```

**If mismatch:**
```
Note: package.json version (0.2.0) doesn't match release (0.3.0).

Update package.json? [y/n]
```

If yes:
```bash
npm version 0.3.0 --no-git-tag-version
```

---

## Phase 3: Generate Release Notes

### 3.1 Extract from CHANGELOG.md

Extract the content for this version from CHANGELOG.md.

### 3.2 Format for GitHub Release

Transform changelog format to GitHub Release format:

**From CHANGELOG.md:**
```markdown
## [0.3.0] - 2025-12-08

### Added
- Add Slack adapter with Socket Mode support (#73)

### Fixed
- Fix worktree cleanup duplicate removal (#72)
```

**To GitHub Release:**
```markdown
## What's New

### New Features
- Add Slack adapter with Socket Mode support (#73)

### Bug Fixes
- Fix worktree cleanup duplicate removal (#72)

---

**Full Changelog**: https://github.com/OWNER/REPO/compare/v0.2.0...v0.3.0
```

### 3.3 Save Release Notes

```bash
mkdir -p .agents/releases
```

Save to: `.agents/releases/v0.3.0-notes.md`

---

## Phase 4: Create Release

### 4.1 Create Git Tag

```bash
# Create annotated tag
git tag -a "v0.3.0" -m "Release v0.3.0"

# Push tag to remote
git push origin "v0.3.0"
```

### 4.2 Create GitHub Release

```bash
# Get repository info
REPO=$(gh repo view --json nameWithOwner -q '.nameWithOwner')

# Create release
gh release create "v0.3.0" \
  --title "v0.3.0" \
  --notes-file .agents/releases/v0.3.0-notes.md
```

### 4.3 Verify Release

```bash
# Check release was created
gh release view "v0.3.0"
```

---

## Phase 5: Output

### 5.1 Success Summary

```
## Release Created

**Version**: v0.3.0
**Tag**: v0.3.0
**Date**: 2025-12-08

**Release URL**: https://github.com/owner/repo/releases/tag/v0.3.0

### Included Changes
- Added: 2 entries
- Fixed: 1 entry

### Verification
- [x] CHANGELOG.md has version entry
- [x] Type check passed
- [x] Lint passed
- [x] Tests passed
- [x] Build passed
- [x] Git tag created
- [x] GitHub Release published

### Next Steps
- Announce the release
- Monitor for issues
- Start working on next version
```

### 5.2 If Something Failed

```
## Release Partially Created

**Issue**: [what failed]

### Completed
- [x] Tag created: v0.3.0

### Failed
- [ ] GitHub Release creation

### Recovery
To retry GitHub Release:
gh release create v0.3.0 --title "v0.3.0" --notes-file .agents/releases/v0.3.0-notes.md

To rollback tag:
git tag -d v0.3.0
git push origin :v0.3.0
```

---

## Special Cases

### Pre-release Version

For alpha/beta releases (e.g., `0.3.0-alpha.1`):

```bash
gh release create "v0.3.0-alpha.1" \
  --title "v0.3.0-alpha.1" \
  --notes-file .agents/releases/v0.3.0-alpha.1-notes.md \
  --prerelease
```

The `--prerelease` flag marks it as non-production.

### Draft Release

To create a draft for review before publishing:

```bash
gh release create "v0.3.0" \
  --title "v0.3.0" \
  --notes-file .agents/releases/v0.3.0-notes.md \
  --draft
```

Then publish via GitHub UI or: `gh release edit v0.3.0 --draft=false`

### No GitHub Release (Tag Only)

If you only want a git tag without GitHub Release:

```bash
git tag -a "v0.3.0" -m "Release v0.3.0"
git push origin "v0.3.0"
```

Skip `gh release create`.

### Hotfix Release

For urgent fixes to a released version:
1. Check out the release tag: `git checkout v0.3.0`
2. Create hotfix branch: `git checkout -b hotfix/0.3.1`
3. Make fixes, commit
4. Update CHANGELOG.md with 0.3.1 section
5. Run `/release 0.3.1`

---

## Rollback

If you need to undo a release:

### Delete GitHub Release
```bash
gh release delete v0.3.0 --yes
```

### Delete Git Tag
```bash
# Delete local tag
git tag -d v0.3.0

# Delete remote tag
git push origin :v0.3.0
```

### Revert CHANGELOG.md
```bash
git revert HEAD  # If changelog commit was most recent
# or manually edit CHANGELOG.md
```

---

## Critical Reminders

1. **Always from main** - Release from main branch (or your default branch)
2. **Clean working directory** - No uncommitted changes
3. **Validation must pass** - All checks green before releasing
4. **Changelog first** - Version must exist in CHANGELOG.md
5. **Annotated tags** - Use `git tag -a` for proper release tags
6. **Verify after** - Check the release was created successfully

Now validate prerequisites, generate release notes, and create the release.
