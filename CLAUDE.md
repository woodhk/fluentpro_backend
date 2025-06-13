# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FluentPro Backend is a FastAPI-based language learning platform API with Auth0 authentication and Supabase database integration. The system uses async-first architecture with no webhooks - all user management flows through direct API calls. The platform features AI-powered job matching using OpenAI embeddings and Azure Cognitive Search for semantic role discovery.

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
pytest -m slow          # Long-running tests

# Run single test file
pytest tests/unit/test_specific.py

# Run with verbose output (default in pytest.ini)
pytest -v
```

### Azure Search Management
```bash
# Create the Azure Search index (one-time setup)
python scripts/azure_search_management.py create-index

# Reindex all roles (update search index)
python scripts/azure_search_management.py reindex

# Clear search index
python scripts/azure_search_management.py clear-index

# Generate missing embeddings
python scripts/azure_search_management.py generate-embeddings
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

### AI-Powered Job Matching Flow
```
User Input → OpenAI Embedding → Azure Search (Vector) → Role Matches → User Selection → Database Update
```

**Vector Search System:**
- Azure Cognitive Search with OpenAI embeddings (text-embedding-3-small, 1536 dimensions)
- HNSW algorithm configuration for semantic search
- Industry-filtered role matching with confidence scores
- Custom role creation with automatic embedding generation and indexing

### Onboarding Flow Architecture
**Three-Part System:**
- **Part 1**: Native language, industry selection, role search/selection with AI matching
- **Part 2**: Communication partner and situation selection with priority-based preferences
- **Part 3**: Additional onboarding steps (placeholder)

**Part 2 Communication Flow:**
```
GET /communication-partners → SELECT partners → GET /situations/{partner_id} → SELECT situations → GET /summary → POST /complete
```

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
- `CommunicationRepository`: Handles communication partners and user selections
- Repositories handle all database interactions and data formatting

### Key Components

**Authentication System:**
- `Auth0ManagementClient`: Programmatic user creation in Auth0
- `get_current_user()` dependency: JWT validation and user retrieval
- Rate limiting on all auth endpoints (30/minute)

**AI Integration Layer:**
- `AzureSearchClient`: Vector search operations with semantic configuration
- `OpenAIClient`: Embedding generation (single and batch operations)
- `JobMatchingService`: Business logic for role search and selection
- `AzureSearchService`: Management operations for reindexing and maintenance

**Data Access Layer:**
- `UserRepository`: All user data operations using repository pattern
- `CommunicationRepository`: Communication partner and situation selection data
- `UserService`: Business logic layer between API and repositories
- `CommunicationService`: Manages Part 2 onboarding flow with partner/situation selections
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
from ..repositories.onboarding.communication_repository import CommunicationRepository

class SomeService:
    def __init__(self, db: Client):
        self.user_repo = UserRepository(db)
        self.comm_repo = CommunicationRepository(db)
    
    async def some_method(self):
        # Use repository methods, not direct database calls
        user = await self.user_repo.get_by_auth0_id(auth0_id)
        partners = await self.comm_repo.get_all_active_partners()
        return await self.user_repo.create_user(user_data)
```

### Error Handling Pattern
```python
# In service methods - proper exception handling
try:
    # Validation errors should raise ValueError
    if invalid_data:
        raise ValueError("Specific validation message")
    
    # Business logic here
    result = await self.repo.some_operation()
    return result
    
except ValueError:
    # Re-raise ValueError as-is for validation errors
    raise
except Exception as e:
    # Wrap other exceptions in DatabaseError
    logger.error(f"Operation failed: {str(e)}")
    raise DatabaseError(f"Operation failed: {str(e)}")
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

**OpenAI:**
- `OPENAI_API_KEY`
- `OPENAI_EMBEDDING_MODEL` (optional, default: "text-embedding-3-small")

**Azure Search:**
- `AZURE_SEARCH_ENDPOINT`
- `AZURE_SEARCH_KEY`
- `AZURE_SEARCH_INDEX_NAME` (optional, default: "roles-index")

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

### Test Structure
- **Unit Tests**: Individual component testing with mocked dependencies
- **Integration Tests**: Cross-component testing with mocked external services
- **E2E Tests**: Full flow testing using FastAPI TestClient with dependency overrides

### Test Database Patterns
- Use mocked repositories in unit tests
- Use `app.dependency_overrides` for E2E test isolation
- Mock external API calls (Auth0, Supabase, OpenAI, Azure Search)

## Communication Partner System

### Part 2 Onboarding Flow
The communication partner system allows users to select who they communicate with and in what situations:

**Database Tables:**
- `communication_partners`: Available partner types (Clients, Colleagues, etc.)
- `user_communication_partners`: User's selected partners with priority
- `units`: Available communication situations (Meetings, Phone Calls, etc.)
- `user_partner_units`: User's selected situations per partner with priority

**API Endpoints:**
- `GET /api/v1/onboarding/part-2/communication-partners`: Get available partners
- `POST /api/v1/onboarding/part-2/select-partners`: Select partners in priority order
- `GET /api/v1/onboarding/part-2/situations/{partner_id}`: Get situations for a partner
- `POST /api/v1/onboarding/part-2/select-situations`: Select situations for a partner
- `GET /api/v1/onboarding/part-2/summary`: Get user's complete selections
- `POST /api/v1/onboarding/part-2/complete`: Complete Part 2 and advance onboarding status

### Service Implementation Pattern
```python
class CommunicationService:
    def __init__(self, db: Client):
        self.comm_repo = CommunicationRepository(db)
        self.profile_repo = ProfileRepository(db)
    
    async def select_communication_partners(self, auth0_id: str, partner_ids: List[str]):
        # 1. Get and validate user exists
        # 2. Validate all partner IDs exist
        # 3. Save selections with priority (order matters)
        # 4. Return success with selection data
```

## AI Integration Patterns

### Role Search and Matching
```python
# In services layer - semantic search pattern
job_matching_service = JobMatchingService(db)
result = await job_matching_service.search_roles(
    auth0_id=auth0_id,
    job_title="Software Engineer", 
    job_description="Building web applications"
)
```

### Custom Role Creation
- User-provided roles automatically generate embeddings
- Real-time indexing in Azure Search
- Industry association for filtered search

### Admin Operations
**Reindexing Endpoint:**
```bash
# Trigger full reindex via API
POST /api/v1/admin/reindex-roles
# Returns: {"success": true, "total_roles": 14, "documents_indexed": 14}
```

**Vector Search Configuration:**
- HNSW algorithm for approximate nearest neighbor search
- Semantic ranking with confidence scores (0.0-1.0)
- Industry-scoped filtering to improve relevance

## Development Notes

**Background Tasks:**
- Celery framework is set up but not yet implemented (empty worker files)
- All operations currently run synchronously within FastAPI request-response cycle
- Long-running operations like role reindexing happen in real-time via admin endpoints

**Code Quality:**
- No linting/formatting tools are currently configured
- Consider adding Black + Ruff for code formatting and linting
- Testing is well-configured with pytest markers and structured test organization

**Build Scripts:**
- `build.sh`: Production dependency installation
- `start.sh`: Uvicorn server startup (uses PORT environment variable)

## Deployment Notes

- Deployed on Render using `render.yaml` configuration
- Rate limiting uses Redis in production, falls back to in-memory for development
- Structured JSON logging for production monitoring
- CORS configured for frontend integration