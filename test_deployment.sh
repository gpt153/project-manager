#!/bin/bash
# Project Orchestrator - Deployment Testing and Validation Script
# This script tests all components of the Project Orchestrator deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEPLOY_DIR="${DEPLOY_DIR:-/home/samuel/po}"
API_URL="${API_URL:-http://localhost:8000}"
TEST_DB="${TEST_DB:-project_orchestrator_test}"

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Project Orchestrator Test Suite${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to print test results
print_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

print_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((TESTS_PASSED++))
    ((TESTS_RUN++))
}

print_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((TESTS_FAILED++))
    ((TESTS_RUN++))
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Change to deployment directory
if [ -d "$DEPLOY_DIR" ]; then
    cd "$DEPLOY_DIR"
    print_info "Testing deployment at: $DEPLOY_DIR"
else
    print_fail "Deployment directory not found: $DEPLOY_DIR"
    exit 1
fi

echo ""

# Test 1: Check directory structure
print_test "1. Checking directory structure..."
if [ -d "src" ] && [ -d "tests" ] && [ -d "frontend" ] && [ -d "docs" ]; then
    print_pass "All required directories exist"
else
    print_fail "Missing required directories"
fi

# Test 2: Check Python virtual environment
print_test "2. Checking Python virtual environment..."
if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    print_pass "Virtual environment found and activated"
else
    print_fail "Virtual environment not found"
    exit 1
fi

# Test 3: Check Python dependencies
print_test "3. Checking Python dependencies..."
if python -c "import fastapi, pydantic, sqlalchemy, telegram" 2>/dev/null; then
    print_pass "Core Python dependencies installed"
else
    print_fail "Missing Python dependencies"
fi

# Test 4: Check configuration file
print_test "4. Checking configuration..."
if [ -f ".env" ]; then
    print_pass ".env file exists"

    # Check for required variables
    if grep -q "ANTHROPIC_API_KEY=" .env && \
       grep -q "TELEGRAM_BOT_TOKEN=" .env && \
       grep -q "GITHUB_ACCESS_TOKEN=" .env; then
        print_pass "Required environment variables defined"
    else
        print_warning "Some required environment variables may be missing"
    fi
else
    print_fail ".env file not found"
fi

echo ""

# Test 5: Check database connection
print_test "5. Testing database connection..."
if command -v psql &> /dev/null; then
    # Extract database URL from .env
    DB_URL=$(grep DATABASE_URL .env | cut -d'=' -f2)

    if psql "$DB_URL" -c "SELECT version();" > /dev/null 2>&1; then
        print_pass "Database connection successful"
    else
        print_warning "Database connection failed (may need configuration)"
    fi

    # Check if database exists
    if psql "$DB_URL" -c "SELECT COUNT(*) FROM projects;" > /dev/null 2>&1; then
        print_pass "Database tables exist"
    else
        print_warning "Database tables not found (may need migration)"
        print_info "Run: alembic upgrade head"
    fi
else
    print_warning "PostgreSQL client not available, skipping database tests"
fi

echo ""

# Test 6: Check API server
print_test "6. Testing API server..."
if curl -f -s "$API_URL/health" > /dev/null 2>&1; then
    HEALTH_RESPONSE=$(curl -s "$API_URL/health")
    print_pass "API server is running"
    print_info "Health response: $HEALTH_RESPONSE"
else
    print_warning "API server not responding (may not be started)"
    print_info "Start with: uvicorn src.main:app --host 0.0.0.0 --port 8000"
fi

# Test 7: Check API endpoints
if curl -f -s "$API_URL/health" > /dev/null 2>&1; then
    print_test "7. Testing API endpoints..."

    # Test /health endpoint
    if curl -f -s "$API_URL/health" | grep -q "status"; then
        print_pass "/health endpoint working"
    else
        print_fail "/health endpoint failed"
    fi

    # Test /docs endpoint (Swagger)
    if curl -f -s "$API_URL/docs" > /dev/null 2>&1; then
        print_pass "/docs (Swagger) endpoint working"
    else
        print_fail "/docs endpoint failed"
    fi

    # Test /api/projects endpoint
    if curl -f -s "$API_URL/api/projects" > /dev/null 2>&1; then
        print_pass "/api/projects endpoint working"
    else
        print_warning "/api/projects endpoint failed (may need database)"
    fi
