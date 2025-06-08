import pytest
from typing import Dict, Any, List, Optional
from unittest.mock import Mock
from domains.onboarding.repositories.interfaces import IIndustryRepository, IPartnerRepository
from domains.onboarding.services.interfaces import (
    IOnboardingService, IEmbeddingService, ICompletionService,
    IRecommendationService, IProfileSetupService
)
from tests.mocks.repositories import MockIndustryRepository, MockPartnerRepository
from tests.mocks.services import MockEmbeddingService, MockCompletionService


class MockOnboardingService(IOnboardingService):
    """Mock implementation of IOnboardingService for testing"""
    
    def __init__(self):
        self.sessions = {}
        self.user_steps = {}
    
    def start_onboarding(self, user_id: str) -> Dict[str, Any]:
        session_id = f"session_{user_id}"
        self.sessions[session_id] = {
            "user_id": user_id,
            "session_id": session_id,
            "current_step": 1,
            "total_steps": 5,
            "status": "in_progress",
            "completed_steps": []
        }
        self.user_steps[user_id] = []
        return self.sessions[session_id]
    
    def get_onboarding_status(self, user_id: str) -> Dict[str, Any]:
        session_id = f"session_{user_id}"
        if session_id not in self.sessions:
            return {
                "is_completed": False,
                "current_step": None,
                "completed_steps": [],
                "remaining_steps": []
            }
        
        session = self.sessions[session_id]
        return {
            "is_completed": session["status"] == "completed",
            "current_step": session["current_step"],
            "completed_steps": session["completed_steps"],
            "remaining_steps": list(range(session["current_step"], session["total_steps"] + 1))
        }
    
    def update_step(self, user_id: str, step_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        session_id = f"session_{user_id}"
        if session_id in self.sessions:
            self.sessions[session_id]["completed_steps"].append(step_name)
            self.sessions[session_id]["current_step"] += 1
            
            if user_id not in self.user_steps:
                self.user_steps[user_id] = []
            self.user_steps[user_id].append({"step": step_name, "data": data})
            
            return {
                "success": True,
                "next_step": self.sessions[session_id]["current_step"],
                "validation_errors": []
            }
        
        return {
            "success": False,
            "next_step": None,
            "validation_errors": ["No active session"]
        }
    
    def complete_onboarding(self, user_id: str) -> bool:
        session_id = f"session_{user_id}"
        if session_id in self.sessions:
            self.sessions[session_id]["status"] = "completed"
            return True
        return False
    
    def skip_onboarding(self, user_id: str, reason: Optional[str] = None) -> bool:
        session_id = f"session_{user_id}"
        if session_id in self.sessions:
            self.sessions[session_id]["status"] = "skipped"
            self.sessions[session_id]["skip_reason"] = reason
            return True
        return False
    
    def reset_onboarding(self, user_id: str) -> bool:
        session_id = f"session_{user_id}"
        if session_id in self.sessions:
            del self.sessions[session_id]
        if user_id in self.user_steps:
            del self.user_steps[user_id]
        return True
    
    def get_onboarding_analytics(self, start_date=None, end_date=None) -> Dict[str, Any]:
        completed = sum(1 for s in self.sessions.values() if s["status"] == "completed")
        in_progress = sum(1 for s in self.sessions.values() if s["status"] == "in_progress")
        skipped = sum(1 for s in self.sessions.values() if s["status"] == "skipped")
        
        return {
            "total_sessions": len(self.sessions),
            "completed": completed,
            "in_progress": in_progress,
            "skipped": skipped,
            "completion_rate": (completed / max(len(self.sessions), 1)) * 100
        }


class MockProfileSetupService(IProfileSetupService):
    """Mock implementation of IProfileSetupService for testing"""
    
    def __init__(self):
        self.user_profiles = {}
    
    def set_industry(self, user_id: str, industry_id: str) -> bool:
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {}
        self.user_profiles[user_id]["industry_id"] = industry_id
        return True
    
    def set_job_title(self, user_id: str, job_title: str, job_description: Optional[str] = None) -> bool:
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {}
        self.user_profiles[user_id]["job_title"] = job_title
        self.user_profiles[user_id]["job_description"] = job_description
        return True
    
    def set_language_preferences(self, user_id: str, native_language: str,
                               target_languages: List[str], proficiency_levels: Dict[str, str]) -> bool:
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {}
        self.user_profiles[user_id]["native_language"] = native_language
        self.user_profiles[user_id]["target_languages"] = target_languages
        self.user_profiles[user_id]["proficiency_levels"] = proficiency_levels
        return True
    
    def set_communication_partners(self, user_id: str, partner_ids: List[str],
                                 custom_partners: Optional[List[str]] = None) -> bool:
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {}
        self.user_profiles[user_id]["partner_ids"] = partner_ids
        self.user_profiles[user_id]["custom_partners"] = custom_partners or []
        return True
    
    def set_communication_units(self, user_id: str, partner_id: str,
                              unit_ids: List[str], custom_units: Optional[List[str]] = None) -> bool:
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {}
        if "units" not in self.user_profiles[user_id]:
            self.user_profiles[user_id]["units"] = {}
        self.user_profiles[user_id]["units"][partner_id] = {
            "unit_ids": unit_ids,
            "custom_units": custom_units or []
        }
        return True
    
    def set_learning_goals(self, user_id: str, goals: List[Dict[str, Any]]) -> bool:
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {}
        self.user_profiles[user_id]["learning_goals"] = goals
        return True
    
    def validate_profile_completeness(self, user_id: str) -> Dict[str, Any]:
        if user_id not in self.user_profiles:
            return {
                "is_complete": False,
                "missing_fields": ["all"],
                "completion_percentage": 0
            }
        
        profile = self.user_profiles[user_id]
        required_fields = ["industry_id", "job_title", "native_language", 
                          "target_languages", "partner_ids"]
        missing_fields = [f for f in required_fields if f not in profile]
        
        completion_percentage = ((len(required_fields) - len(missing_fields)) / 
                               len(required_fields)) * 100
        
        return {
            "is_complete": len(missing_fields) == 0,
            "missing_fields": missing_fields,
            "completion_percentage": completion_percentage
        }


@pytest.fixture
def mock_industry_repository():
    """Provide mock industry repository for onboarding domain tests"""
    return MockIndustryRepository()

@pytest.fixture
def mock_partner_repository():
    """Provide mock partner repository for onboarding domain tests"""
    return MockPartnerRepository()

@pytest.fixture
def mock_embedding_service():
    """Provide mock embedding service for onboarding domain tests"""
    return MockEmbeddingService()

@pytest.fixture
def mock_completion_service():
    """Provide mock completion service for onboarding domain tests"""
    return MockCompletionService()

@pytest.fixture
def mock_onboarding_service():
    """Provide mock onboarding service for onboarding domain tests"""
    return MockOnboardingService()

@pytest.fixture
def mock_profile_setup_service():
    """Provide mock profile setup service for onboarding domain tests"""
    return MockProfileSetupService()

@pytest.fixture
def onboarding_container(mock_industry_repository, mock_partner_repository, 
                       mock_embedding_service, mock_completion_service,
                       mock_onboarding_service, mock_profile_setup_service):
    """Provide complete onboarding domain container"""
    from dependency_injector import containers, providers
    
    class OnboardingTestContainer(containers.DeclarativeContainer):
        industry_repository = providers.Object(mock_industry_repository)
        partner_repository = providers.Object(mock_partner_repository)
        embedding_service = providers.Object(mock_embedding_service)
        completion_service = providers.Object(mock_completion_service)
        onboarding_service = providers.Object(mock_onboarding_service)
        profile_setup_service = providers.Object(mock_profile_setup_service)
    
    return OnboardingTestContainer()