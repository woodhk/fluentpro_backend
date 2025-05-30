# Fluentpro Backend

A Django REST API backend for the Fluentpro iOS application, featuring Auth0 authentication and Supabase data storage.

## Features

- 🔐 **Auth0 Integration**: Secure JWT-based authentication
- 💾 **Supabase Database**: Cloud-hosted PostgreSQL database
- 🌐 **REST API**: RESTful endpoints for user management
- 🔒 **CORS Support**: Configured for iOS app integration
- 📱 **Mobile-Ready**: Optimized for mobile app backends

## API Endpoints

### Authentication Endpoints

All authentication endpoints are under the `/api/v1/auth/` prefix:

#### 1. User Sign Up
- **Endpoint**: `POST /api/v1/auth/signup/`
- **Description**: Register a new user
- **Authentication**: Not required

**Request Body:**
```json
{
    "full_name": "John Doe",
    "email": "john.doe@example.com",
    "password": "SecurePass123!",
    "date_of_birth": "1990-01-15"
}
```

**Response (201 Created):**
```json
{
    "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "user": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "full_name": "John Doe",
        "email": "john.doe@example.com",
        "date_of_birth": "1990-01-15"
    }
}
```

#### 2. User Login
- **Endpoint**: `POST /api/v1/auth/login/`
- **Description**: Authenticate an existing user
- **Authentication**: Not required

**Request Body:**
```json
{
    "email": "john.doe@example.com",
    "password": "SecurePass123!"
}
```

**Response (200 OK):**
```json
{
    "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "user": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "full_name": "John Doe",
        "email": "john.doe@example.com",
        "date_of_birth": "1990-01-15"
    }
}
```

#### 3. Refresh Token
- **Endpoint**: `POST /api/v1/auth/refresh/`
- **Description**: Get a new access token using refresh token
- **Authentication**: Not required

**Request Body:**
```json
{
    "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
    "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600
}
```

#### 4. User Logout
- **Endpoint**: `POST /api/v1/auth/logout/`
- **Description**: Revoke refresh token and log out user
- **Authentication**: Required (Bearer token)

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
    "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
    "message": "Successfully logged out"
}
```

#### 5. User Profile
- **Endpoint**: `GET /api/v1/auth/profile/`
- **Description**: Get current user's profile information
- **Authentication**: Required (Bearer token)

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "full_name": "John Doe",
    "email": "john.doe@example.com",
    "date_of_birth": "1990-01-15",
    "created_at": "2025-05-30T10:30:00Z",
    "updated_at": "2025-05-30T10:30:00Z"
}
```

#### 6. Health Check
- **Endpoint**: `GET /api/v1/auth/health/`
- **Description**: Check API health status
- **Authentication**: Not required

**Response (200 OK):**
```json
{
    "status": "healthy",
    "service": "fluentpro-backend",
    "version": "1.0.0",
    "environment": "production",
    "auth0_configured": true,
    "supabase_configured": true
}
```

### Error Responses

All endpoints may return error responses in the following format:

**400 Bad Request:**
```json
{
    "error": "Validation failed",
    "details": {
        "email": ["This field is required."],
        "password": ["Password must contain at least one uppercase letter"]
    }
}
```

**401 Unauthorized:**
```json
{
    "error": "Invalid credentials",
    "message": "Email or password is incorrect"
}
```

**409 Conflict:**
```json
{
    "error": "User already exists",
    "message": "A user with this email already exists"
}
```

**500 Internal Server Error:**
```json
{
    "error": "Internal server error",
    "message": "An unexpected error occurred"
}
```

## Local Development

### Prerequisites

- Python 3.8+
- pip
- Virtual environment

### Setup

1. Clone the repository
2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create `.env` file based on `.env.example`
5. Configure Auth0 and Supabase credentials
6. Run the development server:
   ```bash
   python manage.py runserver
   ```

### Validation Rules

#### Sign Up Validation:
- **Full Name**: 2-50 characters, letters and spaces only
- **Email**: Valid email format
- **Password**: Minimum 8 characters with uppercase, lowercase, number, and special character
- **Date of Birth**: User must be at least 13 years old

#### Login Validation:
- **Email**: Valid email format
- **Password**: Required

## Authentication Flow

1. **Sign Up**: User creates account → Auth0 user created → Supabase user record created → JWT tokens returned
2. **Login**: User credentials verified with Auth0 → User data fetched from Supabase → JWT tokens returned
3. **API Requests**: Include `Authorization: Bearer <access_token>` header
4. **Token Refresh**: Use refresh token to get new access token when expired
5. **Logout**: Revoke refresh token in Auth0

## Production Deployment

See `DEPLOYMENT.md` for detailed deployment instructions.# fluentpro_backend
