"""Tests for Onboarding Part 3 API Endpoints - TDD Phase 5"""
import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
from uuid import uuid4

from src.core.exceptions import UserNotFoundError
from src.models.enums import OnboardingStatus


@pytest.fixture
def mock_summary_data():
    """Mock onboarding summary data."""
    return {
        "native_language": "english",
        "native_language_display": "English",
        "industry_id": str(uuid4()),
        "industry_name": "Banking & Finance",
        "role": {
            "id": str(uuid4()),
            "title": "Financial Analyst",
            "description": "Analyzes financial data",
            "is_custom": False,
            "industry_name": "Banking & Finance"
        },
        "communication_partners": [{
            "id": str(uuid4()),
            "name": "Clients",
            "description": "External clients",
            "priority": 1,
            "situations": [{
                "id": str(uuid4()),
                "name": "Meetings",
                "description": None,
                "priority": 1
            }]
        }],
        "total_partners": 1,
        "total_situations": 1,
        "onboarding_status": "personalisation",
        "is_complete": False
    }


class TestOnboardingPart3API:
    """Test cases for Onboarding Part 3 API endpoints."""
    
    @pytest.mark.asyncio
    async def test_summary_endpoint_requires_auth(self, test_client: AsyncClient):
        """Test that summary endpoint requires authentication."""
        response = await test_client.get(
            "/api/v1/onboarding/part-3/summary",
            headers={"Authorization": "Bearer fake-token"}
        )
        
        # Should return 401 because token is invalid
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_summary_success(self, test_client: AsyncClient, mock_summary_data):
        """Test successful retrieval of onboarding summary."""
        mock_auth0_id = "auth0|test123"
        
        # Mock dependencies
        with patch("src.api.v1.onboarding.part_3.get_current_user_auth0_id", return_value=mock_auth0_id):
            # Mock service
            mock_service = AsyncMock()
            mock_service.get_onboarding_summary.return_value = mock_summary_data
            
            with patch("src.services.onboarding.summary_service.OnboardingSummaryService", return_value=mock_service):
                response = await test_client.get(
                    "/api/v1/onboarding/part-3/summary",
                    headers={"Authorization": "Bearer fake-token"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["message"] == "Onboarding summary retrieved successfully"
                assert data["summary"]["native_language"] == "english"
                assert data["summary"]["role"]["title"] == "Financial Analyst"
                
                # Verify service was called correctly
                mock_service.get_onboarding_summary.assert_called_once_with(mock_auth0_id)
    
    @pytest.mark.asyncio
    async def test_get_summary_user_not_found(self, test_client: AsyncClient):
        """Test summary when user not found."""
        with patch("src.api.v1.onboarding.part_3.get_current_user_auth0_id", return_value="auth0|123"):
            mock_service = AsyncMock()
            mock_service.get_onboarding_summary.side_effect = UserNotFoundError("User not found")
            
            with patch("src.services.onboarding.summary_service.OnboardingSummaryService", return_value=mock_service):
                response = await test_client.get(
                    "/api/v1/onboarding/part-3/summary",
                    headers={"Authorization": "Bearer fake-token"}
                )
                
                assert response.status_code == 404
                assert "User not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_summary_server_error(self, test_client: AsyncClient):
        """Test summary with server error."""
        with patch("src.api.v1.onboarding.part_3.get_current_user_auth0_id", return_value="auth0|123"):
            mock_service = AsyncMock()
            mock_service.get_onboarding_summary.side_effect = Exception("Database error")
            
            with patch("src.services.onboarding.summary_service.OnboardingSummaryService", return_value=mock_service):
                response = await test_client.get(
                    "/api/v1/onboarding/part-3/summary",
                    headers={"Authorization": "Bearer fake-token"}
                )
                
                assert response.status_code == 500
                assert "Failed to retrieve onboarding summary" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_complete_onboarding_success(self, test_client: AsyncClient):
        """Test successful onboarding completion."""
        mock_auth0_id = "auth0|test123"
        
        with patch("src.api.v1.onboarding.part_3.get_current_user_auth0_id", return_value=mock_auth0_id):
            mock_service = AsyncMock()
            mock_service.complete_onboarding.return_value = {
                "success": True,
                "message": "Onboarding completed successfully!",
                "onboarding_status": OnboardingStatus.COMPLETED.value,
                "next_steps": "You can now access your personalized learning content."
            }
            
            with patch("src.services.onboarding.summary_service.OnboardingSummaryService", return_value=mock_service):
                response = await test_client.post(
                    "/api/v1/onboarding/part-3/complete",
                    headers={"Authorization": "Bearer fake-token"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["onboarding_status"] == "completed"
                assert "next_steps" in data
                
                mock_service.complete_onboarding.assert_called_once_with(mock_auth0_id)
    
    @pytest.mark.asyncio
    async def test_complete_onboarding_validation_error(self, test_client: AsyncClient):
        """Test completion with validation errors."""
        with patch("src.api.v1.onboarding.part_3.get_current_user_auth0_id", return_value="auth0|123"):
            mock_service = AsyncMock()
            mock_service.complete_onboarding.side_effect = ValueError(
                "Onboarding incomplete: Native language not selected, Role not selected"
            )
            
            with patch("src.services.onboarding.summary_service.OnboardingSummaryService", return_value=mock_service):
                response = await test_client.post(
                    "/api/v1/onboarding/part-3/complete",
                    headers={"Authorization": "Bearer fake-token"}
                )
                
                assert response.status_code == 400
                detail = response.json()["detail"]
                assert "Native language not selected" in detail
                assert "Role not selected" in detail
    
    @pytest.mark.asyncio
    async def test_endpoints_require_authentication(self, test_client: AsyncClient):
        """Test that endpoints require authentication."""
        # Test summary endpoint
        response = await test_client.get("/api/v1/onboarding/part-3/summary")
        assert response.status_code == 401  # No auth header
        
        # Test complete endpoint
        response = await test_client.post("/api/v1/onboarding/part-3/complete")
        assert response.status_code == 401  # No auth header
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_rate_limiting(self, test_client: AsyncClient):
        """Test that rate limiting is applied."""
        # Mock auth to avoid that being the issue
        with patch("src.api.v1.onboarding.part_3.get_current_user_auth0_id", return_value="auth0|123"):
            mock_service = AsyncMock()
            mock_service.get_onboarding_summary.return_value = {"test": "data"}
            
            with patch("src.services.onboarding.summary_service.OnboardingSummaryService", return_value=mock_service):
                # Make many requests quickly
                for i in range(101):  # API_RATE_LIMIT is 100/minute
                    response = await test_client.get(
                        "/api/v1/onboarding/part-3/summary",
                        headers={"Authorization": "Bearer fake-token"}
                    )
                    
                    if i < 100:
                        assert response.status_code == 200
                    else:
                        # Should be rate limited
                        assert response.status_code == 429
                        assert "Rate limit exceeded" in response.json()["error"]