# FluentPro Backend Deployment Guide

This guide covers the complete deployment process for the FluentPro backend application across different environments.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Environment Configurations](#environment-configurations)
- [Local Development Deployment](#local-development-deployment)
- [Staging Deployment](#staging-deployment)
- [Production Deployment](#production-deployment)
- [CI/CD Pipeline](#cicd-pipeline)
- [Monitoring and Health Checks](#monitoring-and-health-checks)
- [Rollback Procedures](#rollback-procedures)
- [Security Considerations](#security-considerations)

## Overview

FluentPro backend uses a containerized deployment strategy with Docker and Docker Compose. The application supports multiple deployment environments:

- **Development**: Local development with hot reload
- **Staging**: Production-like environment for testing
- **Production**: Live production environment

## Prerequisites

### Required Software
- Docker Engine 20.0+ and Docker Compose 2.0+
- Git 2.30+
- Node.js 18+ (for frontend dependencies if applicable)

### Access Requirements
- GitHub repository access
- Container registry access (GitHub Container Registry)
- Environment-specific secrets and configuration
- SSH access to deployment servers (for manual deployments)

### Required Secrets

#### Development
- No secrets required (uses default test values)

#### Staging
- `STAGING_SECRET_KEY`: Django secret key
- `STAGING_DB_*`: Database connection credentials
- `STAGING_REDIS_PASSWORD`: Redis authentication
- `STAGING_AUTH0_*`: Auth0 integration credentials
- `STAGING_SUPABASE_*`: Supabase integration credentials
- `STAGING_OPENAI_API_KEY`: OpenAI API access

#### Production
- `PRODUCTION_SECRET_KEY`: Django secret key
- `PRODUCTION_DB_*`: Database connection credentials
- `PRODUCTION_REDIS_PASSWORD`: Redis authentication
- `PRODUCTION_AUTH0_*`: Auth0 integration credentials
- `PRODUCTION_SUPABASE_*`: Supabase integration credentials
- `PRODUCTION_OPENAI_API_KEY`: OpenAI API access
- `PRODUCTION_SENTRY_DSN`: Error monitoring
- `PRODUCTION_APPROVERS`: GitHub usernames for manual approval

## Environment Configurations

### Development Environment

The development environment is optimized for local development with hot reloading and debugging capabilities.

```bash
# Using development Docker Compose
docker-compose -f docker/docker-compose.yml up -d

# Using development Dockerfile directly
docker build -f docker/Dockerfile.dev -t fluentpro:dev .
docker run -p 8000:8000 -e SERVICE_TYPE=web fluentpro:dev
```

**Features:**
- Auto-reload on code changes
- Debug toolbar enabled
- Test data creation
- Simplified logging
- Development-optimized dependencies

### Staging Environment

Staging mimics production but with relaxed security for testing purposes.

```bash
# Set up environment variables
cp .env.staging.example .env.staging
# Edit .env.staging with staging-specific values

# Deploy to staging
docker-compose -f docker/docker-compose.prod.yml --env-file .env.staging up -d
```

**Features:**
- Production-like database (PostgreSQL)
- Production-like caching (Redis)
- Security middleware enabled
- Monitoring and logging
- Performance testing capabilities

### Production Environment

Production deployment with full security, monitoring, and scalability features.

```bash
# Set up environment variables
cp .env.production.example .env.production
# Edit .env.production with production values

# Deploy to production
docker-compose -f docker/docker-compose.prod.yml --env-file .env.production up -d
```

**Features:**
- Full security hardening
- SSL/TLS encryption
- Load balancing with Nginx
- Comprehensive monitoring
- Automated backups
- High availability configuration

## Local Development Deployment

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-org/fluentpro_backend.git
   cd fluentpro_backend
   ```

2. **Set up environment:**
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Install dependencies (if running outside Docker)
   pip install -r requirements/development.txt
   ```

3. **Start services:**
   ```bash
   # Start all development services
   docker-compose up -d
   
   # Or start specific services
   docker-compose up redis postgres -d
   ```

4. **Run the application:**
   ```bash
   # Option 1: Using Docker (recommended)
   docker-compose -f docker/docker-compose.yml up web
   
   # Option 2: Direct Python execution
   python manage.py runserver
   ```

5. **Access the application:**
   - API: http://localhost:8000/
   - Admin: http://localhost:8000/admin/
   - API Docs: http://localhost:8000/api/docs/
   - Flower (Celery): http://localhost:5555/

### Development Services

The development stack includes:

- **Web Application**: Django development server with auto-reload
- **Database**: PostgreSQL (or SQLite for simple setups)
- **Cache/Broker**: Redis for caching and Celery
- **Worker**: Celery worker for background tasks
- **Beat**: Celery beat for scheduled tasks
- **Flower**: Celery monitoring interface

### Development Commands

```bash
# Database operations
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py collectstatic

# Testing
docker-compose exec web python -m pytest
docker-compose exec web python -m pytest --cov=. --cov-report=html

# Code quality
docker-compose exec web black .
docker-compose exec web isort .
docker-compose exec web flake8 .

# Shell access
docker-compose exec web python manage.py shell
docker-compose exec web bash
```

## Staging Deployment

### Manual Staging Deployment

1. **Prepare environment:**
   ```bash
   # Set staging environment variables
   export DJANGO_SETTINGS_MODULE=config.settings.staging
   
   # Verify configuration
   python manage.py check --deploy
   ```

2. **Build and deploy:**
   ```bash
   # Build production image
   docker build -t fluentpro:staging .
   
   # Deploy with staging configuration
   docker-compose -f docker/docker-compose.prod.yml \
     --env-file .env.staging up -d
   ```

3. **Post-deployment verification:**
   ```bash
   # Check service health
   curl -f http://staging-api.fluentpro.com/api/health/
   
   # Run integration tests
   python -m pytest tests/integration/ --base-url=http://staging-api.fluentpro.com
   ```

### Automated Staging Deployment

Staging deployments are triggered automatically:

- **On push to `develop` branch**
- **On manual workflow dispatch**

The GitHub Actions workflow will:
1. Build and test the application
2. Build Docker images
3. Deploy to staging environment
4. Run post-deployment health checks

## Production Deployment

### Production Deployment Process

Production deployments require manual approval and follow a blue-green deployment strategy:

1. **Trigger deployment:**
   - Push to `main` branch
   - Create a git tag (e.g., `v1.2.3`)
   - Manual workflow dispatch

2. **Approval process:**
   - Automated CI checks must pass
   - Manual approval from designated team members
   - Security scans must pass

3. **Deployment execution:**
   - Database backup creation
   - Blue-green deployment with zero downtime
   - Database migrations (if any)
   - Health checks and verification
   - Traffic switching

### Production Deployment Checklist

Before production deployment:

- [ ] All tests pass in CI
- [ ] Security scans completed
- [ ] Database migrations tested in staging
- [ ] Performance benchmarks acceptable
- [ ] Monitoring and alerting configured
- [ ] Rollback plan prepared
- [ ] Team notification sent

### Manual Production Deployment

For emergency deployments or special circumstances:

```bash
# 1. Create production backup
docker-compose -f docker/docker-compose.prod.yml exec db \
  pg_dump -U $DB_USER $DB_NAME > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Deploy new version
docker-compose -f docker/docker-compose.prod.yml pull
docker-compose -f docker/docker-compose.prod.yml up -d

# 3. Run migrations
docker-compose -f docker/docker-compose.prod.yml exec web \
  python manage.py migrate

# 4. Verify deployment
curl -f https://api.fluentpro.com/api/health/
```

## CI/CD Pipeline

### GitHub Actions Workflows

#### Continuous Integration (`ci.yml`)

Triggered on:
- Push to any branch
- Pull requests to `main` or `develop`

Pipeline stages:
1. **Code Quality**: Linting, formatting, type checking
2. **Security**: Dependency scanning, vulnerability checks
3. **Testing**: Unit, integration, and E2E tests
4. **Docker**: Build and security scan containers

#### Deployment (`deploy.yml`)

Triggered on:
- Push to `main` (production)
- Push to `develop` (staging)
- Manual workflow dispatch

Pipeline stages:
1. **Setup**: Determine target environment
2. **Build**: Create and push container images
3. **Deploy**: Environment-specific deployment
4. **Verify**: Post-deployment health checks

### Pipeline Configuration

#### Environment Variables in CI/CD

```yaml
# Development/Testing
DATABASE_URL: postgres://postgres:postgres@localhost:5432/test_fluentpro
REDIS_URL: redis://localhost:6379/15

# Staging (GitHub Secrets)
STAGING_SECRET_KEY: ${{ secrets.STAGING_SECRET_KEY }}
STAGING_DB_PASSWORD: ${{ secrets.STAGING_DB_PASSWORD }}
# ... other staging secrets

# Production (GitHub Secrets)
PRODUCTION_SECRET_KEY: ${{ secrets.PRODUCTION_SECRET_KEY }}
PRODUCTION_DB_PASSWORD: ${{ secrets.PRODUCTION_DB_PASSWORD }}
# ... other production secrets
```

#### Branch Protection Rules

- **main**: Requires PR reviews, CI checks, up-to-date branches
- **develop**: Requires CI checks, allows force push for hotfixes

## Monitoring and Health Checks

### Health Check Endpoints

- `/api/health/`: Basic application health
- `/api/health/database/`: Database connectivity
- `/api/health/cache/`: Redis connectivity
- `/api/health/external/`: External services status

### Monitoring Stack

The production deployment includes:

- **Prometheus**: Metrics collection
- **Grafana**: Metrics visualization
- **Flower**: Celery task monitoring
- **Nginx**: Access logs and performance metrics

### Health Check Commands

```bash
# Application health
curl -f http://localhost:8000/api/health/

# Service-specific health checks
docker-compose exec web python manage.py check_health --database
docker-compose exec web python manage.py check_health --cache
docker-compose exec web python manage.py check_health --external

# Container health status
docker-compose ps
docker inspect --format='{{.State.Health.Status}}' container_name
```

## Rollback Procedures

### Automatic Rollback

The deployment pipeline includes automatic rollback triggers:

- Health check failures post-deployment
- Error rate spikes
- Performance degradation

### Manual Rollback

#### Quick Rollback (Docker)

```bash
# Get previous image tag
PREVIOUS_TAG=$(git describe --tags --abbrev=0 HEAD~1)

# Update compose file with previous tag
sed -i "s/fluentpro:latest/fluentpro:${PREVIOUS_TAG}/" docker-compose.prod.yml

# Redeploy with previous version
docker-compose -f docker-compose.prod.yml up -d
```

#### Database Rollback

```bash
# Stop application
docker-compose -f docker-compose.prod.yml stop web worker

# Restore database backup
docker-compose -f docker-compose.prod.yml exec db \
  psql -U $DB_USER -d $DB_NAME < backup_file.sql

# Start application with previous version
docker-compose -f docker-compose.prod.yml up -d
```

### Rollback Verification

After rollback:

1. **Health Checks**: Verify all endpoints respond correctly
2. **Functionality Tests**: Run critical user journey tests
3. **Performance Monitoring**: Check response times and error rates
4. **Data Integrity**: Verify data consistency

## Security Considerations

### Container Security

- **Non-root user**: All containers run as non-privileged user
- **Minimal base images**: Alpine Linux for reduced attack surface
- **Security scanning**: Trivy scans for vulnerabilities
- **Secrets management**: Environment-based secret injection

### Network Security

- **Internal networks**: Backend services isolated from external access
- **TLS encryption**: All external traffic encrypted
- **Reverse proxy**: Nginx handles SSL termination and security headers

### Data Security

- **Environment isolation**: Staging and production completely separated
- **Backup encryption**: Database backups encrypted at rest
- **Access control**: Role-based access to deployment systems

### Security Monitoring

- **Vulnerability scanning**: Automated scanning in CI/CD
- **Dependency monitoring**: Safety checks for Python packages
- **Runtime monitoring**: Sentry for error tracking and security events

## Troubleshooting

For common deployment issues and solutions, see [Troubleshooting Guide](../troubleshooting.md).

### Common Commands

```bash
# View logs
docker-compose logs -f web
docker-compose logs -f worker

# Debug container
docker-compose exec web bash
docker-compose exec web python manage.py shell

# Reset environment
docker-compose down -v
docker-compose up -d

# Performance analysis
docker stats
docker-compose exec web python manage.py profile_requests
```

---

**Last Updated**: June 2025  
**Version**: 1.0.0  
**Maintainer**: FluentPro Development Team