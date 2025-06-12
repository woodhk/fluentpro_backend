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
API Routes (src/api/v1/) → Services (src/services/) → Repositories (src/repositories/) → Database
                      ↓                          ↓
              Schemas (src/schemas/) for validation    Integrations (src/integrations/) for external APIs
                      ↓
              Core (src/core/) for infrastructure
                      ↓
              Utils (src/utils/) for reusable functions
```

**Repository Pattern Implementation:**
- `BaseRepository`: Abstract base class with CRUD operations
- `SupabaseRepository`: Concrete implementation for Supabase operations
- `UserRepository`: Domain-specific repository extending SupabaseRepository
- Repositories handle all database interactions and data formatting

### Key Components

**Authentication System:**
- `Auth0ManagementClient`: Programmatic user creation in Auth0
- `get_current_user()` dependency: JWT validation and user retrieval
- Rate limiting on all auth endpoints (30/minute)

**Data Access Layer:**
- `UserRepository`: All user data operations using repository pattern
- `UserService`: Business logic layer between API and repositories
- Async-first design with `httpx` for external API calls

**Validation and Utilities:**
- `utils/validators.py`: Input validation functions (email, password strength, etc.)
- `schemas/common.py`: Reusable Pydantic models for pagination, responses
- Proper error handling with custom exceptions in `core/exceptions.py`

**Configuration:**
- Environment-based settings via `pydantic-settings`
- Auth0, Supabase, and Redis configuration
- Structured logging with JSON format

## Development Patterns

### Adding New Features
1. **Repository Layer**: Create or extend repository classes in `src/repositories/`
   - Extend `SupabaseRepository` for new entities
   - Implement domain-specific query methods
2. **Service Layer**: Implement business logic in `src/services/`
   - Use repositories for data access
   - Handle validation and business rules
3. **API Layer**: Create route handlers in `src/api/v1/`
   - Define Pydantic schemas in `src/schemas/`
   - Apply rate limiting with appropriate limits
   - Use dependency injection for database/auth

### Adding New Validations
- Add reusable validators to `src/utils/validators.py`
- Create domain-specific schemas in `src/schemas/`
- Use validators in service layer before calling repositories

### Required Patterns
- **Always use async/await** for I/O operations
- **Apply rate limiting** to all endpoints using `@limiter.limit()`
- **Validate with Pydantic schemas** for request/response
- **Use dependency injection** for shared resources (database, auth)
- **Handle errors with appropriate HTTP status codes**
- **Use repository pattern** for all database operations
- **Use structured logging** with `get_logger(__name__)` instead of print statements
- **Apply input validation** in service layer using utils/validators

### Rate Limiting Configuration
- Auth endpoints: 30/minute (`AUTH_RATE_LIMIT`)
- General API: 100/minute (`API_RATE_LIMIT`)
- Sensitive operations: 5/minute (`STRICT_RATE_LIMIT`)

### Authentication Dependencies
- `get_current_user()`: Full user object from Supabase (creates user if doesn't exist)
- `get_current_user_auth0_id()`: Just the Auth0 ID from JWT token
- `get_db()`: Supabase client instance

### Repository Usage Pattern
```python
# In services layer
from ..repositories.user_repository import UserRepository

class SomeService:
    def __init__(self, db: Client):
        self.user_repo = UserRepository(db)
    
    async def some_method(self):
        # Use repository methods, not direct database calls
        user = await self.user_repo.get_by_auth0_id(auth0_id)
        return await self.user_repo.create_user(user_data)
```

## Environment Variables Required

**Auth0:**
- `AUTH0_DOMAIN`
- `AUTH0_CLIENT_ID`
- `AUTH0_CLIENT_SECRET`
- `AUTH0_AUDIENCE`
- `AUTH0_VERIFY_SIGNATURE` (optional, default: false) - Set to true in production to enable JWT signature verification

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