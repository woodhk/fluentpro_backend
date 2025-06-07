# Architecture Patterns Guide

## Overview
This guide documents the architectural patterns used in the FluentPro backend. These patterns provide consistency, maintainability, and testability across the codebase.

## Core Patterns

### Repository Pattern
**Purpose**: Encapsulate data access logic and provide a more object-oriented view of the persistence layer.

**Location**: `core/patterns/repository.py`

**Usage**:
```python
from core.patterns.repository import IRepository

class IUserRepository(IRepository[User, str]):
    async def find_by_email(self, email: str) -> Optional[User]:
        pass
    
    async def find_by_auth0_id(self, auth0_id: str) -> Optional[User]:
        pass

# Implementation
class UserRepository(IUserRepository):
    def __init__(self, db_session):
        self.db = db_session
    
    async def find_by_email(self, email: str) -> Optional[User]:
        # Database query implementation
        return await self.db.query(User).filter(User.email == email).first()
```

**Benefits**:
- Testability through mock implementations
- Consistent data access interface
- Separation of concerns between business logic and data access
- Easy to switch persistence mechanisms

**Trade-offs**:
- Additional abstraction layer
- Can become complex with many query methods

### Use Case Pattern
**Purpose**: Encapsulate business logic in a reusable, testable unit.

**Location**: `core/patterns/use_case.py`

**Usage**:
```python
from core.patterns.use_case import UseCase

class AuthenticateUserUseCase(UseCase[LoginRequest, TokenResponse]):
    def __init__(self, user_repository: IUserRepository, auth_service: IAuthService):
        self.user_repository = user_repository
        self.auth_service = auth_service
    
    async def execute(self, request: LoginRequest) -> TokenResponse:
        # Validate credentials
        user = await self.user_repository.find_by_email(request.email)
        if not user or not self.auth_service.verify_password(request.password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password")
        
        # Generate tokens
        tokens = await self.auth_service.create_tokens(user)
        return TokenResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            expires_in=tokens.expires_in
        )
```

**Benefits**:
- Clear separation of business logic
- Highly testable
- Reusable across different interfaces (API, CLI, etc.)
- Single responsibility principle

**Trade-offs**:
- Can lead to many small classes
- May be overkill for simple operations

### Unit of Work Pattern
**Purpose**: Maintain a list of objects affected by a business transaction and coordinate writing out changes.

**Location**: `core/unit_of_work.py`

**Usage**:
```python
from core.unit_of_work import IUnitOfWork

class CompleteOnboardingUseCase:
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow
    
    async def execute(self, user_id: str, onboarding_data: OnboardingData):
        async with self.uow:
            user = await self.uow.users.find_by_id(user_id)
            industry = await self.uow.industries.find_by_id(onboarding_data.industry_id)
            
            user.update_profile(onboarding_data)
            user.complete_onboarding()
            
            await self.uow.users.update(user)
            await self.uow.commit()  # All changes committed together
```

**Benefits**:
- Ensures data consistency
- Transaction management
- Better performance (batched operations)

**Trade-offs**:
- Complexity in implementation
- Memory overhead for large transactions

### Value Object Pattern
**Purpose**: Represent a descriptive aspect of the domain with no conceptual identity.

**Location**: `core/patterns/value_object.py`, `domains/shared/value_objects/`

**Usage**:
```python
from core.patterns.value_object import ValueObject
from dataclasses import dataclass

@dataclass(frozen=True)
class Money(ValueObject):
    amount: float
    currency: str
    
    def _validate(self):
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")
        if self.currency not in ['USD', 'EUR', 'GBP']:
            raise ValueError(f"Unsupported currency: {self.currency}")
    
    def add(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)
```

**Benefits**:
- Immutability ensures data integrity
- Rich domain behavior
- Type safety
- Self-validating

**Trade-offs**:
- More objects in memory
- Can be overused for simple primitives

### Saga Pattern
**Purpose**: Manage distributed transactions and ensure consistency across services.

**Location**: `core/patterns/saga.py`

**Usage**:
```python
from core.patterns.saga import Saga, SagaStep

class UserRegistrationSaga(Saga):
    def __init__(self, auth_service, notification_service, analytics_service):
        super().__init__()
        self.auth_service = auth_service
        self.notification_service = notification_service
        self.analytics_service = analytics_service
    
    def define_steps(self) -> List[SagaStep]:
        return [
            SagaStep(
                name="create_auth0_user",
                action=self._create_auth0_user,
                compensation=self._delete_auth0_user
            ),
            SagaStep(
                name="send_welcome_email",
                action=self._send_welcome_email,
                compensation=self._send_cancellation_email
            ),
            SagaStep(
                name="track_registration",
                action=self._track_registration,
                compensation=self._remove_analytics_event
            )
        ]
```

