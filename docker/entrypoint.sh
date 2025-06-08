#!/bin/bash

# Docker entrypoint script for FluentPro backend
# Handles initialization and service startup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting FluentPro Backend...${NC}"

# Default environment settings
export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-config.settings.production}
export PYTHONPATH=${PYTHONPATH:-/app}

# Determine service type from command or environment
SERVICE_TYPE=${SERVICE_TYPE:-web}

# Function to wait for services
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local timeout=${4:-30}
    
    echo -e "${YELLOW}⏳ Waiting for $service_name ($host:$port)...${NC}"
    
    for i in $(seq 1 $timeout); do
        if nc -z "$host" "$port" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name is ready!${NC}"
            return 0
        fi
        echo -e "${YELLOW}   Attempt $i/$timeout: $service_name not ready yet...${NC}"
        sleep 1
    done
    
    echo -e "${RED}❌ $service_name failed to become ready within $timeout seconds${NC}"
    return 1
}

# Function to run database migrations
run_migrations() {
    echo -e "${YELLOW}🔄 Running database migrations...${NC}"
    python manage.py migrate --noinput
    echo -e "${GREEN}✅ Migrations completed${NC}"
}

# Function to collect static files
collect_static() {
    if [ "$DJANGO_SETTINGS_MODULE" = "config.settings.production" ] || [ "$DJANGO_SETTINGS_MODULE" = "config.settings.staging" ]; then
        echo -e "${YELLOW}📦 Collecting static files...${NC}"
        python manage.py collectstatic --noinput --clear
        echo -e "${GREEN}✅ Static files collected${NC}"
    fi
}

# Function to create superuser if needed
create_superuser() {
    if [ "$CREATE_SUPERUSER" = "true" ] && [ -n "$SUPERUSER_EMAIL" ] && [ -n "$SUPERUSER_PASSWORD" ]; then
        echo -e "${YELLOW}👤 Creating superuser...${NC}"
        python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='$SUPERUSER_EMAIL').exists():
    User.objects.create_superuser('$SUPERUSER_EMAIL', '$SUPERUSER_PASSWORD')
    print('✅ Superuser created')
else:
    print('ℹ️  Superuser already exists')
EOF
    fi
}

# Function to validate configuration
validate_config() {
    echo -e "${YELLOW}🔍 Validating configuration...${NC}"
    python manage.py check --deploy
    echo -e "${GREEN}✅ Configuration validated${NC}"
}

# Wait for required services based on service type
if [ "$SERVICE_TYPE" = "web" ] || [ "$SERVICE_TYPE" = "worker" ] || [ "$SERVICE_TYPE" = "beat" ]; then
    # Wait for Redis if configured
    if [ -n "$REDIS_HOST" ]; then
        wait_for_service "$REDIS_HOST" "${REDIS_PORT:-6379}" "Redis"
    elif [ -n "$REDIS_URL" ]; then
        # Extract host and port from Redis URL
        REDIS_HOST=$(echo "$REDIS_URL" | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
        REDIS_PORT=$(echo "$REDIS_URL" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
        if [ -n "$REDIS_HOST" ] && [ -n "$REDIS_PORT" ]; then
            wait_for_service "$REDIS_HOST" "$REDIS_PORT" "Redis"
        fi
    fi
    
    # Wait for database if configured
    if [ -n "$DB_HOST" ]; then
        wait_for_service "$DB_HOST" "${DB_PORT:-5432}" "Database"
    fi
fi

# Service-specific initialization
case "$SERVICE_TYPE" in
    "web")
        echo -e "${GREEN}🌐 Starting web service...${NC}"
        
        # Run migrations and collect static files
        run_migrations
        collect_static
        create_superuser
        validate_config
        
        # Start Gunicorn
        echo -e "${GREEN}🚀 Starting Gunicorn server...${NC}"
        exec gunicorn config.wsgi:application \
            --bind 0.0.0.0:8000 \
            --workers ${GUNICORN_WORKERS:-4} \
            --worker-class ${GUNICORN_WORKER_CLASS:-sync} \
            --worker-connections ${GUNICORN_WORKER_CONNECTIONS:-1000} \
            --max-requests ${GUNICORN_MAX_REQUESTS:-1000} \
            --max-requests-jitter ${GUNICORN_MAX_REQUESTS_JITTER:-100} \
            --timeout ${GUNICORN_TIMEOUT:-30} \
            --keep-alive ${GUNICORN_KEEPALIVE:-2} \
            --access-logfile - \
            --error-logfile - \
            --log-level ${GUNICORN_LOG_LEVEL:-info}
        ;;
        
    "worker")
        echo -e "${GREEN}👷 Starting Celery worker...${NC}"
        exec celery -A workers.celery_app worker \
            --loglevel=${CELERY_LOG_LEVEL:-info} \
            --concurrency=${CELERY_WORKER_CONCURRENCY:-4} \
            --max-tasks-per-child=${CELERY_MAX_TASKS_PER_CHILD:-1000} \
            --time-limit=${CELERY_TASK_TIME_LIMIT:-300} \
            --soft-time-limit=${CELERY_TASK_SOFT_TIME_LIMIT:-240}
        ;;
        
    "beat")
        echo -e "${GREEN}⏰ Starting Celery beat scheduler...${NC}"
        exec celery -A workers.celery_app beat \
            --loglevel=${CELERY_LOG_LEVEL:-info} \
            --scheduler=django_celery_beat.schedulers:DatabaseScheduler
        ;;
        
    "flower")
        echo -e "${GREEN}🌸 Starting Flower monitoring...${NC}"
        exec celery -A workers.celery_app flower \
            --port=5555 \
            --broker=${CELERY_BROKER_URL:-redis://redis:6379/0}
        ;;
        
    "shell")
        echo -e "${GREEN}🐚 Starting Django shell...${NC}"
        exec python manage.py shell
        ;;
        
    "migrate")
        echo -e "${GREEN}🔄 Running migrations only...${NC}"
        run_migrations
        exit 0
        ;;
        
    "collectstatic")
        echo -e "${GREEN}📦 Collecting static files only...${NC}"
        collect_static
        exit 0
        ;;
        
    *)
        echo -e "${GREEN}🔧 Running custom command: $@${NC}"
        exec "$@"
        ;;
esac