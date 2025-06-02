from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from authentication.backends import Auth0JWTAuthentication
from authentication.services.supabase_service import SupabaseService
from authentication.services.conversation_service import ConversationFlowService
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


@csrf_exempt
@api_view(['POST'])
@authentication_classes([Auth0JWTAuthentication])
@permission_classes([IsAuthenticated])
def start_conversation(request):
    """
    API endpoint for Phase 2 onboarding: Start conversation flow
    Expected payload: {} (empty - uses user data from Phase 1)
    """
    try:
        # Get user info from Auth0 token
        auth0_id = request.user.get('sub')
        
        if not auth0_id:
            return Response(
                {"error": "Invalid authentication"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get user data from Supabase
        supabase_service = SupabaseService()
        user = supabase_service.get_user_by_auth0_id(auth0_id)
        
        if not user:
            return Response(
                {"error": "User not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user has completed Phase 1
        if not user.get('native_language') or not user.get('industry_id') or not user.get('selected_role_id'):
            return Response(
                {"error": "Please complete Phase 1 onboarding first"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get industry and role information
        industry_response = supabase_service.client.table('industries').select('name').eq('id', user['industry_id']).execute()
        role_response = supabase_service.client.table('roles').select('title').eq('id', user['selected_role_id']).execute()
        
        if not industry_response.data or not role_response.data:
            return Response(
                {"error": "User's industry or role not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        industry_name = industry_response.data[0]['name']
        role_title = role_response.data[0]['title']
        
        # Start conversation
        conversation_service = ConversationFlowService()
        result = conversation_service.start_conversation(
            user_name=user['full_name'],
            role=role_title,
            industry=industry_name,
            native_language=user['native_language']
        )
        
        if result.get('success'):
            return Response({
                "message": "Conversation started successfully",
                "ai_response": result.get('ai_response'),
                "conversation_state": result.get('conversation_state'),
                "user_context": {
                    "name": user['full_name'],
                    "role": role_title,
                    "industry": industry_name,
                    "native_language": user['native_language']
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": result.get('error', 'Failed to start conversation')}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except Exception as e:
        return Response(
            {"error": f"Internal server error: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@api_view(['POST'])
@authentication_classes([Auth0JWTAuthentication])
@permission_classes([IsAuthenticated])
def continue_conversation(request):
    """
    API endpoint for Phase 2 onboarding: Continue conversation flow
    Expected payload: {
        "message": "user's response",
        "conversation_state": {...}
    }
    """
    try:
        data = json.loads(request.body)
        user_message = data.get('message')
        conversation_state = data.get('conversation_state')
        
        if not user_message:
            return Response(
                {"error": "message is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not conversation_state:
            return Response(
                {"error": "conversation_state is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get user info from Auth0 token
        auth0_id = request.user.get('sub')
        
        if not auth0_id:
            return Response(
                {"error": "Invalid authentication"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get user data from Supabase
        supabase_service = SupabaseService()
        user = supabase_service.get_user_by_auth0_id(auth0_id)
        
        if not user:
            return Response(
                {"error": "User not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get industry and role information
        industry_response = supabase_service.client.table('industries').select('name').eq('id', user['industry_id']).execute()
        role_response = supabase_service.client.table('roles').select('title').eq('id', user['selected_role_id']).execute()
        
        if not industry_response.data or not role_response.data:
            return Response(
                {"error": "User's industry or role not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        industry_name = industry_response.data[0]['name']
        role_title = role_response.data[0]['title']
        
        # Continue conversation
        conversation_service = ConversationFlowService()
        result = conversation_service.process_message(
            user_message=user_message,
            user_name=user['full_name'],
            role=role_title,
            industry=industry_name,
            native_language=user['native_language'],
            conversation_state=conversation_state
        )
        
        if result.get('success'):
            response_data = {
                "message": "Conversation processed successfully",
                "ai_response": result.get('ai_response'),
                "conversation_state": result.get('conversation_state'),
                "is_finished": result.get('is_finished', False),
                "current_step": result.get('current_step', 1)
            }
            
            # If conversation is finished, save the results
            if result.get('is_finished'):
                # Here you could save the conversation results to Supabase
                # For now, we'll just include them in the response
                response_data["conversation_summary"] = {
                    "communication_partners": result.get('conversation_state', {}).get('communication_partners', []),
                    "work_situations": result.get('conversation_state', {}).get('work_situations', {}),
                    "conversation_history": result.get('conversation_state', {}).get('conversation_history', [])
                }
            
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": result.get('error', 'Failed to process conversation')}, 
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


@csrf_exempt
@api_view(['POST'])
@authentication_classes([Auth0JWTAuthentication])
@permission_classes([IsAuthenticated])
def set_industry(request):
    """
    API endpoint for Phase 1 onboarding: Set user's industry
    Expected payload: {"industry_id": "94642aff-7100-431b-a6a8-7fd741064a73"}
    """
    try:
        data = json.loads(request.body)
        industry_id = data.get('industry_id')
        
        if not industry_id:
            return Response(
                {"error": "industry_id is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get user info from Auth0 token
        auth0_id = request.user.get('sub')  # Auth0 user ID from JWT
        
        if not auth0_id:
            return Response(
                {"error": "Invalid authentication"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Update user's industry in Supabase
        supabase_service = SupabaseService()
        result = supabase_service.update_user_industry(auth0_id, industry_id)
        
        if result.get('success'):
            return Response({
                "message": "Industry updated successfully",
                "industry_id": industry_id,
                "industry_name": result.get('industry_name'),
                "user_id": result.get('user_id')
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": result.get('error', 'Failed to update industry')}, 
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


@csrf_exempt
@api_view(['POST'])
@authentication_classes([Auth0JWTAuthentication])
@permission_classes([IsAuthenticated])
def start_conversation(request):
    """
    API endpoint for Phase 2 onboarding: Start conversation flow
    Expected payload: {} (empty - uses user data from Phase 1)
    """
    try:
        # Get user info from Auth0 token
        auth0_id = request.user.get('sub')
        
        if not auth0_id:
            return Response(
                {"error": "Invalid authentication"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get user data from Supabase
        supabase_service = SupabaseService()
        user = supabase_service.get_user_by_auth0_id(auth0_id)
        
        if not user:
            return Response(
                {"error": "User not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user has completed Phase 1
        if not user.get('native_language') or not user.get('industry_id') or not user.get('selected_role_id'):
            return Response(
                {"error": "Please complete Phase 1 onboarding first"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get industry and role information
        industry_response = supabase_service.client.table('industries').select('name').eq('id', user['industry_id']).execute()
        role_response = supabase_service.client.table('roles').select('title').eq('id', user['selected_role_id']).execute()
        
        if not industry_response.data or not role_response.data:
            return Response(
                {"error": "User's industry or role not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        industry_name = industry_response.data[0]['name']
        role_title = role_response.data[0]['title']
        
        # Start conversation
        conversation_service = ConversationFlowService()
        result = conversation_service.start_conversation(
            user_name=user['full_name'],
            role=role_title,
            industry=industry_name,
            native_language=user['native_language']
        )
        
        if result.get('success'):
            return Response({
                "message": "Conversation started successfully",
                "ai_response": result.get('ai_response'),
                "conversation_state": result.get('conversation_state'),
                "user_context": {
                    "name": user['full_name'],
                    "role": role_title,
                    "industry": industry_name,
                    "native_language": user['native_language']
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": result.get('error', 'Failed to start conversation')}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except Exception as e:
        return Response(
            {"error": f"Internal server error: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@api_view(['POST'])
@authentication_classes([Auth0JWTAuthentication])
@permission_classes([IsAuthenticated])
def continue_conversation(request):
    """
    API endpoint for Phase 2 onboarding: Continue conversation flow
    Expected payload: {
        "message": "user's response",
        "conversation_state": {...}
    }
    """
    try:
        data = json.loads(request.body)
        user_message = data.get('message')
        conversation_state = data.get('conversation_state')
        
        if not user_message:
            return Response(
                {"error": "message is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not conversation_state:
            return Response(
                {"error": "conversation_state is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get user info from Auth0 token
        auth0_id = request.user.get('sub')
        
        if not auth0_id:
            return Response(
                {"error": "Invalid authentication"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get user data from Supabase
        supabase_service = SupabaseService()
        user = supabase_service.get_user_by_auth0_id(auth0_id)
        
        if not user:
            return Response(
                {"error": "User not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get industry and role information
        industry_response = supabase_service.client.table('industries').select('name').eq('id', user['industry_id']).execute()
        role_response = supabase_service.client.table('roles').select('title').eq('id', user['selected_role_id']).execute()
        
        if not industry_response.data or not role_response.data:
            return Response(
                {"error": "User's industry or role not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        industry_name = industry_response.data[0]['name']
        role_title = role_response.data[0]['title']
        
        # Continue conversation
        conversation_service = ConversationFlowService()
        result = conversation_service.process_message(
            user_message=user_message,
            user_name=user['full_name'],
            role=role_title,
            industry=industry_name,
            native_language=user['native_language'],
            conversation_state=conversation_state
        )
        
        if result.get('success'):
            response_data = {
                "message": "Conversation processed successfully",
                "ai_response": result.get('ai_response'),
                "conversation_state": result.get('conversation_state'),
                "is_finished": result.get('is_finished', False),
                "current_step": result.get('current_step', 1)
            }
            
            # If conversation is finished, save the results
            if result.get('is_finished'):
                # Here you could save the conversation results to Supabase
                # For now, we'll just include them in the response
                response_data["conversation_summary"] = {
                    "communication_partners": result.get('conversation_state', {}).get('communication_partners', []),
                    "work_situations": result.get('conversation_state', {}).get('work_situations', {}),
                    "conversation_history": result.get('conversation_state', {}).get('conversation_history', [])
                }
            
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": result.get('error', 'Failed to process conversation')}, 
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
def get_available_industries(request):
    """
    API endpoint to get available industries for selection
    """
    try:
        supabase_service = SupabaseService()
        industries = supabase_service.get_available_industries()
        
        return Response({
            "industries": industries
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {"error": f"Internal server error: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@api_view(['POST'])
@authentication_classes([Auth0JWTAuthentication])
@permission_classes([IsAuthenticated])
def start_conversation(request):
    """
    API endpoint for Phase 2 onboarding: Start conversation flow
    Expected payload: {} (empty - uses user data from Phase 1)
    """
    try:
        # Get user info from Auth0 token
        auth0_id = request.user.get('sub')
        
        if not auth0_id:
            return Response(
                {"error": "Invalid authentication"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get user data from Supabase
        supabase_service = SupabaseService()
        user = supabase_service.get_user_by_auth0_id(auth0_id)
        
        if not user:
            return Response(
                {"error": "User not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user has completed Phase 1
        if not user.get('native_language') or not user.get('industry_id') or not user.get('selected_role_id'):
            return Response(
                {"error": "Please complete Phase 1 onboarding first"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get industry and role information
        industry_response = supabase_service.client.table('industries').select('name').eq('id', user['industry_id']).execute()
        role_response = supabase_service.client.table('roles').select('title').eq('id', user['selected_role_id']).execute()
        
        if not industry_response.data or not role_response.data:
            return Response(
                {"error": "User's industry or role not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        industry_name = industry_response.data[0]['name']
        role_title = role_response.data[0]['title']
        
        # Start conversation
        conversation_service = ConversationFlowService()
        result = conversation_service.start_conversation(
            user_name=user['full_name'],
            role=role_title,
            industry=industry_name,
            native_language=user['native_language']
        )
        
        if result.get('success'):
            return Response({
                "message": "Conversation started successfully",
                "ai_response": result.get('ai_response'),
                "conversation_state": result.get('conversation_state'),
                "user_context": {
                    "name": user['full_name'],
                    "role": role_title,
                    "industry": industry_name,
                    "native_language": user['native_language']
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": result.get('error', 'Failed to start conversation')}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except Exception as e:
        return Response(
            {"error": f"Internal server error: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@api_view(['POST'])
@authentication_classes([Auth0JWTAuthentication])
@permission_classes([IsAuthenticated])
def continue_conversation(request):
    """
    API endpoint for Phase 2 onboarding: Continue conversation flow
    Expected payload: {
        "message": "user's response",
        "conversation_state": {...}
    }
    """
    try:
        data = json.loads(request.body)
        user_message = data.get('message')
        conversation_state = data.get('conversation_state')
        
        if not user_message:
            return Response(
                {"error": "message is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not conversation_state:
            return Response(
                {"error": "conversation_state is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get user info from Auth0 token
        auth0_id = request.user.get('sub')
        
        if not auth0_id:
            return Response(
                {"error": "Invalid authentication"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get user data from Supabase
        supabase_service = SupabaseService()
        user = supabase_service.get_user_by_auth0_id(auth0_id)
        
        if not user:
            return Response(
                {"error": "User not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get industry and role information
        industry_response = supabase_service.client.table('industries').select('name').eq('id', user['industry_id']).execute()
        role_response = supabase_service.client.table('roles').select('title').eq('id', user['selected_role_id']).execute()
        
        if not industry_response.data or not role_response.data:
            return Response(
                {"error": "User's industry or role not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        industry_name = industry_response.data[0]['name']
        role_title = role_response.data[0]['title']
        
        # Continue conversation
        conversation_service = ConversationFlowService()
        result = conversation_service.process_message(
            user_message=user_message,
            user_name=user['full_name'],
            role=role_title,
            industry=industry_name,
            native_language=user['native_language'],
            conversation_state=conversation_state
        )
        
        if result.get('success'):
            response_data = {
                "message": "Conversation processed successfully",
                "ai_response": result.get('ai_response'),
                "conversation_state": result.get('conversation_state'),
                "is_finished": result.get('is_finished', False),
                "current_step": result.get('current_step', 1)
            }
            
            # If conversation is finished, save the results
            if result.get('is_finished'):
                # Here you could save the conversation results to Supabase
                # For now, we'll just include them in the response
                response_data["conversation_summary"] = {
                    "communication_partners": result.get('conversation_state', {}).get('communication_partners', []),
                    "work_situations": result.get('conversation_state', {}).get('work_situations', {}),
                    "conversation_history": result.get('conversation_state', {}).get('conversation_history', [])
                }
            
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": result.get('error', 'Failed to process conversation')}, 
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