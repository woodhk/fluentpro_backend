# FluentPro Backend - Local Environment Setup Guide

This guide will help you set up a complete local development environment for the FluentPro backend application.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Detailed Setup](#detailed-setup)
- [Development Tools](#development-tools)
- [IDE Configuration](#ide-configuration)
- [Testing Setup](#testing-setup)
- [Debugging](#debugging)
- [Common Issues](#common-issues)

## Prerequisites

### System Requirements

- **Operating System**: macOS 10.15+, Ubuntu 18.04+, or Windows 10+ with WSL2
- **RAM**: Minimum 8GB, recommended 16GB
- **Storage**: At least 5GB free space
- **Internet**: Stable connection for downloading dependencies

### Required Software

#### 1. Git
```bash
# macOS (with Homebrew)
brew install git

# Ubuntu/Debian
sudo apt update && sudo apt install git

# Windows
# Download from https://git-scm.com/download/win
```

#### 2. Docker & Docker Compose
```bash
# macOS
brew install docker docker-compose
# Or download Docker Desktop from https://www.docker.com/products/docker-desktop

# Ubuntu
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
sudo apt install docker-compose-plugin

# Windows
# Install Docker Desktop for Windows
```

#### 3. Python 3.11+
```bash
# macOS (with Homebrew)
brew install python@3.11

# Ubuntu
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev

# Windows (WSL2)
sudo apt update && sudo apt install python3.11 python3.11-venv python3.11-dev
```

#### 4. Node.js 18+ (for frontend tooling)
```bash
# macOS
brew install node@18

# Ubuntu
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Windows (WSL2)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### Verification

Verify all prerequisites are installed:

```bash
git --version          # Should show git version 2.30+
docker --version       # Should show Docker version 20.0+
docker-compose --version  # Should show docker-compose version 2.0+
python3 --version      # Should show Python 3.11+
node --version         # Should show Node.js 18+
npm --version          # Should show npm 8+
```

## Quick Start

For developers who want to get up and running quickly:

```bash
# 1. Clone the repository
git clone https://github.com/your-org/fluentpro_backend.git
cd fluentpro_backend

# 2. Start services with Docker
docker-compose up -d

# 3. Run initial setup
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser

# 4. Access the application
open http://localhost:8000
```

That's it! You should now have a running development environment.

## Detailed Setup

### 1. Repository Setup

#### Clone the Repository
```bash
git clone https://github.com/your-org/fluentpro_backend.git
cd fluentpro_backend
```

#### Set up Git Configuration
```bash
# Configure your identity
git config user.name "Your Name"
git config user.email "your.email@company.com"

# Set up pre-commit hooks (optional but recommended)
pip install pre-commit
pre-commit install
```

### 2. Environment Configuration

#### Create Environment File
```bash
# Copy the example environment file
cp .env.example .env

# Edit the file with your specific configuration
nano .env  # or use your preferred editor
```

#### Environment Variables
Essential variables for local development:

```bash
# .env file content
DJANGO_SETTINGS_MODULE=config.settings.development
DEBUG=True
SECRET_KEY=your-secret-key-for-development
DATABASE_URL=sqlite:///db.sqlite3
REDIS_URL=redis://localhost:6379/0

# External Services (for testing - use development/sandbox credentials)
AUTH0_DOMAIN=your-dev-domain.auth0.com
AUTH0_CLIENT_ID=your-dev-client-id
AUTH0_CLIENT_SECRET=your-dev-client-secret
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key
OPENAI_API_KEY=your-openai-key

# Optional: Skip validation for development
SKIP_SETTINGS_VALIDATION=False
```

### 3. Docker Development Setup

#### Option A: Full Docker Development (Recommended)

This approach runs everything in containers:

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**Services included:**
- Web application (Django)
- Database (PostgreSQL/SQLite)
- Redis (cache and Celery broker)
- Celery worker
- Celery beat scheduler
- Flower (Celery monitoring)

#### Option B: Hybrid Development

Run supporting services in Docker, Django on your host:

```bash
# Start only supporting services
docker-compose up -d redis postgres

# Install Python dependencies locally
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements/development.txt

# Run Django development server
python manage.py runserver
```

### 4. Database Setup

#### Database Initialization
```bash
# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser account
docker-compose exec web python manage.py createsuperuser

# Load initial data (if available)
docker-compose exec web python manage.py loaddata fixtures/initial_data.json
```

#### Create Test Data
```bash
# Create test users and data
docker-compose exec web python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
from domains.authentication.models import User

# Create test users
User = get_user_model()
if not User.objects.filter(email='test@fluentpro.dev').exists():
    User.objects.create_user(
        email='test@fluentpro.dev',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )
    print('✅ Test user created: test@fluentpro.dev / testpass123')
EOF
```

### 5. Verification

#### Health Checks
```bash
# Check application health
curl http://localhost:8000/api/health/

# Check specific components
curl http://localhost:8000/api/health/database/
curl http://localhost:8000/api/health/cache/
```

#### Access Points
- **Main API**: http://localhost:8000/
- **Admin Interface**: http://localhost:8000/admin/
- **API Documentation**: http://localhost:8000/api/docs/
- **Flower (Celery Monitor)**: http://localhost:5555/

#### Run Tests
```bash
# Run all tests
docker-compose exec web python -m pytest

# Run specific test categories
docker-compose exec web python -m pytest tests/unit/
docker-compose exec web python -m pytest tests/integration/

# Run with coverage
docker-compose exec web python -m pytest --cov=. --cov-report=html
```

## Development Tools

### Python Development

#### Virtual Environment (if not using Docker)
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements/development.txt

# Deactivate when done
deactivate
```

#### Package Management
```bash
# Install new package
pip install package-name

# Update requirements
pip freeze > requirements/development.txt

# Install from requirements
pip install -r requirements/development.txt
```

### Code Quality Tools

#### Linting and Formatting
```bash
# Format code with Black
docker-compose exec web black .

# Sort imports with isort
docker-compose exec web isort .

# Lint with flake8
docker-compose exec web flake8 .

# Type checking with mypy
docker-compose exec web mypy .

# All at once
docker-compose exec web bash -c "black . && isort . && flake8 . && mypy ."
```

#### Pre-commit Hooks
```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

### Database Tools

#### Database Management
```bash
# Connect to database
docker-compose exec postgres psql -U fluentpro -d fluentpro_dev

# Create migration
docker-compose exec web python manage.py makemigrations

# Apply migrations
docker-compose exec web python manage.py migrate

# Reset database
docker-compose exec web python manage.py flush --noinput
```

#### Data Management
```bash
# Create fixture from current data
docker-compose exec web python manage.py dumpdata --indent=2 > fixtures/current_data.json

# Load fixture data
docker-compose exec web python manage.py loaddata fixtures/test_data.json

# Backup database
docker-compose exec postgres pg_dump -U fluentpro fluentpro_dev > backup.sql
```

## IDE Configuration

### Visual Studio Code

#### Recommended Extensions
Create `.vscode/extensions.json`:

```json
{
    "recommendations": [
        "ms-python.python",
        "ms-python.black-formatter",
        "ms-python.isort",
        "ms-python.flake8",
        "ms-python.mypy-type-checker",
        "ms-vscode.vscode-json",
        "redhat.vscode-yaml",
        "ms-vscode-remote.remote-containers",
        "bradlc.vscode-tailwindcss"
    ]
}
```

#### Workspace Settings
Create `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    },
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        ".coverage": true,
        "htmlcov/": true
    }
}
```

#### Launch Configuration
Create `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Django",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/manage.py",
            "args": ["runserver", "0.0.0.0:8000"],
            "django": true,
            "justMyCode": true
        },
        {
            "name": "Django Tests",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": ["tests/"],
            "console": "integratedTerminal",
            "justMyCode": true
        }
    ]
}
```

### PyCharm

#### Project Setup
1. Open the project folder in PyCharm
2. Configure Python interpreter:
   - File → Settings → Project → Python Interpreter
   - Add → Docker Compose → Select `docker-compose.yml`
   - Service: `web`

#### Django Configuration
1. Enable Django support:
   - File → Settings → Languages & Frameworks → Django
   - Enable Django Support: ✓
   - Django project root: `[project root]`
   - Settings: `config/settings/development.py`

### Vim/Neovim

#### Basic Configuration
Add to your `.vimrc` or `init.vim`:

```vim
" Python development
let g:python3_host_prog = './venv/bin/python'

