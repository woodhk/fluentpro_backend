Comprehensive Implementation Plan for FluentPro Backend Refactoring

  Day 5: Standardize Repository Pattern

  ## Goal
  Implement a consistent repository pattern across all domains, separating data access logic from business logic and enabling easy testing with mock repositories.

  ## Step 3: Separate Interface from Implementation

  **Actions:**
  1. Move concrete implementations to infrastructure:
  ```bash
  # Create implementation directories
  mkdir -p infrastructure/persistence/supabase/implementations
  touch infrastructure/persistence/supabase/implementations/__init__.py
  ```

  2. Create concrete repository implementations:
  ```python
  # infrastructure/persistence/supabase/implementations/user_repository_impl.py
  from domains.authentication.repositories.interfaces import IUserRepository
  from domains.authentication.models.user import User
  from infrastructure.persistence.supabase.client import SupabaseClient
  from typing import Optional, List, Dict, Any
  
  class UserRepositoryImpl(IUserRepository):
      def __init__(self, supabase_client: SupabaseClient):
          self.client = supabase_client
          self.table = 'users'
      
      async def find_by_id(self, id: str) -> Optional[User]:
          result = await self.client.table(self.table).select('*').eq('id', id).single()
          return self._to_entity(result.data) if result.data else None
      
      async def find_by_email(self, email: str) -> Optional[User]:
          result = await self.client.table(self.table).select('*').eq('email', email).single()
          return self._to_entity(result.data) if result.data else None
      
      async def save(self, entity: User) -> User:
          data = self._to_dict(entity)
          if entity.id:
              result = await self.client.table(self.table).update(data).eq('id', entity.id).execute()
          else:
              result = await self.client.table(self.table).insert(data).execute()
          return self._to_entity(result.data[0])
      
      def _to_entity(self, data: dict) -> User:
          # Convert database row to User entity
          user = User(
              email=data['email'],
              full_name=data['full_name'],
              password_hash=data['password_hash']
          )
          user.id = data['id']
          user.created_at = data['created_at']
          user.updated_at = data['updated_at']
          return user
      
      def _to_dict(self, entity: User) -> dict:
          # Convert User entity to database row
          return {
              'email': entity.email,
              'full_name': entity.full_name,
              'password_hash': entity.password_hash
          }
  ```

  3. Update domain repositories to be abstract:
  ```python
  # domains/authentication/repositories/user_repository.py
  # This file should now only contain the interface (moved to interfaces.py)
  # Delete this file or keep it for backward compatibility with a deprecation warning
  ```

  **Verification:**
  - Concrete implementations are in `infrastructure/persistence/supabase/implementations/`
  - Domain repositories only contain interfaces
  - Implementations properly map between entities and database rows

  ## Step 4: Update Dependency Injection

  **Actions:**
  1. Register concrete implementations in DI container:
  ```python
  # application/dependencies.py
  from infrastructure.persistence.supabase.implementations.user_repository_impl import UserRepositoryImpl
  from infrastructure.persistence.supabase.implementations.role_repository_impl import RoleRepositoryImpl
  from domains.authentication.repositories.interfaces import IUserRepository, IRoleRepository
  
  def register_repositories(container):
      # Register repository implementations
      container.register(
          IUserRepository,
          UserRepositoryImpl,
          scope='singleton'
      )
      container.register(
          IRoleRepository,
          RoleRepositoryImpl,
          scope='singleton'
      )
  ```

  2. Update use cases to use repository interfaces:
  ```python
  # domains/authentication/use_cases/authenticate_user.py
  from domains.authentication.repositories.interfaces import IUserRepository
  
  class AuthenticateUserUseCase:
      def __init__(self, user_repository: IUserRepository):
          self.user_repository = user_repository  # Interface, not concrete
      
      async def execute(self, email: str, password: str):
          user = await self.user_repository.find_by_email(email)
          # ... rest of implementation
  ```

  **Verification:**
  - DI container registers interfaces with concrete implementations
  - Use cases depend on interfaces, not concrete classes
  - Application can be tested with mock repositories

  ## Step 5: Implement Unit of Work Pattern

  **Actions:**
  1. Create unit of work pattern:
  ```python
  # core/patterns/unit_of_work.py
  from abc import ABC, abstractmethod
  from typing import TypeVar, Generic
  
  T = TypeVar('T')
  
  class IUnitOfWork(ABC):
      """Unit of Work pattern for transactional consistency"""
      
      @abstractmethod
      async def __aenter__(self):
          """Begin transaction"""
          pass
      
      @abstractmethod
      async def __aexit__(self, exc_type, exc_val, exc_tb):
          """End transaction (commit or rollback)"""
          pass
      
      @abstractmethod
      async def commit(self):
          """Commit the transaction"""
          pass
      
      @abstractmethod
      async def rollback(self):
          """Rollback the transaction"""
          pass
  ```

  2. Create domain-specific unit of work:
  ```python
  # domains/authentication/repositories/unit_of_work.py
  from core.patterns.unit_of_work import IUnitOfWork
  from domains.authentication.repositories.interfaces import IUserRepository, IRoleRepository
  
  class AuthenticationUnitOfWork(IUnitOfWork):
      def __init__(self, user_repository: IUserRepository, role_repository: IRoleRepository):
          self.users = user_repository
          self.roles = role_repository
          self._committed = False
      
      async def __aenter__(self):
          # Start transaction if supported by database
          return self
      
      async def __aexit__(self, exc_type, exc_val, exc_tb):
          if exc_type:
              await self.rollback()
          elif not self._committed:
              await self.commit()
      
      async def commit(self):
          # Commit changes and publish domain events
          self._committed = True
      
      async def rollback(self):
          # Rollback changes
          pass
  ```

  3. Update use cases to use unit of work:
  ```python
  # domains/authentication/use_cases/register_user.py
  from domains.authentication.repositories.unit_of_work import AuthenticationUnitOfWork
  
  class RegisterUserUseCase:
      def __init__(self, uow: AuthenticationUnitOfWork):
          self.uow = uow
      
      async def execute(self, request: SignupRequest):
          async with self.uow:
              # Check if user exists
              existing = await self.uow.users.find_by_email(request.email)
              if existing:
                  raise UserAlreadyExistsError()
              
              # Create new user
              user = User(
                  email=request.email,
                  full_name=request.full_name,
                  password_hash=hash_password(request.password)
              )
              
              # Save user
              saved_user = await self.uow.users.save(user)
              
              # Transaction commits automatically on context exit
              return UserMapper.to_response(saved_user)
  ```

  **Verification:**
  - Unit of work pattern is implemented
  - Use cases use unit of work for transactional consistency
  - Domain events are published on commit

  ## Step 6: Remove Direct Database Access

  **Actions:**
  1. Audit all use cases for direct database access:
  ```bash
  # Search for direct Supabase usage
  grep -r "supabase" domains/ --include="*.py" | grep -v "test"
  # Should return no results
  ```

  2. Replace any remaining direct access with repository calls:
  ```python
  # Before (direct access):
  result = await self.supabase.table('users').select('*').execute()
  
  # After (repository pattern):
  users = await self.user_repository.find_all()
  ```

  3. Update tests to use mock repositories:
  ```python
  # tests/mocks/repositories.py
  from domains.authentication.repositories.interfaces import IUserRepository
  from domains.authentication.models.user import User
  from typing import Optional, List, Dict, Any
  
  class MockUserRepository(IUserRepository):
      def __init__(self):
          self.users: Dict[str, User] = {}
      
      async def find_by_id(self, id: str) -> Optional[User]:
          return self.users.get(id)
      
      async def save(self, entity: User) -> User:
          if not entity.id:
              entity.id = str(uuid.uuid4())
          self.users[entity.id] = entity
          return entity
  ```

  **Verification:**
  - No direct database access in domain code
  - All data access goes through repositories
  - Tests use mock repositories instead of real database

  Week 2: Clean Architecture Implementation

  Day 6-7: Implement Use Case Layer

  ## Goal
  Standardize all business operations into a consistent use case pattern with clear inputs, outputs, and error handling.

  ## Current State Before This Step
  - ✅ Use cases exist in domains/*/use_cases/
  - ✅ Repository pattern implemented
  - ❌ No base use case pattern
  - ❌ Use cases may have inconsistent interfaces
  - ❌ Business logic may still exist in views
  - ❌ DTOs created but not fully integrated with use cases

  ## Step 1: Create Base Use Case Pattern

  **Actions:**
  1. Create base use case class:
  ```python
  # core/patterns/use_case.py
  from abc import ABC, abstractmethod
  from typing import TypeVar, Generic, Optional
  from pydantic import BaseModel
  
  TRequest = TypeVar('TRequest', bound=BaseModel)
  TResponse = TypeVar('TResponse', bound=BaseModel)
  
  class UseCase(ABC, Generic[TRequest, TResponse]):
      """Base use case following command pattern"""
      
      @abstractmethod
      async def execute(self, request: TRequest) -> TResponse:
          """Execute the use case with given request"""
          pass
      
      async def __call__(self, request: TRequest) -> TResponse:
          """Allow use case to be called as function"""
          return await self.execute(request)
  
  class NoRequestUseCase(ABC, Generic[TResponse]):
      """Use case that doesn't require input"""
      
      @abstractmethod
      async def execute(self) -> TResponse:
          pass
  ```

  2. Create result pattern for error handling:
  ```python
  # core/patterns/result.py
  from typing import TypeVar, Generic, Union, Optional
  from dataclasses import dataclass
  
  T = TypeVar('T')
  E = TypeVar('E')
  
  @dataclass
  class Success(Generic[T]):
      value: T
  
  @dataclass
  class Failure(Generic[E]):
      error: E
  
  Result = Union[Success[T], Failure[E]]
  
  def is_success(result: Result) -> bool:
      return isinstance(result, Success)
  ```

  **Verification:**
  - Base use case pattern exists in `core/patterns/use_case.py`
  - Result pattern exists for error handling
  - Type hints enable IDE support

  ## Step 2: Standardize All Use Cases

  **Actions:**
  1. Update authentication use cases to follow pattern:
  ```python
  # domains/authentication/use_cases/authenticate_user.py
  from core.patterns.use_case import UseCase
  from domains.authentication.dto.requests import LoginRequest
  from domains.authentication.dto.responses import TokenResponse
  from domains.authentication.repositories.interfaces import IUserRepository
  from application.exceptions.domain_exceptions import InvalidCredentialsError
  
  class AuthenticateUserUseCase(UseCase[LoginRequest, TokenResponse]):
      def __init__(self, 
                   user_repository: IUserRepository,
                   token_service: ITokenService):
          self.user_repository = user_repository
          self.token_service = token_service
      
      async def execute(self, request: LoginRequest) -> TokenResponse:
          # Find user
          user = await self.user_repository.find_by_email(request.email)
          if not user:
              raise InvalidCredentialsError("Invalid email or password")
          
          # Verify password
          if not verify_password(request.password, user.password_hash):
              raise InvalidCredentialsError("Invalid email or password")
          
          # Generate tokens
          access_token = await self.token_service.create_access_token(user)
          refresh_token = await self.token_service.create_refresh_token(user)
          
          return TokenResponse(
              access_token=access_token,
              refresh_token=refresh_token,
              expires_in=3600
          )
  ```

  2. Update onboarding use cases:
  ```python
  # domains/onboarding/use_cases/start_onboarding_session.py
  from core.patterns.use_case import UseCase
  from domains.onboarding.dto.requests import StartOnboardingRequest
  from domains.onboarding.dto.responses import OnboardingSessionResponse
  from domains.onboarding.repositories.interfaces import ISessionRepository
  from domains.onboarding.models.onboarding_session import OnboardingSession
  
  class StartOnboardingSessionUseCase(UseCase[StartOnboardingRequest, OnboardingSessionResponse]):
      def __init__(self, session_repository: ISessionRepository):
          self.session_repository = session_repository
      
      async def execute(self, request: StartOnboardingRequest) -> OnboardingSessionResponse:
          # Check for existing session
          existing = await self.session_repository.find_active_by_user_id(request.user_id)
          if existing:
              return OnboardingSessionMapper.to_response(existing)
          
          # Create new session
          session = OnboardingSession(
              user_id=request.user_id,
              status='in_progress',
              current_step='language_selection'
          )
          
          # Save session
          saved_session = await self.session_repository.save(session)
          
          return OnboardingSessionMapper.to_response(saved_session)
  ```

  **Verification:**
  - All use cases inherit from `UseCase` base class
  - Each use case has defined request and response DTOs
  - Business logic is encapsulated in execute method

  ## Step 3: Create Use Case Factories

  **Actions:**
  1. Create use case factory for each domain:
  ```python
  # domains/authentication/use_cases/factory.py
  from dependency_injector import containers, providers
  from domains.authentication.use_cases.authenticate_user import AuthenticateUserUseCase
  from domains.authentication.use_cases.register_user import RegisterUserUseCase
  
  class AuthenticationUseCaseContainer(containers.DeclarativeContainer):
      # Dependencies
      user_repository = providers.Dependency()
      role_repository = providers.Dependency()
      token_service = providers.Dependency()
      
      # Use cases
      authenticate_user = providers.Factory(
          AuthenticateUserUseCase,
          user_repository=user_repository,
          token_service=token_service
      )
      
      register_user = providers.Factory(
          RegisterUserUseCase,
          user_repository=user_repository,
          role_repository=role_repository
      )
  ```

  2. Register use case containers in main container:
  ```python
  # application/container.py
  from domains.authentication.use_cases.factory import AuthenticationUseCaseContainer
  from domains.onboarding.use_cases.factory import OnboardingUseCaseContainer
  
  class ApplicationContainer(containers.DeclarativeContainer):
      # ... existing configuration ...
      
      # Use case containers
      auth_use_cases = providers.Container(
          AuthenticationUseCaseContainer,
          user_repository=repositories.user_repository,
          token_service=services.token_service
      )
  ```

  **Verification:**
  - Use case factories exist for each domain
  - Dependencies are properly injected
  - Use cases can be easily retrieved from container

  ## Step 4: Refactor Views to Use Use Cases

  **Actions:**
  1. Update views to be thin controllers:
  ```python
  # domains/authentication/api/v1/views.py
  from rest_framework.views import APIView
  from rest_framework.response import Response
  from rest_framework import status
  from domains.authentication.dto.requests import LoginRequest
  from domains.authentication.use_cases.authenticate_user import AuthenticateUserUseCase
  from application.container import container
  
  class LoginView(APIView):
      def __init__(self, **kwargs):
          super().__init__(**kwargs)
          self.authenticate_user = container.auth_use_cases.authenticate_user()
      
      async def post(self, request):
          # Parse request
          login_request = LoginRequest(**request.data)
          
          try:
              # Execute use case
              response = await self.authenticate_user.execute(login_request)
              
              # Return response
              return Response(
                  response.dict(),
                  status=status.HTTP_200_OK
              )
          except InvalidCredentialsError as e:
              return Response(
                  {"error": str(e)},
                  status=status.HTTP_401_UNAUTHORIZED
              )
          except ValidationError as e:
              return Response(
                  {"errors": e.errors()},
                  status=status.HTTP_400_BAD_REQUEST
              )
  ```

  2. Create view base class for common functionality:
  ```python
  # api/common/base_views.py
  from rest_framework.views import APIView
  from rest_framework.response import Response
  from rest_framework import status
  from pydantic import ValidationError
  from application.exceptions.domain_exceptions import DomainException
  
  class BaseAPIView(APIView):
      """Base view with common error handling"""
      
      async def handle_use_case(self, use_case, request_data=None):
          """Execute use case with standard error handling"""
          try:
              if request_data is not None:
                  response = await use_case.execute(request_data)
              else:
                  response = await use_case.execute()
              
              return Response(
                  response.dict(),
                  status=status.HTTP_200_OK
              )
          except ValidationError as e:
              return Response(
                  {"errors": e.errors()},
                  status=status.HTTP_400_BAD_REQUEST
              )
          except DomainException as e:
              return Response(
                  {"error": str(e)},
                  status=e.status_code
              )
  ```

  **Verification:**
  - Views contain no business logic
  - All business logic is in use cases
  - Views handle HTTP concerns only

  ## Step 5: Add Use Case Documentation

  **Actions:**
  1. Create use case documentation template:
  ```python
  # domains/authentication/use_cases/authenticate_user.py
  class AuthenticateUserUseCase(UseCase[LoginRequest, TokenResponse]):
      """
      Authenticates a user with email and password.
      
      Flow:
      1. Find user by email
      2. Verify password matches
      3. Generate access and refresh tokens
      4. Return token response
      
      Errors:
      - InvalidCredentialsError: Email or password is incorrect
      - UserDisabledError: User account is disabled
      
      Dependencies:
      - IUserRepository: To find user by email
      - ITokenService: To generate JWT tokens
      """
  ```

  2. Generate use case documentation:
  ```python
  # scripts/generators/generate_use_case_docs.py
  import inspect
  from pathlib import Path
  
  def generate_use_case_documentation():
      """Generate markdown documentation for all use cases"""
      use_cases = []
      
      # Find all use case classes
      for domain_path in Path('domains').iterdir():
          if domain_path.is_dir():
              use_case_path = domain_path / 'use_cases'
              if use_case_path.exists():
                  for file in use_case_path.glob('*.py'):
                      # Extract use case info
                      pass
      
      # Generate markdown
      with open('docs/use_cases.md', 'w') as f:
          f.write("# Use Cases\n\n")
          for use_case in use_cases:
              f.write(f"## {use_case.name}\n")
              f.write(f"{use_case.docstring}\n\n")
  ```

  **Verification:**
  - All use cases have comprehensive docstrings
  - Documentation is generated automatically
  - Use case flows are clearly documented

  Day 8-9: Standardize Service Layer

  ## Goal
  Create a consistent service layer with clear interfaces, proper error handling, and resilience patterns for all external integrations.

  ## Current State Before This Step
  - ✅ Service interfaces exist in domains/*/services/interfaces.py
  - ✅ Some external service clients exist
  - ❌ Service implementations mixed with interfaces
  - ❌ No consistent error handling
  - ❌ No resilience patterns (retry, circuit breaker)
  - ❌ No mock implementations for testing

  ## Step 1: Define Clear Service Contracts

  **Actions:**
  1. Update authentication service interfaces:
  ```python
  # domains/authentication/services/interfaces.py
  from abc import ABC, abstractmethod
  from typing import Optional, Dict, Any
  from datetime import datetime
  
  class IAuthenticationService(ABC):
      """External authentication service interface"""
      
      @abstractmethod
      async def create_user(self, email: str, password: str, metadata: Dict[str, Any]) -> str:
          """Create user in external auth system, return auth_id"""
          pass
      
      @abstractmethod
      async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
          """Verify JWT token and return claims"""
          pass
      
      @abstractmethod
      async def revoke_token(self, token: str) -> bool:
          """Revoke a token"""
          pass
  
  class ITokenService(ABC):
      """JWT token generation service"""
      
      @abstractmethod
      async def create_access_token(self, user_id: str, claims: Dict[str, Any]) -> str:
          """Create access token"""
          pass
      
      @abstractmethod
      async def create_refresh_token(self, user_id: str) -> str:
          """Create refresh token"""
          pass
  ```

  2. Create AI service interfaces:
  ```python
  # domains/onboarding/services/interfaces.py
  from abc import ABC, abstractmethod
  from typing import List, Dict, Any
  
  class IEmbeddingService(ABC):
      """Text embedding service for semantic search"""
      
      @abstractmethod
      async def create_embedding(self, text: str) -> List[float]:
          """Create embedding vector for text"""
          pass
      
      @abstractmethod
      async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
          """Create embeddings for multiple texts"""
          pass
  
  class ICompletionService(ABC):
      """LLM completion service"""
      
      @abstractmethod
      async def complete(self, prompt: str, max_tokens: int = 100) -> str:
          """Generate completion for prompt"""
          pass
      
      @abstractmethod
      async def complete_with_system(self, system: str, user: str, max_tokens: int = 100) -> str:
          """Generate completion with system message"""
          pass
  ```

  **Verification:**
  - Service interfaces are abstract and technology-agnostic
  - Methods have clear input/output types
  - Interfaces focus on business capabilities

  ## Step 2: Implement Service Clients

  **Actions:**
  1. Create Auth0 service implementation:
  ```python
  # infrastructure/external_services/auth0/auth0_service_impl.py
  from domains.authentication.services.interfaces import IAuthenticationService
  from infrastructure.external_services.auth0.client import Auth0Client
  from application.decorators.retry import retry
  from application.decorators.circuit_breaker import circuit_breaker
  from typing import Optional, Dict, Any
  import logging
  
  logger = logging.getLogger(__name__)
  
  class Auth0ServiceImpl(IAuthenticationService):
      def __init__(self, client: Auth0Client):
          self.client = client
      
      @retry(max_attempts=3, backoff_seconds=1)
      @circuit_breaker(failure_threshold=5, recovery_timeout=60)
      async def create_user(self, email: str, password: str, metadata: Dict[str, Any]) -> str:
          try:
              response = await self.client.users.create({
                  "email": email,
                  "password": password,
                  "connection": "Username-Password-Authentication",
                  "user_metadata": metadata
              })
              return response['user_id']
          except Exception as e:
              logger.error(f"Failed to create Auth0 user: {e}")
              raise InfrastructureException(f"Authentication service error: {str(e)}")
      
      async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
          try:
              claims = await self.client.verify_token(token)
              return claims
          except Exception as e:
              logger.error(f"Token verification failed: {e}")
              return None
  ```

  2. Create OpenAI service implementation:
  ```python
  # infrastructure/external_services/openai/openai_service_impl.py
  from domains.onboarding.services.interfaces import IEmbeddingService, ICompletionService
  from infrastructure.external_services.openai.client import OpenAIClient
  from application.decorators.retry import retry
  from application.exceptions.infrastructure_exceptions import ExternalServiceException
  from typing import List
  
  class OpenAIServiceImpl(IEmbeddingService, ICompletionService):
      def __init__(self, client: OpenAIClient):
          self.client = client
      
      @retry(max_attempts=3, backoff_seconds=2)
      async def create_embedding(self, text: str) -> List[float]:
          try:
              response = await self.client.embeddings.create(
                  model="text-embedding-ada-002",
                  input=text
              )
              return response.data[0].embedding
          except Exception as e:
              raise ExternalServiceException(f"Embedding creation failed: {str(e)}")
      
      @retry(max_attempts=3, backoff_seconds=2)
      async def complete(self, prompt: str, max_tokens: int = 100) -> str:
          try:
              response = await self.client.chat.completions.create(
                  model="gpt-4",
                  messages=[{"role": "user", "content": prompt}],
                  max_tokens=max_tokens
              )
              return response.choices[0].message.content
          except Exception as e:
              raise ExternalServiceException(f"Completion failed: {str(e)}")
  ```

  **Verification:**
  - Service implementations are in infrastructure layer
  - All external calls have retry logic
  - Errors are properly wrapped and logged

  ## Step 3: Implement Resilience Patterns

  **Actions:**
  1. Create retry decorator:
  ```python
  # application/decorators/retry.py
  import asyncio
  import functools
  from typing import TypeVar, Callable, Any
  import logging
  
  logger = logging.getLogger(__name__)
  T = TypeVar('T')
  
  def retry(max_attempts: int = 3, backoff_seconds: float = 1.0, exponential: bool = True):
      """Retry decorator with exponential backoff"""
      def decorator(func: Callable[..., T]) -> Callable[..., T]:
          @functools.wraps(func)
          async def wrapper(*args, **kwargs) -> T:
              last_exception = None
              
              for attempt in range(max_attempts):
                  try:
                      return await func(*args, **kwargs)
                  except Exception as e:
                      last_exception = e
                      if attempt < max_attempts - 1:
                          wait_time = backoff_seconds * (2 ** attempt if exponential else 1)
                          logger.warning(
                              f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                              f"Retrying in {wait_time}s..."
                          )
                          await asyncio.sleep(wait_time)
                      else:
                          logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
              
              raise last_exception
          
          return wrapper
      return decorator
  ```

  2. Create circuit breaker decorator:
  ```python
  # application/decorators/circuit_breaker.py
  import asyncio
  import functools
  from datetime import datetime, timedelta
  from typing import TypeVar, Callable, Any
  from enum import Enum
  
  class CircuitState(Enum):
      CLOSED = "closed"
      OPEN = "open"
      HALF_OPEN = "half_open"
  
  class CircuitBreaker:
      def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
          self.failure_threshold = failure_threshold
          self.recovery_timeout = recovery_timeout
          self.failure_count = 0
          self.last_failure_time = None
          self.state = CircuitState.CLOSED
      
      async def call(self, func, *args, **kwargs):
          if self.state == CircuitState.OPEN:
              if self._should_attempt_reset():
                  self.state = CircuitState.HALF_OPEN
              else:
                  raise Exception("Circuit breaker is OPEN")
          
          try:
              result = await func(*args, **kwargs)
              self._on_success()
              return result
          except Exception as e:
              self._on_failure()
              raise e
      
      def _should_attempt_reset(self) -> bool:
          return (
              self.last_failure_time and
              datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)
          )
      
      def _on_success(self):
          self.failure_count = 0
          self.state = CircuitState.CLOSED
      
      def _on_failure(self):
          self.failure_count += 1
          self.last_failure_time = datetime.now()
          
          if self.failure_count >= self.failure_threshold:
              self.state = CircuitState.OPEN
  
  def circuit_breaker(failure_threshold: int = 5, recovery_timeout: int = 60):
      breaker = CircuitBreaker(failure_threshold, recovery_timeout)
      
      def decorator(func):
          @functools.wraps(func)
          async def wrapper(*args, **kwargs):
              return await breaker.call(func, *args, **kwargs)
          return wrapper
      
      return decorator
  ```

  **Verification:**
  - Retry decorator implements exponential backoff
  - Circuit breaker prevents cascading failures
  - Both decorators are async-compatible

  ## Step 4: Create Mock Services for Testing

  **Actions:**
  1. Create mock service implementations:
  ```python
  # tests/mocks/services.py
  from domains.authentication.services.interfaces import IAuthenticationService, ITokenService
  from domains.onboarding.services.interfaces import IEmbeddingService, ICompletionService
  from typing import Optional, Dict, Any, List
  import uuid
  import jwt
  
  class MockAuthenticationService(IAuthenticationService):
      def __init__(self):
          self.users = {}
      
      async def create_user(self, email: str, password: str, metadata: Dict[str, Any]) -> str:
          auth_id = f"auth0|{uuid.uuid4()}"
          self.users[auth_id] = {
              "email": email,
              "metadata": metadata
          }
          return auth_id
      
      async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
          try:
              # Simple decode for testing
              return jwt.decode(token, "test-secret", algorithms=["HS256"])
          except:
              return None
  
  class MockEmbeddingService(IEmbeddingService):
      async def create_embedding(self, text: str) -> List[float]:
          # Return deterministic embedding based on text length
          return [0.1 * i for i in range(1536)]  # Simulate OpenAI embedding size
      
      async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
          return [await self.create_embedding(text) for text in texts]
  
  class MockCompletionService(ICompletionService):
      async def complete(self, prompt: str, max_tokens: int = 100) -> str:
          # Return predictable response for testing
          return f"Mock response to: {prompt[:50]}..."
  ```

  2. Create service factory for tests:
  ```python
  # tests/fixtures/services.py
  from tests.mocks.services import (
      MockAuthenticationService,
      MockEmbeddingService,
      MockCompletionService
  )
  
  def create_test_services():
      """Create mock services for testing"""
      return {
          'auth_service': MockAuthenticationService(),
          'embedding_service': MockEmbeddingService(),
          'completion_service': MockCompletionService()
      }
  ```

  **Verification:**
  - Mock services implement all interface methods
  - Mocks provide predictable responses
  - Tests can run without external dependencies

  ## Step 5: Standardize Error Handling

  **Actions:**
  1. Create exception hierarchy:
  ```python
  # application/exceptions/base_exceptions.py
  class ApplicationException(Exception):
      """Base exception for all application errors"""
      def __init__(self, message: str, code: str = None):
          super().__init__(message)
          self.code = code
  
  # application/exceptions/domain_exceptions.py
  from application.exceptions.base_exceptions import ApplicationException
  
  class DomainException(ApplicationException):
      """Base for all domain exceptions"""
      status_code = 400
  
  class EntityNotFoundException(DomainException):
      """Entity not found in repository"""
      status_code = 404
  
  class InvalidCredentialsError(DomainException):
      """Invalid authentication credentials"""
      status_code = 401
  
  class BusinessRuleViolationError(DomainException):
      """Business rule violated"""
      status_code = 422
  
  # application/exceptions/infrastructure_exceptions.py
  from application.exceptions.base_exceptions import ApplicationException
  
  class InfrastructureException(ApplicationException):
      """Base for all infrastructure exceptions"""
      status_code = 503
  
  class ExternalServiceException(InfrastructureException):
      """External service call failed"""
      pass
  
  class DatabaseException(InfrastructureException):
      """Database operation failed"""
      pass
  ```

  2. Update services to use standard exceptions:
  ```python
  # Update all service implementations
  # Replace generic exceptions with specific ones:
  # - raise Exception(...) -> raise ExternalServiceException(...)
  # - raise ValueError(...) -> raise ValidationException(...)
  ```

  **Verification:**
  - All exceptions inherit from base classes
  - Each exception has appropriate HTTP status code
  - Services throw meaningful exceptions

  Day 10: Create Shared Patterns Library

  ## Goal
  Establish a comprehensive library of reusable patterns, decorators, and utilities that enforce consistency across the codebase.

  ## Current State Before This Step
  - ✅ Repository and use case patterns created
  - ✅ Some decorators implemented (retry, circuit_breaker)
  - ❌ Patterns scattered across different modules
  - ❌ No centralized pattern library
  - ❌ Missing common decorators (cache, validate, audit)
  - ❌ No pattern usage guidelines

  ## Step 1: Consolidate Core Patterns

  **Actions:**
  1. Ensure all pattern files exist:
  ```bash
  # Already created:
  # - core/patterns/repository.py
  # - core/patterns/use_case.py
  # - core/patterns/unit_of_work.py
  # - core/patterns/specification.py
  # - core/patterns/result.py
  
  # Create additional patterns:
  touch core/patterns/value_object.py
  touch core/patterns/domain_event.py
  touch core/patterns/saga.py
  ```

  2. Create value object pattern:
  ```python
  # core/patterns/value_object.py
  from abc import ABC
  from typing import Any
  from dataclasses import dataclass
  
  @dataclass(frozen=True)
  class ValueObject(ABC):
      """Base class for value objects - immutable domain objects"""
      
      def __post_init__(self):
          """Validate after initialization"""
          self._validate()
      
      def _validate(self):
          """Override to add validation logic"""
          pass
      
      def equals(self, other: Any) -> bool:
          """Value equality comparison"""
          if not isinstance(other, self.__class__):
              return False
          return self.__dict__ == other.__dict__
  ```

  3. Create saga pattern for distributed transactions:
  ```python
  # core/patterns/saga.py
  from abc import ABC, abstractmethod
  from typing import List, Dict, Any
  from dataclasses import dataclass
  
  @dataclass
  class SagaStep:
      name: str
      action: callable
      compensation: callable
  
  class Saga(ABC):
      """Saga pattern for distributed transactions"""
      
      def __init__(self):
          self.steps: List[SagaStep] = []
          self.executed_steps: List[SagaStep] = []
      
      @abstractmethod
      def define_steps(self) -> List[SagaStep]:
          """Define saga steps"""
          pass
      
      async def execute(self, context: Dict[str, Any]):
          """Execute saga with automatic compensation on failure"""
          self.steps = self.define_steps()
          
          try:
              for step in self.steps:
                  result = await step.action(context)
                  context[f"{step.name}_result"] = result
                  self.executed_steps.append(step)
          except Exception as e:
              # Compensate in reverse order
              for step in reversed(self.executed_steps):
                  try:
                      await step.compensation(context)
                  except Exception as comp_error:
                      # Log compensation failure
                      pass
              raise e
  ```

  **Verification:**
  - All core patterns are in `core/patterns/`
  - Patterns are well-documented with docstrings
  - Patterns are generic and reusable

  ## Step 2: Create Comprehensive Decorator Library

  **Actions:**
  1. Create cache decorator:
  ```python
  # application/decorators/cache.py
  import functools
  import hashlib
  import json
  from typing import TypeVar, Callable, Any, Optional
  from datetime import timedelta
  from infrastructure.persistence.cache.redis_client import get_redis_client
  
  T = TypeVar('T')
  
  def cache(key_prefix: str, ttl: timedelta = timedelta(minutes=5)):
      """Cache decorator with Redis backend"""
      def decorator(func: Callable[..., T]) -> Callable[..., T]:
          @functools.wraps(func)
          async def wrapper(*args, **kwargs) -> T:
              # Generate cache key
              cache_key = _generate_cache_key(key_prefix, func.__name__, args, kwargs)
              
              # Try to get from cache
              redis = get_redis_client()
              cached_value = await redis.get(cache_key)
              
              if cached_value:
                  return json.loads(cached_value)
              
              # Execute function
              result = await func(*args, **kwargs)
              
              # Store in cache
              await redis.setex(
                  cache_key,
                  int(ttl.total_seconds()),
                  json.dumps(result, default=str)
              )
              
              return result
          
          return wrapper
      return decorator
  
  def invalidate_cache(key_pattern: str):
      """Invalidate cache entries matching pattern"""
      async def _invalidate():
          redis = get_redis_client()
          keys = await redis.keys(key_pattern)
          if keys:
              await redis.delete(*keys)
      return _invalidate
  ```

  2. Create validation decorator:
  ```python
  # application/decorators/validate.py
  import functools
  from typing import TypeVar, Callable, Type
  from pydantic import BaseModel, ValidationError
  from application.exceptions.domain_exceptions import ValidationException
  
  T = TypeVar('T')
  
  def validate_input(model: Type[BaseModel]):
      """Validate function input using Pydantic model"""
      def decorator(func: Callable[..., T]) -> Callable[..., T]:
          @functools.wraps(func)
          async def wrapper(*args, **kwargs) -> T:
              try:
                  # Validate kwargs against model
                  validated_data = model(**kwargs)
                  return await func(*args, **validated_data.dict())
              except ValidationError as e:
                  raise ValidationException(str(e))
          
          return wrapper
      return decorator
  
  def validate_output(model: Type[BaseModel]):
      """Validate function output using Pydantic model"""
      def decorator(func: Callable[..., T]) -> Callable[..., T]:
          @functools.wraps(func)
          async def wrapper(*args, **kwargs) -> T:
              result = await func(*args, **kwargs)
              
              try:
                  # Validate output
                  validated = model(**result) if isinstance(result, dict) else model.from_orm(result)
                  return validated
              except ValidationError as e:
                  raise ValidationException(f"Output validation failed: {str(e)}")
          
          return wrapper
      return decorator
  ```

  3. Create audit decorator:
  ```python
  # application/decorators/audit.py
  import functools
  from typing import TypeVar, Callable
  from datetime import datetime
  import json
  from application.context import get_current_user
  
  T = TypeVar('T')
  
  def audit_log(action: str, resource_type: str):
      """Audit log decorator for tracking user actions"""
      def decorator(func: Callable[..., T]) -> Callable[..., T]:
          @functools.wraps(func)
          async def wrapper(*args, **kwargs) -> T:
              user = get_current_user()
              start_time = datetime.utcnow()
              
              audit_entry = {
                  "action": action,
                  "resource_type": resource_type,
                  "user_id": user.id if user else None,
                  "timestamp": start_time.isoformat(),
                  "function": func.__name__,
                  "arguments": _sanitize_args(args, kwargs)
              }
              
              try:
                  result = await func(*args, **kwargs)
                  audit_entry["status"] = "success"
                  audit_entry["duration_ms"] = (datetime.utcnow() - start_time).total_seconds() * 1000
                  
                  # Log successful action
                  await _save_audit_log(audit_entry)
                  
                  return result
              except Exception as e:
                  audit_entry["status"] = "failure"
                  audit_entry["error"] = str(e)
                  audit_entry["duration_ms"] = (datetime.utcnow() - start_time).total_seconds() * 1000
                  
                  # Log failed action
                  await _save_audit_log(audit_entry)
                  
                  raise
          
          return wrapper
      return decorator
  
  def _sanitize_args(args, kwargs):
      """Remove sensitive data from arguments"""
      sensitive_keys = ['password', 'token', 'secret', 'api_key']
      sanitized_kwargs = {}
      
      for key, value in kwargs.items():
          if any(sensitive in key.lower() for sensitive in sensitive_keys):
              sanitized_kwargs[key] = "***REDACTED***"
          else:
              sanitized_kwargs[key] = str(value)[:100]  # Truncate long values
      
      return sanitized_kwargs
  ```

  **Verification:**
  - All decorators are in `application/decorators/`
  - Decorators handle both sync and async functions
  - Error handling is comprehensive

  ## Step 3: Create Utility Functions

  **Actions:**
  1. Create validation utilities:
  ```python
  # core/utils/validation_utils.py
  import re
  from typing import Optional
  from email_validator import validate_email, EmailNotValidError
  
  def is_valid_email(email: str) -> bool:
      """Validate email format"""
      try:
          validate_email(email)
          return True
      except EmailNotValidError:
          return False
  
  def is_strong_password(password: str) -> tuple[bool, Optional[str]]:
      """Check password strength"""
      if len(password) < 8:
          return False, "Password must be at least 8 characters long"
      
      if not re.search(r"[A-Z]", password):
          return False, "Password must contain at least one uppercase letter"
      
      if not re.search(r"[a-z]", password):
          return False, "Password must contain at least one lowercase letter"
      
      if not re.search(r"\d", password):
          return False, "Password must contain at least one digit"
      
      if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
          return False, "Password must contain at least one special character"
      
      return True, None
  
  def sanitize_input(text: str, max_length: int = 1000) -> str:
      """Sanitize user input"""
      # Remove control characters
      text = ''.join(char for char in text if ord(char) >= 32)
      
      # Truncate to max length
      text = text[:max_length]
      
      # Remove multiple spaces
      text = ' '.join(text.split())
      
      return text.strip()
  ```

  2. Create datetime utilities:
  ```python
  # core/utils/datetime_utils.py
  from datetime import datetime, timedelta, timezone
  from typing import Optional
  
  def utc_now() -> datetime:
      """Get current UTC datetime"""
      return datetime.now(timezone.utc)
  
  def format_datetime(dt: datetime, format: str = "%Y-%m-%d %H:%M:%S") -> str:
      """Format datetime to string"""
      return dt.strftime(format)
  
  def parse_datetime(date_string: str, format: str = "%Y-%m-%d %H:%M:%S") -> datetime:
      """Parse string to datetime"""
      return datetime.strptime(date_string, format).replace(tzinfo=timezone.utc)
  
  def time_ago(dt: datetime) -> str:
      """Human-readable time ago"""
      now = utc_now()
      diff = now - dt
      
      if diff < timedelta(minutes=1):
          return "just now"
      elif diff < timedelta(hours=1):
          minutes = int(diff.total_seconds() / 60)
          return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
      elif diff < timedelta(days=1):
          hours = int(diff.total_seconds() / 3600)
          return f"{hours} hour{'s' if hours > 1 else ''} ago"
      elif diff < timedelta(days=30):
          days = diff.days
          return f"{days} day{'s' if days > 1 else ''} ago"
      else:
          return format_datetime(dt, "%Y-%m-%d")
  ```

  **Verification:**
  - Utilities are organized by functionality
  - Functions are pure and testable
  - Common operations are standardized

  ## Step 4: Update Code to Use Shared Patterns

  **Actions:**
  1. Update views to use decorators:
  ```python
  # domains/authentication/api/v1/views.py
  from api.common.base_views import BaseAPIView
  from application.decorators.validate import validate_input
  from application.decorators.audit import audit_log
  from application.decorators.cache import cache
  from domains.authentication.dto.requests import LoginRequest
  
  class LoginView(BaseAPIView):
      @validate_input(LoginRequest)
      @audit_log(action="user_login", resource_type="authentication")
      async def post(self, request, validated_data: dict):
          login_request = LoginRequest(**validated_data)
          return await self.handle_use_case(
              self.authenticate_user,
              login_request
          )
  
  class UserProfileView(BaseAPIView):
      @cache(key_prefix="user_profile", ttl=timedelta(minutes=15))
      async def get(self, request, user_id: str):
          return await self.handle_use_case(
              self.get_user_profile,
              user_id
          )
  ```

  2. Update value objects to use pattern:
  ```python
  # domains/shared/value_objects/email.py
  from core.patterns.value_object import ValueObject
  from core.utils.validation_utils import is_valid_email
  from dataclasses import dataclass
  
  @dataclass(frozen=True)
  class Email(ValueObject):
      value: str
      
      def _validate(self):
          if not is_valid_email(self.value):
              raise ValueError(f"Invalid email format: {self.value}")
      
      def domain(self) -> str:
          """Get email domain"""
          return self.value.split('@')[1]
      
      def __str__(self) -> str:
          return self.value
  ```

  **Verification:**
  - Decorators are applied consistently
  - Value objects use base pattern
  - Code is more concise and maintainable

  ## Step 5: Document Pattern Usage

  **Actions:**
  1. Create comprehensive pattern documentation:
  ```markdown
  # docs/architecture/patterns.md
  # Architecture Patterns Guide
  
  ## Overview
  This guide documents the architectural patterns used in the FluentPro backend.
  
  ## Core Patterns
  
  ### Repository Pattern
  **Purpose**: Encapsulate data access logic and provide a more object-oriented view of the persistence layer.
  
  **Usage**:
  ```python
  from core.patterns.repository import IRepository
  
  class IUserRepository(IRepository[User, str]):
      async def find_by_email(self, email: str) -> Optional[User]:
          pass
  ```
  
  **Benefits**:
  - Testability through mock implementations
  - Consistent data access interface
  - Separation of concerns
  
  ### Use Case Pattern
  **Purpose**: Encapsulate business logic in a reusable, testable unit.
  
  **Usage**:
  ```python
  from core.patterns.use_case import UseCase
  
  class AuthenticateUserUseCase(UseCase[LoginRequest, TokenResponse]):
      async def execute(self, request: LoginRequest) -> TokenResponse:
          # Business logic here
          pass
  ```
  
  ### Unit of Work Pattern
  **Purpose**: Maintain a list of objects affected by a business transaction and coordinate writing out changes.
  
  ### Value Object Pattern
  **Purpose**: Represent a descriptive aspect of the domain with no conceptual identity.
  
  ## Decorators
  
  ### @retry
  Automatically retry failed operations with exponential backoff.
  
  ### @circuit_breaker
  Prevent cascading failures in distributed systems.
  
  ### @cache
  Cache function results in Redis.
  
  ### @validate_input / @validate_output
  Validate function inputs and outputs using Pydantic models.
  
  ### @audit_log
  Track user actions for compliance and debugging.
  ```

  2. Create pattern examples:
  ```python
  # docs/examples/pattern_usage.py
  # Example: Using multiple patterns together
  
  from core.patterns.use_case import UseCase
  from application.decorators.validate import validate_input
  from application.decorators.audit import audit_log
  from application.decorators.cache import cache
  
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
          
          # Calculate stats
          stats = await self._calculate_stats(user)
          
          return UserStatsResponse(
              user_id=user.id,
              stats=stats
          )
  ```

  **Verification:**
  - Pattern documentation is comprehensive
  - Examples show real-world usage
  - Benefits and trade-offs are documented

  Week 3: Consistency & Documentation

  Day 11-12: Enforce Architectural Rules

  ## Goal
  Establish automated enforcement of architectural decisions and create tooling to maintain consistency as the codebase grows.

  ## Current State Before This Step
  - ✅ Clean architecture implemented
  - ✅ Patterns library created
  - ❌ No formal architectural documentation
  - ❌ No automated architecture validation
  - ❌ No code generation templates
  - ❌ Manual enforcement of patterns

  ## Step 1: Create Architecture Decision Records (ADRs)

  **Actions:**
  1. Create ADR directory structure:
  ```bash
  mkdir -p docs/architecture/decisions
  touch docs/architecture/decisions/README.md
  ```

  2. Create first ADR for Domain-Driven Design:
  ```markdown
  # docs/architecture/decisions/001-use-ddd.md
  # ADR-001: Use Domain-Driven Design
  
  ## Status
  Accepted
  
  ## Context
  The FluentPro backend needs to handle complex business logic around user authentication, onboarding flows, and AI-driven communication scenarios. The codebase was becoming difficult to maintain with business logic scattered across views, managers, and services.
  
  ## Decision
  We will adopt Domain-Driven Design (DDD) principles:
  - Organize code into domain modules (authentication, onboarding)
  - Use aggregate roots to enforce business invariants
  - Implement repositories for data access
  - Use domain events for cross-domain communication
  
  ## Consequences
  ### Positive
  - Clear separation of business logic from infrastructure
  - Better testability through dependency injection
  - Easier to understand and modify domain logic
  - Natural boundaries for microservice extraction
  
  ### Negative
  - Initial complexity in setup
  - Learning curve for developers new to DDD
  - More files and abstractions
  
  ## References
  - Domain-Driven Design by Eric Evans
  - Implementing Domain-Driven Design by Vaughn Vernon
  ```

  3. Create ADR for async-first architecture:
  ```markdown
  # docs/architecture/decisions/002-async-first.md
  # ADR-002: Async-First Architecture
  
  ## Status
  Accepted
  
  ## Context
  FluentPro will integrate with multiple AI services (OpenAI, Azure Cognitive Services) and needs to handle real-time communication features. These operations are I/O bound and can benefit from asynchronous processing.
  
  ## Decision
  We will adopt an async-first approach:
  - All views, use cases, and services will be async by default
  - Use Django's async views (Django 4.1+)
  - Implement Celery for background tasks
  - Use Redis for caching and message passing
  
  ## Consequences
  ### Positive
  - Better performance for I/O operations
  - Ability to handle WebSocket connections
  - Preparation for real-time features
  - Better resource utilization
  
  ### Negative
  - Complexity in debugging async code
  - Need for async-compatible libraries
  - Potential for race conditions
  ```

  **Verification:**
  - ADRs exist in `docs/architecture/decisions/`
  - Each ADR follows the standard template
  - Decisions are justified with context

  ## Step 2: Implement Import Restrictions

  **Actions:**
  1. Install and configure import-linter:
  ```toml
  # pyproject.toml
  [tool.poetry.dev-dependencies]
  import-linter = "^1.2.0"
  
  [tool.importlinter]
  root_package = "fluentpro_backend"
  
  [[tool.importlinter.contracts]]
  name = "Domain independence"
  type = "independence"
  modules = [
      "domains.authentication",
      "domains.onboarding",
  ]
  
  [[tool.importlinter.contracts]]
  name = "Layers respect boundaries"
  type = "layers"
  layers = [
      "api",
      "application",
      "domains",
      "infrastructure",
  ]
  
  [[tool.importlinter.contracts]]
  name = "Use cases cannot import from views"
  type = "forbidden"
  source_modules = [
      "domains.authentication.use_cases",
      "domains.onboarding.use_cases",
  ]
  forbidden_modules = [
      "api",
      "domains.authentication.api",
      "domains.onboarding.api",
  ]
  ```

  2. Create import validation script:
  ```python
  # scripts/validate_imports.py
  #!/usr/bin/env python
  import subprocess
  import sys
  
  def validate_imports():
      """Run import-linter to validate architecture"""
      result = subprocess.run(
          ["lint-imports"],
          capture_output=True,
          text=True
      )
      
      if result.returncode != 0:
          print("\u274c Import violations detected:")
          print(result.stdout)
          print(result.stderr)
          return False
      
      print("\u2705 All import rules passed")
      return True
  
  if __name__ == "__main__":
      if not validate_imports():
          sys.exit(1)
  ```

  **Verification:**
  - Run `lint-imports` and ensure it passes
  - Try violating a rule and verify it's caught
  - Import rules match architectural decisions

  ## Step 3: Create Code Generation Templates

  **Actions:**
  1. Create domain generator script:
  ```python
  # scripts/generators/create_domain.py
  #!/usr/bin/env python
  import os
  import sys
  from pathlib import Path
  from typing import Optional
  import click
  
  TEMPLATE_DIR = Path(__file__).parent / "templates"
  
  @click.command()
  @click.argument('domain_name')
  @click.option('--with-api', is_flag=True, help='Include API layer')
  def create_domain(domain_name: str, with_api: bool):
      """Create a new domain with standard structure"""
      domain_path = Path(f"domains/{domain_name}")
      
      if domain_path.exists():
          click.echo(f"\u274c Domain {domain_name} already exists")
          sys.exit(1)
      
      # Create directory structure
      directories = [
          "",
          "models",
          "repositories",
          "services",
          "use_cases",
          "dto",
          "events",
          "tasks",
      ]
      
      if with_api:
          directories.extend(["api", "api/v1"])
      
      for dir_name in directories:
          dir_path = domain_path / dir_name
          dir_path.mkdir(parents=True)
          
          # Create __init__.py
          (dir_path / "__init__.py").touch()
      
      # Create standard files from templates
      create_file_from_template(
          "domain_models.py.template",
          domain_path / "models" / "__init__.py",
          {"domain_name": domain_name}
      )
      
      create_file_from_template(
          "domain_interfaces.py.template",
          domain_path / "repositories" / "interfaces.py",
          {"domain_name": domain_name}
      )
      
      create_file_from_template(
          "domain_dto.py.template",
          domain_path / "dto" / "requests.py",
          {"domain_name": domain_name}
      )
      
      click.echo(f"\u2705 Created domain: {domain_name}")
      click.echo("\nNext steps:")
      click.echo("1. Define your domain models")
      click.echo("2. Create repository interfaces")
      click.echo("3. Implement use cases")
      click.echo("4. Add to application container")
  
  def create_file_from_template(template_name: str, target_path: Path, context: dict):
      """Create file from template with variable substitution"""
      template_path = TEMPLATE_DIR / template_name
      
      with open(template_path, 'r') as f:
          content = f.read()
      
      # Simple template substitution
      for key, value in context.items():
          content = content.replace(f"{{{{ {key} }}}}", value)
      
      with open(target_path, 'w') as f:
          f.write(content)
  
  if __name__ == "__main__":
      create_domain()
  ```

  2. Create template files:
  ```python
  # scripts/generators/templates/domain_models.py.template
  """{{ domain_name }} domain models"""
  from domains.shared.models.base_entity import BaseEntity
  from dataclasses import dataclass
  from typing import Optional
  
  @dataclass
  class {{ domain_name.title() }}(BaseEntity):
      """Main aggregate root for {{ domain_name }} domain"""
      # TODO: Add domain-specific fields
      pass
  ```

  ```python
  # scripts/generators/templates/domain_interfaces.py.template
  """{{ domain_name }} repository interfaces"""
  from abc import ABC, abstractmethod
  from core.patterns.repository import IRepository
  from typing import Optional
  
  # TODO: Import domain models
  
  class I{{ domain_name.title() }}Repository(IRepository[{{ domain_name.title() }}, str]):
      """Repository interface for {{ domain_name }} aggregate"""
      
      # TODO: Add domain-specific query methods
      pass
  ```

  **Verification:**
  - Run `python scripts/generators/create_domain.py test_domain`
  - Verify directory structure is created
  - Check that templates are properly substituted

  ## Step 4: Add Pre-commit Hooks

  **Actions:**
  1. Create pre-commit configuration:
  ```yaml
  # .pre-commit-config.yaml
  repos:
    # Python formatting
    - repo: https://github.com/psf/black
      rev: 23.1.0
      hooks:
        - id: black
          language_version: python3.10
    
    # Import sorting
    - repo: https://github.com/pycqa/isort
      rev: 5.12.0
      hooks:
        - id: isort
          args: ["--profile", "black"]
    
    # Linting
    - repo: https://github.com/pycqa/flake8
      rev: 6.0.0
      hooks:
        - id: flake8
          args: ["--max-line-length=100", "--extend-ignore=E203"]
    
    # Type checking
    - repo: https://github.com/pre-commit/mirrors-mypy
      rev: v1.0.0
      hooks:
        - id: mypy
          additional_dependencies: [types-all]
    
    # Security
    - repo: https://github.com/pycqa/bandit
      rev: 1.7.4
      hooks:
        - id: bandit
          args: ["-r", "domains/", "application/", "infrastructure/"]
    
    # Custom hooks
    - repo: local
      hooks:
        - id: validate-imports
          name: Validate import rules
          entry: python scripts/validate_imports.py
          language: system
          pass_filenames: false
        
        - id: check-domain-structure
          name: Check domain structure
          entry: python scripts/check_domain_structure.py
          language: system
          pass_filenames: false
  ```

  2. Create domain structure validator:
  ```python
  # scripts/check_domain_structure.py
  #!/usr/bin/env python
  import os
  from pathlib import Path
  import sys
  
  REQUIRED_SUBDIRS = [
      "models",
      "repositories",
      "services",
      "use_cases",
      "dto",
      "events",
      "tasks"
  ]
  
  def check_domain_structure():
      """Validate that all domains have required structure"""
      domains_path = Path("domains")
      errors = []
      
      for domain_dir in domains_path.iterdir():
          if domain_dir.is_dir() and domain_dir.name != "shared":
              for required_dir in REQUIRED_SUBDIRS:
                  dir_path = domain_dir / required_dir
                  if not dir_path.exists():
                      errors.append(f"Missing {required_dir} in {domain_dir.name}")
                  elif not (dir_path / "__init__.py").exists():
                      errors.append(f"Missing __init__.py in {domain_dir.name}/{required_dir}")
      
      if errors:
          print("\u274c Domain structure violations:")
          for error in errors:
              print(f"  - {error}")
          return False
      
      print("\u2705 All domains have correct structure")
      return True
  
  if __name__ == "__main__":
      if not check_domain_structure():
          sys.exit(1)
  ```

  **Verification:**
  - Run `pre-commit install`
  - Make a change and commit to test hooks
  - Verify all checks pass

  Day 13-14: Module Independence Verification

  ## Goal
  Ensure complete domain independence through testing, eliminate cross-domain dependencies, and implement proper communication patterns.

  ## Current State Before This Step
  - ✅ Domains are structurally separated
  - ✅ Import rules are defined
  - ❌ Domains may still have hidden dependencies
  - ❌ No event-driven communication
  - ❌ Domains cannot be tested in isolation
  - ❌ No clear module interfaces documented

  ## Step 1: Create Independent Test Structure

  **Actions:**
  1. Create domain-specific test directories:
  ```bash
  mkdir -p tests/unit/domains/authentication/{models,use_cases,services}
  mkdir -p tests/unit/domains/onboarding/{models,use_cases,services}
  mkdir -p tests/integration/domains/authentication
  mkdir -p tests/integration/domains/onboarding
  touch tests/unit/domains/__init__.py
  touch tests/unit/domains/authentication/__init__.py
  touch tests/unit/domains/onboarding/__init__.py
  ```

  2. Create domain-specific test configuration:
  ```python
  # tests/unit/domains/authentication/conftest.py
  import pytest
  from unittest.mock import Mock
  from domains.authentication.repositories.interfaces import IUserRepository, IRoleRepository
  from domains.authentication.services.interfaces import IAuthenticationService
  from tests.mocks.repositories import MockUserRepository, MockRoleRepository
  from tests.mocks.services import MockAuthenticationService
  
  @pytest.fixture
  def mock_user_repository():
      """Provide mock user repository for authentication domain tests"""
      return MockUserRepository()
  
  @pytest.fixture
  def mock_role_repository():
      """Provide mock role repository for authentication domain tests"""
      return MockRoleRepository()
  
  @pytest.fixture
  def mock_auth_service():
      """Provide mock authentication service"""
      return MockAuthenticationService()
  
  @pytest.fixture
  def authentication_container(mock_user_repository, mock_role_repository, mock_auth_service):
      """Provide complete authentication domain container"""
      from application.container import Container
      
      container = Container()
      container.repositories.user_repository.override(mock_user_repository)
      container.repositories.role_repository.override(mock_role_repository)
      container.services.auth_service.override(mock_auth_service)
      
      return container
  ```

  3. Create isolated domain tests:
  ```python
  # tests/unit/domains/authentication/test_use_cases.py
  import pytest
  from domains.authentication.use_cases.register_user import RegisterUserUseCase
  from domains.authentication.dto.requests import SignupRequest
  from domains.authentication.models.user import User
  
  class TestRegisterUserUseCase:
      @pytest.mark.asyncio
      async def test_register_new_user(self, mock_user_repository, mock_role_repository):
          # Arrange
          use_case = RegisterUserUseCase(
              user_repository=mock_user_repository,
              role_repository=mock_role_repository
          )
          
          request = SignupRequest(
              email="test@example.com",
              password="SecurePass123!",
              full_name="Test User"
          )
          
          # Act
          response = await use_case.execute(request)
          
          # Assert
          assert response.email == request.email
          assert response.full_name == request.full_name
          assert mock_user_repository.users  # User was saved
      
      @pytest.mark.asyncio
      async def test_cannot_register_duplicate_email(self, mock_user_repository, mock_role_repository):
          # Arrange
          existing_user = User(
              email="existing@example.com",
              full_name="Existing User",
              password_hash="hash"
          )
          await mock_user_repository.save(existing_user)
          
          use_case = RegisterUserUseCase(
              user_repository=mock_user_repository,
              role_repository=mock_role_repository
          )
          
          request = SignupRequest(
              email="existing@example.com",
              password="SecurePass123!",
              full_name="New User"
          )
          
          # Act & Assert
          with pytest.raises(UserAlreadyExistsError):
              await use_case.execute(request)
  ```

  **Verification:**
  - Each domain can be tested without importing from other domains
  - Tests use only mocks for external dependencies
  - Test fixtures are domain-specific

  ## Step 2: Audit and Remove Cross-Domain Imports

  **Actions:**
  1. Create import audit script:
  ```python
  # scripts/audit_cross_domain_imports.py
  #!/usr/bin/env python
  import ast
  import os
  from pathlib import Path
  from typing import Set, Dict, List
  
  class ImportAuditor(ast.NodeVisitor):
      def __init__(self, current_domain: str):
          self.current_domain = current_domain
          self.imports: Set[str] = set()
      
      def visit_Import(self, node):
          for alias in node.names:
              self.imports.add(alias.name)
      
      def visit_ImportFrom(self, node):
          if node.module:
              self.imports.add(node.module)
  
  def audit_domain_imports(domain_name: str) -> Dict[str, List[str]]:
      """Find all cross-domain imports in a domain"""
      violations = {}
      domain_path = Path(f"domains/{domain_name}")
      
      for py_file in domain_path.rglob("*.py"):
          with open(py_file, 'r') as f:
              tree = ast.parse(f.read())
          
          auditor = ImportAuditor(domain_name)
          auditor.visit(tree)
          
          # Check for cross-domain imports
          file_violations = []
          for import_name in auditor.imports:
              if import_name.startswith("domains.") and domain_name not in import_name:
                  if not import_name.startswith("domains.shared"):
                      file_violations.append(import_name)
          
          if file_violations:
              violations[str(py_file)] = file_violations
      
      return violations
  
  def main():
      print("Auditing cross-domain imports...\n")
      
      domains = [d.name for d in Path("domains").iterdir() if d.is_dir() and d.name != "shared"]
      
      all_violations = {}
      for domain in domains:
          violations = audit_domain_imports(domain)
          if violations:
              all_violations[domain] = violations
      
      if all_violations:
          print("\u274c Cross-domain import violations found:\n")
          for domain, files in all_violations.items():
              print(f"Domain: {domain}")
              for file, imports in files.items():
                  print(f"  {file}:")
                  for imp in imports:
                      print(f"    - {imp}")
          return False
      else:
          print("\u2705 No cross-domain imports found")
          return True
  
  if __name__ == "__main__":
      import sys
      if not main():
          sys.exit(1)
  ```

  2. Fix any cross-domain imports found:
  ```python
  # Instead of direct cross-domain imports:
  # from domains.authentication.models.user import User  # ❌ Bad
  
  # Use interfaces and events:
  # from domains.shared.events import UserCreatedEvent  # ✅ Good
  ```

  **Verification:**
  - Run audit script and ensure no violations
  - Each domain only imports from itself and shared
  - No circular dependencies exist

  ## Step 3: Implement Event Bus for Communication

  **Actions:**
  1. Create event bus implementation:
  ```python
  # infrastructure/messaging/event_bus.py
  from abc import ABC, abstractmethod
  from typing import Dict, List, Callable, Any, Type
  from dataclasses import dataclass
  import asyncio
  import logging
  from domains.shared.events.base_event import DomainEvent
  
  logger = logging.getLogger(__name__)
  
  EventHandler = Callable[[DomainEvent], asyncio.coroutine]
  
  class IEventBus(ABC):
      @abstractmethod
      async def publish(self, event: DomainEvent) -> None:
          """Publish an event to the bus"""
          pass
      
      @abstractmethod
      def subscribe(self, event_type: Type[DomainEvent], handler: EventHandler) -> None:
          """Subscribe to an event type"""
          pass
  
  class InMemoryEventBus(IEventBus):
      """In-memory event bus for development/testing"""
      
      def __init__(self):
          self._handlers: Dict[str, List[EventHandler]] = {}
      
      async def publish(self, event: DomainEvent) -> None:
          event_type = event.event_type
          handlers = self._handlers.get(event_type, [])
          
          if not handlers:
              logger.warning(f"No handlers registered for event type: {event_type}")
              return
          
          # Execute all handlers concurrently
          tasks = [handler(event) for handler in handlers]
          results = await asyncio.gather(*tasks, return_exceptions=True)
          
          # Log any handler errors
          for i, result in enumerate(results):
              if isinstance(result, Exception):
                  logger.error(f"Handler {handlers[i].__name__} failed: {result}")
      
      def subscribe(self, event_type: Type[DomainEvent], handler: EventHandler) -> None:
          event_type_str = event_type.__name__
          if event_type_str not in self._handlers:
              self._handlers[event_type_str] = []
          self._handlers[event_type_str].append(handler)
  
  class RedisEventBus(IEventBus):
      """Redis-based event bus for production"""
      
      def __init__(self, redis_client):
          self.redis = redis_client
          self._handlers: Dict[str, List[EventHandler]] = {}
          self._subscriber_task = None
      
      async def start(self):
          """Start listening for events"""
          self._subscriber_task = asyncio.create_task(self._listen_for_events())
      
      async def stop(self):
          """Stop listening for events"""
          if self._subscriber_task:
              self._subscriber_task.cancel()
      
      async def publish(self, event: DomainEvent) -> None:
          # Serialize event
          event_data = event.json()
          
          # Publish to Redis channel
          await self.redis.publish(f"events:{event.event_type}", event_data)
      
      def subscribe(self, event_type: Type[DomainEvent], handler: EventHandler) -> None:
          event_type_str = event_type.__name__
          if event_type_str not in self._handlers:
              self._handlers[event_type_str] = []
          self._handlers[event_type_str].append(handler)
      
      async def _listen_for_events(self):
          """Listen for events from Redis"""
          pubsub = self.redis.pubsub()
          
          # Subscribe to all event channels
          for event_type in self._handlers.keys():
              await pubsub.subscribe(f"events:{event_type}")
          
          async for message in pubsub.listen():
              if message['type'] == 'message':
                  await self._handle_message(message)
  ```

  2. Create event registration:
  ```python
  # infrastructure/messaging/event_registry.py
  from infrastructure.messaging.event_bus import IEventBus
  from domains.authentication.events import UserRegisteredEvent, UserLoggedInEvent
  from domains.onboarding.events import OnboardingCompletedEvent
  
  async def register_event_handlers(event_bus: IEventBus):
      """Register all event handlers"""
      
      # Authentication events trigger onboarding
      from domains.onboarding.events.handlers import handle_user_registered
      event_bus.subscribe(UserRegisteredEvent, handle_user_registered)
      
      # Onboarding events trigger notifications
      from domains.authentication.events.handlers import handle_onboarding_completed
      event_bus.subscribe(OnboardingCompletedEvent, handle_onboarding_completed)
  ```

  3. Update use cases to publish events:
  ```python
  # domains/authentication/use_cases/register_user.py
  class RegisterUserUseCase(UseCase[SignupRequest, UserResponse]):
      def __init__(self, uow: AuthenticationUnitOfWork, event_bus: IEventBus):
          self.uow = uow
          self.event_bus = event_bus
      
      async def execute(self, request: SignupRequest) -> UserResponse:
          async with self.uow:
              # Create user
              user = User(
                  email=request.email,
                  full_name=request.full_name,
                  password_hash=hash_password(request.password)
              )
              
              # Save user
              saved_user = await self.uow.users.save(user)
              
              # Publish event
              event = UserRegisteredEvent(
                  user_id=saved_user.id,
                  email=saved_user.email,
                  full_name=saved_user.full_name
              )
              await self.event_bus.publish(event)
              
              return UserMapper.to_response(saved_user)
  ```

  **Verification:**
  - Event bus can publish and handle events
  - Cross-domain communication happens via events only
  - Events are properly logged and traceable

  ## Step 4: Document Module Interfaces

  **Actions:**
  1. Create module interface documentation:
  ```markdown
  # docs/architecture/module_interfaces.md
  # Module Interface Documentation
  
  ## Authentication Domain
  
  ### Purpose
  Handles user authentication, authorization, and session management.
  
  ### Public Interface
  
  #### Use Cases
  - `RegisterUserUseCase`: Register a new user
  - `AuthenticateUserUseCase`: Authenticate with credentials
  - `RefreshTokenUseCase`: Refresh access token
  - `LogoutUserUseCase`: Terminate user session
  
  #### Events Published
  - `UserRegisteredEvent`: When a new user is created
  - `UserLoggedInEvent`: When a user successfully authenticates
  - `UserLoggedOutEvent`: When a user logs out
  
  #### Events Consumed
  - `OnboardingCompletedEvent`: Update user profile with onboarding data
  
  ### Dependencies
  - External: Auth0, JWT libraries
  - Infrastructure: Redis (for sessions), PostgreSQL
  
  ## Onboarding Domain
  
  ### Purpose
  Manages user onboarding flow and initial configuration.
  
  ### Public Interface
  
  #### Use Cases
  - `StartOnboardingSessionUseCase`: Begin onboarding
  - `SelectNativeLanguageUseCase`: Set user's native language
  - `SelectUserIndustryUseCase`: Set user's industry
  - `CompleteOnboardingFlowUseCase`: Finalize onboarding
  
  #### Events Published
  - `OnboardingStartedEvent`: When onboarding begins
  - `OnboardingStepCompletedEvent`: When a step is completed
  - `OnboardingCompletedEvent`: When onboarding finishes
  
  #### Events Consumed
  - `UserRegisteredEvent`: Create onboarding session for new user
  
  ### Dependencies
  - External: OpenAI (for recommendations)
  - Infrastructure: Redis (for session state), PostgreSQL
  ```

  2. Generate architecture diagrams:
  ```python
  # scripts/generate_architecture_diagrams.py
  import matplotlib.pyplot as plt
  import matplotlib.patches as patches
  from matplotlib.patches import FancyBboxPatch, ConnectionPatch
  
  def generate_domain_diagram():
      fig, ax = plt.subplots(1, 1, figsize=(12, 8))
      
      # Define domain boxes
      domains = {
          'API Layer': (2, 7, 8, 1),
          'Authentication': (1, 4, 3, 2),
          'Onboarding': (6, 4, 3, 2),
          'Shared': (3.5, 2, 3, 1),
          'Infrastructure': (2, 0, 8, 1)
      }
      
      # Draw domain boxes
      for name, (x, y, w, h) in domains.items():
          if name == 'Shared':
              color = 'lightgreen'
          elif name in ['API Layer', 'Infrastructure']:
              color = 'lightgray'
          else:
              color = 'lightblue'
          
          box = FancyBboxPatch(
              (x, y), w, h,
              boxstyle="round,pad=0.1",
              facecolor=color,
              edgecolor='black',
              linewidth=2
          )
          ax.add_patch(box)
          ax.text(x + w/2, y + h/2, name, ha='center', va='center', fontsize=12, fontweight='bold')
      
      # Draw arrows for event flow
      arrow1 = ConnectionPatch((4, 5), (6, 5), "data", "data",
                              arrowstyle="->", shrinkA=5, shrinkB=5,
                              mutation_scale=20, fc="red")
      ax.add_artist(arrow1)
      ax.text(5, 5.2, "UserRegisteredEvent", ha='center', fontsize=8)
      
      ax.set_xlim(0, 12)
      ax.set_ylim(-1, 9)
      ax.axis('off')
      ax.set_title('Domain Architecture with Event Flow', fontsize=16, fontweight='bold')
      
      plt.tight_layout()
      plt.savefig('docs/architecture/diagrams/domain_architecture.png', dpi=300, bbox_inches='tight')
  
  if __name__ == "__main__":
      generate_domain_diagram()
      print("\u2705 Architecture diagrams generated")
  ```

  **Verification:**
  - Each domain's interface is clearly documented
  - Event flow between domains is visualized
  - Dependencies are explicitly listed

  Phase 2: API Design and Communication (1 week)

  Week 4: RESTful API Standardization

  Day 15-16: API Structure Refactoring

  ## Goal
  Implement a versioned, consistent API structure that supports future growth and maintains backward compatibility.

  ## Current State Before This Step
  - ✅ Views moved to domain API directories
  - ✅ DTOs created for request/response
  - ❌ No API versioning strategy
  - ❌ Inconsistent URL patterns
  - ❌ No centralized API routing
  - ❌ Missing API documentation

  ## Step 1: Implement API Versioning Strategy

  **Actions:**
  1. Create API directory structure:
  ```bash
  mkdir -p api/{v1,v2,common}
  touch api/__init__.py
  touch api/urls.py
  touch api/v1/{__init__.py,urls.py}
  touch api/v2/{__init__.py,urls.py}
  touch api/common/{__init__.py,base_views.py,mixins.py,pagination.py,responses.py}
  ```

  2. Create main API URL configuration:
  ```python
  # api/urls.py
  from django.urls import path, include
  
  app_name = 'api'
  
  urlpatterns = [
      path('v1/', include('api.v1.urls', namespace='v1')),
      path('v2/', include('api.v2.urls', namespace='v2')),
      # Default to latest stable version
      path('', include('api.v1.urls')),
  ]
  ```

  3. Create v1 API aggregator:
  ```python
  # api/v1/urls.py
  from django.urls import path, include
  
  app_name = 'v1'
  
  urlpatterns = [
      # Authentication endpoints
      path('auth/', include('domains.authentication.api.v1.urls')),
      
      # Onboarding endpoints
      path('onboarding/', include('domains.onboarding.api.v1.urls')),
      
      # Health check
      path('health/', include('api.common.health')),
      
      # API documentation
      path('docs/', include('api.common.docs')),
  ]
  ```

  4. Create API version middleware:
  ```python
  # api/common/middleware.py
  from django.http import HttpRequest
  import re
  
  class APIVersionMiddleware:
      """Extract and validate API version from URL"""
      
      VERSION_REGEX = re.compile(r'^/api/v(\d+)/')
      SUPPORTED_VERSIONS = ['1', '2']
      
      def __init__(self, get_response):
          self.get_response = get_response
      
      def __call__(self, request: HttpRequest):
          # Extract API version from path
          match = self.VERSION_REGEX.match(request.path)
          
          if match:
              version = match.group(1)
              if version in self.SUPPORTED_VERSIONS:
                  request.api_version = f'v{version}'
              else:
                  # Invalid version
                  request.api_version = None
          else:
              # No version specified, use default
              request.api_version = 'v1'
          
          response = self.get_response(request)
          
          # Add version header to response
          if hasattr(request, 'api_version'):
              response['X-API-Version'] = request.api_version
          
          return response
  ```

  **Verification:**
  - API URLs follow pattern: `/api/v1/domain/resource`
  - Version is extracted and available in request
  - Unknown versions return appropriate error

  ## Step 2: Standardize URL Patterns

  **Actions:**
  1. Update authentication URLs:
  ```python
  # domains/authentication/api/v1/urls.py
  from django.urls import path
  from .views import (
      LoginView,
      LogoutView,
      SignupView,
      RefreshTokenView,
      UserProfileView,
      ChangePasswordView
  )
  
  app_name = 'authentication'
  
  urlpatterns = [
      # Session management
      path('sessions/login/', LoginView.as_view(), name='login'),
      path('sessions/logout/', LogoutView.as_view(), name='logout'),
      path('sessions/refresh/', RefreshTokenView.as_view(), name='refresh-token'),
      
      # User management
      path('users/signup/', SignupView.as_view(), name='signup'),
      path('users/me/', UserProfileView.as_view(), name='current-user'),
      path('users/me/password/', ChangePasswordView.as_view(), name='change-password'),
      path('users/<str:user_id>/', UserProfileView.as_view(), name='user-detail'),
  ]
  ```

  2. Update onboarding URLs:
  ```python
  # domains/onboarding/api/v1/urls.py
  from django.urls import path
  from .views import (
      OnboardingSessionView,
      LanguageSelectionView,
      IndustrySelectionView,
      RoleMatchingView,
      PartnerSelectionView,
      OnboardingSummaryView
  )
  
  app_name = 'onboarding'
  
  urlpatterns = [
      # Session management
      path('sessions/', OnboardingSessionView.as_view(), name='session-list'),
      path('sessions/<str:session_id>/', OnboardingSessionView.as_view(), name='session-detail'),
      
      # Onboarding steps
      path('sessions/<str:session_id>/language/', LanguageSelectionView.as_view(), name='select-language'),
      path('sessions/<str:session_id>/industry/', IndustrySelectionView.as_view(), name='select-industry'),
      path('sessions/<str:session_id>/role/', RoleMatchingView.as_view(), name='match-role'),
      path('sessions/<str:session_id>/partners/', PartnerSelectionView.as_view(), name='select-partners'),
      path('sessions/<str:session_id>/summary/', OnboardingSummaryView.as_view(), name='session-summary'),
      
      # Reference data
      path('languages/', LanguageListView.as_view(), name='language-list'),
      path('industries/', IndustryListView.as_view(), name='industry-list'),
      path('roles/', RoleListView.as_view(), name='role-list'),
  ]
  ```

  3. Create URL naming conventions:
  ```python
  # api/common/url_patterns.py
  """
  URL Pattern Conventions:
  
  Collections:
  - GET    /api/v1/{domain}/{resources}/          - List resources
  - POST   /api/v1/{domain}/{resources}/          - Create resource
  
  Single Resource:
  - GET    /api/v1/{domain}/{resources}/{id}/     - Get resource
  - PUT    /api/v1/{domain}/{resources}/{id}/     - Update resource
  - PATCH  /api/v1/{domain}/{resources}/{id}/     - Partial update
  - DELETE /api/v1/{domain}/{resources}/{id}/     - Delete resource
  
  Sub-resources:
  - GET    /api/v1/{domain}/{resources}/{id}/{sub-resources}/
  
  Actions:
  - POST   /api/v1/{domain}/{resources}/{id}/{action}/
  
  Examples:
  - GET    /api/v1/auth/users/me/
  - POST   /api/v1/onboarding/sessions/
  - PUT    /api/v1/onboarding/sessions/123/language/
  """
  ```

  **Verification:**
  - All URLs follow RESTful conventions
  - Resource names are plural
  - Actions are clearly distinguished from resources

  ## Step 3: Create API Documentation Standards

  **Actions:**
  1. Create API style guide:
  ```markdown
  # docs/api/style_guide.md
  # FluentPro API Style Guide
  
  ## General Principles
  
  1. **Consistency**: All endpoints follow the same patterns
  2. **Predictability**: Developers can guess endpoint URLs
  3. **Versioning**: Breaking changes require new version
  4. **Documentation**: All endpoints must be documented
  
  ## URL Structure
  
  ### Base URL
  ```
  https://api.fluentpro.com/api/v{version}/
  ```
  
  ### Resource Naming
  - Use plural nouns: `/users` not `/user`
  - Use kebab-case: `/user-profiles` not `/userProfiles`
  - Nest related resources: `/users/{id}/sessions`
  
  ## HTTP Methods
  
  | Method | Action | Example |
  |--------|--------|---------|
  | GET | Retrieve resource(s) | GET /users/123 |
  | POST | Create new resource | POST /users |
  | PUT | Replace entire resource | PUT /users/123 |
  | PATCH | Update partial resource | PATCH /users/123 |
  | DELETE | Remove resource | DELETE /users/123 |
  
  ## Status Codes
  
  ### Success Codes
  - 200 OK: Successful GET, PUT, PATCH
  - 201 Created: Successful POST
  - 204 No Content: Successful DELETE
  
  ### Error Codes
  - 400 Bad Request: Invalid input
  - 401 Unauthorized: Authentication required
  - 403 Forbidden: Insufficient permissions
  - 404 Not Found: Resource doesn't exist
  - 422 Unprocessable Entity: Business rule violation
  - 500 Internal Server Error: Server fault
  
  ## Request/Response Format
  
  ### Request Headers
  ```
  Content-Type: application/json
  Accept: application/json
  Authorization: Bearer {token}
  X-Request-ID: {uuid}
  ```
  
  ### Response Format
  
  #### Success Response
  ```json
  {
    "data": {
      "id": "123",
      "type": "user",
      "attributes": {
        "email": "user@example.com",
        "full_name": "John Doe"
      }
    },
    "meta": {
      "timestamp": "2024-01-15T10:30:00Z",
      "version": "v1"
    }
  }
  ```
  
  #### Error Response
  ```json
  {
    "error": {
      "code": "VALIDATION_ERROR",
      "message": "Invalid input data",
      "details": [
        {
          "field": "email",
          "message": "Invalid email format"
        }
      ]
    },
    "meta": {
      "timestamp": "2024-01-15T10:30:00Z",
      "request_id": "550e8400-e29b-41d4-a716-446655440000"
    }
  }
  ```
  
  ## Pagination
  
  ### Request
  ```
  GET /api/v1/users?page=2&per_page=20
  ```
  
  ### Response
  ```json
  {
    "data": [...],
    "pagination": {
      "current_page": 2,
      "per_page": 20,
      "total_pages": 10,
      "total_items": 200
    },
    "links": {
      "first": "/api/v1/users?page=1&per_page=20",
      "prev": "/api/v1/users?page=1&per_page=20",
      "next": "/api/v1/users?page=3&per_page=20",
      "last": "/api/v1/users?page=10&per_page=20"
    }
  }
  ```
  
  ## Filtering & Sorting
  
  ### Filtering
  ```
  GET /api/v1/users?filter[status]=active&filter[role]=admin
  ```
  
  ### Sorting
  ```
  GET /api/v1/users?sort=-created_at,full_name
  ```
  (- prefix for descending order)
  
  ## API Evolution
  
  ### Non-Breaking Changes (same version)
  - Adding new endpoints
  - Adding optional parameters
  - Adding fields to responses
  
  ### Breaking Changes (new version required)
  - Removing endpoints
  - Changing required parameters
  - Removing or renaming response fields
  - Changing response structure
  ```

  2. Create endpoint documentation template:
  ```python
  # api/common/documentation.py
  from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
  from drf_spectacular.types import OpenApiTypes
  
  # Decorator for standardized documentation
  def document_endpoint(
      summary: str,
      description: str,
      request_examples: list = None,
      response_examples: list = None,
      parameters: list = None
  ):
      """Standard endpoint documentation decorator"""
      
      return extend_schema(
          summary=summary,
          description=description,
          parameters=parameters or [],
          examples=[
              OpenApiExample(
                  name=example['name'],
                  value=example['value'],
                  request_only=example.get('request_only', False),
                  response_only=example.get('response_only', False)
              )
              for example in (request_examples or []) + (response_examples or [])
          ]
      )
  ```

  **Verification:**
  - API style guide is comprehensive
  - All patterns are documented
  - Examples provided for each concept

  Day 17-18: DTO Implementation

  ## Goal
  Implement a comprehensive DTO (Data Transfer Object) layer to decouple API contracts from domain models and ensure consistent data validation.

  ## Current State Before This Step
  - ✅ Basic DTOs created in domains/*/dto/
  - ✅ Request/response files exist
  - ❌ DTOs not fully integrated with views
  - ❌ Still using Django serializers in places
  - ❌ No consistent validation
  - ❌ Missing DTO mappers

  ## Step 1: Enhance DTO Implementation

  **Actions:**
  1. Create comprehensive authentication DTOs:
  ```python
  # domains/authentication/dto/requests.py
  from pydantic import BaseModel, EmailStr, validator, Field
  from typing import Optional
  from datetime import datetime
  
  class LoginRequest(BaseModel):
      """Login request DTO"""
      email: EmailStr
      password: str = Field(..., min_length=8)
      remember_me: bool = False
      
      class Config:
          schema_extra = {
              "example": {
                  "email": "user@example.com",
                  "password": "SecurePass123!",
                  "remember_me": True
              }
          }
  
  class SignupRequest(BaseModel):
      """User registration request DTO"""
      email: EmailStr
      password: str = Field(..., min_length=8)
      confirm_password: str
      full_name: str = Field(..., min_length=2, max_length=100)
      accept_terms: bool
      
      @validator('confirm_password')
      def passwords_match(cls, v, values):
          if 'password' in values and v != values['password']:
              raise ValueError('Passwords do not match')
          return v
      
      @validator('accept_terms')
      def terms_accepted(cls, v):
          if not v:
              raise ValueError('Terms must be accepted')
          return v
  
  class RefreshTokenRequest(BaseModel):
      """Token refresh request DTO"""
      refresh_token: str
  
  class ChangePasswordRequest(BaseModel):
      """Change password request DTO"""
      current_password: str
      new_password: str = Field(..., min_length=8)
      confirm_password: str
      
      @validator('confirm_password')
      def passwords_match(cls, v, values):
          if 'new_password' in values and v != values['new_password']:
              raise ValueError('Passwords do not match')
          return v
  ```

  2. Create response DTOs with computed fields:
  ```python
  # domains/authentication/dto/responses.py
  from pydantic import BaseModel, Field
  from typing import Optional, List
  from datetime import datetime
  
  class TokenResponse(BaseModel):
      """Authentication token response"""
      access_token: str
      refresh_token: str
      token_type: str = "Bearer"
      expires_in: int = Field(..., description="Seconds until expiration")
      scope: Optional[str] = None
      
      class Config:
          schema_extra = {
              "example": {
                  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                  "refresh_token": "def50200b5d3e2e8f6a8f7e9c4d3b2a1...",
                  "token_type": "Bearer",
                  "expires_in": 3600
              }
          }
  
  class UserResponse(BaseModel):
      """User profile response"""
      id: str
      email: str
      full_name: str
      created_at: datetime
      updated_at: datetime
      is_active: bool = True
      is_verified: bool = False
      profile_completion: int = Field(default=0, ge=0, le=100)
      roles: List[str] = []
      
      # Computed fields
      display_name: str = None
      
      def __init__(self, **data):
          super().__init__(**data)
          # Set display name if not provided
          if not self.display_name:
              self.display_name = self.full_name.split()[0] if self.full_name else self.email.split('@')[0]
      
      class Config:
          orm_mode = True  # Allow creation from ORM models
          json_encoders = {
              datetime: lambda v: v.isoformat()
          }
  ```

  3. Create nested DTOs for complex responses:
  ```python
  # domains/onboarding/dto/responses.py
  from pydantic import BaseModel, Field
  from typing import Optional, List, Dict, Any
  from datetime import datetime
  from enum import Enum
  
  class OnboardingStatus(str, Enum):
      NOT_STARTED = "not_started"
      IN_PROGRESS = "in_progress"
      COMPLETED = "completed"
      ABANDONED = "abandoned"
  
  class OnboardingStepResponse(BaseModel):
      """Individual onboarding step"""
      step_id: str
      name: str
      status: str
      completed_at: Optional[datetime] = None
      data: Dict[str, Any] = {}
  
  class OnboardingSessionResponse(BaseModel):
      """Complete onboarding session response"""
      session_id: str
      user_id: str
      status: OnboardingStatus
      current_step: Optional[str] = None
      progress_percentage: int = Field(ge=0, le=100)
      steps: List[OnboardingStepResponse] = []
      started_at: datetime
      completed_at: Optional[datetime] = None
      metadata: Dict[str, Any] = Field(default_factory=dict)
      
      @property
      def duration_seconds(self) -> Optional[int]:
          """Calculate session duration"""
          if self.completed_at:
              return int((self.completed_at - self.started_at).total_seconds())
          return None
      
      class Config:
          use_enum_values = True
  ```

  **Verification:**
  - All DTOs use Pydantic for validation
  - Complex validations are implemented
  - Response DTOs handle serialization properly

  ## Step 2: Create DTO Mappers

  **Actions:**
  1. Create generic mapper base:
  ```python
  # core/patterns/mapper.py
  from abc import ABC, abstractmethod
  from typing import TypeVar, Generic, List
  
  TModel = TypeVar('TModel')
  TDto = TypeVar('TDto')
  
  class Mapper(ABC, Generic[TModel, TDto]):
      """Base mapper for model <-> DTO conversion"""
      
      @abstractmethod
      def to_dto(self, model: TModel) -> TDto:
          """Convert model to DTO"""
          pass
      
      @abstractmethod
      def to_model(self, dto: TDto) -> TModel:
          """Convert DTO to model"""
          pass
      
      def to_dto_list(self, models: List[TModel]) -> List[TDto]:
          """Convert list of models to DTOs"""
          return [self.to_dto(model) for model in models]
      
      def to_model_list(self, dtos: List[TDto]) -> List[TModel]:
          """Convert list of DTOs to models"""
          return [self.to_model(dto) for dto in dtos]
  ```

  2. Implement domain-specific mappers:
  ```python
  # domains/authentication/dto/mappers.py
  from core.patterns.mapper import Mapper
  from domains.authentication.models.user import User
  from domains.authentication.dto.responses import UserResponse
  from typing import List
  
  class UserMapper(Mapper[User, UserResponse]):
      """Maps between User model and UserResponse DTO"""
      
      def to_dto(self, model: User) -> UserResponse:
          return UserResponse(
              id=model.id,
              email=model.email,
              full_name=model.full_name,
              created_at=model.created_at,
              updated_at=model.updated_at,
              is_active=model.is_active,
              is_verified=model.is_verified,
              profile_completion=self._calculate_profile_completion(model),
              roles=self._get_user_roles(model)
          )
      
      def to_model(self, dto: UserResponse) -> User:
          # Note: Not all fields can be mapped back
          user = User(
              email=dto.email,
              full_name=dto.full_name
          )
          user.id = dto.id
          user.is_active = dto.is_active
          user.is_verified = dto.is_verified
          return user
      
      def _calculate_profile_completion(self, user: User) -> int:
          """Calculate profile completion percentage"""
          fields = [
              user.email,
              user.full_name,
              user.is_verified,
              user.profile_picture,
              user.bio
          ]
          completed = sum(1 for field in fields if field)
          return int((completed / len(fields)) * 100)
      
      def _get_user_roles(self, user: User) -> List[str]:
          """Get user role names"""
          # Assuming user has a roles relationship
          return [role.name for role in user.roles.all()] if hasattr(user, 'roles') else []
  
  # Singleton instance
  user_mapper = UserMapper()
  ```

  3. Create composite mappers for complex objects:
  ```python
  # domains/onboarding/dto/mappers.py
  from domains.onboarding.models.onboarding_session import OnboardingSession
  from domains.onboarding.dto.responses import OnboardingSessionResponse, OnboardingStepResponse
  
  class OnboardingSessionMapper(Mapper[OnboardingSession, OnboardingSessionResponse]):
      """Maps onboarding session with nested steps"""
      
      def __init__(self, step_mapper: 'OnboardingStepMapper'):
          self.step_mapper = step_mapper
      
      def to_dto(self, model: OnboardingSession) -> OnboardingSessionResponse:
          return OnboardingSessionResponse(
              session_id=model.id,
              user_id=model.user_id,
              status=model.status,
              current_step=model.current_step,
              progress_percentage=self._calculate_progress(model),
              steps=self.step_mapper.to_dto_list(model.steps),
              started_at=model.created_at,
              completed_at=model.completed_at,
              metadata=model.metadata or {}
          )
      
      def _calculate_progress(self, session: OnboardingSession) -> int:
          """Calculate onboarding progress"""
          if not session.steps:
              return 0
          completed = sum(1 for step in session.steps if step.is_completed)
          return int((completed / len(session.steps)) * 100)
  ```

  **Verification:**
  - Mappers handle all conversions
  - Complex nested objects are properly mapped
  - Computed fields are calculated during mapping

  ## Step 3: Update Views to Use DTOs

  **Actions:**
  1. Remove Django serializers and use DTOs:
  ```python
  # domains/authentication/api/v1/views.py
  from rest_framework import status
  from rest_framework.response import Response
  from api.common.base_views import BaseAPIView
  from domains.authentication.dto.requests import LoginRequest, SignupRequest
  from domains.authentication.dto.responses import TokenResponse, UserResponse
  from domains.authentication.dto.mappers import user_mapper
  from application.container import container
  from application.decorators.validate import validate_input
  from api.common.documentation import document_endpoint
  
  class LoginView(BaseAPIView):
      @document_endpoint(
          summary="User Login",
          description="Authenticate user with email and password",
          request_examples=[{
              "name": "Valid Login",
              "value": {
                  "email": "user@example.com",
                  "password": "SecurePass123!",
                  "remember_me": True
              }
          }]
      )
      async def post(self, request):
          # Parse and validate request
          try:
              login_dto = LoginRequest(**request.data)
          except ValidationError as e:
              return Response(
                  {"errors": e.errors()},
                  status=status.HTTP_400_BAD_REQUEST
              )
          
          # Execute use case
          use_case = container.auth_use_cases.authenticate_user()
          token_response = await use_case.execute(login_dto)
          
          # Return DTO response
          return Response(
              token_response.dict(),
              status=status.HTTP_200_OK
          )
  
  class UserProfileView(BaseAPIView):
      authentication_classes = [JWTAuthentication]
      
      async def get(self, request, user_id: str = None):
          # Get current user if no ID provided
          if not user_id or user_id == 'me':
              user_id = request.user.id
          
          # Execute use case
          use_case = container.auth_use_cases.get_user_profile()
          user = await use_case.execute(user_id)
          
          # Map to DTO and return
          user_dto = user_mapper.to_dto(user)
          return Response(
              user_dto.dict(),
              status=status.HTTP_200_OK
          )
  ```

  2. Create standardized error responses:
  ```python
  # api/common/responses.py
  from rest_framework.response import Response
  from rest_framework import status
  from typing import List, Dict, Any, Optional
  from datetime import datetime
  import uuid
  
  class APIResponse:
      """Standardized API response builder"""
      
      @staticmethod
      def success(
          data: Any,
          message: str = None,
          status_code: int = status.HTTP_200_OK,
          meta: Dict[str, Any] = None
      ) -> Response:
          """Create success response"""
          response_data = {
              "data": data,
              "meta": {
                  "timestamp": datetime.utcnow().isoformat(),
                  "version": "v1",
                  **(meta or {})
              }
          }
          
          if message:
              response_data["message"] = message
          
          return Response(response_data, status=status_code)
      
      @staticmethod
      def error(
          message: str,
          code: str = "ERROR",
          details: List[Dict[str, Any]] = None,
          status_code: int = status.HTTP_400_BAD_REQUEST,
          request_id: str = None
      ) -> Response:
          """Create error response"""
          return Response({
              "error": {
                  "code": code,
                  "message": message,
                  "details": details or []
              },
              "meta": {
                  "timestamp": datetime.utcnow().isoformat(),
                  "request_id": request_id or str(uuid.uuid4())
              }
          }, status=status_code)
      
      @staticmethod
      def validation_error(errors: List[Dict[str, Any]]) -> Response:
          """Create validation error response"""
          return APIResponse.error(
              message="Validation failed",
              code="VALIDATION_ERROR",
              details=errors,
              status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
          )
  ```

  **Verification:**
  - All views use DTOs exclusively
  - Django serializers are removed
  - Responses follow consistent format

  ## Step 4: Add DTO Validation Middleware

  **Actions:**
  1. Create validation middleware:
  ```python
  # api/common/middleware.py
  from django.http import JsonResponse
  from pydantic import ValidationError
  import json
  
  class DTOValidationMiddleware:
      """Automatically validate request bodies against DTOs"""
      
      def __init__(self, get_response):
          self.get_response = get_response
      
      def __call__(self, request):
          # Only process JSON requests
          if request.content_type == 'application/json' and request.body:
              try:
                  # Parse JSON body
                  request.json = json.loads(request.body)
              except json.JSONDecodeError as e:
                  return JsonResponse({
                      "error": {
                          "code": "INVALID_JSON",
                          "message": "Invalid JSON in request body",
                          "details": [{"error": str(e)}]
                      }
                  }, status=400)
          
          response = self.get_response(request)
          return response
  ```

  2. Create DTO validation decorator:
  ```python
  # api/common/decorators.py
  from functools import wraps
  from pydantic import BaseModel, ValidationError
  from rest_framework.response import Response
  from rest_framework import status
  from api.common.responses import APIResponse
  
  def validate_dto(dto_class: type[BaseModel]):
      """Decorator to validate request data against a DTO"""
      def decorator(view_func):
          @wraps(view_func)
          async def wrapper(self, request, *args, **kwargs):
              try:
                  # Validate request data
                  dto_instance = dto_class(**request.data)
                  
                  # Add validated DTO to request
                  request.validated_data = dto_instance
                  
                  # Call view with validated data
                  return await view_func(self, request, *args, **kwargs)
                  
              except ValidationError as e:
                  # Format validation errors
                  errors = [
                      {
                          "field": error["loc"][0],
                          "message": error["msg"],
                          "type": error["type"]
                      }
                      for error in e.errors()
                  ]
                  
                  return APIResponse.validation_error(errors)
          
          return wrapper
      return decorator
  ```

  **Verification:**
  - Request validation happens automatically
  - Validation errors return consistent format
  - DTOs enforce type safety

  Day 19: API Documentation & Contracts

  ## Goal
  Generate comprehensive, interactive API documentation and establish clear API contracts for external consumers.

  ## Current State Before This Step
  - ✅ API structure standardized
  - ✅ DTOs implemented with validation
  - ❌ No automated API documentation
  - ❌ No OpenAPI specification
  - ❌ Missing API contracts
  - ❌ No versioning migration strategy

  ## Step 1: Integrate OpenAPI Documentation

  **Actions:**
  1. Install and configure drf-spectacular:
  ```bash
  # Add to requirements/base.txt
  drf-spectacular==0.26.5
  drf-spectacular[sidecar]==0.26.5
  ```

  2. Configure in Django settings:
  ```python
  # fluentpro_backend/settings.py
  INSTALLED_APPS = [
      # ... existing apps
      'drf_spectacular',
      'drf_spectacular_sidecar',
  ]
  
  REST_FRAMEWORK = {
      'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
      'DEFAULT_AUTHENTICATION_CLASSES': [
          'rest_framework_simplejwt.authentication.JWTAuthentication',
      ],
      'DEFAULT_PERMISSION_CLASSES': [
          'rest_framework.permissions.IsAuthenticated',
      ],
      'DEFAULT_PAGINATION_CLASS': 'api.common.pagination.StandardResultsSetPagination',
      'PAGE_SIZE': 20,
  }
  
  SPECTACULAR_SETTINGS = {
      'TITLE': 'FluentPro API',
      'DESCRIPTION': 'API for FluentPro language learning platform',
      'VERSION': '1.0.0',
      'SERVE_INCLUDE_SCHEMA': False,
      'SWAGGER_UI_DIST': 'SIDECAR',
      'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
      'REDOC_DIST': 'SIDECAR',
      
      # API versioning
      'SCHEMA_PATH_PREFIX': r'/api/v[0-9]',
      'SCHEMA_PATH_PREFIX_TRIM': True,
      
      # Security
      'COMPONENT_SPLIT_REQUEST': True,
      'COMPONENT_NO_READ_ONLY_REQUIRED': True,
      
      # Tags
      'TAGS': [
          {'name': 'Authentication', 'description': 'User authentication and authorization'},
          {'name': 'Onboarding', 'description': 'User onboarding flow'},
          {'name': 'Health', 'description': 'API health checks'},
      ],
      
      # Examples
      'SWAGGER_UI_SETTINGS': {
          'deepLinking': True,
          'persistAuthorization': True,
          'displayOperationId': True,
      }
  }
  ```

  3. Add documentation URLs:
  ```python
  # api/urls.py
  from drf_spectacular.views import (
      SpectacularAPIView,
      SpectacularSwaggerView,
      SpectacularRedocView
  )
  
  urlpatterns = [
      # API versions
      path('v1/', include('api.v1.urls', namespace='v1')),
      
      # Documentation
      path('schema/', SpectacularAPIView.as_view(), name='schema'),
      path('docs/', SpectacularSwaggerView.as_view(url_name='api:schema'), name='swagger-ui'),
      path('redoc/', SpectacularRedocView.as_view(url_name='api:schema'), name='redoc'),
  ]
  ```

  **Verification:**
  - Visit `/api/docs/` for Swagger UI
  - Visit `/api/redoc/` for ReDoc
  - Schema is accessible at `/api/schema/`

  ## Step 2: Enhance View Documentation

  **Actions:**
  1. Add comprehensive schemas to views:
  ```python
  # domains/authentication/api/v1/views.py
  from drf_spectacular.utils import (
      extend_schema,
      extend_schema_view,
      OpenApiParameter,
      OpenApiExample,
      OpenApiResponse
  )
  from drf_spectacular.types import OpenApiTypes
  
  @extend_schema_view(
      post=extend_schema(
          summary="User Login",
          description="Authenticate user with email and password. Returns JWT tokens for subsequent API calls.",
          tags=["Authentication"],
          request={
              'application/json': {
                  'type': 'object',
                  'properties': {
                      'email': {'type': 'string', 'format': 'email'},
                      'password': {'type': 'string', 'minLength': 8},
                      'remember_me': {'type': 'boolean', 'default': False}
                  },
                  'required': ['email', 'password']
              }
          },
          responses={
              200: OpenApiResponse(
                  description="Login successful",
                  examples=[
                      OpenApiExample(
                          name="Successful login",
                          value={
                              "data": {
                                  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                                  "refresh_token": "def50200b5d3e2e8f6a8f7e9c4d3b2a1...",
                                  "token_type": "Bearer",
                                  "expires_in": 3600
                              },
                              "meta": {
                                  "timestamp": "2024-01-15T10:30:00Z",
                                  "version": "v1"
                              }
                          }
                      )
                  ]
              ),
              401: OpenApiResponse(
                  description="Invalid credentials",
                  examples=[
                      OpenApiExample(
                          name="Invalid credentials",
                          value={
                              "error": {
                                  "code": "INVALID_CREDENTIALS",
                                  "message": "Invalid email or password"
                              }
                          }
                      )
                  ]
              ),
              422: OpenApiResponse(description="Validation errors")
          },
          examples=[
              OpenApiExample(
                  name="Basic login",
                  request_only=True,
                  value={
                      "email": "user@example.com",
                      "password": "SecurePass123!"
                  }
              ),
              OpenApiExample(
                  name="Login with remember me",
                  request_only=True,
                  value={
                      "email": "user@example.com",
                      "password": "SecurePass123!",
                      "remember_me": True
                  }
              )
          ]
      )
  )
  class LoginView(BaseAPIView):
      authentication_classes = []  # Public endpoint
      permission_classes = []
      
      async def post(self, request):
          # Implementation from previous step
          pass
  ```

  2. Create reusable schema components:
  ```python
  # api/common/schemas.py
  from drf_spectacular.utils import OpenApiResponse, OpenApiExample
  
  # Common response schemas
  ERROR_RESPONSES = {
      400: OpenApiResponse(
          description="Bad Request",
          examples=[
              OpenApiExample(
                  name="Validation Error",
                  value={
                      "error": {
                          "code": "VALIDATION_ERROR",
                          "message": "Invalid input data",
                          "details": [
                              {
                                  "field": "email",
                                  "message": "Invalid email format"
                              }
                          ]
                      }
                  }
              )
          ]
      ),
      401: OpenApiResponse(
          description="Unauthorized",
          examples=[
              OpenApiExample(
                  name="Missing Token",
                  value={
                      "error": {
                          "code": "UNAUTHORIZED",
                          "message": "Authentication credentials were not provided"
                      }
                  }
              )
          ]
      ),
      403: OpenApiResponse(
          description="Forbidden",
          examples=[
              OpenApiExample(
                  name="Insufficient Permissions",
                  value={
                      "error": {
                          "code": "FORBIDDEN",
                          "message": "You do not have permission to perform this action"
                      }
                  }
              )
          ]
      ),
      404: OpenApiResponse(
          description="Not Found",
          examples=[
              OpenApiExample(
                  name="Resource Not Found",
                  value={
                      "error": {
                          "code": "NOT_FOUND",
                          "message": "The requested resource was not found"
                      }
                  }
              )
          ]
      )
  }
  
  # Security schemes
  BEARER_TOKEN_SECURITY = {
      'bearerAuth': {
          'type': 'http',
          'scheme': 'bearer',
          'bearerFormat': 'JWT'
      }
  }
  ```

  **Verification:**
  - All endpoints have detailed documentation
  - Request/response examples are provided
  - Error responses are documented

  ## Step 3: Generate and Export Documentation

  **Actions:**
  1. Create documentation export script:
  ```python
  # scripts/export_api_docs.py
  #!/usr/bin/env python
  import os
  import django
  import json
  import yaml
  from pathlib import Path
  
  # Setup Django
  os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fluentpro_backend.settings')
  django.setup()
  
  from drf_spectacular.openapi import AutoSchema
  from drf_spectacular.plumbing import build_schema_from_config
  
  def export_openapi_schema():
      """Export OpenAPI schema to files"""
      # Generate schema
      schema = build_schema_from_config()
      
      # Ensure docs directory exists
      docs_dir = Path('docs/api')
      docs_dir.mkdir(parents=True, exist_ok=True)
      
      # Export as JSON
      with open(docs_dir / 'openapi.json', 'w') as f:
          json.dump(schema, f, indent=2)
      
      # Export as YAML
      with open(docs_dir / 'openapi.yaml', 'w') as f:
          yaml.dump(schema, f, default_flow_style=False)
      
      print(f"✅ OpenAPI schema exported to {docs_dir}/")
      
      return schema
  
  def generate_postman_collection(schema):
      """Generate Postman collection from OpenAPI schema"""
      from openapi_to_postman import convert
      
      # Convert OpenAPI to Postman
      postman_collection = convert(schema)
      
      # Save collection
      with open('docs/api/postman_collection.json', 'w') as f:
          json.dump(postman_collection, f, indent=2)
      
      print("✅ Postman collection generated")
  
  if __name__ == "__main__":
      schema = export_openapi_schema()
      generate_postman_collection(schema)
  ```

  2. Create API documentation site:
  ```html
  <!-- docs/api/index.html -->
  <!DOCTYPE html>
  <html lang="en">
  <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>FluentPro API Documentation</title>
      <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui.css" />
      <style>
          .swagger-ui .topbar { display: none; }
          .swagger-ui .info { margin: 20px 0; }
      </style>
  </head>
  <body>
      <div id="swagger-ui"></div>
      <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-bundle.js"></script>
      <script>
      window.onload = function() {
          SwaggerUIBundle({
              url: './openapi.yaml',
              dom_id: '#swagger-ui',
              deepLinking: true,
              presets: [
                  SwaggerUIBundle.presets.apis,
                  SwaggerUIBundle.presets.standalone
              ],
              layout: 'StandaloneLayout',
              tryItOutEnabled: true,
              supportedSubmitMethods: ['get', 'post', 'put', 'patch', 'delete'],
              onComplete: function() {
                  console.log('API documentation loaded');
              }
          });
      };
      </script>
  </body>
  </html>
  ```

  **Verification:**
  - OpenAPI files are generated correctly
  - Postman collection works for testing
  - Static documentation site is functional

  ## Step 4: Create API Versioning Strategy

  **Actions:**
  1. Document versioning policy:
  ```markdown
  # docs/api/versioning_guide.md
  # API Versioning Guide
  
  ## Versioning Strategy
  
  FluentPro API uses **URL versioning** with the following format:
  ```
  https://api.fluentpro.com/api/v{major}/
  ```
  
  ### Version Lifecycle
  
  1. **Development** (v2-dev): New features under development
  2. **Beta** (v2-beta): Feature complete, testing in progress
  3. **Stable** (v2): Production ready, fully supported
  4. **Deprecated** (v1): Old version, maintenance only
  5. **Sunset** (v0): No longer supported
  
  ### Breaking Changes
  
  The following changes require a new major version:
  
  - Removing endpoints
  - Removing or renaming request/response fields
  - Changing field types
  - Adding required fields without defaults
  - Changing HTTP status codes
  - Changing error response format
  
  ### Non-Breaking Changes
  
  The following can be added to existing versions:
  
  - Adding new endpoints
  - Adding optional request fields
  - Adding response fields
  - Adding new HTTP methods to existing endpoints
  - Changing internal implementation
  
  ## Migration Process
  
  ### For API Consumers
  
  1. **Monitor deprecation notices** in API responses
  2. **Test new version** in development environment
  3. **Update client code** to handle new response format
  4. **Switch to new version** before old version sunset
  
  ### Deprecation Notice Format
  
  ```json
  {
    "data": { ... },
    "meta": {
      "deprecation": {
        "version": "v1",
        "sunset_date": "2024-12-31",
        "migration_guide": "https://docs.fluentpro.com/api/v1-to-v2",
        "message": "This version will be sunset on 2024-12-31. Please migrate to v2."
      }
    }
  }
  ```
  
  ## Version Support Policy
  
  - **Current version**: Full support, new features
  - **Previous version**: Bug fixes only, 12 months support
  - **Deprecated versions**: Security fixes only, 6 months notice before sunset
  ```

  2. Implement deprecation warnings:
  ```python
  # api/common/deprecation.py
  from datetime import datetime, date
  from typing import Optional
  import warnings
  
  class DeprecationWarning:
      def __init__(
          self,
          version: str,
          sunset_date: date,
          migration_guide: str,
          message: str = None
      ):
          self.version = version
          self.sunset_date = sunset_date
          self.migration_guide = migration_guide
          self.message = message or f"Version {version} is deprecated"
      
      def to_dict(self) -> dict:
          return {
              "version": self.version,
              "sunset_date": self.sunset_date.isoformat(),
              "migration_guide": self.migration_guide,
              "message": self.message
          }
  
  def add_deprecation_warning(response_data: dict, warning: DeprecationWarning):
      """Add deprecation warning to response"""
      if "meta" not in response_data:
          response_data["meta"] = {}
      
      response_data["meta"]["deprecation"] = warning.to_dict()
      
      # Also log the warning
      warnings.warn(
          f"API {warning.version} deprecated: {warning.message}",
          category=DeprecationWarning,
          stacklevel=2
      )
  ```

  **Verification:**
  - Versioning policy is clearly documented
  - Deprecation warnings are implemented
  - Migration guides are available

  ## Step 5: Implement Backward Compatibility Layer

  **Actions:**
  1. Create compatibility middleware:
  ```python
  # api/common/compatibility.py
  from django.http import JsonResponse
  import json
  from typing import Dict, Any
  
  class BackwardCompatibilityMiddleware:
      """Handle backward compatibility transformations"""
      
      def __init__(self, get_response):
          self.get_response = get_response
          self.transformations = {
              'v1': self._transform_v1_response,
              'v2': self._transform_v2_response
          }
      
      def __call__(self, request):
          response = self.get_response(request)
          
          # Apply version-specific transformations
          if hasattr(request, 'api_version') and response.get('content-type') == 'application/json':
              transformation = self.transformations.get(request.api_version)
              if transformation:
                  response = transformation(response, request)
          
          return response
      
      def _transform_v1_response(self, response, request):
          """Transform response for v1 compatibility"""
          if response.status_code == 200:
              try:
                  data = json.loads(response.content)
                  
                  # V1 format: flatten data structure
                  if 'data' in data:
                      flattened = data['data']
                      flattened['_meta'] = data.get('meta', {})
                      
                      response.content = json.dumps(flattened)
              except (json.JSONDecodeError, KeyError):
                  pass
          
          return response
      
      def _transform_v2_response(self, response, request):
          """V2 is current format, no transformation needed"""
          return response
  ```

  2. Create field mapping for legacy support:
  ```python
  # api/common/field_mapping.py
  from typing import Dict, Any
  
  class FieldMapper:
      """Map field names between API versions"""
      
      V1_TO_V2_MAPPING = {
          'user_name': 'full_name',
          'user_email': 'email',
          'created': 'created_at',
          'modified': 'updated_at'
      }
      
      V2_TO_V1_MAPPING = {v: k for k, v in V1_TO_V2_MAPPING.items()}
      
      @classmethod
      def map_request_fields(cls, data: Dict[str, Any], from_version: str, to_version: str) -> Dict[str, Any]:
          """Map request fields between versions"""
          if from_version == 'v1' and to_version == 'v2':
              mapping = cls.V1_TO_V2_MAPPING
          elif from_version == 'v2' and to_version == 'v1':
              mapping = cls.V2_TO_V1_MAPPING
          else:
              return data
          
          mapped_data = {}
          for key, value in data.items():
              new_key = mapping.get(key, key)
              mapped_data[new_key] = value
          
          return mapped_data
      
      @classmethod
      def map_response_fields(cls, data: Dict[str, Any], from_version: str, to_version: str) -> Dict[str, Any]:
          """Map response fields between versions"""
          return cls.map_request_fields(data, from_version, to_version)
  ```

  **Verification:**
  - Legacy API versions continue to work
  - Field mappings are applied correctly
  - Responses are transformed appropriately

  ## Phase 1-2 Completion Status

  **✅ PHASE 1 COMPLETE** - Foundation & Clean Architecture
  - Dependency injection infrastructure
  - Domain-driven design structure 
  - Repository pattern implementation
  - Use case layer with consistent patterns
  - Service layer with resilience patterns
  - Shared patterns library
  - Architectural rule enforcement
  - Module independence verification

  **✅ PHASE 2 COMPLETE** - API Design & Communication
  - RESTful API standardization with versioning
  - DTO implementation with comprehensive validation
  - Interactive API documentation with OpenAPI/Swagger
  - Backward compatibility and deprecation strategy

  **Next Steps:** The remaining phases (AI Workflow, Testing, DevOps) can be implemented following the same detailed approach established in Phases 1-2.

  Phase 3: AI Workflow & Real-Time Integration Readiness (2 weeks)

  Week 5: Async Infrastructure

  Day 20-21: Celery Integration

  Step 1: Set up Celery with Redis broker
  Relevant files:
  - workers/celery_app.py (new file)
  - workers/celery_config.py (new file)
  - requirements/base.txt (modify)

  Step 2: Create domains/tasks/ structure
  Relevant files:
  - domains/authentication/tasks/__init__.py (new file)
  - domains/onboarding/tasks/__init__.py (new file)
  - workers/tasks/base_task.py (new file)

  Step 3: Implement base task classes with retry logic
  Relevant files:
  - workers/tasks/base_task.py (modify)
  - application/decorators/retry.py (modify)

  Step 4: Create task registry for each domain
  Relevant files:
  - domains/authentication/tasks/send_welcome_email.py (new file)
  - domains/onboarding/tasks/generate_recommendations.py (new file)

  Step 5: Add task monitoring with Flower
  Relevant files:
  - requirements/development.txt (modify)
  - docker/docker-compose.yml (new file)

  Day 22-23: Event-Driven Architecture

  Step 1: Implement event bus using Redis Streams
  Relevant files:
  - infrastructure/messaging/event_bus.py (modify)
  - infrastructure/persistence/cache/redis_client.py (new file)

  Step 2: Create event definitions
  Relevant files:
  - domains/authentication/events/user_registered.py (modify)
  - domains/onboarding/events/onboarding_completed.py (modify)
  - domains/onboarding/events/scenario_generation_requested.py (new file)

  Step 3: Implement event handlers for each domain
  Relevant files:
  - domains/authentication/events/handlers.py (new file)
  - domains/onboarding/events/handlers.py (new file)

  Step 4: Add event sourcing for audit trail
  Relevant files:
  - infrastructure/persistence/event_store.py (new file)
  - core/patterns/event_sourcing.py (new file)

  Day 24: WebSocket Foundation

  Step 1: Add Django Channels to requirements
  Relevant files:
  - requirements/base.txt (modify)
  - config/asgi.py (modify)

  Step 2: Create websocket/ app structure
  Relevant files:
  - api/websocket/routing.py (new file)
  - api/websocket/consumers/__init__.py (new file)

  Step 3: Implement base consumer classes
  Relevant files:
  - api/websocket/consumers/base_consumer.py (new file)

  Step 4: Add connection management
  Relevant files:
  - infrastructure/messaging/websocket/connection_manager.py (new file)

  Step 5: Create WebSocket routing configuration
  Relevant files:
  - api/websocket/routing.py (modify)
  - config/asgi.py (modify)

  Week 6: AI-Ready Architecture

  Day 25-26: Async View Support

  Step 1: Create async view base classes
  Relevant files:
  - api/common/base_views.py (modify)
  - api/common/async_views.py (new file)

  Step 2: Implement streaming response support
  Relevant files:
  - api/common/streaming.py (new file)
  - api/common/responses.py (modify)

  Step 3: Add Server-Sent Events endpoint pattern
  Relevant files:
  - api/common/sse.py (new file)

  Step 4: Create async service interfaces
  Relevant files:
  - domains/authentication/services/interfaces.py (modify)
  - domains/onboarding/services/interfaces.py (modify)

  Step 5: Document async patterns
  Relevant files:
  - docs/architecture/async_patterns.md (new file)

  Day 27-28: State Management Infrastructure

  Step 1: Implement Redis-based session store
  Relevant files:
  - infrastructure/persistence/cache/session_store.py (new file)
  - infrastructure/persistence/cache/redis_client.py (modify)

  Step 2: Create conversation state manager
  Relevant files:
  - infrastructure/messaging/state_manager.py (new file)

  Step 3: Add distributed locking for state updates
  Relevant files:
  - infrastructure/persistence/cache/distributed_lock.py (new file)

  Step 4: Implement state recovery mechanisms
  Relevant files:
  - infrastructure/messaging/state_recovery.py (new file)

  Step 5: Create state debugging tools
  Relevant files:
  - scripts/debug/state_inspector.py (new file)

  Phase 4: Testing, Debugging & DevOps (1.5 weeks)

  Week 7: Testing Infrastructure

  Day 29-30: Unit Testing Framework

  Step 1: Create tests/ structure mirroring domains/
  Relevant files:
  - tests/unit/domains/authentication/test_models.py (new file)
  - tests/unit/domains/authentication/test_use_cases.py (new file)
  - tests/unit/domains/onboarding/test_models.py (new file)
  - tests/unit/domains/onboarding/test_use_cases.py (new file)

  Step 2: Implement test fixtures and factories
  Relevant files:
  - tests/fixtures/users.py (new file)
  - tests/fixtures/test_data.py (new file)

  Step 3: Create mock service implementations
  Relevant files:
  - tests/mocks/services.py (modify)
  - tests/mocks/repositories.py (modify)

  Step 4: Add pytest configuration
  Relevant files:
  - pytest.ini (new file)
  - tests/conftest.py (modify)

  Step 5: Achieve 80% code coverage target
  Relevant files:
  - .coveragerc (new file)
  - pyproject.toml (modify)

  Day 31-32: Integration Testing

  Step 1: Set up test database with migrations
  Relevant files:
  - config/settings/testing.py (new file)
  - tests/integration/test_database.py (new file)

  Step 2: Create API client test utilities
  Relevant files:
  - tests/utils/api_client.py (new file)

  Step 3: Implement end-to-end test scenarios
  Relevant files:
  - tests/e2e/test_user_journey.py (new file)
  - tests/integration/test_auth_flow.py (new file)

  Step 4: Add performance benchmarks
  Relevant files:
  - tests/performance/benchmarks.py (new file)

  Step 5: Create test data generators
  Relevant files:
  - tests/fixtures/generators.py (new file)

  Week 8: Observability & DevOps

  Day 33-34: Structured Logging

  Step 1: Implement structured logging with structlog
  Relevant files:
  - infrastructure/monitoring/logging_config.py (new file)
  - config/settings/base.py (modify)

  Step 2: Add request correlation IDs
  Relevant files:
  - application/middleware/correlation_id.py (new file)

  Step 3: Create logging middleware
  Relevant files:
  - application/middleware/logging_middleware.py (new file)

  Step 4: Add performance metrics collection
  Relevant files:
  - infrastructure/monitoring/metrics.py (new file)

  Step 5: Integrate with monitoring tools
  Relevant files:
  - infrastructure/monitoring/tracing.py (new file)

  Day 35: Environment Management

  Step 1: Create environment-specific settings
  Relevant files:
  - config/settings/base.py (modify)
  - config/settings/development.py (modify)
  - config/settings/staging.py (modify)
  - config/settings/production.py (modify)

  Step 2: Add configuration validation
  Relevant files:
  - config/settings/validation.py (new file)

  Step 3: Create deployment configurations
  Relevant files:
  - docker/Dockerfile (new file)
  - docker/Dockerfile.dev (new file)
  - .github/workflows/deploy.yml (new file)

  Step 4: Add health check endpoints
  Relevant files:
  - api/common/health.py (new file)
  - infrastructure/monitoring/health_checks.py (new file)

  Step 5: Document deployment process
  Relevant files:
  - docs/development/deployment.md (new file)
  - README.md (modify)
