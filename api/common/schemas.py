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