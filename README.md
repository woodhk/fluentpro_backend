# FluentPro Backend

A scalable Django REST API backend for the FluentPro language learning platform, featuring modern architecture, comprehensive authentication, and production-ready deployment.

## Features

- 🏗️ **Domain-Driven Design**: Clean architecture with separated business domains
- 🔐 **Auth0 Integration**: Secure JWT-based authentication and authorization
- 💾 **Multi-Database Support**: PostgreSQL for production, SQLite for development
- 🚀 **Async-First Architecture**: Celery workers, WebSocket support, and event-driven patterns
- 🌐 **RESTful API**: Comprehensive API with versioning and documentation
- 🐳 **Containerized Deployment**: Docker and Docker Compose for all environments
- 📊 **Monitoring & Observability**: Health checks, metrics, logging, and tracing
- 🧪 **Comprehensive Testing**: Unit, integration, and E2E test coverage
- 🔄 **CI/CD Pipeline**: Automated testing, security scanning, and deployment
- 🔒 **Security First**: Environment-specific configurations and security hardening

## API Endpoints

### Authentication Endpoints

All authentication endpoints are under the `/api/v1/auth/` prefix:

#### 1. User Sign Up
- **Endpoint**: `POST /api/v1/auth/signup/`
- **Description**: Register a new user
- **Authentication**: Not required

**Request Body:**
```json
{
    "full_name": "John Doe",
    "email": "john.doe@example.com",
    "password": "SecurePass123!",
    "date_of_birth": "1990-01-15"
}
```

**Response (201 Created):**
```json
{
    "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "user": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "full_name": "John Doe",
        "email": "john.doe@example.com",
        "date_of_birth": "1990-01-15"
    }
}
```

#### 2. User Login
- **Endpoint**: `POST /api/v1/auth/login/`
- **Description**: Authenticate an existing user
- **Authentication**: Not required

**Request Body:**
```json
{
    "email": "john.doe@example.com",
    "password": "SecurePass123!"
}
```

**Response (200 OK):**
```json
{
    "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "user": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "full_name": "John Doe",
        "email": "john.doe@example.com",
        "date_of_birth": "1990-01-15"
    }
}
```

#### 3. Refresh Token
- **Endpoint**: `POST /api/v1/auth/refresh/`
- **Description**: Get a new access token using refresh token
- **Authentication**: Not required

**Request Body:**
```json
{
    "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
    "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600
}
```

#### 4. User Logout
- **Endpoint**: `POST /api/v1/auth/logout/`
- **Description**: Revoke refresh token and log out user
- **Authentication**: Required (Bearer token)

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
    "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
    "message": "Successfully logged out"
}
```

#### 5. User Profile
- **Endpoint**: `GET /api/v1/auth/profile/`
- **Description**: Get current user's profile information
- **Authentication**: Required (Bearer token)

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "full_name": "John Doe",
    "email": "john.doe@example.com",
    "date_of_birth": "1990-01-15",
    "created_at": "2025-05-30T10:30:00Z",
    "updated_at": "2025-05-30T10:30:00Z"
}
```

#### 6. Health Check
- **Endpoint**: `GET /api/v1/auth/health/`
- **Description**: Check API health status
- **Authentication**: Not required

**Response (200 OK):**
```json
{
    "status": "healthy",
    "service": "fluentpro-backend",
    "version": "1.0.0",
    "environment": "production",
    "auth0_configured": true,
    "supabase_configured": true
}
```

### Error Responses

All endpoints may return error responses in the following format:

**400 Bad Request:**
```json
{
    "error": "Validation failed",
    "details": {
        "email": ["This field is required."],
        "password": ["Password must contain at least one uppercase letter"]
    }
}
```

**401 Unauthorized:**
```json
{
    "error": "Invalid credentials",
    "message": "Email or password is incorrect"
}
```

**409 Conflict:**
```json
{
    "error": "User already exists",
    "message": "A user with this email already exists"
}
```

**500 Internal Server Error:**
```json
{
    "error": "Internal server error",
    "message": "An unexpected error occurred"
}
```

## Quick Start

### Prerequisites

- **Docker & Docker Compose** (recommended)
- **Python 3.11+** (for local development)
- **Git** for version control

### 🚀 Get Running in 30 Seconds

