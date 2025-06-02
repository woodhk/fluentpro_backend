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


# Phase 2: Structured Communication Needs Collection

@api_view(['GET'])
@authentication_classes([Auth0JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_communication_partners(request):
    """
    API endpoint to get available communication partners for selection
    """
    try:
        supabase_service = SupabaseService()
        
        # Get all active communication partners from database
        response = supabase_service.client.table('communication_partners')\
            .select('id, name, description')\
            .eq('is_active', True)\
            .order('name')\
            .execute()
        
        partners = []
        for partner in response.data:
            partners.append({
                "id": partner['id'],
                "name": partner['name'],
                "description": partner['description']
            })
        
        return Response({
            "communication_partners": partners
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
def select_communication_partners(request):
    """
    API endpoint for Phase 2 Step 1: User selects their communication partners
    Expected payload: {
        "partner_ids": ["uuid1", "uuid2", "uuid3"],
        "other_partners": ["Custom Partner 1", "Custom Partner 2"]  # optional
    }
    """
    try:
        data = json.loads(request.body)
        partner_ids = data.get('partner_ids', [])
        other_partners = data.get('other_partners', [])
        
        if not partner_ids and not other_partners:
            return Response(
                {"error": "At least one communication partner must be selected"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get user info from Auth0 token
        auth0_id = request.user.get('sub')
        if not auth0_id:
            return Response(
                {"error": "Invalid authentication"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        supabase_service = SupabaseService()
        
        # Get user ID
        user = supabase_service.get_user_by_auth0_id(auth0_id)
        if not user:
            return Response(
                {"error": "User not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        user_id = user['id']
        
        # Validate partner IDs exist
        if partner_ids:
            partners_response = supabase_service.client.table('communication_partners')\
                .select('id, name')\
                .in_('id', partner_ids)\
                .eq('is_active', True)\
                .execute()
            
            valid_partner_ids = [p['id'] for p in partners_response.data]
            invalid_ids = [pid for pid in partner_ids if pid not in valid_partner_ids]
            
            if invalid_ids:
                return Response(
                    {"error": f"Invalid partner IDs: {invalid_ids}"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Clear existing user communication partners
        supabase_service.client.table('user_communication_partners')\
            .delete()\
            .eq('user_id', user_id)\
            .execute()
        
        # Store selected partners with priority
        stored_partners = []
        priority = 1
        
        # Store database partners
        for partner_id in partner_ids:
            result = supabase_service.client.table('user_communication_partners').insert({
                'user_id': user_id,
                'communication_partner_id': partner_id,
                'priority': priority
            }).execute()
            
            if result.data:
                partner_info = next(p for p in partners_response.data if p['id'] == partner_id)
                stored_partners.append({
                    'id': partner_id,
                    'name': partner_info['name'],
                    'priority': priority,
                    'is_custom': False
                })
                priority += 1
        
        # Store custom "other" partners in user needs table for now
        # (These will be handled separately as they're user-specific)
        for other_partner in other_partners:
            if other_partner.strip():
                stored_partners.append({
                    'name': other_partner.strip(),
                    'priority': priority,
                    'is_custom': True
                })
                priority += 1
        
        return Response({
            "message": "Communication partners selected successfully",
            "selected_partners": stored_partners,
            "total_selected": len(stored_partners)
        }, status=status.HTTP_200_OK)
        
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
def get_user_communication_partners(request):
    """
    API endpoint to get user's selected communication partners for unit selection flow
    """
    try:
        # Get user info from Auth0 token
        auth0_id = request.user.get('sub')
        if not auth0_id:
            return Response(
                {"error": "Invalid authentication"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        supabase_service = SupabaseService()
        
        # Get user ID
        user = supabase_service.get_user_by_auth0_id(auth0_id)
        if not user:
            return Response(
                {"error": "User not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        user_id = user['id']
        
        # Get user's selected communication partners
        response = supabase_service.client.table('user_communication_partners')\
            .select('*, communication_partners(id, name, description)')\
            .eq('user_id', user_id)\
            .order('priority')\
            .execute()
        
        partners = []
        for item in response.data:
            partners.append({
                'id': item['communication_partners']['id'],
                'name': item['communication_partners']['name'],
                'description': item['communication_partners']['description'],
                'priority': item['priority']
            })
        
        return Response({
            "communication_partners": partners
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {"error": f"Internal server error: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@authentication_classes([Auth0JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_units_for_partner(request, partner_id):
    """
    API endpoint to get available units/situations for a specific communication partner
    """
    try:
        supabase_service = SupabaseService()
        
        # Get all active units from database
        response = supabase_service.client.table('units')\
            .select('id, name, description')\
            .eq('is_active', True)\
            .order('name')\
            .execute()
        
        units = []
        for unit in response.data:
            units.append({
                "id": unit['id'],
                "name": unit['name'],
                "description": unit['description']
            })
        
        # Get partner name for context
        partner_response = supabase_service.client.table('communication_partners')\
            .select('name')\
            .eq('id', partner_id)\
            .execute()
        
        partner_name = partner_response.data[0]['name'] if partner_response.data else "Unknown Partner"
        
        return Response({
            "partner_id": partner_id,
            "partner_name": partner_name,
            "units": units
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
def select_units_for_partner(request, partner_id):
    """
    API endpoint for Phase 2 Step 2+: User selects units/situations for a specific communication partner
    Expected payload: {
        "unit_ids": ["uuid1", "uuid2", "uuid3"],
        "other_units": ["Custom Situation 1", "Custom Situation 2"]  # optional
    }
    """
    try:
        data = json.loads(request.body)
        unit_ids = data.get('unit_ids', [])
        other_units = data.get('other_units', [])
        
        if not unit_ids and not other_units:
            return Response(
                {"error": "At least one unit must be selected"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get user info from Auth0 token
        auth0_id = request.user.get('sub')
        if not auth0_id:
            return Response(
                {"error": "Invalid authentication"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        supabase_service = SupabaseService()
        
        # Get user ID
        user = supabase_service.get_user_by_auth0_id(auth0_id)
        if not user:
            return Response(
                {"error": "User not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        user_id = user['id']
        
        # Validate partner ID belongs to user
        partner_check = supabase_service.client.table('user_communication_partners')\
            .select('communication_partner_id')\
            .eq('user_id', user_id)\
            .eq('communication_partner_id', partner_id)\
            .execute()
        
        if not partner_check.data:
            return Response(
                {"error": "Partner not found in user's selected partners"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validate unit IDs exist
        if unit_ids:
            units_response = supabase_service.client.table('units')\
                .select('id, name')\
                .in_('id', unit_ids)\
                .eq('is_active', True)\
                .execute()
            
            valid_unit_ids = [u['id'] for u in units_response.data]
            invalid_ids = [uid for uid in unit_ids if uid not in valid_unit_ids]
            
            if invalid_ids:
                return Response(
                    {"error": f"Invalid unit IDs: {invalid_ids}"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Clear existing units for this user/partner combination
        supabase_service.client.table('user_partner_units')\
            .delete()\
            .eq('user_id', user_id)\
            .eq('communication_partner_id', partner_id)\
            .execute()
        
        # Store selected units with priority
        stored_units = []
        priority = 1
        
        # Store database units using the new user_partner_units table
        for unit_id in unit_ids:
            result = supabase_service.client.table('user_partner_units').insert({
                'user_id': user_id,
                'communication_partner_id': partner_id,
                'unit_id': unit_id,
                'priority': priority,
                'is_custom': False
            }).execute()
            
            if result.data:
                unit_info = next(u for u in units_response.data if u['id'] == unit_id)
                stored_units.append({
                    'id': unit_id,
                    'name': unit_info['name'],
                    'priority': priority,
                    'is_custom': False
                })
                priority += 1
        
        # Store custom "other" units using the new table structure
        for other_unit in other_units:
            if other_unit.strip():
                result = supabase_service.client.table('user_partner_units').insert({
                    'user_id': user_id,
                    'communication_partner_id': partner_id,
                    'unit_id': None,  # NULL for custom units
                    'priority': priority,
                    'is_custom': True,
                    'custom_unit_name': other_unit.strip(),
                    'custom_unit_description': f"Custom communication situation: {other_unit.strip()}"
                }).execute()
                
                if result.data:
                    stored_units.append({
                        'name': other_unit.strip(),
                        'priority': priority,
                        'is_custom': True
                    })
                    priority += 1
        
        # Get partner name for response
        partner_response = supabase_service.client.table('communication_partners')\
            .select('name')\
            .eq('id', partner_id)\
            .execute()
        partner_name = partner_response.data[0]['name'] if partner_response.data else "Unknown Partner"
        
        return Response({
            "message": f"Units selected successfully for {partner_name}",
            "partner_id": partner_id,
            "partner_name": partner_name,
            "selected_units": stored_units,
            "total_selected": len(stored_units)
        }, status=status.HTTP_200_OK)
        
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
def get_user_units_for_partner(request, partner_id):
    """
    API endpoint to get user's selected units for a specific communication partner
    """
    try:
        # Get user info from Auth0 token
        auth0_id = request.user.get('sub')
        if not auth0_id:
            return Response(
                {"error": "Invalid authentication"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        supabase_service = SupabaseService()
        
        # Get user ID
        user = supabase_service.get_user_by_auth0_id(auth0_id)
        if not user:
            return Response(
                {"error": "User not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        user_id = user['id']
        
        # Validate partner belongs to user
        partner_check = supabase_service.client.table('user_communication_partners')\
            .select('communication_partner_id')\
            .eq('user_id', user_id)\
            .eq('communication_partner_id', partner_id)\
            .execute()
        
        if not partner_check.data:
            return Response(
                {"error": "Partner not found in user's selected partners"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get user's selected units for this specific partner
        units_response = supabase_service.client.table('user_partner_units')\
            .select('*, units(id, name, description)')\
            .eq('user_id', user_id)\
            .eq('communication_partner_id', partner_id)\
            .order('priority')\
            .execute()
        
        # Get partner info
        partner_response = supabase_service.client.table('communication_partners')\
            .select('id, name, description')\
            .eq('id', partner_id)\
            .execute()
        
        partner_info = partner_response.data[0] if partner_response.data else None
        if not partner_info:
            return Response(
                {"error": "Communication partner not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        units = []
        for item in units_response.data:
            if item['is_custom']:
                # Custom unit
                units.append({
                    'name': item['custom_unit_name'],
                    'description': item['custom_unit_description'],
                    'priority': item['priority'],
                    'is_custom': True
                })
            else:
                # Database unit
                units.append({
                    'id': item['units']['id'],
                    'name': item['units']['name'],
                    'description': item['units']['description'],
                    'priority': item['priority'],
                    'is_custom': False
                })
        
        return Response({
            "partner": partner_info,
            "selected_units": units,
            "total_selected": len(units)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {"error": f"Internal server error: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@authentication_classes([Auth0JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_onboarding_summary(request):
    """
    API endpoint to get complete onboarding summary showing all selected partners and units
    """
    try:
        # Get user info from Auth0 token
        auth0_id = request.user.get('sub')
        if not auth0_id:
            return Response(
                {"error": "Invalid authentication"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        supabase_service = SupabaseService()
        
        # Get user ID and profile
        user = supabase_service.get_user_full_profile(auth0_id)
        if not user:
            return Response(
                {"error": "User not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        user_id = user['id']
        
        # Get user's selected communication partners
        partners_response = supabase_service.client.table('user_communication_partners')\
            .select('*, communication_partners(id, name, description)')\
            .eq('user_id', user_id)\
            .order('priority')\
            .execute()
        
        # Get user's selected partner-specific units using the new table
        partner_units_response = supabase_service.client.table('user_partner_units')\
            .select('*, communication_partners(id, name, description), units(id, name, description)')\
            .eq('user_id', user_id)\
            .order('communication_partner_id, priority')\
            .execute()
        
        partners = []
        for item in partners_response.data:
            partners.append({
                'id': item['communication_partners']['id'],
                'name': item['communication_partners']['name'],
                'description': item['communication_partners']['description'],
                'priority': item['priority']
            })
        
        # Group units by communication partner
        partners_with_units = []
        units_by_partner = {}
        
        # Group partner units by partner
        for item in partner_units_response.data:
            partner_id = item['communication_partner_id']
            if partner_id not in units_by_partner:
                units_by_partner[partner_id] = []
            
            if item['is_custom']:
                # Custom unit
                units_by_partner[partner_id].append({
                    'name': item['custom_unit_name'],
                    'description': item['custom_unit_description'],
                    'priority': item['priority'],
                    'is_custom': True
                })
            else:
                # Database unit
                units_by_partner[partner_id].append({
                    'id': item['units']['id'],
                    'name': item['units']['name'],
                    'description': item['units']['description'],
                    'priority': item['priority'],
                    'is_custom': False
                })
        
        # Combine partners with their units
        for partner in partners:
            partner_id = partner['id']
            partner_units = units_by_partner.get(partner_id, [])
            partners_with_units.append({
                'partner': partner,
                'units': partner_units,
                'unit_count': len(partner_units)
            })
        
        # Also create a flat list of all units for backward compatibility
        all_units = []
        for partner_units in units_by_partner.values():
            all_units.extend(partner_units)
        
        return Response({
            "user_profile": {
                "name": user['full_name'],
                "native_language": user['native_language'],
                "industry": user['industry_name'],
                "role": user['role_title'],
                "onboarding_status": user['onboarding_status']
            },
            "communication_partners": partners,
            "partners_with_units": partners_with_units,  # New: grouped by partner
            "units_situations": all_units,  # Legacy: flat list for backward compatibility
            "total_partners": len(partners),
            "total_units": len(all_units)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {"error": f"Internal server error: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )