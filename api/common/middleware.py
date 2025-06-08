from django.http import HttpRequest, JsonResponse
from pydantic import ValidationError
import json
import re

class APIVersionMiddleware:
    """Extract and validate API version from URL"""
    
    VERSION_REGEX = re.compile(r'^/api/v(\d+)/')
    SUPPORTED_VERSIONS = ['1', '2']
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request: HttpRequest):
        # Extract API version from path
        match = self.VERSION_REGEX.match(request.path)
        
        if match:
            version = match.group(1)
            if version in self.SUPPORTED_VERSIONS:
                request.api_version = f'v{version}'
            else:
                # Invalid version
                request.api_version = None
        else:
            # No version specified, use default
            request.api_version = 'v1'
        
        response = self.get_response(request)
        
        # Add version header to response
        if hasattr(request, 'api_version'):
            response['X-API-Version'] = request.api_version
        
        return response


class DTOValidationMiddleware:
    """Automatically validate request bodies against DTOs"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Only process JSON requests
        if request.content_type == 'application/json' and request.body:
            try:
                # Parse JSON body
                request.json = json.loads(request.body)
            except json.JSONDecodeError as e:
                return JsonResponse({
                    "error": {
                        "code": "INVALID_JSON",
                        "message": "Invalid JSON in request body",
                        "details": [{"error": str(e)}]
                    }
                }, status=400)
        
        response = self.get_response(request)
        return response