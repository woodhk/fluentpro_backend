#!/bin/bash

# Development entrypoint script for FluentPro backend
# Optimized for development workflow

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Starting FluentPro Backend (Development Mode)...${NC}"

# Development environment settings
export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-config.settings.development}
export PYTHONPATH=${PYTHONPATH:-/app}
export DEBUG=${DEBUG:-True}

# Service type from environment or default to web
SERVICE_TYPE=${SERVICE_TYPE:-web}

# Function to wait for services (simpler version for development)
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local timeout=${4:-15}
    
    echo -e "${YELLOW}⏳ Waiting for $service_name ($host:$port)...${NC}"
    
    for i in $(seq 1 $timeout); do
        if nc -z "$host" "$port" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name is ready!${NC}"
            return 0
        fi
        sleep 1
    done
    
    echo -e "${YELLOW}⚠️  $service_name not available, continuing anyway (development mode)${NC}"
    return 0
}

# Function to run database migrations
run_migrations() {
    echo -e "${YELLOW}🔄 Running database migrations...${NC}"
    python manage.py migrate --noinput
    echo -e "${GREEN}✅ Migrations completed${NC}"
}

# Function to create test data
create_test_data() {
    if [ "$CREATE_TEST_DATA" = "true" ]; then
        echo -e "${YELLOW}🧪 Creating test data...${NC}"
        python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

# Create test superuser
if not User.objects.filter(email='admin@fluentpro.dev').exists():
    User.objects.create_superuser(
        email='admin@fluentpro.dev',
        password='admin123'
    )
    print('✅ Test superuser created: admin@fluentpro.dev / admin123')

# Create test users
test_users = [
    ('user1@fluentpro.dev', 'Test User 1'),
    ('user2@fluentpro.dev', 'Test User 2'),
]

for email, name in test_users:
    if not User.objects.filter(email=email).exists():
        User.objects.create_user(
            email=email,
            password='testpass123',
            first_name=name.split()[0],
            last_name=name.split()[-1]
        )
        print(f'✅ Test user created: {email} / testpass123')
EOF
        echo -e "${GREEN}✅ Test data creation completed${NC}"
    fi
}

# Function to install frontend dependencies (if applicable)
install_frontend_deps() {
    if [ -f "package.json" ]; then
        echo -e "${YELLOW}📦 Installing frontend dependencies...${NC}"
        npm install
        echo -e "${GREEN}✅ Frontend dependencies installed${NC}"
    fi
}

# Function to show development info
show_dev_info() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}🔧 DEVELOPMENT ENVIRONMENT INFORMATION${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}🌐 Django Admin: http://localhost:8000/admin/${NC}"
    echo -e "${GREEN}📚 API Documentation: http://localhost:8000/api/docs/${NC}"
    echo -e "${GREEN}🌸 Flower (Celery Monitor): http://localhost:5555/${NC}"
    echo -e "${GREEN}🔍 Django Debug Toolbar: Enabled${NC}"
    echo -e "${YELLOW}👤 Test Superuser: admin@fluentpro.dev / admin123${NC}"
    echo -e "${YELLOW}👥 Test Users: user1@fluentpro.dev / testpass123${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Wait for services in development
wait_for_service "redis" "6379" "Redis" 10

# Service-specific startup
case "$SERVICE_TYPE" in
    "web")
        echo -e "${GREEN}🌐 Starting development web server...${NC}"
        
        # Install frontend dependencies
        install_frontend_deps
        
        # Run migrations
        run_migrations
        
        # Create test data
        create_test_data
        
        # Show development information
        show_dev_info
        
        # Start Django development server with auto-reload
        echo -e "${GREEN}🚀 Starting Django development server...${NC}"
        exec python manage.py runserver 0.0.0.0:8000
        ;;
        
    "worker")
        echo -e "${GREEN}👷 Starting Celery worker (development)...${NC}"
        exec celery -A workers.celery_app worker \
            --loglevel=debug \
            --concurrency=2 \
            --reload
        ;;
        
    "beat")
        echo -e "${GREEN}⏰ Starting Celery beat scheduler (development)...${NC}"
        exec celery -A workers.celery_app beat \
            --loglevel=debug
        ;;
        
    "flower")
        echo -e "${GREEN}🌸 Starting Flower monitoring (development)...${NC}"
        exec celery -A workers.celery_app flower \
            --port=5555 \
            --broker=redis://redis:6379/0 \
            --basic_auth=admin:dev123
        ;;
        
    "shell")
        echo -e "${GREEN}🐚 Starting Django shell...${NC}"
        exec python manage.py shell_plus --ipython
        ;;
        
    "notebook")
        echo -e "${GREEN}📓 Starting Jupyter notebook...${NC}"
        exec python manage.py shell_plus --notebook
        ;;
        
    "test")
        echo -e "${GREEN}🧪 Running tests...${NC}"
        exec python -m pytest "${@:-tests/}" -v --tb=short
        ;;
        
    "test-watch")
        echo -e "${GREEN}🔍 Running tests in watch mode...${NC}"
        exec python -m pytest_watch "${@:-tests/}" -- -v --tb=short
        ;;
        
    "migrate")
        echo -e "${GREEN}🔄 Running migrations only...${NC}"
        run_migrations
        exit 0
        ;;
        
    "setup")
        echo -e "${GREEN}🛠️  Setting up development environment...${NC}"
        install_frontend_deps
        run_migrations
        create_test_data
        show_dev_info
        echo -e "${GREEN}✅ Development setup completed!${NC}"
        exit 0
        ;;
        
    *)
        echo -e "${GREEN}🔧 Running custom command: $@${NC}"
        exec "$@"
        ;;
esac