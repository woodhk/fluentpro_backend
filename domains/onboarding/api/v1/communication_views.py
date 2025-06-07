"""
Communication needs selection views for FluentPro v1.
Handles communication partner and unit selection during onboarding.
"""

from rest_framework import status
import logging

from core.view_base import AuthenticatedView, VersionedView, CachedView
from core.responses import APIResponse
from core.exceptions import ValidationError
from onboarding.business.communication_manager import CommunicationManager

logger = logging.getLogger(__name__)


class GetCommunicationPartnersView(CachedView, VersionedView):
    """
    Get available communication partners endpoint.
    Returns list of communication partners for selection.
    """
    cache_timeout = 1800  # 30 minutes cache
    
    def get(self, request):
        """Get available communication partners."""
        try:
            # Check cache first
            cache_key = self.get_cache_key("partners")
            cached_partners = self.get_cached_response(cache_key)
            
            if cached_partners:
                return APIResponse.success(data=cached_partners)
            
            # Get partners using communication manager
            communication_manager = CommunicationManager()
            partners = communication_manager.get_available_partners()
            
            # Create reverse mapping for slugs
            name_to_slug = {v: k for k, v in communication_manager.PARTNER_SLUG_TO_NAME.items()}
            
            # Format response
            formatted_partners = []
            for partner in partners:
                formatted_partners.append({
                    'id': partner.id,
                    'slug': name_to_slug.get(partner.name, partner.name.lower().replace(' ', '-')),
                    'name': partner.name,
                    'description': partner.description
                })
            
            response_data = {'communication_partners': formatted_partners}
            
            # Cache the response
            self.set_cached_response(cache_key, response_data)
            
            return APIResponse.success(data=response_data)
            
        except Exception as e:
            logger.error(f"Get communication partners error: {str(e)}")
            return APIResponse.error(
                message="Failed to get communication partners",
                details=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SelectCommunicationPartnersView(AuthenticatedView, VersionedView):
    """
    Select communication partners endpoint.
    Phase 2 Step 1: User selects their communication partners.
    """
    
    def post(self, request):
        """Select communication partners."""
        try:
            partner_ids = request.data.get('partner_ids', [])
            other_partners = request.data.get('other_partners', [])
            
            if not partner_ids and not other_partners:
                raise ValidationError("At least one communication partner must be selected")
            
            # Get current user
            user = self.get_current_user()
            
            # Use communication manager to save selections
            communication_manager = CommunicationManager()
            selections = communication_manager.save_partner_selections(
                user_id=user.id,
                partner_ids=partner_ids,
                custom_partners=other_partners
            )
            
            # Format response
            stored_partners = []
            for selection in selections:
                stored_partners.append({
                    'id': selection.communication_partner_id if not selection.is_custom else None,
                    'name': selection.display_name,
                    'priority': selection.priority,
                    'is_custom': selection.is_custom
                })
            
            return APIResponse.success(
                data={
                    'message': 'Communication partners selected successfully',
                    'selected_partners': stored_partners,
                    'total_selected': len(stored_partners)
                }
            )
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Select communication partners error: {str(e)}")
            return APIResponse.error(
                message="Failed to select communication partners",
                details=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetUserCommunicationPartnersView(AuthenticatedView, VersionedView):
    """
    Get user's selected communication partners endpoint.
    Returns user's selected partners for unit selection flow.
    """
    
    def get(self, request):
        """Get user's selected communication partners."""
        try:
            # Get current user
            user = self.get_current_user()
            
            # Get user's selected partners
            communication_manager = CommunicationManager()
            selections = communication_manager.get_user_partners(user.id)
            
            # Format response
            partners = []
            for selection in selections:
                partners.append({
                    'id': selection.communication_partner_id if not selection.is_custom else None,
                    'name': selection.display_name,
                    'description': selection.custom_partner_description if selection.is_custom else 'Standard communication partner',
                    'priority': selection.priority,
                    'is_custom': selection.is_custom
                })
            
            return APIResponse.success(
                data={'communication_partners': partners}
            )
            
        except Exception as e:
            logger.error(f"Get user communication partners error: {str(e)}")
            return APIResponse.error(
                message="Failed to get user communication partners",
                details=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetUnitsForPartnerView(CachedView, VersionedView):
    """
    Get available units for a specific communication partner.
    Returns list of communication units/situations.
    """
    cache_timeout = 1800  # 30 minutes cache
    
    def get(self, request, partner_id):
        """Get available units for a communication partner."""
        try:
            # Resolve partner_id (handle both UUIDs and slugs)
            communication_manager = CommunicationManager()
            if len(partner_id) != 36 or '-' not in partner_id:
                # It's a slug, resolve to UUID
                resolved_partner_ids = communication_manager._resolve_partner_ids([partner_id])
                partner_id = resolved_partner_ids[0]
                
            # Check cache first
            cache_key = self.get_cache_key("units", partner_id)
            cached_units = self.get_cached_response(cache_key)
            
            if cached_units:
                return APIResponse.success(data=cached_units)
            
            # Get units using communication manager
            units = communication_manager.get_available_units()
            
            # Get partner name for context
            partners = communication_manager.get_available_partners()
            partner = next((p for p in partners if p.id == partner_id), None)
            partner_name = partner.name if partner else "Unknown Partner"
            
            # Create reverse mapping for unit slugs
            unit_name_to_slug = {v: k for k, v in communication_manager.UNIT_SLUG_TO_NAME.items()}
            
            # Format response
            formatted_units = []
            for unit in units:
                formatted_units.append({
                    'id': unit.id,
                    'slug': unit_name_to_slug.get(unit.name, unit.name.lower().replace(' ', '-')),
                    'name': unit.name,
                    'description': unit.description
                })
            
            response_data = {
                'partner_id': partner_id,
                'partner_name': partner_name,
                'units': formatted_units
            }
            
            # Cache the response
            self.set_cached_response(cache_key, response_data)
            
            return APIResponse.success(data=response_data)
            
        except Exception as e:
            logger.error(f"Get units for partner error: {str(e)}")
            return APIResponse.error(
                message="Failed to get units for partner",
                details=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SelectUnitsForPartnerView(AuthenticatedView, VersionedView):
    """
    Select units for a specific communication partner.
    Phase 2 Step 2+: User selects units/situations for a partner.
    """
    
    def post(self, request, partner_id):
        """Select units for a communication partner."""
        try:
            # Handle different request formats
            unit_selections = request.data.get('unit_selections', [])
            unit_ids = request.data.get('unit_ids', [])
            other_units = request.data.get('other_units', [])
            
            # If frontend sends unit_selections format, extract unit_ids
            if unit_selections and not unit_ids:
                unit_ids = [selection.get('unit_id') for selection in unit_selections if selection.get('unit_id')]
                # Filter out None values
                unit_ids = [uid for uid in unit_ids if uid is not None]
            
            # Resolve partner_id (handle both UUIDs and slugs)
            communication_manager = CommunicationManager()
            if len(partner_id) != 36 or '-' not in partner_id:
                # It's a slug, resolve to UUID
                resolved_partner_ids = communication_manager._resolve_partner_ids([partner_id])
                partner_id = resolved_partner_ids[0]
            
            if not unit_ids and not other_units:
                raise ValidationError("At least one unit must be selected")
            
            # Get current user
            user = self.get_current_user()
            
            # Validate partner belongs to user (now using resolved partner_id)
            user_partners = communication_manager.get_user_partners(user.id)
            
            if not any(p.communication_partner_id == partner_id for p in user_partners):
                return APIResponse.error(
                    message="Partner not found in user's selected partners",
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            # Save unit selections
            selections = communication_manager.save_unit_selections(
                user_id=user.id,
                partner_id=partner_id,
                unit_ids=unit_ids,
                custom_units=other_units
            )
            
            # Format response
            stored_units = []
            for selection in selections:
                stored_units.append({
                    'id': selection.unit_id if not selection.is_custom else None,
                    'name': selection.display_name,
                    'priority': selection.priority,
                    'is_custom': selection.is_custom
                })
            
            # Get partner name for response
            partners = communication_manager.get_available_partners()
            partner = next((p for p in partners if p.id == partner_id), None)
            partner_name = partner.name if partner else "Unknown Partner"
            
            return APIResponse.success(
                data={
                    'message': f'Units selected successfully for {partner_name}',
                    'partner_id': partner_id,
                    'partner_name': partner_name,
                    'selected_units': stored_units,
                    'total_selected': len(stored_units)
                }
            )
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Select units for partner error: {str(e)}")
            return APIResponse.error(
                message="Failed to select units for partner",
                details=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetUserUnitsForPartnerView(AuthenticatedView, VersionedView):
    """
    Get user's selected units for a specific communication partner.
    Returns user's unit selections for a partner.
    """
    
    def get(self, request, partner_id):
        """Get user's selected units for a communication partner."""
        try:
            # Resolve partner_id (handle both UUIDs and slugs)
            communication_manager = CommunicationManager()
            if len(partner_id) != 36 or '-' not in partner_id:
                # It's a slug, resolve to UUID
                resolved_partner_ids = communication_manager._resolve_partner_ids([partner_id])
                partner_id = resolved_partner_ids[0]
            
            # Get current user
            user = self.get_current_user()
            
            # Validate partner belongs to user
            user_partners = communication_manager.get_user_partners(user.id)
            
            partner_selection = next(
                (p for p in user_partners if p.communication_partner_id == partner_id), 
                None
            )
            
            if not partner_selection:
                return APIResponse.error(
                    message="Partner not found in user's selected partners",
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            # Get user's unit selections for this partner
            unit_selections = communication_manager.get_user_units(user.id, partner_id)
            
            # Format response
            units = []
            for selection in unit_selections:
                units.append({
                    'id': selection.unit_id if not selection.is_custom else None,
                    'name': selection.display_name,
                    'description': selection.custom_unit_description if selection.is_custom else 'Standard communication unit',
                    'priority': selection.priority,
                    'is_custom': selection.is_custom
                })
            
            return APIResponse.success(
                data={
                    'partner': {
                        'id': partner_selection.communication_partner_id,
                        'name': partner_selection.display_name,
                        'description': partner_selection.custom_partner_description if partner_selection.is_custom else 'Standard communication partner'
                    },
                    'selected_units': units,
                    'total_selected': len(units)
                }
            )
            
        except Exception as e:
            logger.error(f"Get user units for partner error: {str(e)}")
            return APIResponse.error(
                message="Failed to get user units for partner",
                details=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )