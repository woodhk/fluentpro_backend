# Phase 2 Refactoring Examples

This document demonstrates how to use the new business logic layer created in Phase 2.

## Using the New Business Logic Architecture

### Example 1: Refactored SignUp View

#### Before (640 lines of mixed concerns):
```python
# authentication/views.py (old monolithic approach)
class SignUpView(APIView):
    def post(self, request):
        # 100+ lines of validation, service calls, error handling mixed together
        serializer = SignUpSerializer(data=request.data)
        if not serializer.is_valid():
            # Manual error formatting
        
        try:
            auth0_service = Auth0Service()
            supabase_service = SupabaseService()
            # Manual Auth0 user creation
            # Manual Supabase user creation
            # Manual token generation
            # Manual error handling
        except Exception as e:
            # Repetitive error handling
```

#### After (Clean business logic separation):
```python
# authentication/views/auth_views.py (new structured approach)
from core.mixins import PublicBaseView
from core.responses import APIResponse
from authentication.use_cases.signup_user import SignUpUserUseCase

class SignUpView(PublicBaseView):
    
    def post(self, request):
        signup_use_case = SignUpUserUseCase()
        
        try:
            result = signup_use_case.execute(request.data)
            return APIResponse.created(
                data=result,
                message="User registered successfully"
            )
        except Exception as e:
            # Exception handling is centralized in the base class
            raise
```

### Example 2: Refactored Role Matching

#### Before (Complex view with business logic):
```python
# authentication/views.py (old approach - 200+ lines)
class JobInputView(APIView):
    def post(self, request):
        # Manual validation
        # Manual service initialization
        # Manual embedding generation
        # Manual search operations
        # Manual role creation logic
        # Manual error handling
        # 200+ lines of mixed concerns
```

#### After (Clean use case orchestration):
```python
# authentication/views/role_views.py (new approach)
from core.mixins import BaseFluentProView
from core.responses import APIResponse
from authentication.use_cases.role_matching import RoleMatchingUseCase

class JobInputView(BaseFluentProView):
    
    def post(self, request):
        role_matching = RoleMatchingUseCase()
        auth0_id = self.get_auth0_user_id()
        
        # Extract and validate data
        job_title = request.data.get('job_title', '').strip()
        job_description = request.data.get('job_description', '').strip()
        hierarchy_level = request.data.get('hierarchy_level', 'associate')
        
        result = role_matching.find_matching_roles(
            auth0_id=auth0_id,
            job_title=job_title,
            job_description=job_description,
            hierarchy_level=hierarchy_level
        )
        
        return APIResponse.success(result)

class RoleSelectionView(BaseFluentProView):
    
    def post(self, request):
        role_matching = RoleMatchingUseCase()
        auth0_id = self.get_auth0_user_id()
        role_id = request.data.get('role_id')
        
        result = role_matching.select_existing_role(auth0_id, role_id)
        
        return APIResponse.success(result)

class NewRoleCreationView(BaseFluentProView):
    
    def post(self, request):
        role_matching = RoleMatchingUseCase()
        auth0_id = self.get_auth0_user_id()
        
        result = role_matching.create_custom_role(
            auth0_id=auth0_id,
            job_title=request.data.get('job_title'),
            job_description=request.data.get('job_description'),
            hierarchy_level=request.data.get('hierarchy_level', 'associate')
        )
        
        return APIResponse.created(result)
```

### Example 3: Domain Model Usage

#### Working with User Domain Models:
```python
# Example: Using the User domain model
from authentication.models.user import User, UserProfile, OnboardingStatus

# Create user from Supabase data
user = User.from_supabase_data(supabase_response)

# Check user properties
if user.is_adult:
    print(f"User {user.full_name} is {user.age} years old")

# Work with user profile
profile = UserProfile.from_supabase_data(profile_data)

# Check onboarding progress
if profile.has_completed_basic_info:
    print(f"Progress: {profile.onboarding_progress_percentage}%")

# Advance onboarding status
profile.advance_onboarding_status(OnboardingStatus.INDUSTRY_SELECTED)
```

#### Working with Role Domain Models:
```python
# Example: Using Role domain models
from authentication.models.role import Role, JobDescription, RoleMatch

# Create job description for matching
job_desc = JobDescription(
    title="Software Engineer",
    description="Develop web applications using Python and React",
    hierarchy_level=HierarchyLevel.ASSOCIATE
)

# Work with role matches
role_matches = role_manager.find_matching_roles(job_desc, industry_filter="Technology")

for match in role_matches:
    if match.is_excellent_match:
        print(f"Excellent match: {match.role.title} (score: {match.relevance_score})")
    elif match.is_good_match:
        print(f"Good match: {match.role.title}")
```

### Example 4: Business Manager Usage

#### User Management:
```python
# Example: Using UserManager
from authentication.business.user_manager import UserManager

user_manager = UserManager()

# Get user profile
profile = user_manager.get_user_profile(auth0_id)

# Update native language with validation
result = user_manager.update_native_language(auth0_id, "chinese_traditional")

# Check feature access
can_access = user_manager.can_access_feature(auth0_id, OnboardingStatus.ROLE_SELECTED)
```

#### Role Management:
```python
# Example: Using RoleManager
from authentication.business.role_manager import RoleManager

role_manager = RoleManager()

# Find matching roles
matches = role_manager.find_matching_roles(job_description, industry_filter="Healthcare")

# Create custom role
custom_role = role_manager.create_custom_role(
    job_description=job_desc,
    industry_id=industry_id,
    created_by_user_id=user_id
)

# Get role statistics
stats = role_manager.get_role_statistics()
```

### Example 5: Exception Handling

#### Before (Manual error handling everywhere):
```python
try:
    # Business logic
    result = some_operation()
    return Response(result, status=200)
except Exception as e:
    logger.error(f"Operation failed: {str(e)}")
    return Response({
        'error': 'Operation failed',
        'message': str(e)
    }, status=500)
```

#### After (Centralized exception handling):
```python
# Exceptions are automatically handled by BaseFluentProView
from core.exceptions import ValidationError, SupabaseUserNotFoundError

def some_view_method(self):
    # Just raise domain-specific exceptions
    if not valid_data:
        raise ValidationError("Invalid input data")
    
    user = user_manager.get_user_profile(auth0_id)
    if not user:
        raise SupabaseUserNotFoundError(auth0_id)
    
    # Exceptions are automatically converted to proper API responses
    return result
```

## Benefits Achieved in Phase 2

### 1. **Clear Separation of Concerns**
- **Views**: Only HTTP concerns and request/response handling
- **Use Cases**: Complex business workflows and orchestration
- **Managers**: Domain-specific business logic
- **Models**: Data validation and business rules
- **Services**: External system integration

### 2. **Improved Testability**
```python
# Easy to test business logic in isolation
def test_user_signup():
    signup_use_case = SignUpUserUseCase(
        auth_manager=MockAuthManager(),
        user_manager=MockUserManager()
    )
    
    result = signup_use_case.execute(valid_registration_data)
    
    assert result['success'] == True
    assert 'user' in result
    assert 'tokens' in result
```

### 3. **Domain-Driven Design**
- Rich domain models with business logic
- Clear business rules and validation
- Expressive APIs that match business language

### 4. **Better Error Handling**
- Domain-specific exceptions
- Automatic error conversion to API responses
- Consistent error formats across all endpoints

### 5. **Easier Maintenance**
- Business logic changes isolated to specific managers
- Views become thin wrappers around use cases
- Clear dependency injection for services

## File Structure After Phase 2

```
authentication/
├── models/                 # Domain models
│   ├── user.py            # User, UserProfile domain models
│   ├── auth.py            # Authentication domain models  
│   └── role.py            # Role, Industry domain models
├── business/              # Business logic managers
│   ├── user_manager.py    # User CRUD and profile management
│   ├── auth_manager.py    # Authentication workflows
│   └── role_manager.py    # Role matching and management
├── use_cases/             # Complex business workflows
│   ├── signup_user.py     # Complete signup orchestration
│   ├── authenticate_user.py # Login workflow
│   └── role_matching.py   # Role matching workflow
├── views/                 # Thin HTTP handlers (to be created)
│   ├── auth_views.py      # Login, signup, logout
│   ├── user_views.py      # Profile management
│   └── role_views.py      # Role selection and creation
└── services/              # External system integration
    ├── auth0_service.py   # Auth0 integration
    ├── supabase_service.py # Supabase integration
    └── azure_*_service.py # Azure services
```

## Migration Strategy

1. **Start with new endpoints** - Use the new architecture for any new features
2. **Gradually refactor existing views** - One endpoint at a time
3. **Keep old views during transition** - Maintain backward compatibility
4. **Update tests to use business logic** - Test managers and use cases directly
5. **Remove old views once migrated** - Clean up after successful migration

This Phase 2 refactoring provides a solid foundation for maintainable, testable, and scalable business logic while keeping views clean and focused.