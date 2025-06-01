from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from authentication.backends import Auth0JWTAuthentication
from authentication.services.supabase_service import SupabaseService
from django.views.decorators.csrf import csrf_exempt
import json


@csrf_exempt
@api_view(['POST'])
@authentication_classes([Auth0JWTAuthentication])
@permission_classes([IsAuthenticated])
def set_native_language(request):
    """
    API endpoint for Phase 1 onboarding: Set user's native language
    Expected payload: {"native_language": "chinese_traditional"}
    """
    try:
        data = json.loads(request.body)
        native_language = data.get('native_language')
        
        if not native_language:
            return Response(
                {"error": "native_language is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Validate native_language against allowed values
        allowed_languages = ['english', 'chinese_traditional', 'chinese_simplified']
        if native_language not in allowed_languages:
            return Response(
                {"error": f"native_language must be one of: {', '.join(allowed_languages)}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get user info from Auth0 token
        auth0_id = request.user.get('sub')  # Auth0 user ID from JWT
        
        if not auth0_id:
            return Response(
                {"error": "Invalid authentication"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Update user's native language in Supabase
        supabase_service = SupabaseService()
        result = supabase_service.update_user_native_language(auth0_id, native_language)
        
        if result.get('success'):
            return Response({
                "message": "Native language updated successfully",
                "native_language": native_language,
                "user_id": result.get('user_id')
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": result.get('error', 'Failed to update native language')}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except json.JSONDecodeError:
        return Response(
            {"error": "Invalid JSON payload"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {"error": f"Internal server error: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@authentication_classes([Auth0JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_available_languages(request):
    """
    API endpoint to get available native languages for selection
    """
    languages = [
        {"value": "english", "label": "English"},
        {"value": "chinese_traditional", "label": "Chinese Traditional"},
        {"value": "chinese_simplified", "label": "Chinese Simplified"}
    ]
    
    return Response({
        "languages": languages
    }, status=status.HTTP_200_OK)