else
    print_warning "Skipping API endpoint tests (server not running)"
fi

echo ""

# Test 8: Check Telegram bot
print_test "8. Checking Telegram bot..."
if pgrep -f "bot_main" > /dev/null; then
    print_pass "Telegram bot process is running"
else
    print_warning "Telegram bot not running"
    print_info "Start with: python -m src.bot_main"
fi

# Test bot token
if [ -f ".env" ]; then
    BOT_TOKEN=$(grep TELEGRAM_BOT_TOKEN .env | cut -d'=' -f2)
    if [ ! -z "$BOT_TOKEN" ] && [ "$BOT_TOKEN" != "your-telegram-bot-token-here" ]; then
        if curl -s "https://api.telegram.org/bot$BOT_TOKEN/getMe" | grep -q "ok.*true"; then
            print_pass "Telegram bot token is valid"
        else
            print_fail "Telegram bot token is invalid"
        fi
    else
        print_warning "Telegram bot token not configured"
    fi
fi

echo ""

# Test 9: Check GitHub integration
print_test "9. Checking GitHub integration..."
if [ -f ".env" ]; then
    GITHUB_TOKEN=$(grep GITHUB_ACCESS_TOKEN .env | cut -d'=' -f2)
    if [ ! -z "$GITHUB_TOKEN" ] && [ "$GITHUB_TOKEN" != "your-github-token-here" ]; then
        if curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user | grep -q "login"; then
            print_pass "GitHub token is valid"
        else
            print_fail "GitHub token is invalid"
        fi
    else
        print_warning "GitHub token not configured"
    fi
fi

echo ""

# Test 10: Check frontend (WebUI)
print_test "10. Checking frontend (WebUI)..."
if [ -d "frontend" ]; then
    cd frontend

    # Check if node_modules exists
    if [ -d "node_modules" ]; then
        print_pass "Frontend dependencies installed"
    else
        print_warning "Frontend dependencies not installed"
        print_info "Run: cd frontend && npm install"
    fi

    # Check if build exists
    if [ -d "dist" ]; then
        print_pass "Frontend built (production)"
    else
        print_warning "Frontend not built"
        print_info "Run: cd frontend && npm run build"
    fi

    # Check if dev server is running
    if curl -f -s "http://localhost:5173" > /dev/null 2>&1; then
        print_pass "Frontend dev server is running"
    else
        print_warning "Frontend dev server not running"
        print_info "Start with: cd frontend && npm run dev"
    fi

    cd "$DEPLOY_DIR"
else
    print_fail "Frontend directory not found"
fi

echo ""

# Test 11: Run automated test suite
print_test "11. Running automated test suite..."
if command -v pytest &> /dev/null; then
    print_info "Running pytest..."

    # Create test database if it doesn't exist
    if command -v psql &> /dev/null; then
        sudo -u postgres psql -c "CREATE DATABASE $TEST_DB;" 2>/dev/null || true
    fi

    # Run tests
    if pytest tests/ -v --tb=short 2>&1 | tee /tmp/pytest_output.log; then
        TEST_COUNT=$(grep -c "PASSED\|FAILED" /tmp/pytest_output.log || echo "0")
        PASS_COUNT=$(grep -c "PASSED" /tmp/pytest_output.log || echo "0")
        FAIL_COUNT=$(grep -c "FAILED" /tmp/pytest_output.log || echo "0")

        print_pass "Test suite completed: $PASS_COUNT passed, $FAIL_COUNT failed"

        if [ "$FAIL_COUNT" -gt 0 ]; then
            print_warning "Some tests failed. Check /tmp/pytest_output.log for details"
        fi
    else
        print_warning "Test suite had errors. Check /tmp/pytest_output.log"
    fi
else
    print_warning "pytest not installed, skipping automated tests"
    print_info "Install with: pip install pytest"
fi

echo ""

