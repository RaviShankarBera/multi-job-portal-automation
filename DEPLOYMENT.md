# Deployment Guide

## Overview

This guide covers deploying the Multi Job Portal Automation Tool in various environments.

## Prerequisites

### System Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 2 cores | 4 cores |
| RAM | 4 GB | 8 GB |
| Storage | 20 GB | 50 GB |
| OS | Ubuntu 20.04+ / Windows 10+ / macOS 12+ |

### Required Software

- Docker 24.0+ and Docker Compose 2.20+
- Node.js 18.0+ (for manual deployment)
- PostgreSQL 15+ (for manual deployment)
- Redis 7+ (for manual deployment)
- Git 2.30+

---

## Docker Deployment (Recommended)

### Quick Start

```bash
# Clone repository
git clone https://github.com/your-org/job-portal-automation.git
cd job-portal-automation

# Create environment file
cp .env.example .env

# Edit .env with your configuration
nano .env

# Start all services
docker compose up -d

# Check service status
docker compose ps

# View logs
docker compose logs -f
```

### Docker Compose Configuration

```yaml
# docker compose.yml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./docker/nginx.conf:/etc/nginx/nginx.conf
      - ./certs:/etc/nginx/certs
    depends_on:
      - backend
      - frontend
    restart: unless-stopped

  backend:
    build:
      context: ./backend
      dockerfile: ../docker/Dockerfile.backend
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/job_portal
      - REDIS_URL=redis://redis:6379
      - JWT_SECRET=${JWT_SECRET}
      - JWT_REFRESH_SECRET=${JWT_REFRESH_SECRET}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./backend/uploads:/app/uploads
      - ./logs:/app/logs
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: ../docker/Dockerfile.frontend
    depends_on:
      - backend
    restart: unless-stopped

  automation:
    build:
      context: ./automation
      dockerfile: ../docker/Dockerfile.automation
    environment:
      - REDIS_URL=redis://redis:6379
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - HEADLESS_BROWSER=true
    volumes:
      - ./automation/screenshots:/app/screenshots
    depends_on:
      - redis
      - backend
    restart: unless-stopped

  worker:
    build:
      context: ./backend
      dockerfile: ../docker/Dockerfile.worker
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/job_portal
      - REDIS_URL=redis://redis:6379
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=job_portal
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### Environment Variables for Docker

Create `.env` file:

```env
# Application
NODE_ENV=production
APP_URL=https://yourdomain.com
API_URL=https://api.yourdomain.com

# Database
POSTGRES_PASSWORD=your-strong-password-here
DATABASE_URL=postgresql://postgres:your-strong-password-here@postgres:5432/job_portal

# Redis
REDIS_PASSWORD=your-redis-password-here
REDIS_URL=redis://:your-redis-password-here@redis:6379

# Authentication
JWT_SECRET=your-jwt-secret-minimum-32-characters-long
JWT_REFRESH_SECRET=your-refresh-secret-minimum-32-characters-long

# AI Integration
OPENAI_API_KEY=sk-your-openai-api-key

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password

# Browser Automation
HEADLESS_BROWSER=true
CHROME_PATH=/usr/bin/chromium
```

### Docker Commands Reference

```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# View logs
docker compose logs -f backend
docker compose logs -f automation

# Restart a service
docker compose restart backend

# Scale workers
docker compose up -d --scale worker=3

# Access container shell
docker compose exec backend sh

# Run database migrations
docker compose exec backend npm run prisma:migrate

# Seed database
docker compose exec backend npm run seed

# Backup database
docker compose exec postgres pg_dump -U postgres job_portal > backup.sql

# Restore database
docker compose exec -T postgres psql -U postgres job_portal < backup.sql
```

---

## Manual Deployment

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Install dependencies
npm install

# Create .env file
cp .env.example .env

# Edit .env with your configuration
nano .env

# Generate Prisma client
npx prisma generate

# Run database migrations
npx prisma migrate deploy

# Seed database (optional)
npm run seed

# Build for production
npm run build

# Start server
npm start
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create .env file
cp .env.example .env

# Edit .env
nano .env

# Build for production
npm run build

# Serve with a static server
npx serve -s dist -l 3000
```

### Automation Engine Setup

```bash
# Navigate to automation directory
cd automation

# Install dependencies
npm install

# Install Chromium
npx puppeteer browsers install chrome

# Create .env file
cp .env.example .env

# Edit .env
nano .env

# Build for production
npm run build

# Start automation service
npm start
```

### Process Manager (PM2)

```bash
# Install PM2 globally
npm install -g pm2

# Start backend
pm2 start dist/index.js --name "job-portal-api"

# Start worker
pm2 start dist/worker.js --name "job-portal-worker"

# Start automation
pm2 start dist/automation.js --name "job-portal-automation"

# Save PM2 configuration
pm2 save

# Setup PM2 startup script
pm2 startup

# Monitor processes
pm2 monit

# View logs
pm2 logs
```

### Nginx Configuration

```nginx
# /etc/nginx/sites-available/job-portal

upstream backend {
    server localhost:5000;
}

upstream frontend {
    server localhost:3000;
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # File uploads
    client_max_body_size 10M;
}
```

### SSL/TLS Setup (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

---

## Environment Setup

### Development Environment

```bash
# Clone and setup
git clone https://github.com/your-org/job-portal-automation.git
cd job-portal-automation

# Start development services (PostgreSQL + Redis)
docker compose -f docker compose.dev.yml up -d

# Install and start backend
cd backend && npm install && npm run dev

# Install and start frontend (new terminal)
cd frontend && npm install && npm run dev
```

