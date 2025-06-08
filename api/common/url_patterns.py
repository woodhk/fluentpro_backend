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