# Test 12: Check systemd services (if installed)
print_test "12. Checking systemd services..."
if systemctl list-unit-files | grep -q "project-orchestrator"; then
    # Check API service
    if systemctl is-active --quiet project-orchestrator-api; then
        print_pass "API systemd service is active"
    else
        print_warning "API systemd service not active"
        print_info "Start with: sudo systemctl start project-orchestrator-api"
    fi

    # Check bot service
    if systemctl is-active --quiet project-orchestrator-bot; then
        print_pass "Bot systemd service is active"
    else
        print_warning "Bot systemd service not active"
        print_info "Start with: sudo systemctl start project-orchestrator-bot"
    fi
else
    print_warning "Systemd services not installed"
    print_info "Install with the deploy.sh script"
fi

echo ""

# Test 13: Check logs for errors
print_test "13. Checking logs for errors..."
if [ -f "api.log" ]; then
    ERROR_COUNT=$(grep -c "ERROR\|CRITICAL" api.log || echo "0")
    if [ "$ERROR_COUNT" -eq 0 ]; then
        print_pass "No errors in API logs"
    else
        print_warning "Found $ERROR_COUNT errors in API logs"
        print_info "Check: tail -100 api.log"
    fi
else
    print_info "No api.log file found (using systemd or not started)"
fi

echo ""

# Test 14: Check port availability
print_test "14. Checking port availability..."
if command -v netstat &> /dev/null || command -v ss &> /dev/null; then
    if netstat -tuln 2>/dev/null | grep -q ":8000 " || ss -tuln 2>/dev/null | grep -q ":8000 "; then
        print_pass "Port 8000 (API) is in use (server running)"
    else
        print_warning "Port 8000 (API) is not in use (server may not be running)"
    fi

    if netstat -tuln 2>/dev/null | grep -q ":5432 " || ss -tuln 2>/dev/null | grep -q ":5432 "; then
        print_pass "Port 5432 (PostgreSQL) is in use"
    else
        print_warning "Port 5432 (PostgreSQL) is not in use"
    fi
else
    print_info "netstat/ss not available, skipping port check"
fi

echo ""

# Test 15: Security checks
print_test "15. Running security checks..."

# Check .env permissions
if [ -f ".env" ]; then
    PERMS=$(stat -c "%a" .env)
    if [ "$PERMS" = "600" ] || [ "$PERMS" = "400" ]; then
        print_pass ".env file has secure permissions ($PERMS)"
    else
        print_warning ".env file permissions are $PERMS (should be 600)"
        print_info "Fix with: chmod 600 .env"
    fi
fi

# Check for default secrets
if grep -q "your-secret-key-here\|dev_password" .env 2>/dev/null; then
    print_warning "Default secrets detected in .env"
    print_info "Change all default passwords and secrets"
else
    print_pass "No default secrets detected"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Tests run: $TESTS_RUN"
echo -e "${GREEN}Tests passed: $TESTS_PASSED${NC}"
echo -e "${RED}Tests failed: $TESTS_FAILED${NC}"
echo ""

# Calculate success rate
if [ $TESTS_RUN -gt 0 ]; then
    SUCCESS_RATE=$((TESTS_PASSED * 100 / TESTS_RUN))
    echo "Success rate: $SUCCESS_RATE%"
    echo ""

    if [ $SUCCESS_RATE -ge 90 ]; then
        echo -e "${GREEN}✓ Deployment is in excellent condition!${NC}"
    elif [ $SUCCESS_RATE -ge 70 ]; then
        echo -e "${YELLOW}⚠ Deployment is operational but has some issues${NC}"
    else
        echo -e "${RED}✗ Deployment needs attention${NC}"
    fi
fi

echo ""
echo "Recommendations:"
echo "1. Fix any failed tests above"
echo "2. Ensure all services are running"
echo "3. Configure all API keys in .env"
echo "4. Run: alembic upgrade head (if database tests failed)"
echo "5. Check logs for errors: tail -f api.log bot.log"
echo "6. Test Telegram bot by sending /start"
echo "7. Test API: curl $API_URL/health"
echo "8. Access WebUI: http://localhost:5173"
echo ""

# Exit with error if tests failed
if [ $TESTS_FAILED -gt 0 ]; then
    exit 1
else
    exit 0
fi