```bash
# Clone the repository
git clone https://github.com/your-org/fluentpro_backend.git
cd fluentpro_backend

# Start all services with Docker
docker-compose up -d

# Run initial setup
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser

# Access the application
open http://localhost:8000
```

### 🎯 What You Get

- **API Server**: http://localhost:8000/
- **Admin Interface**: http://localhost:8000/admin/
- **API Documentation**: http://localhost:8000/api/docs/
- **Celery Monitor**: http://localhost:5555/

### 📖 Complete Setup Guide

For detailed setup instructions, environment configuration, and troubleshooting:

👉 **[Environment Setup Guide](docs/development/environment_setup.md)**

### Validation Rules

#### Sign Up Validation:
- **Full Name**: 2-50 characters, letters and spaces only
- **Email**: Valid email format
- **Password**: Minimum 8 characters with uppercase, lowercase, number, and special character
- **Date of Birth**: User must be at least 13 years old

#### Login Validation:
- **Email**: Valid email format
- **Password**: Required

## Authentication Flow

1. **Sign Up**: User creates account → Auth0 user created → Supabase user record created → JWT tokens returned
2. **Login**: User credentials verified with Auth0 → User data fetched from Supabase → JWT tokens returned
3. **API Requests**: Include `Authorization: Bearer <access_token>` header
4. **Token Refresh**: Use refresh token to get new access token when expired
5. **Logout**: Revoke refresh token in Auth0

## Architecture

This project follows Domain-Driven Design (DDD) principles with a clean, scalable architecture:

```
fluentpro_backend/
├── api/                    # API layer (views, serializers, routing)
├── application/            # Application services and containers
├── authentication/        # Authentication domain
├── config/                 # Django settings and configuration
├── core/                   # Shared utilities and base classes
├── domains/                # Business domains
│   ├── authentication/    # User authentication and authorization
│   ├── onboarding/        # User onboarding workflows  
│   └── shared/            # Shared domain models and events
├── infrastructure/        # External integrations and persistence
├── workers/               # Background task processing
└── docs/                  # Comprehensive documentation
```

## Documentation

### 📚 Complete Documentation

- **[Environment Setup](docs/development/environment_setup.md)** - Complete local development setup
- **[Deployment Guide](docs/development/deployment.md)** - Staging and production deployment
- **[Troubleshooting](docs/troubleshooting.md)** - Common issues and solutions
- **[Architecture Decisions](docs/architecture/decisions/)** - Technical decisions and rationale
- **[API Documentation](docs/api/)** - API versioning and style guide

### 🚀 Development Workflows

```bash
# Run tests
docker-compose exec web python -m pytest

# Code formatting
docker-compose exec web black .
docker-compose exec web isort .

# Type checking  
docker-compose exec web mypy .

# Database migrations
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate

# Access shell
docker-compose exec web python manage.py shell
```

### 🔧 Common Commands

```bash
# View logs
docker-compose logs -f web

# Restart services
docker-compose restart

# Clean reset
docker-compose down -v && docker-compose up -d

# Production deployment
docker-compose -f docker/docker-compose.prod.yml up -d
```

## Testing

```bash
# Run all tests
docker-compose exec web python -m pytest

# Run with coverage
docker-compose exec web python -m pytest --cov=. --cov-report=html

# Run specific test categories
docker-compose exec web python -m pytest tests/unit/
docker-compose exec web python -m pytest tests/integration/
docker-compose exec web python -m pytest tests/e2e/
```

## Deployment

### Development
```bash
docker-compose up -d
```

### Staging
```bash
docker-compose -f docker/docker-compose.prod.yml --env-file .env.staging up -d
```

### Production
Automated via GitHub Actions on push to `main` branch.

**👉 [Complete Deployment Guide](docs/development/deployment.md)**

## Getting Help

- **📖 Documentation**: Check the [docs/](docs/) directory
- **🐛 Issues**: Review [troubleshooting guide](docs/troubleshooting.md)
- **💬 Team**: Slack channel `#fluentpro-backend`
- **🚨 Emergencies**: See [troubleshooting guide](docs/troubleshooting.md#emergency-procedures)

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Follow the [environment setup guide](docs/development/environment_setup.md)
4. Make your changes and add tests
5. Run the test suite: `docker-compose exec web python -m pytest`
6. Submit a pull request

## License

This project is proprietary to FluentPro. All rights reserved.

---

**Version**: 1.0.0  
**Last Updated**: June 2025  
**Maintainer**: FluentPro Development Team
