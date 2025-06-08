Comprehensive Implementation Plan for FluentPro Backend Refactoring

  Phase 2: API Design and Communication (1 week)

  Week 4: RESTful API Standardization

  Day 17-18: DTO Implementation

  ## Goal
  Implement a comprehensive DTO (Data Transfer Object) layer to decouple API contracts from domain models and ensure consistent data validation.

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
