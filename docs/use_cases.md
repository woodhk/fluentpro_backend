# Use Cases Documentation

This document provides comprehensive documentation for all use cases in the FluentPro backend.

## Table of Contents

- [Authentication Domain](#authentication-domain)
  - [AuthenticateUserUseCase](#authenticateuserusecase)
  - [RegisterUserUseCase](#registeruserusecase)
- [Onboarding Domain](#onboarding-domain)
  - [CompleteOnboardingFlowUseCase](#completeonboardingflowusecase)
  - [MatchUserRoleFromDescription](#matchuserrolefromdescription)
  - [SelectCommunicationPartnersUseCase](#selectcommunicationpartnersusecase)
  - [SelectNativeLanguage](#selectnativelanguage)
  - [SelectUserIndustry](#selectuserindustry)
  - [StartOnboardingSessionUseCase](#startonboardingsessionusecase)

---

## Authentication Domain

### AuthenticateUserUseCase

**File:** `domains/authentication/use_cases/authenticate_user.py`

**Description:**
Authenticates a user with email and password.

**Signature:**
```python
execute(self, ...)
```

**Flow:**
1. 1. Authenticate user via Auth0 service
2. 2. Verify user exists in Supabase database
3. 3. Check if user account is active
4. 4. Generate user and token response objects
5. 5. Return authentication response with tokens

**Errors:**
- AuthenticationError: Invalid email/password or deactivated account
- SupabaseUserNotFoundError: User authenticated but not in database
- BusinessLogicError: General authentication process failure

**Dependencies:**
- IAuthService: For Auth0 authentication
- IUserRepository: To verify user existence and status

---

### RegisterUserUseCase

**File:** `domains/authentication/use_cases/register_user.py`

**Description:**
Registers a new user in the system.

**Signature:**
```python
execute(self, ...)
```

**Flow:**
1. 1. Check if user already exists in database
2. 2. Create user in Auth0 with email and password
3. 3. Save user record in Supabase database
4. 4. Authenticate user to get initial tokens
5. 5. Return authentication response with user data

**Errors:**
- ValidationError: Invalid registration data
- ConflictError: User with email already exists
- Auth0Error: Failed to create user in Auth0
- BusinessLogicError: General registration process failure

**Dependencies:**
- IAuthService: For Auth0 user creation and authentication
- IUserRepository: To check existence and save user data

---

## Onboarding Domain

### CompleteOnboardingFlowUseCase

**File:** `domains/onboarding/use_cases/complete_onboarding_flow.py`

**Description:**
Completes the user onboarding flow and generates a summary.

**Signature:**
```python
execute(self, ...)
```

**Flow:**
1. 1. Extract user ID from session ID
2. 2. Retrieve user profile with all onboarding data
3. 3. Validate all required onboarding steps are completed
4. 4. Update user's onboarding status to completed
5. 5. Gather all onboarding selections (language, industry, role, partners)
6. 6. Generate comprehensive onboarding summary
7. 7. Return summary with completion timestamp

**Errors:**
- SupabaseUserNotFoundError: User not found in database
- BusinessLogicError: Missing required onboarding data or completion failed

**Dependencies:**
- IUserRepository: To retrieve and update user profile
- IPartnerRepository: To fetch selected partner details
- IOnboardingService: For onboarding completion business logic

---

### MatchUserRoleFromDescription

**File:** `domains/onboarding/use_cases/match_user_role_from_description.py`

**Description:**
Matches existing roles to a user's job description using AI.

**Signature:**
```python
execute(self, ...)
```

**Flow:**
1. 1. Generate embedding from job description using OpenAI
2. 2. Search for similar roles in Azure Cognitive Search
3. 3. Apply industry filter if provided
4. 4. Filter results by minimum relevancy score (70%)
5. 5. Rank and limit results to requested maximum
6. 6. Return list of matched roles with scores

**Errors:**
- AzureOpenAIError: Failed to generate job description embedding
- AzureSearchError: Failed to search for matching roles
- BusinessLogicError: General role matching failure

**Dependencies:**
- IAzureCognitiveSearchClient: For semantic role search
- IOpenAIClient: For embedding generation

---

### SelectCommunicationPartnersUseCase

**File:** `domains/onboarding/use_cases/select_communication_partners.py`

**Description:**
Selects communication partners for user's English practice scenarios.

**Signature:**
```python
execute(self, ...)
```

**Flow:**
1. 1. Validate at least one partner is selected
2. 2. Find user to ensure they exist
3. 3. Resolve partner IDs (supports both UUIDs and slugs)
4. 4. Validate all partner IDs exist and are active
5. 5. Save partner selections to repository
6. 6. Convert saved data to domain objects with priority
7. 7. Return list of partner selections

**Errors:**
- ValidationError: No partners selected or invalid partner IDs
- SupabaseUserNotFoundError: User not found in database
- BusinessLogicError: Failed to save partner selections

**Dependencies:**
- IPartnerRepository: To validate partners and save selections
- IUserRepository: To verify user exists
- IProfileSetupService: For profile setup business logic

---

### SelectNativeLanguage

**File:** `domains/onboarding/use_cases/select_native_language.py`

**Description:**
Selects and assigns a native language to a user profile.

**Signature:**
```python
execute(self, ...)
```

**Flow:**
1. 1. Validate language code against NativeLanguage enum
2. 2. Find user by Auth0 ID
3. 3. Update user profile with selected native language
4. 4. Return success response with language selection

**Errors:**
- ValidationError: Invalid language code not in enum
- SupabaseUserNotFoundError: User not found by Auth0 ID
- BusinessLogicError: Failed to update native language

**Dependencies:**
- IUserRepository: To find and update user profile

---

### SelectUserIndustry

**File:** `domains/onboarding/use_cases/select_user_industry.py`

**Description:**
Selects and assigns an industry to a user profile.

**Signature:**
```python
execute(self, ...)
```

**Flow:**
1. 1. Validate industry selection (either ID or name required)
2. 2. Look up industry by ID or name in repository
3. 3. Find user by Auth0 ID
4. 4. Update user profile with selected industry
5. 5. Return success response with industry details

**Errors:**
- ValidationError: Missing industry or invalid industry ID/name
- SupabaseUserNotFoundError: User not found by Auth0 ID
- BusinessLogicError: Failed to update user industry

**Dependencies:**
- IUserRepository: To find and update user profile
- IIndustryRepository: To validate and retrieve industry data

---

### StartOnboardingSessionUseCase

**File:** `domains/onboarding/use_cases/start_onboarding_session.py`

**Description:**
Starts or resumes an onboarding session for a user.

**Signature:**
```python
execute(self, ...)
```

**Flow:**
1. 1. Retrieve user profile to check onboarding status
2. 2. Determine current onboarding phase from user data
3. 3. Create onboarding flow instance with progress
4. 4. Update flow steps based on completed items
5. 5. Generate session ID and calculate expiration
6. 6. Return session response with current step and progress

**Errors:**
- SupabaseUserNotFoundError: User not found in database
- BusinessLogicError: Failed to create onboarding session

**Dependencies:**
- IUserRepository: To retrieve user profile and onboarding status

---
