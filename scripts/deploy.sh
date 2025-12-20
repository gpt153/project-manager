#!/bin/bash
# Production deployment script for Project Orchestrator
# Usage: ./scripts/deploy.sh

set -e

echo "🚀 Starting deployment..."

# Configuration
PROJECT_DIR="/home/samuel/po"
COMPOSE_FILE="docker-compose.yml"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

cd "$PROJECT_DIR"

# Pull latest changes
echo -e "${YELLOW}📥 Pulling latest changes from git...${NC}"
git pull origin main

# Stop existing containers
echo -e "${YELLOW}🛑 Stopping existing containers...${NC}"
docker compose -f "$COMPOSE_FILE" down

# Build new images
echo -e "${YELLOW}🔨 Building Docker images...${NC}"
docker compose -f "$COMPOSE_FILE" build --no-cache

# Start services
echo -e "${YELLOW}▶️  Starting services...${NC}"
docker compose -f "$COMPOSE_FILE" up -d

# Wait for health checks
echo -e "${YELLOW}⏳ Waiting for services to be healthy...${NC}"
sleep 15

# Check service status
echo -e "${YELLOW}📊 Service status:${NC}"
docker compose -f "$COMPOSE_FILE" ps

# Test health endpoint
echo -e "${YELLOW}🏥 Testing health endpoint...${NC}"
if curl -f http://localhost:8001/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Health check passed!${NC}"
else
    echo -e "${YELLOW}⚠️  Health check failed - service may still be starting${NC}"
fi

# Clean up old images
echo -e "${YELLOW}🧹 Cleaning up old Docker images...${NC}"
docker image prune -f

echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "Service endpoints:"
echo "  - API: http://localhost:8001"
echo "  - Health: http://localhost:8001/health"
echo ""
echo "View logs with: docker compose -f $COMPOSE_FILE logs -f"
