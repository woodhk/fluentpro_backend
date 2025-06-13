Testing Onboarding Progress Feature - User Authentication Guide
This guide focuses on creating a new user and obtaining authentication for testing the onboarding progress feature on the deployed server.
Prerequisites

Access to the deployed server at https://fluentpro-backend.onrender.com
Supabase MCP tool for database verification
curl for making HTTP requests
Python for generating test JWT tokens

Important Note
The deployed API has JWT verification disabled for testing purposes. This allows us to create simple JWT tokens without going through the full Auth0 flow.
Step 1: Create a New User
1.1 Prepare the signup request
Create a JSON file with user details:
bashcat > /tmp/signup_request.json << EOF
{
  "email": "test.user@example.com",
  "password": "SecurePassword123!",
  "full_name": "Test User"
}
EOF
1.2 Send the signup request
bashcurl -X POST https://fluentpro-backend.onrender.com/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d @/tmp/signup_request.json
Expected response:
json{
  "success": true,
  "message": "User created successfully",
  "user_id": "d0af4236-edcf-467c-be16-c6c2e5421f76",
  "auth0_id": "auth0|684c359a76f59c7dcff28e72"
}
Save the auth0_id from the response - you'll need it for creating the JWT token.
Step 2: Verify User Creation in Database
Use Supabase MCP to verify the user was created:
sqlSELECT * FROM users WHERE email = 'test.user@example.com';
Also check that onboarding progress was initialized:
sqlSELECT * FROM user_onboarding_progress WHERE user_id = '[USER_ID_FROM_SIGNUP]';
You should see:

User record with all fields populated
Onboarding progress record with current_step = 'not_started' and completed = false

Step 3: Create a Test JWT Token
Since the system uses Auth0 but JWT verification is disabled on the deployed server, create a simple JWT token:
3.1 Create a Python script
python#!/usr/bin/env python3
import jwt
import json
import time

# Use the auth0_id from the signup response
auth0_id = "auth0|684c359a76f59c7dcff28e72"  # Replace with your actual auth0_id

payload = {
    "sub": auth0_id,
    "email": "test.user@example.com",
    "name": "Test User",
    "email_verified": True,
    "iss": "https://dev-47g5ypdrz64lekwg.us.auth0.com/",
    "aud": "https://api.fluentpro.com",
    "iat": int(time.time()),
    "exp": int(time.time()) + 3600  # Token expires in 1 hour
}

# Create token with a simple secret (only works because JWT verification is disabled)
token = jwt.encode(payload, "test-secret", algorithm="HS256")
print(token)
3.2 Generate the token
bashpython3 create_jwt.py
This will output a JWT token that you can use for authenticated requests.
Step 4: Test Authentication
Verify the token works by checking auth status:
bashTOKEN="[YOUR_GENERATED_TOKEN]"

curl -X GET https://fluentpro-backend.onrender.com/api/v1/auth/status \
  -H "Authorization: Bearer $TOKEN"
Expected response:
json{
  "authenticated": true,
  "user_id": "d0af4236-edcf-467c-be16-c6c2e5421f76",
  "message": "User is authenticated"
}
Step 5: Use Token for Onboarding Tests
Now you can use this token for all authenticated onboarding endpoints:
bash# Example: Set native language
curl -X POST https://fluentpro-backend.onrender.com/api/v1/onboarding/part-1/native-language \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"native_language": "english"}'
Common Issues and Solutions
Issue: JSON parsing error in signup
json{"detail": [{"type": "json_invalid", ...}]}
Solution: Ensure your JSON is properly formatted. Use a file instead of inline JSON.
Issue: Authentication fails
json{"authenticated": false, "message": "Invalid token"}
Solution:

Ensure you're using the correct auth0_id from the signup response
Check that the token hasn't expired
Verify you're including "Bearer " prefix in the Authorization header

Issue: No login endpoint found
Explanation: The system uses Auth0 for authentication. In production, users authenticate through Auth0 and receive JWT tokens. For testing on the deployed server with JWT verification disabled, we create tokens manually.
Summary
This authentication approach works specifically for the deployed test environment where JWT verification is disabled. In production:

Users would authenticate through Auth0
Auth0 would issue properly signed JWT tokens
The backend would verify these tokens against Auth0's public keys

For testing purposes, this simplified approach allows you to:

Create test users quickly
Generate working JWT tokens without Auth0 integration
Test the complete onboarding flow with proper authentication