" Syntax highlighting
syntax on
filetype plugin indent on

" Python-specific settings
autocmd FileType python setlocal expandtab shiftwidth=4 softtabstop=4

" Django template syntax
autocmd BufNewFile,BufRead *.html set filetype=htmldjango
```

## Testing Setup

### Test Environment

#### Running Tests
```bash
# Run all tests
docker-compose exec web python -m pytest

# Run with specific markers
docker-compose exec web python -m pytest -m unit
docker-compose exec web python -m pytest -m integration
docker-compose exec web python -m pytest -m slow

# Run specific test file
docker-compose exec web python -m pytest tests/unit/test_models.py

# Run with coverage
docker-compose exec web python -m pytest --cov=. --cov-report=html --cov-report=term
```

#### Test Configuration
The project uses `pytest.ini` for test configuration:

```ini
[tool:pytest]
DJANGO_SETTINGS_MODULE = config.settings.testing
addopts = --tb=short --strict-markers --disable-warnings
markers = 
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
    external: Tests requiring external services
```

#### Test Database
Tests use a separate test database:
- **Development**: `fluentpro_dev`
- **Testing**: `test_fluentpro` (created/destroyed automatically)

### Continuous Testing

#### Watch Mode
```bash
# Install pytest-watch
pip install pytest-watch

