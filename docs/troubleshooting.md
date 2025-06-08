# FluentPro Backend - Troubleshooting Guide

This guide provides solutions to common issues you might encounter while developing, deploying, or maintaining the FluentPro backend application.

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Development Environment Issues](#development-environment-issues)
- [Docker and Container Issues](#docker-and-container-issues)
- [Database Issues](#database-issues)
- [Authentication and Authorization](#authentication-and-authorization)
- [API and Network Issues](#api-and-network-issues)
- [Performance Issues](#performance-issues)
- [Deployment Issues](#deployment-issues)
- [External Service Integration](#external-service-integration)
- [Testing Issues](#testing-issues)
- [Monitoring and Logging](#monitoring-and-logging)
- [Getting Help](#getting-help)

## Quick Diagnostics

### Health Check Commands

Run these commands to quickly identify issues:

```bash
# Application health
curl -f http://localhost:8000/api/health/

# Service status
docker-compose ps

# System resources
docker stats --no-stream

# Recent logs
docker-compose logs --tail=50 web

# Configuration validation
docker-compose exec web python manage.py check
```

### Emergency Reset

If everything seems broken, try this emergency reset:

```bash
# Stop all services
docker-compose down -v

# Clean up Docker resources
docker system prune -f

# Rebuild and restart
docker-compose build --no-cache
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate
```

## Development Environment Issues

### Issue: Application Won't Start

**Symptoms:**
- Server fails to start
- Import errors on startup
- Django configuration errors

**Solutions:**

1. **Check Python Path and Virtual Environment:**
   ```bash
   # Verify Python version
   python --version  # Should be 3.11+
   
   # Check virtual environment
   which python
   pip list | grep Django
   ```

2. **Verify Django Settings:**
   ```bash
   # Check settings module
   echo $DJANGO_SETTINGS_MODULE
   
   # Validate configuration
   python manage.py check --deploy
   
   # Check for syntax errors
   python -m py_compile manage.py
   ```

3. **Install Missing Dependencies:**
   ```bash
   # Reinstall requirements
   pip install -r requirements/development.txt
   
   # Or with Docker
   docker-compose build web
   ```

### Issue: Import Errors

**Symptoms:**
- `ModuleNotFoundError`
- `ImportError: No module named 'xxx'`

**Solutions:**

1. **Check PYTHONPATH:**
   ```bash
   # Add project root to PYTHONPATH
   export PYTHONPATH="${PYTHONPATH}:/path/to/fluentpro_backend"
   
   # Or in Docker
   docker-compose exec web python -c "import sys; print(sys.path)"
   ```

2. **Verify Package Installation:**
   ```bash
   # Check if package is installed
   pip show package-name
   
   # Reinstall specific package
   pip uninstall package-name
   pip install package-name
   ```

3. **Domain Import Issues:**
   ```bash
   # Check domain structure
   find domains/ -name "*.py" -exec python -m py_compile {} \;
   
   # Verify __init__.py files exist
   find domains/ -type d -exec test -f {}/__init__.py \; -print
   ```

### Issue: Environment Variables Not Loaded

**Symptoms:**
- Configuration errors
- Default values being used
- External services not connecting

**Solutions:**

1. **Check .env File:**
   ```bash
   # Verify .env file exists and is readable
   ls -la .env
   cat .env | grep -v "^#" | grep -v "^$"
   ```

2. **Load Environment Variables:**
   ```bash
   # Source environment manually
   set -a; source .env; set +a
   
   # Or use python-decouple
   python -c "from decouple import config; print(config('DEBUG'))"
   ```

3. **Docker Environment Issues:**
   ```bash
   # Check environment in container
   docker-compose exec web env | grep DJANGO
   
   # Update docker-compose.yml
   services:
     web:
       env_file: .env
   ```

## Docker and Container Issues

### Issue: Port Already in Use

**Symptoms:**
- `Port 8000 is already allocated`
- `Address already in use`

**Solutions:**

1. **Find and Kill Process:**
   ```bash
   # Find process using port
   lsof -i :8000
   netstat -tulpn | grep 8000
   
   # Kill process
   kill -9 [PID]
   
   # Or kill all Python processes (careful!)
   pkill -f python
   ```

2. **Change Port Configuration:**
   ```bash
   # Modify docker-compose.yml
   services:
     web:
       ports:
         - "8001:8000"  # Use different external port
   
   # Or set in environment
   export PORT=8001
   ```

### Issue: Permission Denied

**Symptoms:**
- `Permission denied` errors
- Files owned by root
- Cannot write to volumes

**Solutions:**

1. **Fix File Permissions:**
   ```bash
   # Change ownership to current user
   sudo chown -R $USER:$USER .
   
   # Make scripts executable
   chmod +x docker/entrypoint*.sh
   ```

2. **Docker User Configuration:**
   ```bash
   # Add user to docker group (Linux)
   sudo usermod -aG docker $USER
   newgrp docker
   
   # Fix Docker Desktop permissions (macOS)
   # Restart Docker Desktop
   ```

3. **Volume Permission Issues:**
   ```dockerfile
   # In Dockerfile, create user with matching UID
   ARG USER_ID=1000
   ARG GROUP_ID=1000
   RUN groupadd -g $GROUP_ID app && \
       useradd -u $USER_ID -g app app
   ```

### Issue: Container Won't Build

**Symptoms:**
- Build failures
- Package installation errors
- Dependency conflicts

**Solutions:**

1. **Clear Docker Cache:**
   ```bash
   # Clean build cache
   docker-compose build --no-cache
   
   # Remove unused images
   docker image prune -f
   
   # Full system cleanup
   docker system prune -af
   ```

2. **Fix Package Dependencies:**
   ```bash
   # Update package lists
   docker run --rm ubuntu:latest apt-get update
   
   # Check requirements conflicts
   pip-compile requirements/base.in
   ```

3. **Dockerfile Issues:**
   ```dockerfile
   # Add error handling
   RUN apt-get update && apt-get install -y \
       package1 \
       package2 \
       && rm -rf /var/lib/apt/lists/*
   
   # Pin package versions
   RUN pip install --no-cache-dir \
       Django==4.2.0 \
       psycopg2-binary==2.9.5
   ```

## Database Issues

### Issue: Database Connection Failed

**Symptoms:**
- `django.db.utils.OperationalError`
- `FATAL: database "fluentpro" does not exist`
- Connection timeouts

**Solutions:**

1. **Check Database Service:**
   ```bash
   # Verify database is running
   docker-compose ps postgres
   
   # Check database logs
   docker-compose logs postgres
   
   # Restart database
   docker-compose restart postgres
   ```

2. **Database Configuration:**
   ```bash
   # Test connection manually
   docker-compose exec postgres psql -U fluentpro -d fluentpro_dev
   
   # Check connection settings
   python manage.py dbshell
   ```

3. **Create Missing Database:**
   ```bash
   # Connect as superuser and create database
   docker-compose exec postgres psql -U postgres
   CREATE DATABASE fluentpro_dev;
   CREATE USER fluentpro WITH PASSWORD 'password';
   GRANT ALL PRIVILEGES ON DATABASE fluentpro_dev TO fluentpro;
   ```

### Issue: Migration Failures

**Symptoms:**
- Migration conflicts
- `django.db.migrations.exceptions.InconsistentMigrationHistory`
- Foreign key constraint errors

**Solutions:**

1. **Reset Migrations (Development Only):**
   ```bash
   # WARNING: This deletes all data
   docker-compose down -v
   docker-compose up -d postgres
   
   # Delete migration files (keep __init__.py)
   find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
   find . -path "*/migrations/*.pyc" -delete
   
   # Create fresh migrations
   docker-compose exec web python manage.py makemigrations
   docker-compose exec web python manage.py migrate
   ```

2. **Resolve Migration Conflicts:**
   ```bash
   # Show migration status
   docker-compose exec web python manage.py showmigrations
   
   # Merge migrations
   docker-compose exec web python manage.py makemigrations --merge
   ```

3. **Manual Migration Fix:**
   ```bash
   # Fake problematic migration
   docker-compose exec web python manage.py migrate --fake [app_name] [migration_name]
   
   # Then run normal migrate
   docker-compose exec web python manage.py migrate
   ```

### Issue: Database Performance

**Symptoms:**
- Slow queries
- High database CPU usage
- Connection pool exhaustion

**Solutions:**

1. **Optimize Queries:**
   ```python
   # Use Django Debug Toolbar to identify slow queries
   # Add select_related/prefetch_related
   queryset = Model.objects.select_related('foreign_key').all()
   
   # Use raw SQL for complex queries
   Model.objects.raw("SELECT * FROM table WHERE condition")
   ```

2. **Database Indexing:**
   ```python
   # Add database indexes
   class Meta:
       indexes = [
           models.Index(fields=['field1', 'field2']),
           models.Index(fields=['-created_at']),
       ]
   ```

3. **Connection Pool Configuration:**
   ```python
   # In settings
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'OPTIONS': {
               'MAX_CONNS': 20,
               'MIN_CONNS': 5,
           }
       }
   }
   ```

## Authentication and Authorization

### Issue: Auth0 Integration Failures

**Symptoms:**
- `Invalid token` errors
- Authentication redirects fail
- User creation errors

**Solutions:**

1. **Verify Auth0 Configuration:**
   ```bash
   # Check environment variables
   echo $AUTH0_DOMAIN
   echo $AUTH0_CLIENT_ID
   
   # Test token validation
   python manage.py shell
   >>> from authentication.backends import Auth0JWTAuthentication
   >>> # Test token validation logic
   ```

2. **Token Debugging:**
   ```python
   import jwt
   
   # Decode token without verification (debugging only)
   token = "your.jwt.token"
   decoded = jwt.decode(token, options={"verify_signature": False})
   print(decoded)
   ```

3. **CORS Issues:**
   ```python
   # In settings, ensure proper CORS configuration
   CORS_ALLOWED_ORIGINS = [
       "http://localhost:3000",
       "https://your-frontend-domain.com",
   ]
   CORS_ALLOW_CREDENTIALS = True
   ```

### Issue: Permission Denied

**Symptoms:**
- `403 Forbidden` responses
- `PermissionDenied` exceptions
- User cannot access resources

**Solutions:**

1. **Check User Permissions:**
   ```bash
   # In Django shell
   docker-compose exec web python manage.py shell
   >>> from django.contrib.auth import get_user_model
   >>> User = get_user_model()
   >>> user = User.objects.get(email='user@example.com')
   >>> user.user_permissions.all()
   >>> user.groups.all()
   ```

2. **Verify API Permissions:**
   ```python
   # Check view permissions
   class MyAPIView(APIView):
       permission_classes = [IsAuthenticated, CustomPermission]
       
       def get(self, request):
           # Debug permission check
           self.check_permissions(request)
   ```

## API and Network Issues

### Issue: CORS Errors

**Symptoms:**
- Browser console shows CORS errors
- `Access-Control-Allow-Origin` header missing
- Preflight requests failing

**Solutions:**

1. **Configure CORS Headers:**
   ```python
   # Install django-cors-headers
   pip install django-cors-headers
   
   # Add to INSTALLED_APPS
   INSTALLED_APPS = [
       'corsheaders',
       # ...
   ]
   
   # Add middleware
   MIDDLEWARE = [
       'corsheaders.middleware.CorsMiddleware',
       'django.middleware.common.CommonMiddleware',
       # ...
   ]
   ```

2. **CORS Settings:**
   ```python
   # Allow specific origins
   CORS_ALLOWED_ORIGINS = [
       "http://localhost:3000",
       "https://app.fluentpro.com",
   ]
   
   # Or allow all (development only)
   CORS_ALLOW_ALL_ORIGINS = True
   
   # Allow credentials
   CORS_ALLOW_CREDENTIALS = True
   ```

### Issue: API Response Errors

**Symptoms:**
- `500 Internal Server Error`
- Malformed JSON responses
- Timeout errors

**Solutions:**

1. **Debug API Errors:**
   ```bash
   # Check detailed error logs
   docker-compose logs web | grep ERROR
   
   # Test API endpoints
   curl -v http://localhost:8000/api/health/
   
   # Use Django shell for debugging
   docker-compose exec web python manage.py shell
   ```

2. **API Serialization Issues:**
   ```python
   # Debug serializer errors
   serializer = MySerializer(data=request.data)
   if not serializer.is_valid():
       print(serializer.errors)
   ```

### Issue: Rate Limiting

**Symptoms:**
- `429 Too Many Requests`
- API calls being throttled
- Users can't access services

**Solutions:**

1. **Configure Rate Limits:**
   ```python
   # In DRF settings
   REST_FRAMEWORK = {
       'DEFAULT_THROTTLE_CLASSES': [
           'rest_framework.throttling.AnonRateThrottle',
           'rest_framework.throttling.UserRateThrottle'
       ],
       'DEFAULT_THROTTLE_RATES': {
           'anon': '100/hour',
           'user': '1000/hour'
       }
   }
   ```

2. **Bypass Rate Limiting (Development):**
   ```python
   # Temporarily disable throttling
   REST_FRAMEWORK = {
       'DEFAULT_THROTTLE_CLASSES': [],
       'DEFAULT_THROTTLE_RATES': {}
   }
   ```

## Performance Issues

### Issue: Slow Response Times

**Symptoms:**
- High response latency
- Timeout errors
- Poor user experience

**Solutions:**

1. **Profile Performance:**
   ```bash
   # Install django-debug-toolbar
   pip install django-debug-toolbar
   
   # Enable profiling
   docker-compose exec web python manage.py profile_requests
   ```

2. **Database Query Optimization:**
   ```python
   # Use Django Debug Toolbar SQL panel
   # Identify N+1 queries
   # Add select_related/prefetch_related
   
   queryset = MyModel.objects.select_related('related_field') \
                             .prefetch_related('many_to_many_field')
   ```

3. **Caching Implementation:**
   ```python
   # Add caching decorators
   from django.views.decorators.cache import cache_page
   
   @cache_page(60 * 15)  # Cache for 15 minutes
   def my_view(request):
       # View logic
   ```

### Issue: High Memory Usage

**Symptoms:**
- Container memory limits exceeded
- OOM (Out of Memory) errors
- Slow garbage collection

**Solutions:**

1. **Monitor Memory Usage:**
   ```bash
   # Check container memory usage
   docker stats --no-stream
   
   # Monitor Python memory usage
   docker-compose exec web python -c "
   import psutil
   process = psutil.Process()
   print(f'Memory: {process.memory_info().rss / 1024 / 1024:.2f} MB')
   "
   ```

2. **Optimize Memory Usage:**
   ```python
   # Use Django's iterator() for large querysets
   for obj in MyModel.objects.iterator():
       process(obj)
   
   # Clear unused variables
   del large_variable
   
   # Use generators instead of lists
   def my_generator():
       for item in large_dataset:
           yield process(item)
   ```

3. **Configure Memory Limits:**
   ```yaml
   # In docker-compose.yml
   services:
     web:
       mem_limit: 1g
       memswap_limit: 2g
   ```

## Deployment Issues

### Issue: Build Failures in CI/CD

**Symptoms:**
- GitHub Actions failing
- Docker build errors in pipeline
- Test failures in CI

**Solutions:**

1. **Check CI/CD Logs:**
   ```bash
   # View GitHub Actions logs
   # Go to Actions tab in GitHub repository
   # Click on failed workflow run
   # Examine each step's logs
   ```

2. **Reproduce Locally:**
   ```bash
   # Run the same commands locally
   docker build -f Dockerfile -t fluentpro:test .
   
   # Run tests in same environment
   docker run --rm fluentpro:test python -m pytest
   ```

3. **Fix Common CI Issues:**
   ```yaml
   # Ensure consistent Python version
   - uses: actions/setup-python@v4
     with:
       python-version: '3.11'
   
   # Cache dependencies
   - uses: actions/cache@v3
     with:
       path: ~/.cache/pip
       key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
   ```

### Issue: Production Deployment Failures

**Symptoms:**
- Service unavailable after deployment
- Database migration errors
- Configuration issues

**Solutions:**

1. **Check Deployment Health:**
   ```bash
   # Health check endpoints
   curl -f https://api.fluentpro.com/api/health/
   
   # Check service status
   docker-compose -f docker-compose.prod.yml ps
   
   # View production logs
   docker-compose -f docker-compose.prod.yml logs web
   ```

2. **Rollback Procedure:**
   ```bash
   # Quick rollback to previous version
   docker-compose -f docker-compose.prod.yml down
   
   # Update image tag to previous version
   sed -i 's/fluentpro:latest/fluentpro:v1.2.3/' docker-compose.prod.yml
   
   # Redeploy
   docker-compose -f docker-compose.prod.yml up -d
   ```

## External Service Integration

### Issue: OpenAI API Errors

**Symptoms:**
- `openai.error.RateLimitError`
- `openai.error.InvalidRequestError`
- AI features not working

**Solutions:**

1. **Check API Credentials:**
   ```bash
   # Verify API key
   echo $OPENAI_API_KEY
   
   # Test API connection
   curl -H "Authorization: Bearer $OPENAI_API_KEY" \
        https://api.openai.com/v1/models
   ```

2. **Handle Rate Limits:**
   ```python
   import openai
   import time
   from tenacity import retry, wait_exponential, stop_after_attempt
   
   @retry(wait=wait_exponential(multiplier=1, min=4, max=10),
          stop=stop_after_attempt(3))
   def call_openai_api():
       return openai.ChatCompletion.create(...)
   ```

### Issue: Supabase Connection Issues

**Symptoms:**
- Database connection failures
- Authentication errors with Supabase
- RLS policy violations

**Solutions:**

1. **Verify Supabase Configuration:**
   ```python
   from supabase import create_client
   
   supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
   response = supabase.table('test').select('*').execute()
   print(response)
   ```

2. **Handle RLS Policies:**
   ```sql
   -- Check Row Level Security policies
   SELECT * FROM pg_policies WHERE tablename = 'your_table';
   
   -- Temporarily disable RLS for debugging (development only)
   ALTER TABLE your_table DISABLE ROW LEVEL SECURITY;
   ```

## Testing Issues

### Issue: Tests Failing Randomly

**Symptoms:**
- Intermittent test failures
- Tests pass locally but fail in CI
- Race conditions in tests

**Solutions:**

1. **Fix Test Isolation:**
   ```python
   # Use pytest fixtures for proper setup/teardown
   @pytest.fixture
   def clean_database():
       # Setup
       yield
       # Cleanup
       
   # Use transaction rollback
   @pytest.mark.django_db(transaction=True)
   def test_my_function():
       # Test code
   ```

2. **Handle Async Code:**
   ```python
   import pytest
   import asyncio
   
   @pytest.mark.asyncio
   async def test_async_function():
       result = await my_async_function()
       assert result is not None
   ```

3. **Mock External Services:**
   ```python
   from unittest.mock import patch
   
   @patch('domains.external.openai_service.OpenAIService.call_api')
   def test_ai_integration(mock_openai):
       mock_openai.return_value = {"response": "test"}
       # Test code
   ```

## Monitoring and Logging

### Issue: Missing Logs

**Symptoms:**
- No logs appearing
- Silent failures
- Cannot debug issues

**Solutions:**

1. **Configure Logging:**
   ```python
   # In settings
   LOGGING = {
       'version': 1,
       'disable_existing_loggers': False,
       'handlers': {
           'console': {
               'class': 'logging.StreamHandler',
           },
       },
       'root': {
           'handlers': ['console'],
       },
   }
   ```

2. **Check Log Output:**
   ```bash
   # Docker logs
   docker-compose logs -f web
   
   # Application logs
   tail -f logs/fluentpro.log
   
   # System logs
   journalctl -u docker -f
   ```

### Issue: Performance Monitoring

**Symptoms:**
- Cannot identify bottlenecks
- No visibility into system performance
- Reactive rather than proactive monitoring

**Solutions:**

1. **Enable Application Monitoring:**
   ```python
   # Install django-prometheus
   pip install django-prometheus
   
   # Add to INSTALLED_APPS
   INSTALLED_APPS = ['django_prometheus']
   
   # Add middleware
   MIDDLEWARE = [
       'django_prometheus.middleware.PrometheusBeforeMiddleware',
       # ... other middleware
       'django_prometheus.middleware.PrometheusAfterMiddleware',
   ]
   ```

2. **Set Up Alerting:**
   ```yaml
   # prometheus/alerts.yml
   groups:
   - name: fluentpro
     rules:
     - alert: HighErrorRate
       expr: rate(django_http_responses_total{status=~"5.."}[5m]) > 0.1
       for: 5m
   ```

## Getting Help

### Internal Resources

1. **Documentation:**
   - [Environment Setup](development/environment_setup.md)
   - [Deployment Guide](development/deployment.md)
   - [Architecture Documentation](architecture/README.md)

2. **Team Communication:**
   - Slack channel: `#fluentpro-backend`
   - Team email: `backend-team@fluentpro.com`
   - Stand-up meetings: Daily at 9:00 AM

### External Resources

1. **Django Documentation:**
   - [Django Official Docs](https://docs.djangoproject.com/)
   - [Django REST Framework](https://www.django-rest-framework.org/)

2. **Docker Documentation:**
   - [Docker Docs](https://docs.docker.com/)
   - [Docker Compose](https://docs.docker.com/compose/)

3. **Community Support:**
   - Stack Overflow tags: `django`, `docker`, `python`
   - Django Discord: [discord.gg/django](https://discord.gg/django)

### Creating Bug Reports

When reporting bugs, include:

1. **Environment Information:**
   ```bash
   # System info
   uname -a
   docker --version
   python --version
   
   # Application info
   git rev-parse HEAD
   docker-compose config --services
   ```

2. **Steps to Reproduce:**
   - Exact commands run
   - Expected vs actual behavior
   - Screenshots or logs

3. **Error Messages:**
   - Full stack traces
   - Relevant log entries
   - Configuration details

### Emergency Procedures

For production issues:

1. **Immediate Response:**
   - Check monitoring dashboards
   - Review error logs
   - Notify team in Slack `#incidents`

2. **Escalation Path:**
   - Level 1: Development Team
   - Level 2: Senior Engineers
   - Level 3: System Administrators

3. **Communication:**
   - Update status page
   - Notify stakeholders
   - Document resolution

---

**Remember**: When in doubt, don't hesitate to ask for help. It's better to ask questions than to spend hours debugging alone!

**Last Updated**: June 2025  
**Version**: 1.0.0  
**Maintainer**: FluentPro Development Team