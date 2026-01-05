# GitHub Actions Workflows

This directory contains CI/CD workflows for the Project Manager.

## Available Workflows

### 1. CI - Test Suite (`ci.yml`)

**Triggers:** Pull requests and pushes to `develop` branch

**Jobs:**
- **test** - Runs the full test suite (67+ tests)
  - Sets up Python 3.11
  - Starts PostgreSQL test database
  - Runs pytest with coverage
  - Uploads coverage to Codecov

- **lint** - Code quality checks
  - Runs ruff (linter)
  - Runs black (formatter)
  - Runs mypy (type checker)

- **frontend** - Frontend build test
  - Sets up Node.js 20
  - Installs dependencies
  - Builds React app
  - Uploads build artifacts

**Required Secrets:**
- `ANTHROPIC_API_KEY` - For AI agent tests

### 2. Docker Build and Push (`docker-build.yml`)

**Triggers:** Pushes to `main` branch, tags, and pull requests

**What it does:**
- Builds Docker image for the application
- Pushes to GitHub Container Registry (ghcr.io)
- Tags images appropriately:
  - `latest` for main branch
  - `main-<sha>` for commits
  - `v1.0.0` for version tags

**Image location:** `ghcr.io/gpt153/project-manager`

**No secrets required** (uses `GITHUB_TOKEN` automatically)

### 3. CD - Deploy to Production (`cd.yml`)

**Triggers:** Pushes to `main` branch and manual workflow dispatch

**Jobs:**
- **build-and-push** - Builds and pushes Docker image
- **deploy** - Deploys to production VM
  - Pulls latest Docker image
  - Updates deployment files
  - Restarts services
  - Runs database migrations
  - Performs health checks
- **rollback** - Automatically rolls back on failure

**Required Setup:**
1. Self-hosted GitHub Actions runner on the VM
2. Deployment directory: `/home/samuel/po`

**Required Secrets:**
- `ANTHROPIC_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `GITHUB_ACCESS_TOKEN`
- `GITHUB_WEBHOOK_SECRET`
- `SECRET_KEY`
- `DATABASE_URL`

## Setting Up GitHub Secrets

### Navigate to Secrets

1. Go to: https://github.com/gpt153/project-manager/settings/secrets/actions
2. Click "New repository secret"

### Add Each Secret

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude | `sk-ant-xxxxx` |
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather | `1234567890:xxxxx` |
| `GITHUB_ACCESS_TOKEN` | Personal access token | `ghp_xxxxx` |
| `GITHUB_WEBHOOK_SECRET` | Webhook secret | `your-secret-string` |
| `SECRET_KEY` | App secret key | Generate: `openssl rand -hex 32` |
| `DATABASE_URL` | Production database URL | `postgresql+asyncpg://user:pass@host:5432/db` |

## Setting Up Self-Hosted Runner

The CD workflow requires a self-hosted runner on your VM to deploy directly.

### On Your VM

```bash
# Navigate to home directory
cd /home/samuel

# Create a folder for the runner
mkdir actions-runner && cd actions-runner

# Download the latest runner package
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz

# Extract the installer
tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz

# Configure the runner
./config.sh --url https://github.com/gpt153/project-manager --token YOUR_RUNNER_TOKEN

# Install as a service
sudo ./svc.sh install

# Start the runner
sudo ./svc.sh start
```

**Get your runner token:**
1. Go to: https://github.com/gpt153/project-manager/settings/actions/runners/new
2. Copy the token shown
3. Use it in the config.sh command above

### Verify Runner

1. Go to: https://github.com/gpt153/project-manager/settings/actions/runners
2. You should see your runner listed as "Idle"

## Workflow Status Badges

Add these to your README.md:

```markdown
![CI Status](https://github.com/gpt153/project-manager/workflows/CI%20-%20Test%20Suite/badge.svg)
![Docker Build](https://github.com/gpt153/project-manager/workflows/Docker%20Build%20and%20Push/badge.svg)
![CD Status](https://github.com/gpt153/project-manager/workflows/CD%20-%20Deploy%20to%20Production/badge.svg)
```

## Typical Workflow

### Development Flow

1. **Create feature branch**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make changes and commit**
   ```bash
   git add .
   git commit -m "Add my feature"
   git push origin feature/my-feature
   ```

3. **Create Pull Request**
   - CI workflow runs automatically
   - Tests, linting, and frontend build execute
   - Review test results before merging

4. **Merge to main**
   - Docker image builds automatically
   - CD workflow deploys to production VM
   - Health checks verify deployment

### Manual Deployment

You can manually trigger deployment:

1. Go to: https://github.com/gpt153/project-manager/actions/workflows/cd.yml
2. Click "Run workflow"
3. Select branch (usually `main`)
4. Click "Run workflow"

## Debugging Workflow Issues

### View Workflow Runs

1. Go to: https://github.com/gpt153/project-manager/actions
2. Click on the workflow run
3. Click on the failed job
4. Expand the failed step to see logs

### Common Issues

#### Tests Failing

**Problem:** Test suite fails in CI

**Solution:**
- Check if `ANTHROPIC_API_KEY` secret is set
- Verify database migrations are up to date
- Run tests locally: `pytest tests/ -v`

#### Docker Build Failing

**Problem:** Docker image build fails

**Solution:**
- Check Dockerfile syntax
- Verify all dependencies in pyproject.toml
- Test build locally: `docker build -t test .`

#### Deployment Failing

**Problem:** CD workflow can't deploy

**Solution:**
- Verify self-hosted runner is online
- Check runner has access to `/home/samuel/po`
- Verify all secrets are configured
- Check deployment directory permissions

#### Self-Hosted Runner Offline

**Problem:** Runner shows as "Offline"

**Solution:**
```bash
# On VM
cd /home/samuel/actions-runner
sudo ./svc.sh status
sudo ./svc.sh start
```

## Disabling Workflows

If you want to disable a workflow temporarily:

1. Go to `.github/workflows/`
2. Rename the workflow file (e.g., `cd.yml.disabled`)
3. Commit and push

Or disable via GitHub UI:
1. Go to: https://github.com/gpt153/project-manager/actions
2. Click on the workflow
3. Click "..." → "Disable workflow"

## Customizing Workflows

### Change Python Version

Edit the workflow file:
```yaml
- name: Set up Python 3.11
  uses: actions/setup-python@v5
  with:
    python-version: '3.12'  # Change here
```

### Change Deployment Directory

Edit `cd.yml`:
```yaml
- name: Set deployment directory
  run: echo "DEPLOY_DIR=/your/custom/path" >> $GITHUB_ENV
```

### Add More Tests

Edit `ci.yml` to add additional test jobs:
```yaml
security-scan:
  name: Security Scan
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Run Bandit
      run: bandit -r src/
```

## Monitoring

### Check Workflow Status

```bash
# Using GitHub CLI
gh workflow list
gh run list --workflow=ci.yml
gh run view <run-id>
```

### Notifications

Set up notifications for workflow failures:
1. Go to: https://github.com/settings/notifications
2. Enable "Actions" notifications
3. Choose email or GitHub notifications

## Best Practices

1. **Always run tests locally before pushing**
   ```bash
   pytest tests/ -v
   ```

2. **Use feature branches**
   - Never commit directly to `main`
   - Create PRs for review

3. **Keep secrets secure**
   - Never commit `.env` files
   - Rotate secrets periodically

4. **Monitor workflow runs**
   - Check CI results before merging
   - Review deployment logs

5. **Update dependencies regularly**
   - GitHub Actions updates monthly
   - Check for deprecation warnings

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Self-Hosted Runners Guide](https://docs.github.com/en/actions/hosting-your-own-runners)
- [Workflow Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
