# FluentPro Celery & Flower Docker Setup

This directory contains Docker Compose configuration for running FluentPro's Celery workers, Redis broker, and Flower monitoring dashboard.

## Services

### 🔴 Redis
- **Port**: 6379
- **Purpose**: Celery broker and result backend
- **Health Check**: Redis ping command

### 👷 Celery Worker
- **Purpose**: Process background tasks
- **Concurrency**: 2 workers (1 in development)
- **Queues**: `auth`, `onboarding`, `default`
- **Health Check**: Celery inspect ping

### ⏰ Celery Beat
- **Purpose**: Periodic task scheduler
- **Schedule**: Configurable task scheduling

### 🌸 Flower Dashboard
- **Port**: 5555
- **Purpose**: Monitor Celery workers and tasks
- **URL**: http://localhost:5555
- **Auth**: admin/dev123 (development)

## Quick Start

### 1. Start All Services
```bash
cd docker
./start-services.sh
```

### 2. Access Flower Dashboard
Open http://localhost:5555 in your browser
- **Username**: admin
- **Password**: dev123

### 3. Stop Services
```bash
./stop-services.sh
```

## Manual Commands

### Start Services
```bash
cd docker
docker-compose up -d
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f flower
docker-compose logs -f celery_worker
```

### Check Status
```bash
docker-compose ps
```

### Stop Services
```bash
docker-compose down
```

## Configuration Files

- `docker-compose.yml` - Main service definitions
- `docker-compose.override.yml` - Development overrides
- `flower_config.py` - Flower dashboard configuration
- `start-services.sh` - Helper script to start services
- `stop-services.sh` - Helper script to stop services

## Environment Variables

### Development (automatic)
- `DEBUG=True`
- `FLOWER_BASIC_AUTH=admin:dev123`
- `REDIS_URL=redis://redis:6379/0`

### Production (override)
- `REQUIREMENTS_FILE=requirements/production.txt`
- `FLOWER_BASIC_AUTH=admin:your_secure_password`

## Monitoring Tasks

Once services are running, you can:

1. **View Active Workers**
   - Go to http://localhost:5555/workers

2. **Monitor Task Execution**
   - Go to http://localhost:5555/tasks

3. **Send Test Tasks**
   ```python
   from domains.authentication.tasks import send_welcome_email
   from domains.onboarding.tasks import generate_user_recommendations
   
   # Send test tasks
   send_welcome_email.delay("user_123", "test@example.com", "Test User")
   generate_user_recommendations.delay("user_123", {"industry": "tech"})
   ```

## Troubleshooting

### Services Won't Start
```bash
# Check Docker status
docker info

# Rebuild services
docker-compose build --no-cache

# Check logs
docker-compose logs
```

### Can't Access Flower
- Verify port 5555 is not in use: `lsof -i :5555`
- Check Flower logs: `docker-compose logs flower`
- Ensure Redis is healthy: `docker-compose ps redis`

### Tasks Not Appearing
- Check worker logs: `docker-compose logs celery_worker`
- Verify Redis connection: `docker-compose exec redis redis-cli ping`
- Restart worker: `docker-compose restart celery_worker`

## Health Checks

All services include health checks:
- **Redis**: Redis ping
- **Celery Worker**: Celery inspect ping  
- **Flower**: HTTP endpoint check

Check health status:
```bash
docker-compose ps
```

## Scaling Workers

To run multiple workers:
```bash
docker-compose up -d --scale celery_worker=3
```