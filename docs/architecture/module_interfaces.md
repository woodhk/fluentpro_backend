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