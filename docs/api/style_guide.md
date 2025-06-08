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