### Staging Environment

```bash
# Use staging docker compose
docker compose -f docker compose.staging.yml up -d

# Run migrations
docker compose -f docker compose.staging.yml exec backend npm run prisma:migrate

# Seed with test data
docker compose -f docker compose.staging.yml exec backend npm run seed:staging
```

### Production Environment

```bash
# Use production docker compose
docker compose -f docker compose.prod.yml up -d

# Run migrations
docker compose -f docker compose.prod.yml exec backend npm run prisma:migrate:prod

# Setup monitoring
docker compose -f docker compose.prod.yml up -d prometheus grafana
```

---

## Database Setup

### Initial Setup

```bash
# Connect to PostgreSQL
docker compose exec postgres psql -U postgres

# Create database (if not using Docker)
CREATE DATABASE job_portal;

# Create user
CREATE USER job_portal_user WITH PASSWORD 'secure_password';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE job_portal TO job_portal_user;

# Enable extensions
\c job_portal
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
```

### Migration Commands

```bash
# Run all pending migrations
npx prisma migrate deploy

# Reset database (WARNING: destroys data)
npx prisma migrate reset

# Generate Prisma client
npx prisma generate

# View migration status
npx prisma migrate status

# Create new migration
npx prisma migrate dev --name migration_name
```

### Backup Strategy

```bash
# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
docker compose exec -T postgres pg_dump -U postgres job_portal | gzip > "$BACKUP_DIR/backup_$DATE.sql.gz"

# Keep only last 30 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete
```

### Cron Job for Backups

```bash
# Add to crontab
crontab -e

# Daily backup at 2 AM
0 2 * * * /path/to/backup.sh >> /var/log/backup.log 2>&1
```

---

## Monitoring

### Health Check Endpoints

```bash
# Backend health
curl http://localhost:5000/api/health

# Response
{
  "status": "healthy",
  "services": {
    "database": "connected",
    "redis": "connected",
    "automation": "ready"
  },
  "uptime": "2d 5h 30m"
}
```

### Prometheus Metrics

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'job-portal-backend'
    static_configs:
      - targets: ['backend:5000']
    metrics_path: '/api/metrics'

  - job_name: 'job-portal-redis'
    static_configs:
      - targets: ['redis:6379']
```

### Grafana Dashboard

Access Grafana at `http://localhost:3000` (default credentials: admin/admin)

Import dashboard:
- Node.js Application Dashboard
- PostgreSQL Dashboard
- Redis Dashboard

### Log Management

```bash
# View Docker logs
docker compose logs -f --tail=100 backend

# Filter by time
docker compose logs --since="2024-01-15T10:00:00" backend

# Export logs
docker compose logs backend > backend_logs.txt
```

### Alerting Rules

```yaml
# alertmanager.yml
groups:
  - name: job-portal
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: High error rate detected

      - alert: HighMemoryUsage
        expr: process_resident_memory_bytes / process_heap_limit > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: High memory usage

      - alert: DatabaseDown
        expr: pg_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: PostgreSQL is down
```

---

## Troubleshooting

### Common Issues

#### Database Connection Issues

```bash
# Check PostgreSQL status
docker compose ps postgres

# Check logs
docker compose logs postgres

# Test connection
docker compose exec postgres psql -U postgres -c "SELECT 1"

# Reset database
docker compose down -v
docker compose up -d postgres
```

#### Redis Connection Issues

```bash
# Check Redis status
docker compose ps redis

# Test connection
docker compose exec redis redis-cli ping

# Check memory usage
docker compose exec redis redis-cli info memory
```

#### Backend Startup Issues

```bash
# Check backend logs
docker compose logs backend

# Check environment variables
docker compose exec backend env

# Run in debug mode
docker compose exec backend node --inspect dist/index.js
```

#### Automation Issues

```bash
# Check Chromium installation
docker compose exec automation npx puppeteer browsers inspect

# Check browser logs
docker compose logs automation

# Run with visible browser (for debugging)
docker compose -f docker compose.debug.yml up automation
```

### Performance Issues

```bash
# Check resource usage
docker stats

# Check database queries
docker compose exec postgres psql -U postgres -c "
SELECT query, calls, mean_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
"

# Check Redis slow log
docker compose exec redis redis-cli slowlog get 10
```

### Network Issues

```bash
# Check network configuration
docker network ls
docker network inspect job-portal_default

# Test service connectivity
docker compose exec backend ping postgres
docker compose exec backend ping redis
```

### Log Analysis

```bash
# Search for errors
docker compose logs backend | grep -i error

# Count errors by type
docker compose logs backend | grep -o "ERROR:.*" | sort | uniq -c | sort -rn

# Export logs for analysis
docker compose logs --no-color backend > backend.log
```

---

## Rollback Procedures

### Database Rollback

```bash
# Backup current state
docker compose exec postgres pg_dump -U postgres job_portal > backup_rollback.sql

# Reset to previous migration
npx prisma migrate reset

# Restore from backup
docker compose exec -T postgres psql -U postgres job_portal < backup_rollback.sql
```

### Application Rollback

```bash
# List available images
docker images | grep job-portal

# Rollback to previous version
docker compose up -d --no-deps backend=job-portal-backend:previous-tag

# Or rebuild from previous commit
git checkout <previous-commit>
docker compose build backend
docker compose up -d backend
```

---

## Support

For deployment issues:
- Check [Troubleshooting](#troubleshooting) section
- Review logs: `docker compose logs -f`
- Open issue: GitHub Issues
- Contact: devops@yourdomain.com
