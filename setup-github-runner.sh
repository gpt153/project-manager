#!/bin/bash
# Setup GitHub Actions Self-Hosted Runner
# This enables automatic deployment from GitHub Actions

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}GitHub Actions Runner Setup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if running as correct user
if [ "$EUID" -eq 0 ]; then
    print_error "Please do not run as root"
    exit 1
fi

# Step 1: Get runner token
echo "Step 1: Get GitHub Runner Token"
echo ""
echo "Go to:"
echo "https://github.com/gpt153/project-orchestrator/settings/actions/runners/new"
echo ""
echo "Click 'New self-hosted runner' and select Linux x64"
print_warning "Copy the token from the command shown there"
echo ""
read -p "Enter your runner token: " RUNNER_TOKEN

if [ -z "$RUNNER_TOKEN" ]; then
    print_error "Token cannot be empty"
    exit 1
fi

# Step 2: Create runner directory
echo ""
echo "Step 2: Setting up runner directory..."

RUNNER_DIR="$HOME/actions-runner"
mkdir -p "$RUNNER_DIR"
cd "$RUNNER_DIR"

print_status "Runner directory created: $RUNNER_DIR"

# Step 3: Download runner
echo ""
echo "Step 3: Downloading GitHub Actions runner..."

# Get latest runner version
RUNNER_VERSION="2.311.0"  # Update this to latest version as needed

if [ ! -f "actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz" ]; then
    curl -o "actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz" -L \
        "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz"
    print_status "Runner downloaded"
else
    print_status "Runner already downloaded"
fi

# Step 4: Extract runner
echo ""
echo "Step 4: Extracting runner..."

if [ ! -f "./config.sh" ]; then
    tar xzf "./actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz"
    print_status "Runner extracted"
else
    print_status "Runner already extracted"
fi

# Step 5: Configure runner
echo ""
echo "Step 5: Configuring runner..."

./config.sh \
    --url https://github.com/gpt153/project-orchestrator \
    --token "$RUNNER_TOKEN" \
    --name "$(hostname)-runner" \
    --labels "self-hosted,Linux,X64,production" \
    --work _work \
    --replace

print_status "Runner configured"

# Step 6: Install as service
echo ""
echo "Step 6: Installing runner as systemd service..."

sudo ./svc.sh install
print_status "Service installed"

sudo ./svc.sh start
print_status "Service started"

# Step 7: Verify
echo ""
echo "Step 7: Verifying installation..."

sleep 3

if sudo ./svc.sh status | grep -q "active (running)"; then
    print_status "Runner is active and running!"
else
    print_warning "Runner may not be running. Check status with:"
    echo "  cd $RUNNER_DIR && sudo ./svc.sh status"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "The GitHub Actions runner is now installed and running."
echo ""
echo "Verify in GitHub:"
echo "1. Go to: https://github.com/gpt153/project-orchestrator/settings/actions/runners"
echo "2. You should see your runner listed as 'Idle'"
echo ""
echo "Management commands:"
echo "  Status:  cd $RUNNER_DIR && sudo ./svc.sh status"
echo "  Stop:    cd $RUNNER_DIR && sudo ./svc.sh stop"
echo "  Start:   cd $RUNNER_DIR && sudo ./svc.sh start"
echo "  Logs:    sudo journalctl -u actions.runner.* -f"
echo ""
echo "Next steps:"
echo "1. Verify runner appears in GitHub"
echo "2. Push to main branch to trigger deployment"
echo "3. Monitor deployment: https://github.com/gpt153/project-orchestrator/actions"
echo ""
print_status "GitHub Actions runner setup complete!"