**Benefits**:
- Handles complex distributed transactions
- Automatic compensation on failure
- Maintains system consistency

**Trade-offs**:
- Complex to implement and debug
- May not be needed for simple operations

### Specification Pattern
**Purpose**: Encapsulate business rules in reusable objects.

**Location**: `core/patterns/specification.py`

**Usage**:
```python
from core.patterns.specification import Specification

class ActiveUserSpecification(Specification[User]):
    def is_satisfied_by(self, user: User) -> bool:
        return user.is_active and not user.is_deleted

class PremiumUserSpecification(Specification[User]):
    def is_satisfied_by(self, user: User) -> bool:
        return user.subscription_type == 'premium'

# Combine specifications
premium_active_users = ActiveUserSpecification() & PremiumUserSpecification()
```

**Benefits**:
- Reusable business rules
- Composable with AND/OR operations
- Clear business logic expression

### Result Pattern
**Purpose**: Handle success and failure cases without exceptions.

**Location**: `core/patterns/result.py`

**Usage**:
```python
from core.patterns.result import Result, Success, Failure

async def authenticate_user(email: str, password: str) -> Result[User, str]:
    user = await user_repository.find_by_email(email)
    if not user:
        return Failure("User not found")
    
    if not verify_password(password, user.password_hash):
        return Failure("Invalid password")
    
    return Success(user)

# Usage
result = await authenticate_user("user@example.com", "password")
if result.is_success():
    user = result.value
    print(f"Welcome {user.name}!")
else:
    print(f"Login failed: {result.error}")
```

## Decorators

### @retry
**Purpose**: Automatically retry failed operations with exponential backoff.

**Location**: `application/decorators/retry.py`

**Usage**:
```python
from application.decorators import retry

@retry(max_attempts=3, backoff_seconds=1.0, exponential=True)
async def call_external_api():
    # Will retry up to 3 times with exponential backoff
    response = await external_service.call_api()
    return response
```

**Benefits**:
- Handles transient failures automatically
- Configurable retry strategies
- Reduces boilerplate error handling

**Trade-offs**:
- Can mask real issues if overused
- May increase latency

### @circuit_breaker
**Purpose**: Prevent cascading failures in distributed systems.

**Location**: `application/decorators/circuit_breaker.py`

**Usage**:
```python
from application.decorators import circuit_breaker

@circuit_breaker(failure_threshold=5, recovery_timeout=60)
async def call_payment_service():
    # Circuit opens after 5 failures, stays open for 60 seconds
    return await payment_service.process_payment()
```

**Benefits**:
- Prevents cascading failures
- Fast failure when service is down
- Automatic recovery detection

**Trade-offs**:
- Adds complexity to debugging
- May reject valid requests during recovery

### @cache
**Purpose**: Cache function results to improve performance.

**Location**: `application/decorators/cache.py`

**Usage**:
```python
from application.decorators import cache
from datetime import timedelta

@cache(key_prefix="user_profile", ttl=timedelta(minutes=15))
async def get_user_profile(user_id: str):
    # Results cached for 15 minutes
    return await user_repository.get_profile(user_id)
```

**Benefits**:
- Automatic caching with minimal code changes
- Configurable TTL
- Performance improvements

**Trade-offs**:
- Memory usage
- Cache invalidation complexity
- Potential stale data

### @validate_input / @validate_output
**Purpose**: Validate function inputs and outputs using Pydantic models.

**Location**: `application/decorators/validate.py`

**Usage**:
```python
from application.decorators import validate_input, validate_output

@validate_input(UserCreateRequest)
@validate_output(UserResponse)
async def create_user(request_data: dict) -> dict:
    # Input automatically validated against UserCreateRequest model
    # Output automatically validated against UserResponse model
    user = await user_service.create(request_data)
    return user.to_dict()
```

**Benefits**:
- Automatic validation
- Clear API contracts
- Consistent error handling

**Trade-offs**:
- Performance overhead
- Additional model definitions needed

### @audit_log
**Purpose**: Track user actions for compliance and debugging.

**Location**: `application/decorators/audit.py`

**Usage**:
```python
from application.decorators import audit_log

@audit_log(action="delete_user", resource_type="user")
async def delete_user(user_id: str):
    # Automatically logs who deleted which user and when
    await user_repository.delete(user_id)
```

**Benefits**:
- Automatic audit trail
- Compliance support
- Debugging assistance

**Trade-offs**:
- Storage overhead
- Performance impact
- Privacy considerations

## Utilities

### Validation Utils
**Location**: `core/utils/validation_utils.py`

**Purpose**: Common validation functions for emails, passwords, URLs, etc.

