Project Overview

  FluentPro is a sophisticated language learning platform backend built with Django 5.2.1. The backend serves as an API-first
  platform providing:

  - User authentication and authorization via Auth0 integration
  - Multi-step onboarding flow for personalized learning experiences
  - Role-based access control with industry-specific job matching
  - Real-time communication via WebSockets
  - Background task processing for heavy operations
  - AI-powered features using OpenAI and Azure Cognitive Search

  Major Modules & Features

  Core Domains

  - Authentication Domain (domains/authentication/)
    - User registration, login, JWT token management
    - Role-based permissions and user profiles
    - Auth0 integration for secure authentication
  - Onboarding Domain (domains/onboarding/)
    - Multi-step user onboarding workflow
    - Industry selection and job role matching
    - Communication partner configuration
    - Personalization based on user preferences
  - Shared Domain (domains/shared/)
    - Common models, events, and value objects
    - Base repository implementations
    - Cross-domain utilities

  Infrastructure & External Integrations

  - Auth0: User authentication and JWT verification
  - Supabase: PostgreSQL database with real-time capabilities
  - OpenAI: AI-powered features and content generation
  - Azure Cognitive Search: Advanced search and indexing
  - Redis: Caching and session management
  - Celery: Asynchronous task processing

  Project Structure Summary

  Architecture Pattern: Domain-Driven Design (DDD)

  fluentpro_backend/
  ├── api/                    # API layer (views, serializers, routing)
  │   ├── v1/, v2/           # API versioning
  │   ├── common/            # Shared API components
  │   └── websocket/         # WebSocket consumers
  ├── application/           # Application services layer
  │   ├── container.py       # Dependency injection
  │   ├── decorators/        # Cross-cutting concerns (cache, retry, etc.)
  │   └── middleware/        # Request/response processing
  ├── domains/               # Business domains (DDD)
  │   ├── authentication/   # User auth domain
  │   ├── onboarding/       # User onboarding domain
  │   └── shared/           # Shared domain models
  ├── infrastructure/       # External integrations
  │   ├── external_services/ # Auth0, OpenAI, Azure clients
  │   ├── persistence/      # Database implementations
  │   └── messaging/        # Event bus and WebSocket management
  ├── core/                 # Framework abstractions
  ├── workers/              # Celery background tasks
  └── config/               # Django settings

  Design Patterns Used

  - Use Case Pattern: Business logic encapsulation
  - Repository Pattern: Data access abstraction
  - Event Sourcing: Domain events for cross-cutting concerns
  - Dependency Injection: Loose coupling via containers
  - Circuit Breaker: External service resilience
  - CQRS: Command/Query separation in use cases

  Key Components Explained

  Domain Models (domains/*/models/)

  Example: User Model (domains/authentication/models/user.py)
  - Rich domain models with business logic and validation
  - Enums for type safety (OnboardingStatus, NativeLanguage)
  - Domain events for cross-cutting concerns
  - Value objects for data integrity

  API Views (domains/*/api/v*/views.py)

  Example: UserProfileView (domains/authentication/api/v1/user_views.py)
  - Class-based views extending framework base classes
  - Auth0 JWT authentication
  - Caching and audit logging decorators
  - Comprehensive error handling
  - API documentation via decorators

  Use Cases (domains/*/use_cases/)

  Example: StartOnboardingSessionUseCase
  - Implements Command pattern for business operations
  - Async/await support for I/O operations
  - Clear separation of business logic from infrastructure
  - Dependency injection for testability

  Repository Implementations (infrastructure/persistence/)

  - Abstract interfaces in domain layer
  - Concrete implementations in infrastructure
  - Supabase client abstraction for database operations
  - Connection pooling and transaction support

  How Data Flows

  Request Processing Flow

  1. HTTP Request → Django Middleware (CORS, Auth, Logging)
  2. API Router → Versioned Endpoint (v1/v2)
  3. View Authentication → Auth0 JWT verification
  4. View Logic → Use Case execution
  5. Use Case → Domain Services & Repositories
  6. Repository → Supabase database operations
  7. Response → JSON serialization & caching

  Background Processing

  1. Domain Events → Event Publisher
  2. Celery Tasks → Background worker processing
  3. External API calls → Circuit breaker protection
  4. Task Results → Redis caching

  Business Logic Location

  - Domain Models: Core business rules and validation
  - Use Cases: Application workflows and orchestration
  - Domain Services: Complex business operations
  - Repositories: Data persistence abstraction

  Database Usage

  - Supabase PostgreSQL: Primary data store with real-time capabilities
  - Redis: Session storage, caching, and Celery message broker
  - SQLite: Development/testing database (configurable)

  Notable Technical Features

  - Async-First Architecture: Full async/await support throughout
  - API Versioning: v1/v2 with backward compatibility
  - Comprehensive Monitoring: Structured logging, metrics, health checks
  - Security: JWT tokens, CORS, environment-specific configurations
  - Testing: Unit, integration, and E2E test coverage
  - Documentation: OpenAPI/Swagger auto-generation
  - Deployment: Docker containerization with multi-environment support

  This backend demonstrates enterprise-grade architecture with clean separation of concerns, making it highly maintainable and
  scalable for a production language learning platform.