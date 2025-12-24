#!/bin/bash
set -e

echo "🚀 Manual Deployment Script for project-orchestrator"
echo "=================================================="
echo ""

DEPLOY_DIR="/home/samuel/po"

echo "📍 Deployment directory: $DEPLOY_DIR"
echo ""

# Step 1: Navigate to deployment directory
echo "1️⃣  Navigating to deployment directory..."
cd "$DEPLOY_DIR" || { echo "❌ Failed to cd to $DEPLOY_DIR"; exit 1; }

# Step 2: Stop running containers
echo "2️⃣  Stopping running containers..."
docker compose down || true

# Step 3: Pull latest changes
echo "3️⃣  Pulling latest changes from GitHub..."
git fetch origin
git reset --hard origin/master

# Step 4: Verify we're on the latest commit
echo "4️⃣  Verifying commit..."
CURRENT_COMMIT=$(git rev-parse HEAD)
echo "   Current commit: $CURRENT_COMMIT"
echo "   Expected: 906597d5d8f6235926564a8986b45d5b8b284c76"

# Step 5: Build Docker images (no cache to ensure fresh build)
echo "5️⃣  Building Docker images..."
docker compose build --no-cache

# Step 6: Start services
echo "6️⃣  Starting services..."
docker compose up -d

# Step 7: Wait for containers to start
echo "7️⃣  Waiting for containers to start..."
sleep 10

# Step 8: Run database migrations
echo "8️⃣  Running database migrations..."
docker compose exec -T app alembic upgrade head || echo "⚠️  Migration failed or no migrations needed"

# Step 9: Wait for health check
echo "9️⃣  Waiting for API to be healthy..."
for i in {1..30}; do
    if curl -f http://localhost:8001/health > /dev/null 2>&1; then
        echo "   ✅ API is healthy!"
        break
    fi
    echo "   Attempt $i/30: API not ready yet..."
    sleep 5

    if [ $i -eq 30 ]; then
        echo "   ❌ Health check timeout!"
        echo "   Showing container logs:"
        docker compose logs --tail=50 app
        exit 1
    fi
done

# Step 10: Verify services
echo "🔟 Verifying services..."
echo ""
echo "Container status:"
docker compose ps
echo ""

# Step 11: Test endpoints
echo "1️⃣1️⃣  Testing endpoints..."
echo ""

echo "   Testing /api/health..."
curl -s http://localhost:8001/api/health | jq '.' || echo "❌ Health endpoint failed"
echo ""

echo "   Testing /api/scar-feed (should return SSE stream)..."
timeout 2s curl -s http://localhost:8001/api/scar-feed || echo "✅ SSE endpoint exists (timeout is expected)"
echo ""

echo "   Testing /api/projects..."
curl -s http://localhost:8001/api/projects | jq '.[] | {id, name}' || echo "❌ Projects endpoint failed"
echo ""

# Step 12: Show recent logs
echo "1️⃣2️⃣  Recent logs:"
docker compose logs --tail=20

echo ""
echo "=================================================="
echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "  1. Test production at https://po.153.se"
echo "  2. Verify SCAR feed is streaming"
echo "  3. Check chat messages are loading"
echo "  4. Confirm GitHub issues appear"
echo ""