**Key Functions**:
- `is_valid_email(email: str) -> bool`
- `is_strong_password(password: str) -> tuple[bool, Optional[str]]`
- `sanitize_input(text: str, max_length: int) -> str`
- `validate_phone_number(phone: str) -> bool`

### Datetime Utils
**Location**: `core/utils/datetime_utils.py`

**Purpose**: Consistent datetime handling across the application.

**Key Functions**:
- `utc_now() -> datetime`
- `time_ago(dt: datetime) -> str`
- `add_business_days(dt: datetime, days: int) -> datetime`
- `calculate_duration(start_dt: datetime, end_dt: datetime) -> dict`

### String Utils
**Location**: `core/utils/string_utils.py`

**Purpose**: Common string operations and text processing.

**Key Functions**:
- `slugify(text: str, max_length: int) -> str`
- `truncate_text(text: str, max_length: int) -> str`
- `extract_keywords(text: str, max_keywords: int) -> List[str]`
- `mask_string(text: str, visible_chars: int) -> str`

### Data Utils
**Location**: `core/utils/data_utils.py`

**Purpose**: Data manipulation and processing utilities.

**Key Functions**:
- `flatten_dict(data: Dict, sep: str) -> Dict`
- `paginate_results(results: List, page: int, page_size: int) -> Dict`
- `deep_merge(dict1: Dict, dict2: Dict) -> Dict`
- `remove_none_values(data: Dict, recursive: bool) -> Dict`

## Best Practices

### Pattern Selection Guidelines

1. **Use Repository Pattern when**:
   - You have complex data access logic
   - You need to support multiple data sources
   - Testing with mocked data is important

2. **Use Use Case Pattern when**:
   - You have complex business logic
   - Logic needs to be reused across interfaces
   - You want clear separation of concerns

3. **Use Value Objects when**:
   - You have domain concepts with validation rules
   - Immutability is important
   - You want type safety

4. **Use Decorators when**:
   - You have cross-cutting concerns (logging, caching, validation)
   - You want to keep business logic clean
   - You need consistent behavior across multiple functions

### Combining Patterns

Patterns work best when combined thoughtfully:

```python
# Good: Repository + Use Case + Decorators
class GetUserStatsUseCase(UseCase[UserStatsRequest, UserStatsResponse]):
    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository
    
    @validate_input(UserStatsRequest)
    @audit_log(action="view_stats", resource_type="user")
    @cache(key_prefix="user_stats", ttl=timedelta(hours=1))
    async def execute(self, request: UserStatsRequest) -> UserStatsResponse:
        user = await self.user_repository.find_by_id(request.user_id)
        if not user:
            raise EntityNotFoundException("User not found")
        
        return UserStatsResponse(user_id=user.id, stats=user.calculate_stats())
```

### Anti-Patterns to Avoid

1. **Overusing Patterns**: Don't use complex patterns for simple operations
2. **Circular Dependencies**: Ensure clean dependency graphs
3. **God Objects**: Keep classes focused on single responsibilities
4. **Leaky Abstractions**: Don't expose implementation details through interfaces

## Testing Strategies

### Repository Testing
```python
# Mock repository for testing
class MockUserRepository(IUserRepository):
    def __init__(self):
        self.users = {}
    
    async def find_by_id(self, user_id: str) -> Optional[User]:
        return self.users.get(user_id)

# Test use case with mock
async def test_authenticate_user():
    mock_repo = MockUserRepository()
    use_case = AuthenticateUserUseCase(mock_repo, mock_auth_service)
    
    result = await use_case.execute(LoginRequest(email="test@example.com", password="password"))
    assert result.access_token is not None
```

### Decorator Testing
```python
# Test decorator behavior
@patch('application.decorators.cache.CacheService')
async def test_cache_decorator(mock_cache):
    @cache(key_prefix="test", ttl=timedelta(minutes=5))
    async def cached_function(value: str) -> str:
        return f"processed_{value}"
    
    result = await cached_function("input")
    mock_cache.return_value.set.assert_called_once()
```

## Migration Guide

When introducing these patterns to existing code:

1. **Start with decorators** - Easy to add without major refactoring
2. **Extract repositories** - Move data access logic to repository classes
3. **Create use cases** - Move business logic to dedicated use case classes
4. **Introduce value objects** - Replace primitive types with domain objects
5. **Add comprehensive tests** - Ensure patterns work as expected

## Performance Considerations

- **Caching**: Use appropriate TTL values, monitor cache hit rates
- **Validation**: Consider validation overhead for high-throughput endpoints
- **Audit Logging**: Use async logging to minimize performance impact
- **Value Objects**: Monitor memory usage with many small objects
- **Retry Logic**: Set reasonable timeouts to avoid blocking operations

This guide provides the foundation for maintaining a clean, scalable architecture. Each pattern should be evaluated for its specific use case and combined thoughtfully with others.