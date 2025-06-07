"""
Onboarding DTO mappers.
These mappers handle conversion between domain models and DTOs.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from onboarding.models.onboarding import OnboardingSession, OnboardingProgress
from onboarding.models.communication import (
    CommunicationPartner,
    Unit,
    UserCommunicationPartnerSelection,
    UserUnitSelection
)
from authentication.models.role import Role, RoleMatch

from domains.onboarding.dto.responses import (
    OnboardingSessionResponse,
    OnboardingStep,
    OnboardingSessionStatus,
    IndustryOption,
    RoleOption,
    RoleMatchResponse,
    CommunicationPartnerOption,
    CommunicationUnitOption,
    OnboardingStepResponse,
    OnboardingSummaryResponse
)


class OnboardingSessionMapper:
    """Mapper for OnboardingSession model to DTOs."""
    
    @staticmethod
    def to_response(session: OnboardingSession) -> OnboardingSessionResponse:
        """Convert OnboardingSession model to OnboardingSessionResponse DTO."""
        # Map current step from model to DTO enum
        step_mapping = {
            'language': OnboardingStep.LANGUAGE_SELECTION,
            'industry': OnboardingStep.INDUSTRY_SELECTION,
            'role': OnboardingStep.ROLE_SELECTION,
            'partners': OnboardingStep.PARTNER_SELECTION,
            'situations': OnboardingStep.SITUATION_CONFIGURATION,
            'complete': OnboardingStep.COMPLETION
        }
        
        # Map status
        status_mapping = {
            'active': OnboardingSessionStatus.ACTIVE,
            'paused': OnboardingSessionStatus.PAUSED,
            'completed': OnboardingSessionStatus.COMPLETED,
            'expired': OnboardingSessionStatus.EXPIRED
        }
        
        # Build progress dict
        progress = {
            OnboardingStep.LANGUAGE_SELECTION.value: session.progress.language_selected,
            OnboardingStep.INDUSTRY_SELECTION.value: session.progress.industry_selected,
            OnboardingStep.ROLE_SELECTION.value: session.progress.role_selected,
            OnboardingStep.PARTNER_SELECTION.value: session.progress.partners_selected,
            OnboardingStep.SITUATION_CONFIGURATION.value: session.progress.situations_configured
        }
        
        return OnboardingSessionResponse(
            session_id=session.id,
            user_id=session.user_id,
            current_step=step_mapping.get(session.current_step, OnboardingStep.LANGUAGE_SELECTION),
            status=status_mapping.get(session.status, OnboardingSessionStatus.ACTIVE),
            started_at=session.created_at,
            expires_at=session.expires_at,
            progress=progress
        )
    
    @staticmethod
    def to_step_response(
        session_id: str,
        completed_step: str,
        next_step: Optional[str],
        progress: OnboardingProgress,
        message: str = "Step completed successfully"
    ) -> OnboardingStepResponse:
        """Create OnboardingStepResponse for a completed step."""
        step_mapping = {
            'language': OnboardingStep.LANGUAGE_SELECTION,
            'industry': OnboardingStep.INDUSTRY_SELECTION,
            'role': OnboardingStep.ROLE_SELECTION,
            'partners': OnboardingStep.PARTNER_SELECTION,
            'situations': OnboardingStep.SITUATION_CONFIGURATION,
            'complete': OnboardingStep.COMPLETION
        }
        
        progress_dict = {
            OnboardingStep.LANGUAGE_SELECTION.value: progress.language_selected,
            OnboardingStep.INDUSTRY_SELECTION.value: progress.industry_selected,
            OnboardingStep.ROLE_SELECTION.value: progress.role_selected,
            OnboardingStep.PARTNER_SELECTION.value: progress.partners_selected,
            OnboardingStep.SITUATION_CONFIGURATION.value: progress.situations_configured
        }
        
        return OnboardingStepResponse(
            session_id=session_id,
            completed_step=step_mapping.get(completed_step, OnboardingStep.LANGUAGE_SELECTION),
            next_step=step_mapping.get(next_step) if next_step else None,
            progress=progress_dict,
            message=message
        )


class IndustryMapper:
    """Mapper for Industry data to DTOs."""
    
    @staticmethod
    def to_option(industry_data: Dict[str, Any]) -> IndustryOption:
        """Convert industry data to IndustryOption DTO."""
        return IndustryOption(
            id=industry_data['id'],
            name=industry_data['name'],
            description=industry_data.get('description'),
            role_count=industry_data.get('role_count', 0)
        )
    
    @staticmethod
    def to_option_list(industries: List[Dict[str, Any]]) -> List[IndustryOption]:
        """Convert list of industry data to list of IndustryOption DTOs."""
        return [IndustryMapper.to_option(industry) for industry in industries]


class RoleMapper:
    """Mapper for Role model to onboarding DTOs."""
    
    @staticmethod
    def to_option(role: Role, relevance_score: Optional[float] = None) -> RoleOption:
        """Convert Role model to RoleOption DTO."""
        return RoleOption(
            id=role.id,
            title=role.title,
            description=role.description,
            hierarchy_level=role.hierarchy_level.value,
            relevance_score=relevance_score
        )
    
    @staticmethod
    def to_option_list(roles: List[Role]) -> List[RoleOption]:
        """Convert list of Role models to list of RoleOption DTOs."""
        return [RoleMapper.to_option(role) for role in roles]
    
    @staticmethod
    def to_match_response(
        matches: List[RoleMatch],
        confidence_score: float = 0.0
    ) -> RoleMatchResponse:
        """Convert RoleMatch results to RoleMatchResponse DTO."""
        role_options = [
            RoleMapper.to_option(match.role, match.relevance_score)
            for match in matches
        ]
        
        suggested_role = role_options[0] if role_options else None
        
        return RoleMatchResponse(
            matches=role_options,
            suggested_role=suggested_role,
            confidence_score=confidence_score or (matches[0].relevance_score if matches else 0.0)
        )


class CommunicationMapper:
    """Mapper for Communication models to DTOs."""
    
    @staticmethod
    def partner_to_option(partner: CommunicationPartner) -> CommunicationPartnerOption:
        """Convert CommunicationPartner model to CommunicationPartnerOption DTO."""
        return CommunicationPartnerOption(
            id=partner.id,
            name=partner.name,
            description=partner.description,
            icon=partner.icon
        )
    
    @staticmethod
    def partners_to_options(partners: List[CommunicationPartner]) -> List[CommunicationPartnerOption]:
        """Convert list of CommunicationPartner models to list of DTOs."""
        return [CommunicationMapper.partner_to_option(partner) for partner in partners]
    
    @staticmethod
    def unit_to_option(unit: Unit) -> CommunicationUnitOption:
        """Convert Unit model to CommunicationUnitOption DTO."""
        return CommunicationUnitOption(
            id=unit.id,
            name=unit.name,
            description=unit.description,
            example_phrases=unit.example_phrases if hasattr(unit, 'example_phrases') else None
        )
    
    @staticmethod
    def units_to_options(units: List[Unit]) -> List[CommunicationUnitOption]:
        """Convert list of Unit models to list of DTOs."""
        return [CommunicationMapper.unit_to_option(unit) for unit in units]


class OnboardingSummaryMapper:
    """Mapper for creating onboarding summary responses."""
    
    @staticmethod
    def to_summary_response(
        user_id: str,
        profile_data: Dict[str, Any],
        completed_at: Optional[datetime] = None
    ) -> OnboardingSummaryResponse:
        """Create OnboardingSummaryResponse from profile data."""
        # Extract profile summary
        profile_summary = {
            "native_language": profile_data.get("native_language"),
            "proficiency_level": profile_data.get("proficiency_level"),
            "industry": profile_data.get("industry_name"),
            "role": profile_data.get("role_title"),
            "communication_partners": profile_data.get("partner_names", []),
            "total_situations": profile_data.get("total_situations", 0)
        }
        
        # Generate recommendations based on profile
        recommendations = OnboardingSummaryMapper._generate_recommendations(profile_data)
        
        # Define next steps
        next_steps = [
            "Complete your first lesson",
            "Set up daily practice reminders",
            "Explore practice scenarios for your role",
            "Connect with other learners in your industry"
        ]
        
        return OnboardingSummaryResponse(
            user_id=user_id,
            completed_at=completed_at or datetime.utcnow(),
            profile_summary=profile_summary,
            recommendations=recommendations,
            next_steps=next_steps
        )
    
    @staticmethod
    def _generate_recommendations(profile_data: Dict[str, Any]) -> List[str]:
        """Generate personalized recommendations based on user profile."""
        recommendations = []
        
        # Based on proficiency level
        proficiency = profile_data.get("proficiency_level", "").lower()
        if proficiency in ["beginner", "elementary"]:
            recommendations.append("Start with basic vocabulary and common phrases")
            recommendations.append("Focus on pronunciation and listening exercises")
        elif proficiency in ["intermediate", "upper_intermediate"]:
            recommendations.append("Practice complex sentence structures")
            recommendations.append("Work on industry-specific terminology")
        
        # Based on role
        if profile_data.get("role_title"):
            recommendations.append(f"Explore scenarios specific to {profile_data['role_title']} role")
        
        # Based on partners
        partner_names = profile_data.get("partner_names", [])
        if "Clients" in partner_names or "Customers" in partner_names:
            recommendations.append("Practice professional email writing and phone conversations")
        if "Executives" in partner_names or "Board" in partner_names:
            recommendations.append("Focus on presentation skills and executive communication")
        
        return recommendations[:4]  # Limit to 4 recommendations