# Run tests in watch mode
docker-compose exec web ptw -- tests/
```

#### Coverage Monitoring
```bash
# Generate coverage report
docker-compose exec web coverage run -m pytest
docker-compose exec web coverage report
docker-compose exec web coverage html

# View coverage report
open htmlcov/index.html
```

## Debugging

### Django Debug Toolbar

The development environment includes Django Debug Toolbar:

1. Ensure `DEBUG=True` in your environment
2. Access any page at http://localhost:8000
3. Look for the debug toolbar on the right side

### Python Debugger

#### Using pdb
```python
# Add to your code
import pdb; pdb.set_trace()

# Or use ipdb for enhanced debugging
import ipdb; ipdb.set_trace()
```

#### Remote Debugging with PyCharm/VSCode
```bash
# Install debugpy
pip install debugpy

# Add to your Django settings (development only)
if DEBUG:
    import debugpy
    debugpy.listen(("0.0.0.0", 5678))
    print("Waiting for debugger...")
    # debugpy.wait_for_client()  # Uncomment to wait for debugger
```

### Logging

#### Development Logging
```python
import logging
logger = logging.getLogger(__name__)

# Use throughout your code
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

#### View Logs
```bash
# Application logs
docker-compose logs -f web

# Database logs
docker-compose logs -f postgres

# Redis logs
docker-compose logs -f redis

# All logs
docker-compose logs -f
```

## Common Issues

### Docker Issues

#### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 [PID]

# Or change port in docker-compose.yml
```

#### Permission Issues
```bash
# Fix file permissions
sudo chown -R $USER:$USER .

# On Linux, add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

#### Container Won't Start
```bash
# View detailed logs
docker-compose logs web

# Rebuild containers
docker-compose build --no-cache
docker-compose up -d
```

### Database Issues

#### Migration Conflicts
```bash
# Reset migrations (development only)
docker-compose exec web python manage.py migrate --fake-initial

# Or reset database completely
docker-compose down -v
docker-compose up -d
docker-compose exec web python manage.py migrate
```

#### Connection Refused
```bash
# Check if database is running
docker-compose ps

# Restart database
docker-compose restart postgres

# Check database logs
docker-compose logs postgres
```

### Python Issues

#### Module Not Found
```bash
# Rebuild Python dependencies
docker-compose build web

# Or install in running container
docker-compose exec web pip install -r requirements/development.txt
```

#### Import Errors
```bash
# Check Python path
docker-compose exec web python -c "import sys; print(sys.path)"

# Verify Django settings
docker-compose exec web python manage.py check
```

### Performance Issues

#### Slow Startup
```bash
# Use cached images
docker-compose build --parallel

# Skip unnecessary services
docker-compose up web redis
```

#### High Memory Usage
```bash
# Monitor container resources
docker stats

# Limit memory usage in docker-compose.yml
services:
  web:
    mem_limit: 1g
```

## Next Steps

After setting up your environment:

1. **Read the [Architecture Documentation](../architecture/README.md)**
2. **Review [API Documentation](../api/versioning_guide.md)**
3. **Check [Deployment Guide](./deployment.md) for production deployment**
4. **Browse [Troubleshooting Guide](../troubleshooting.md) for common issues**

---

**Need Help?**
- Check the [Troubleshooting Guide](../troubleshooting.md)
- Ask in the team Slack channel `#fluentpro-backend`
- Create an issue in the GitHub repository

**Last Updated**: June 2025  
**Version**: 1.0.0  
**Maintainer**: FluentPro Development Team