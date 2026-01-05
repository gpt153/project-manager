# Deployment Guide: Project Manager WebUI

This guide explains how to deploy the Project Manager WebUI to production (po.153.se).

## Architecture Overview

The application consists of three main services:
- **PostgreSQL**: Database for projects, conversations, and workflow state
- **Backend API**: FastAPI application with REST, WebSocket, and SSE endpoints
- **Frontend**: React SPA served by Nginx with API proxying

## Local Development

### Prerequisites
- Docker and Docker Compose
- Node.js 20+ (for frontend development)
- Python 3.11+ (for backend development)

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/gpt153/project-manager.git
   cd project-manager
   ```

2. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Start all services**:
   ```bash
   docker-compose up -d
   ```

4. **Access the application**:
   - Frontend: http://localhost:3002
   - Backend API: http://localhost:8001
   - API Docs: http://localhost:8001/docs

**Port Mapping (Docker Compose)**:

| Service     | Container Port | Host Port | Access URL                    |
|-------------|----------------|-----------|-------------------------------|
| Backend API | 8000           | 8001      | http://localhost:8001         |
| Frontend    | 80             | 3002      | http://localhost:3002         |
| PostgreSQL  | 5432           | 5435      | localhost:5435                |
| Redis       | 6379           | 6379      | localhost:6379                |

### Frontend Development

For active frontend development with hot reload:

```bash
cd frontend
npm install
npm run dev
```

The dev server runs on http://localhost:3002 with Vite's hot module replacement.

## Production Deployment to po.153.se

### Prerequisites on Production Server

- Docker and Docker Compose installed
- Nginx or Caddy for reverse proxy
- SSL certificate (Let's Encrypt recommended)
- Domain pointing to server: po.153.se

### Step 1: Set Up Reverse Proxy

#### Option A: Nginx Configuration

Create `/etc/nginx/sites-available/po.153.se`:

```nginx
# HTTP redirect to HTTPS
server {
    listen 80;
    server_name po.153.se;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name po.153.se;

    # SSL certificates (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/po.153.se/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/po.153.se/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Proxy to frontend container
    location / {
        proxy_pass http://localhost:3002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support is handled by frontend Nginx
    # (frontend/nginx.conf proxies to backend)
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/po.153.se /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### Option B: Caddy Configuration

Create `/etc/caddy/Caddyfile`:

```caddyfile
po.153.se {
    reverse_proxy localhost:3002
}
```

Reload Caddy:
```bash
sudo systemctl reload caddy
```

### Step 2: SSL Certificate Setup

Using Let's Encrypt with Certbot:

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d po.153.se
```

Certbot will automatically configure Nginx with SSL. Test auto-renewal:

```bash
sudo certbot renew --dry-run
```

### Step 3: Deploy Application

1. **SSH to production server**:
   ```bash
   ssh user@po.153.se
   ```

2. **Clone repository** (or pull latest):
   ```bash
   cd /opt
   sudo git clone https://github.com/gpt153/project-manager.git
   cd project-manager
   sudo git checkout master  # or specific release tag
   ```

3. **Create production environment file**:
   ```bash
   sudo cp .env.example .env.production
   sudo nano .env.production
   ```

   Required variables:
   ```bash
   # Application
   APP_ENV=production
   DEBUG=false

   # Database
   DATABASE_URL=postgresql+asyncpg://orchestrator:SECURE_PASSWORD@postgres:5432/project_orchestrator

   # API Keys
   ANTHROPIC_API_KEY=your_anthropic_api_key
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   GITHUB_ACCESS_TOKEN=your_github_token
   GITHUB_WEBHOOK_SECRET=your_webhook_secret

   # Frontend
   FRONTEND_URL=https://po.153.se
   ```

4. **Build and start services**:
   ```bash
   sudo docker-compose --env-file .env.production up -d --build
   ```

5. **Check logs**:
   ```bash
   sudo docker-compose logs -f
   ```

6. **Verify services are running**:
   ```bash
   sudo docker-compose ps
   ```

   Expected output:
   ```
   NAME       SERVICE    STATUS       PORTS
   backend    app        running      0.0.0.0:8001->8000/tcp
   frontend   frontend   running      0.0.0.0:3002->80/tcp
   postgres   postgres   running      0.0.0.0:5435->5432/tcp
   redis      redis      running      0.0.0.0:6379->6379/tcp
   ```

### Step 4: Database Initialization

On first deployment, initialize the database:

```bash
sudo docker-compose exec app alembic upgrade head
```

### Step 5: Verify Deployment

1. **Visit https://po.153.se** - should see the 3-panel WebUI
2. **Check API**: https://po.153.se/api/health
3. **Check API docs**: https://po.153.se/api/docs

## Monitoring

### View Logs

```bash
# All services
sudo docker-compose logs -f

# Specific service
sudo docker-compose logs -f frontend
sudo docker-compose logs -f app
sudo docker-compose logs -f postgres
```

### Check Service Health

```bash
# All containers
sudo docker-compose ps

# Backend health
curl https://po.153.se/api/health

# Frontend health
curl https://po.153.se/health
```

## Updating

To deploy a new version:

```bash
cd /opt/project-manager
sudo git pull origin master
sudo docker-compose --env-file .env.production up -d --build
```

To rollback:

```bash
sudo git checkout <previous-commit-hash>
sudo docker-compose --env-file .env.production up -d --build
```

## Backup

### Database Backup

```bash
# Create backup
sudo docker-compose exec postgres pg_dump -U orchestrator project_orchestrator > backup_$(date +%Y%m%d).sql

# Restore backup
sudo docker-compose exec -T postgres psql -U orchestrator project_orchestrator < backup_20231220.sql
```

### Full System Backup

```bash
# Backup volumes
sudo docker run --rm \
  -v project_orchestrator_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/postgres_data_backup.tar.gz -C /data .
```

## Troubleshooting

### Frontend Not Loading

1. Check frontend container is running:
   ```bash
   sudo docker-compose ps frontend
   ```

2. Check frontend logs:
   ```bash
   sudo docker-compose logs frontend
   ```

3. Verify Nginx is proxying correctly:
   ```bash
   sudo nginx -t
   sudo systemctl status nginx
   ```

### WebSocket Connection Fails

1. Ensure Nginx has WebSocket support (should be in frontend/nginx.conf)
2. Check browser console for errors
3. Test WebSocket directly:
   ```bash
   wscat -c wss://po.153.se/api/ws/chat/<project-id>
   ```

### SSE Connection Fails

1. Check that SSE buffering is disabled in frontend/nginx.conf
2. Test SSE directly:
   ```bash
   curl -N https://po.153.se/api/sse/scar/<project-id>
   ```

### Backend API Not Responding

1. Check backend container:
   ```bash
   sudo docker-compose logs app
   ```

2. Check database connection:
   ```bash
   sudo docker-compose exec app python -c "from src.database.connection import engine; import asyncio; asyncio.run(engine.dispose())"
   ```

### Database Connection Issues

1. Check PostgreSQL is running:
   ```bash
   sudo docker-compose ps postgres
   ```

2. Test connection from backend:
   ```bash
   sudo docker-compose exec app python -c "import asyncpg; import asyncio; asyncio.run(asyncpg.connect('postgresql://orchestrator:dev_password@postgres:5432/project_orchestrator'))"
   ```

## Security Considerations

### Production Checklist

- [ ] Change default database password
- [ ] Use strong secrets for GITHUB_WEBHOOK_SECRET
- [ ] Enable HTTPS only (no HTTP)
- [ ] Set up firewall rules (allow only 80, 443, 22)
- [ ] Regular security updates: `sudo apt update && sudo apt upgrade`
- [ ] Monitor logs for suspicious activity
- [ ] Set up automated backups
- [ ] Use environment-specific API keys (not dev keys in production)

### Environment Variables Security

Never commit `.env.production` to git. Store secrets securely:
- Use Docker secrets
- Or use environment variable injection from CI/CD
- Or use a secrets manager (AWS Secrets Manager, HashiCorp Vault)

## Performance Optimization

### Frontend

- Brotli compression is enabled in Nginx
- Static assets are cached for 1 year
- SPA routing via try_files

### Backend

- Connection pooling in database config
- Redis for caching (optional, configured in docker-compose.yml)
- Async I/O throughout

### Database

- Regular VACUUM and ANALYZE
- Index optimization
- Connection pooling

## Scaling Considerations

For high traffic:

1. **Horizontal scaling**: Deploy multiple backend containers behind load balancer
2. **Database**: Use managed PostgreSQL (AWS RDS, Google Cloud SQL)
3. **Cache**: Use Redis for session storage and caching
4. **CDN**: Serve static assets via CloudFlare or similar
5. **Monitoring**: Add Prometheus + Grafana for metrics

## Support

For issues or questions:
- GitHub Issues: https://github.com/gpt153/project-manager/issues
- Documentation: README.md
