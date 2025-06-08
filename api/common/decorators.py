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