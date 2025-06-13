Onboarding Progress Tracking API Testing Documentation

  This document outlines the complete curl-based testing process for the FluentPro onboarding progress tracking system, including user creation, JWT token generation, and endpoint testing.

  Prerequisites

  - Access to the FluentPro backend API at https://fluentpro-backend.onrender.com
  - Python 3 for JWT token generation
  - Supabase access for database verification
  - Understanding of the onboarding flow structure

  Overview of Testing Process

  The testing process follows this sequence:
  1. Create a new user via signup API
  2. Generate a test JWT token for authentication
  3. Test all onboarding endpoints in sequence
  4. Verify progress tracking in database

  Step 1: User Creation

  Create User Data File

  # Create JSON file with user data
  echo '{
    "full_name": "Test User Progress",
    "email": "testprogress@example.com",
    "password": "TestPassword123@",
    "date_of_birth": "1990-01-01"
  }' > /tmp/signup_data.json

  Create User via Signup API

  curl -X POST "https://fluentpro-backend.onrender.com/api/v1/auth/signup" \
    -H "Content-Type: application/json" \
    -d @/tmp/signup_data.json

  Expected Response:
  {
    "success": true,
    "message": "User created successfully",
    "user_id": "d84dad33-bb3e-4dbe-9964-5929822d26fc"
  }

  Verify User in Database

  -- Check user was created with Auth0 ID
  SELECT id, full_name, email, auth0_id, native_language, industry_id, selected_role_id
  FROM users
  WHERE email = 'testprogress@example.com';

  Step 2: JWT Token Generation

  Since the system uses Auth0 JWT tokens but verification is disabled in development, we can create test tokens:

  Generate Test JWT Token

  python3 -c "
  import json
  import base64

  # Create test JWT payload matching expected format
  header = {'typ': 'JWT', 'alg': 'HS256'}
  payload = {
      'sub': 'auth0|684c26b278bc64b837aafc44',  # Use actual Auth0 ID from database
      'email': 'testprogress@example.com',
      'name': 'Test User Progress',
      'email_verified': True,
      'iss': 'https://dev-47g5ypdrz64lekwg.us.auth0.com/',
      'aud': 'https://api.fluentpro.com',
      'iat': 1640995200,
      'exp': 9999999999  # Far future expiration
  }

  # Base64 encode header and payload
  header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
  payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')

  # Create JWT with fake signature (verification disabled in dev)
  jwt_token = f'{header_b64}.{payload_b64}.fake_signature'
  print(jwt_token)
  "

  Store the generated token for use in subsequent requests.

  Step 3: Onboarding Endpoint Testing

  Part 1: Core Profile Setup

  3.1 Set Native Language

  curl -X POST "https://fluentpro-backend.onrender.com/api/v1/onboarding/part-1/native-language" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE" \
    -d '{"native_language": "english"}'

  Expected Response:
  {
    "success": true,
    "message": "Native language set to english",
    "data": null,
    "timestamp": "2025-06-13T13:36:41.207362",
    "native_language": "english"
  }

  Database Verification:
  -- Check progress tracking
  SELECT current_step, data FROM user_onboarding_progress
  WHERE user_id = 'YOUR_USER_ID';

  -- Check user profile update
  SELECT native_language FROM users
  WHERE email = 'testprogress@example.com';

  3.2 Set Industry

  # First, check available industries
  curl -X GET "https://fluentpro-backend.onrender.com/api/v1/onboarding/part-1/industries" \
    -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"

  # Set industry (using enum value)
  curl -X POST "https://fluentpro-backend.onrender.com/api/v1/onboarding/part-1/industry" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE" \
    -d '{"industry": "shipping_logistics"}'

  Expected Response:
  {
    "success": true,
    "message": "Industry set to shipping_logistics",
    "data": null,
    "timestamp": "2025-06-13T13:36:41.207362",
    "industry": "shipping_logistics"
  }

  3.3 Search for Roles

  curl -X POST "https://fluentpro-backend.onrender.com/api/v1/onboarding/part-1/search-roles" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE" \
    -d '{
      "job_title": "shipping and logistics operator",
      "job_description": "Responsible for coordinating shipments, managing inventory, and ensuring timely delivery of goods. Works with suppliers, transporters, and customers to optimize logistics 
  operations."
    }'

  Expected Response:
  {
    "success": true,
    "message": "Found 2 matching roles",
    "data": null,
    "timestamp": "2025-06-13T13:36:41.207362",
    "matches": [
      {
        "id": "e02c5a84-0c29-4d6e-b882-e363f97ed488",
        "title": "Logistics Coordinator",
        "description": "Coordinate shipping operations, manage supply chain logistics...",
        "industry_name": "Shipping & Logistics",
        "confidence_score": 0.8437564
      }
    ],
    "search_id": null
  }

  3.4 Select Role

  curl -X POST "https://fluentpro-backend.onrender.com/api/v1/onboarding/part-1/select-role" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE" \
    -d '{"role_id": "e02c5a84-0c29-4d6e-b882-e363f97ed488"}'

  Expected Response:
  {
    "success": true,
    "message": "Role selected successfully",
    "data": null,
    "timestamp": "2025-06-13T13:36:41.207362",
    "role_id": "e02c5a84-0c29-4d6e-b882-e363f97ed488",
    "is_custom": false
  }

  Part 2: Communication Preferences

  3.5 Get Available Communication Partners

  curl -X GET "https://fluentpro-backend.onrender.com/api/v1/onboarding/part-2/communication-partners" \
    -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"

  3.6 Select Communication Partners

  curl -X POST "https://fluentpro-backend.onrender.com/api/v1/onboarding/part-2/select-partners" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE" \
    -d '{
      "partner_ids": [
        "21ef7d7d-336f-4d45-9ce1-3139407135f2",
        "cfdb398d-a61d-46e3-b23b-d321dc1ce141",
        "60b4fffd-df0d-4916-a789-9fc303a7313f"
      ]
    }'

  Expected Response:
  {
    "success": true,
    "message": "Selected 3 communication partners",
    "data": null,
    "timestamp": "2025-06-13T13:36:41.207362",
    "selected_count": 3,
    "partner_selections": [...]
  }

  3.7 Get Situations for Partner

  curl -X GET "https://fluentpro-backend.onrender.com/api/v1/onboarding/part-2/situations/21ef7d7d-336f-4d45-9ce1-3139407135f2" \
    -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"

  3.8 Select Situations for Partner

  curl -X POST "https://fluentpro-backend.onrender.com/api/v1/onboarding/part-2/select-situations" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE" \
    -d '{
      "partner_id": "21ef7d7d-336f-4d45-9ce1-3139407135f2",
      "situation_ids": [
        "f3c4329c-c2ac-4c6b-9f71-cdd88dfad294",
        "c47ba504-4812-4568-9319-3a3aaca30d87",
        "def02870-d662-4f0e-b9f5-9696a318c97b"
      ]
    }'

  3.9 Part 2 Summary (Review Only - No Progress Tracking)

  curl -X GET "https://fluentpro-backend.onrender.com/api/v1/onboarding/part-2/summary" \
    -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"

  Part 3: Final Summary & Completion

  3.10 Part 3 Summary (WITH Progress Tracking)

  curl -X GET "https://fluentpro-backend.onrender.com/api/v1/onboarding/part-3/summary" \
    -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"

  Expected Response:
  {
    "success": true,
    "message": "Onboarding summary retrieved successfully",
    "data": null,
    "timestamp": "2025-06-13T13:51:01.182084",
    "summary": {
      "native_language": "english",
      "native_language_display": "English",
      "industry_id": "78b10bf2-e514-4c38-a174-060eaac13cf1",
      "industry_name": "Shipping & Logistics",
      "role": {...},
      "communication_partners": [...],
      "total_partners": 3,
      "total_situations": 5,
      "onboarding_status": "pending",
      "is_complete": false
    }
  }

  3.11 Complete Onboarding

  curl -X POST "https://fluentpro-backend.onrender.com/api/v1/onboarding/part-3/complete" \
    -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"

  Expected Response:
  {
    "success": true,
    "message": "Onboarding completed successfully!",
    "data": null,
    "timestamp": "2025-06-13T14:02:26.846982",
    "onboarding_status": "completed",
    "next_steps": "You can now access your personalized learning content."
  }

  Step 4: Progress Verification

  Check Final Progress State

  SELECT current_step, completed, data
  FROM user_onboarding_progress
  WHERE user_id = 'YOUR_USER_ID';

  Expected Final State:
  {
    "current_step": "completed",
    "completed": true,
    "data": {
      "set_native_language": {"native_language": "english"},
      "set_industry": {"industry": "shipping_logistics", "industry_id": "..."},
      "search_roles": {"job_title": "...", "matches_found": 2},
      "select_role": {"selected_role_id": "...", "is_custom": false},
      "select_communication_partners": {"partner_ids": [...], "selected_count": 3},
      "select_situations": {"partner_id": "...", "situation_ids": [...], "count": 2},
      "view_summary": {"viewed_at": "now()"},
      "complete_onboarding": {"completed_at": "now()"}
    }
  }

  Verify Database Updates

  -- Check user profile was updated
  SELECT native_language, industry_id, selected_role_id
  FROM users
  WHERE email = 'testprogress@example.com';

  -- Check communication partners were created
  SELECT COUNT(*) as partner_count
  FROM user_communication_partners
  WHERE user_id = 'YOUR_USER_ID';

  -- Check situations were created
  SELECT COUNT(*) as situation_count
  FROM user_partner_units
  WHERE user_id = 'YOUR_USER_ID';

  Progress Step Mapping

  The onboarding flow progresses through these steps:

  1. not_started → native_language (Part 1)
  2. native_language → industry_selection (Part 1)
  3. industry_selection → role_input (Part 1)
  4. role_input → role_selection (Part 1)
  5. role_selection → communication_partners (Part 2)
  6. communication_partners → situation_selection (Part 2)
  7. situation_selection → summary (Part 3)
  8. summary → completed (Part 3)

  Important Notes

  1. JWT Token Security: In production, use proper Auth0 authentication. The fake tokens only work because JWT verification is disabled in development.
  2. Progress Tracking: Only specific endpoints track progress:
    - Part 1: All endpoints track progress
    - Part 2: Partner/situation selection track progress, but summary does NOT
    - Part 3: Both summary and complete track progress
  3. Error Handling: If an endpoint fails, check:
    - JWT token format and Auth0 ID
    - Request body schema matches expected format
    - User exists and has required previous steps completed
  4. Database Constraints: The system uses foreign key constraints, so ensure:
    - Industry IDs exist in industries table
    - Role IDs exist in roles table
    - Partner/situation IDs exist in their respective tables

  This comprehensive testing process ensures the onboarding progress tracking system works correctly end-to-end.