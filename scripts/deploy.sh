#!/bin/bash
set -e

# Project Orchestrator - Production Deployment Script
# This script handles local deployment on the production VM

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO="ghcr.io/gpt153/project-orchestrator"
TAG="${1:-latest}"
COMPOSE_FILE="docker-compose.yml"
DEPLOY_DIR="/home/samuel/po"

echo -e "${BLUE}🚀 Project Orchestrator Deployment${NC}"
echo -e "${BLUE}====================================${NC}"
echo ""

# Function to print colored messages
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running in deployment directory
if [ "$PWD" != "$DEPLOY_DIR" ]; then
    print_warning "Not in deployment directory. Changing to $DEPLOY_DIR"
    cd "$DEPLOY_DIR"
fi

# Check if .env file exists
if [ ! -f .env ]; then
    print_error ".env file not found in $DEPLOY_DIR"
    print_info "Please create .env file with production credentials"
    exit 1
fi

# Check if docker-compose.yml exists
if [ ! -f "$COMPOSE_FILE" ]; then
    print_error "docker-compose.yml not found in $DEPLOY_DIR"
    print_info "Please ensure docker-compose.prod.yml was copied as docker-compose.yml"
    exit 1
fi

# Pull latest Docker image
print_info "Pulling Docker image: $REPO:$TAG"
if docker pull "$REPO:$TAG"; then
    print_success "Docker image pulled successfully"
else
    print_error "Failed to pull Docker image"
    exit 1
fi

# Run database migrations
print_info "Running database migrations..."
if docker run --rm \
    --network host \
    --env-file .env \
    "$REPO:$TAG" \
    alembic upgrade head; then
    print_success "Database migrations completed"
else
    print_error "Database migrations failed"
    exit 1
fi

# Check if containers are already running
if docker-compose ps | grep -q "Up"; then
    print_info "Updating existing deployment (zero-downtime restart)"

    # Pull all images defined in compose file
    docker-compose pull

    # Perform rolling update
    docker-compose up -d --no-deps app

    print_success "Containers updated"
else
    print_info "Starting new deployment"
    docker-compose up -d
    print_success "Containers started"
fi

# Wait for application to be healthy
print_info "Waiting for application health check..."
MAX_RETRIES=24
RETRY_COUNT=0
HEALTH_ENDPOINT="http://localhost:8000/health"

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f -s "$HEALTH_ENDPOINT" > /dev/null 2>&1; then
        print_success "Application is healthy!"
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        print_error "Health check failed after $MAX_RETRIES attempts"
        print_info "Checking container logs..."
        docker-compose logs --tail=50 app
        exit 1
    fi

    echo -n "."
    sleep 5
done
echo ""

# Display deployment status
print_info "Deployment Status:"
docker-compose ps

# Display container logs (last 20 lines)
print_info "Recent logs:"
docker-compose logs --tail=20 app

# Success message
echo ""
print_success "Deployment completed successfully! 🎉"
print_info "Application is running at http://localhost:8000"
print_info "API documentation: http://localhost:8000/docs"
echo ""

# Cleanup old images (keep last 3)
print_info "Cleaning up old Docker images..."
docker image prune -a -f --filter "until=72h" || true

print_success "Deployment script finished"
