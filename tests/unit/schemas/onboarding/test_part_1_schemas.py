import pytest
from pydantic import ValidationError
from src.schemas.onboarding.part_1 import (
    RoleSearchRequest, RoleSearchResponse, RoleMatch,
    RoleSelectionRequest, RoleSelectionResponse
)

class TestRoleSearchSchemas:
    """Test role search schemas."""
    
    def test_role_search_request_valid(self):
        """Test valid role search request."""
        # This should fail initially (RED)
        request = RoleSearchRequest(
            job_title="Software Engineer",
            job_description="I develop web applications using Python"
        )
        
        assert request.job_title == "Software Engineer"
        assert request.job_description == "I develop web applications using Python"
    
    def test_role_search_request_validation(self):
        """Test role search request validation."""
        # This should fail initially (RED)
        
        # Test empty title
        with pytest.raises(ValidationError) as exc_info:
            RoleSearchRequest(
                job_title="",
                job_description="Valid description"
            )
        assert "at least 2 characters" in str(exc_info.value)
        
        # Test short description
        with pytest.raises(ValidationError) as exc_info:
            RoleSearchRequest(
                job_title="Valid Title",
                job_description="Too short"
            )
        assert "at least 10 characters" in str(exc_info.value)
        
        # Test max length
        with pytest.raises(ValidationError) as exc_info:
            RoleSearchRequest(
                job_title="T" * 201,  # 201 characters
                job_description="Valid description"
            )
        assert "at most 200 characters" in str(exc_info.value)
    
    def test_role_match_schema(self):
        """Test role match schema."""
        # This should fail initially (RED)
        match = RoleMatch(
            id="role123",
            title="Software Engineer",
            description="Develops software",
            industry_name="Banking & Finance",
            confidence_score=0.95
        )
        
        assert match.id == "role123"
        assert match.confidence_score == 0.95
    
    def test_role_search_response(self):
        """Test role search response schema."""
        # This should fail initially (RED)
        matches = [
            RoleMatch(
                id="role1",
                title="Software Engineer",
                description="Develops software",
                industry_name="Banking",
                confidence_score=0.95
            ),
            RoleMatch(
                id="role2",
                title="Data Analyst",
                description="Analyzes data",
                industry_name="Banking",
                confidence_score=0.85
            )
        ]
        
        response = RoleSearchResponse(
            success=True,
            message="Found 2 matching roles",
            matches=matches,
            search_id="search123"
        )
        
        assert response.success == True
        assert len(response.matches) == 2
        assert response.search_id == "search123"
    
    def test_role_selection_request(self):
        """Test role selection request schema."""
        # This should fail initially (RED)
        
        # Test with role_id
        request = RoleSelectionRequest(role_id="role123")
        assert request.role_id == "role123"
        assert request.custom_title is None
        
        # Test with custom role
        request = RoleSelectionRequest(
            custom_title="Custom Developer",
            custom_description="I do custom work"
        )
        assert request.role_id is None
        assert request.custom_title == "Custom Developer"
    
    def test_role_selection_response(self):
        """Test role selection response schema."""
        # This should fail initially (RED)
        response = RoleSelectionResponse(
            success=True,
            message="Role selected successfully",
            role_id="role123",
            is_custom=False
        )
        
        assert response.success == True
        assert response.role_id == "role123"
        assert response.is_custom == False