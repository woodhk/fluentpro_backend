# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FluentPro Backend is a FastAPI-based language learning platform API with Auth0 authentication and Supabase database integration. The system uses async-first architecture with no webhooks - all user management flows through direct API calls.

## Development Commands

### Setup and Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

### Running the Application
```bash
# Run development server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Run from main.py
python -m src.main
```

### Testing
```bash
# Run all tests
pytest

# Run specific test markers
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m auth          # Authentication tests
pytest -m rate_limit    # Rate limiting tests

# Run single test file
pytest tests/test_specific.py

# Run with verbose output
pytest -v
```

## Architecture Overview

### Core Authentication Flow
```
Swift App → POST /api/v1/auth/signup → Backend creates user in Auth0 → Backend creates user in Supabase → Returns success
```

**Key Decision: No Webhooks**
- All user operations go through the backend API
- Direct creation in both Auth0 and Supabase via API calls
- Simpler architecture, no webhook sync issues

### Layer Architecture
```
API Routes (src/api/v1/) → Services (src/services/) → Integrations (src/integrations/)
                      ↓
              Schemas (src/schemas/) for validation
                      ↓
              Core (src/core/) for infrastructure
```

### Key Components

**Authentication System:**
- `Auth0ManagementClient`: Programmatic user creation in Auth0
- `get_current_user()` dependency: JWT validation and user retrieval
- Rate limiting on all auth endpoints (30/minute)

**Database Integration:**
- `SupabaseUserRepository`: All user data operations
- `UserService`: Business logic layer between API and database
- Async-first design with `httpx` for external API calls

**Configuration:**
- Environment-based settings via `pydantic-settings`
- Auth0, Supabase, and Redis configuration
- Structured logging with JSON format

## Development Patterns

### Adding New Endpoints
1. Define Pydantic schemas in `src/schemas/`
2. Implement business logic in `src/services/`
3. Create route handlers in `src/api/v1/`
4. Apply rate limiting with appropriate limits
5. Use dependency injection for database/auth

### Required Patterns
- **Always use async/await** for I/O operations
- **Apply rate limiting** to all endpoints using `@limiter.limit()`
- **Validate with Pydantic schemas** for request/response
- **Use dependency injection** for shared resources (database, auth)
- **Handle errors with appropriate HTTP status codes**

### Rate Limiting Configuration
- Auth endpoints: 30/minute (`AUTH_RATE_LIMIT`)
- General API: 100/minute (`API_RATE_LIMIT`)
- Sensitive operations: 5/minute (`STRICT_RATE_LIMIT`)

### Authentication Dependencies
- `get_current_user()`: Full user object from Supabase
- `get_current_user_auth0_id()`: Just the Auth0 ID from JWT
- `get_db()`: Supabase client instance

## Environment Variables Required

**Auth0:**
- `AUTH0_DOMAIN`
- `AUTH0_CLIENT_ID`
- `AUTH0_CLIENT_SECRET`
- `AUTH0_AUDIENCE`

**Supabase:**
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_KEY`

**Optional:**
- `REDIS_URL` (for distributed rate limiting)
- `LOG_LEVEL`, `LOG_FORMAT`, `LOG_FILE` (for logging configuration)

## Testing Strategy

The project uses pytest with specific markers:
- `unit`: No external dependencies
- `integration`: May require network/deployed API  
- `auth`: Authentication-related tests
- `rate_limit`: Rate limiting functionality
- `slow`: Long-running tests

Integration tests can be run against the deployed API at `https://fluentpro-backend.onrender.com`

## Deployment Notes

- Deployed on Render
- Rate limiting uses Redis in production, falls back to in-memory for development
- Structured JSON logging for production monitoring
- CORS configured for frontend integration