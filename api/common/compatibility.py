from django.http import JsonResponse
import json
from typing import Dict, Any

class BackwardCompatibilityMiddleware:
    """Handle backward compatibility transformations"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.transformations = {
            'v1': self._transform_v1_response,
            'v2': self._transform_v2_response
        }
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Apply version-specific transformations
        if hasattr(request, 'api_version') and response.get('content-type') == 'application/json':
            transformation = self.transformations.get(request.api_version)
            if transformation:
                response = transformation(response, request)
        
        return response
    
    def _transform_v1_response(self, response, request):
        """Transform response for v1 compatibility"""
        if response.status_code == 200:
            try:
                data = json.loads(response.content)
                
                # V1 format: flatten data structure
                if 'data' in data:
                    flattened = data['data']
                    flattened['_meta'] = data.get('meta', {})
                    
                    response.content = json.dumps(flattened)
            except (json.JSONDecodeError, KeyError):
                pass
        
        return response
    
    def _transform_v2_response(self, response, request):
        """V2 is current format, no transformation needed"""
        return response