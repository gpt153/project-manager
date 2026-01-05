#!/bin/bash
# Project Manager - Production Deployment Script
# This script deploys the Project Manager to /home/samuel/po

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DEPLOY_DIR="/home/samuel/po"
REPO_URL="https://github.com/gpt153/project-manager.git"
PYTHON_VERSION="3.11"
NODE_VERSION="20"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Project Manager Deployment Script${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Function to print status messages
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check if running as correct user
if [ "$EUID" -eq 0 ]; then
    print_error "Please do not run as root. Run as user 'samuel' or appropriate user."
    exit 1
fi

# Step 1: Check prerequisites
echo "Step 1: Checking prerequisites..."

# Check Python version
if command -v python3 &> /dev/null; then
    PYTHON_VER=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    print_status "Python $PYTHON_VER found"
    if (( $(echo "$PYTHON_VER < $PYTHON_VERSION" | bc -l) )); then
        print_error "Python $PYTHON_VERSION or higher required. Found: $PYTHON_VER"
        echo "Install with: sudo apt install python3.11 python3.11-venv python3-pip"
        exit 1
    fi
else
    print_error "Python 3 not found"
    echo "Install with: sudo apt install python3.11 python3.11-venv python3-pip"
    exit 1
fi

# Check PostgreSQL
if command -v psql &> /dev/null; then
    print_status "PostgreSQL found"
else
    print_warning "PostgreSQL not found. You'll need to install it."
    echo "Install with: sudo apt install postgresql postgresql-contrib"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check Node.js for WebUI
if command -v node &> /dev/null; then
    NODE_VER=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    print_status "Node.js v$NODE_VER found"
    if (( NODE_VER < NODE_VERSION )); then
        print_warning "Node.js $NODE_VERSION or higher recommended. Found: $NODE_VER"
    fi
else
    print_warning "Node.js not found. WebUI won't be available."
    echo "Install with: curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt install -y nodejs"
fi

# Check git
if ! command -v git &> /dev/null; then
    print_error "Git not found"
    echo "Install with: sudo apt install git"
    exit 1
fi

print_status "All prerequisites checked"
echo ""

# Step 2: Create deployment directory
echo "Step 2: Setting up deployment directory..."

if [ -d "$DEPLOY_DIR" ]; then
    print_warning "Deployment directory already exists: $DEPLOY_DIR"
    read -p "Do you want to remove it and start fresh? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$DEPLOY_DIR"
        print_status "Removed existing directory"
    else
        print_status "Using existing directory"
    fi
fi

mkdir -p "$DEPLOY_DIR"
print_status "Deployment directory ready: $DEPLOY_DIR"
echo ""

# Step 3: Clone or update repository
echo "Step 3: Fetching source code..."

if [ -d "$DEPLOY_DIR/.git" ]; then
    print_status "Repository exists, pulling latest changes..."
    cd "$DEPLOY_DIR"
    git pull origin main
else
    print_status "Cloning repository..."
    git clone "$REPO_URL" "$DEPLOY_DIR"
    cd "$DEPLOY_DIR"
fi

print_status "Source code ready"
echo ""

# Step 4: Set up Python virtual environment
echo "Step 4: Setting up Python environment..."

if [ ! -d "$DEPLOY_DIR/venv" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv venv
else
    print_status "Virtual environment exists"
fi

print_status "Activating virtual environment..."
source venv/bin/activate

print_status "Upgrading pip..."
pip install --upgrade pip --quiet

print_status "Installing Python dependencies..."
pip install -e . --quiet

print_status "Installing development dependencies..."
pip install -e ".[dev]" --quiet

print_status "Python environment ready"
echo ""

# Step 5: Configure environment variables
echo "Step 5: Configuring environment..."

if [ ! -f "$DEPLOY_DIR/.env" ]; then
    print_warning ".env file not found. Creating from template..."
    cp .env.example .env
    print_status "Created .env file"
    print_warning "IMPORTANT: You need to edit .env with your actual API keys!"
    print_warning "Required: ANTHROPIC_API_KEY, TELEGRAM_BOT_TOKEN, GITHUB_ACCESS_TOKEN"
    echo ""
    read -p "Press Enter to edit .env now, or Ctrl+C to exit and edit later..."
    ${EDITOR:-nano} .env
else
    print_status ".env file exists"
fi

echo ""

# Step 6: Set up database
echo "Step 6: Setting up database..."

# Check if PostgreSQL is running
if systemctl is-active --quiet postgresql; then
    print_status "PostgreSQL is running"

    # Ask user if they want to create database
    read -p "Create database 'project_manager'? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter PostgreSQL admin password: " -s PG_PASS
        echo

        # Create database user and database
        sudo -u postgres psql -c "CREATE USER manager WITH PASSWORD 'dev_password';" 2>/dev/null || print_warning "User already exists"
        sudo -u postgres psql -c "CREATE DATABASE project_manager OWNER manager;" 2>/dev/null || print_warning "Database already exists"
        sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE project_manager TO manager;" 2>/dev/null

        print_status "Database created"
    fi

    # Run migrations
    print_status "Running database migrations..."
    alembic upgrade head
    print_status "Database migrations complete"
else
    print_warning "PostgreSQL is not running. Please start it and run migrations manually:"
    echo "  sudo systemctl start postgresql"
    echo "  alembic upgrade head"
fi

echo ""

# Step 7: Set up frontend (WebUI)
echo "Step 7: Setting up WebUI..."

if command -v npm &> /dev/null; then
    cd "$DEPLOY_DIR/frontend"

    print_status "Installing Node.js dependencies..."
    npm install --quiet

    print_status "Building frontend for production..."
    npm run build

    print_status "WebUI ready"
    cd "$DEPLOY_DIR"
else
    print_warning "npm not found. Skipping WebUI setup."
fi

echo ""

# Step 8: Create systemd service files
echo "Step 8: Creating systemd services..."

cat > /tmp/project-manager-api.service << EOF
[Unit]
Description=Project Manager FastAPI Application
After=network.target postgresql.service

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$DEPLOY_DIR
Environment="PATH=$DEPLOY_DIR/venv/bin"
EnvironmentFile=$DEPLOY_DIR/.env
ExecStart=$DEPLOY_DIR/venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

cat > /tmp/project-manager-bot.service << EOF
[Unit]
Description=Project Manager Telegram Bot
After=network.target project-manager-api.service

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$DEPLOY_DIR
Environment="PATH=$DEPLOY_DIR/venv/bin"
EnvironmentFile=$DEPLOY_DIR/.env
ExecStart=$DEPLOY_DIR/venv/bin/python -m src.bot_main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

print_status "Systemd service files created in /tmp"
print_warning "To install systemd services, run as root:"
echo "  sudo cp /tmp/project-manager-*.service /etc/systemd/system/"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl enable project-manager-api project-manager-bot"
echo "  sudo systemctl start project-manager-api project-manager-bot"
echo ""

# Step 9: Summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Deployment directory: $DEPLOY_DIR"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys: nano $DEPLOY_DIR/.env"
echo "2. Install systemd services (see commands above)"
echo "3. Start the services:"
echo "   sudo systemctl start project-manager-api"
echo "   sudo systemctl start project-manager-bot"
echo "4. Check service status:"
echo "   sudo systemctl status project-manager-api"
echo "   sudo systemctl status project-manager-bot"
echo "5. Test the API:"
echo "   curl http://localhost:8000/health"
echo "6. View logs:"
echo "   sudo journalctl -u project-manager-api -f"
echo ""
echo "Documentation:"
echo "- Deployment guide: $DEPLOY_DIR/docs/DEPLOYMENT.md"
echo "- Testing guide: $DEPLOY_DIR/docs/TESTING_GUIDE.md"
echo "- Quick start: $DEPLOY_DIR/docs/QUICK_START.md"
echo ""

# Option to start services manually (non-systemd)
read -p "Start services manually now (without systemd)? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Starting API server in background..."
    nohup $DEPLOY_DIR/venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000 > $DEPLOY_DIR/api.log 2>&1 &
    API_PID=$!
    echo "API server PID: $API_PID"

    print_status "Starting Telegram bot in background..."
    nohup $DEPLOY_DIR/venv/bin/python -m src.bot_main > $DEPLOY_DIR/bot.log 2>&1 &
    BOT_PID=$!
    echo "Bot PID: $BOT_PID"

    sleep 3

    print_status "Testing API health..."
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_status "API is running!"
        curl http://localhost:8000/health
    else
        print_error "API health check failed. Check logs: tail -f $DEPLOY_DIR/api.log"
    fi

    echo ""
    echo "To stop services:"
    echo "  kill $API_PID $BOT_PID"
    echo ""
    echo "Logs:"
    echo "  API: tail -f $DEPLOY_DIR/api.log"
    echo "  Bot: tail -f $DEPLOY_DIR/bot.log"
fi

echo ""
print_status "Deployment script complete!"
