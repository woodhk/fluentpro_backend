import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from uuid import uuid4
from src.main import app
from src.core.dependencies import get_current_user_auth0_id, get_db


class TestPart2Endpoints:
    """Test Part 2 onboarding endpoints."""
    
    @pytest.fixture
    def client(self):
        """Test client for FastAPI."""
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        """Mock authentication headers."""
        return {"Authorization": "Bearer test-token"}
    
    @pytest.fixture
    def mock_dependencies(self):
        """Mock all endpoint dependencies."""
        with patch('src.api.v1.onboarding.part_2.CommunicationService') as mock_service_class:
            # Create mock service instance
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            # Override FastAPI dependencies
            app.dependency_overrides[get_current_user_auth0_id] = lambda: "auth0|test123"
            app.dependency_overrides[get_db] = lambda: Mock()
            
            yield {
                'service_class': mock_service_class,
                'service': mock_service
            }
            
            # Clear overrides after test
            app.dependency_overrides.clear()
    
    def test_get_communication_partners_success(self, client, auth_headers, mock_dependencies):
        """Test getting available communication partners."""
        # This will FAIL initially
        # Setup mock response
        mock_partners = [
            {
                "id": str(uuid4()),
                "name": "Clients",
                "description": "External clients"
            },
            {
                "id": str(uuid4()),
                "name": "Colleagues",
                "description": "Team members"
            }
        ]
        
        mock_dependencies['service'].get_available_partners = AsyncMock(
            return_value={
                "partners": mock_partners,
                "total": 2
            }
        )
        
        # Make request
        response = client.get(
            "/api/v1/onboarding/part-2/communication-partners",
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert len(data["partners"]) == 2
        assert data["partners"][0]["name"] == "Clients"
        
        # Verify service was called
        mock_dependencies['service'].get_available_partners.assert_called_once()
    
    def test_select_partners_success(self, client, auth_headers, mock_dependencies):
        """Test selecting communication partners."""
        # This will FAIL initially
        partner_ids = [str(uuid4()), str(uuid4())]
        
        # Setup mock response
        mock_dependencies['service'].select_communication_partners = AsyncMock(
            return_value={
                "success": True,
                "selected_count": 2,
                "partner_selections": [
                    {"id": str(uuid4()), "priority": 1},
                    {"id": str(uuid4()), "priority": 2}
                ]
            }
        )
        
        # Make request
        response = client.post(
            "/api/v1/onboarding/part-2/select-partners",
            headers=auth_headers,
            json={"partner_ids": partner_ids}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["selected_count"] == 2
        
        # Verify service was called with correct params
        mock_dependencies['service'].select_communication_partners.assert_called_once()
        call_args = mock_dependencies['service'].select_communication_partners.call_args
        assert call_args[1]["auth0_id"] == "auth0|test123"
        assert len(call_args[1]["partner_ids"]) == 2
    
    def test_select_partners_empty_list(self, client, auth_headers, mock_dependencies):
        """Test selecting partners with empty list fails."""
        # This will FAIL initially
        response = client.post(
            "/api/v1/onboarding/part-2/select-partners",
            headers=auth_headers,
            json={"partner_ids": []}  # Empty list
        )
        
        # Should fail validation
        assert response.status_code == 422
        assert "at least 1 item" in response.text.lower()
    
    def test_get_situations_for_partner(self, client, auth_headers, mock_dependencies):
        """Test getting situations for a specific partner."""
        # This will FAIL initially
        partner_id = str(uuid4())
        
        # Setup mock response
        mock_dependencies['service'].get_situations_for_partner = AsyncMock(
            return_value={
                "partner_id": partner_id,
                "partner_name": "Clients",
                "available_situations": [
                    {"id": str(uuid4()), "name": "Meetings"},
                    {"id": str(uuid4()), "name": "Phone Calls"}
                ],
                "selected_situations": []
            }
        )
        
        # Make request
        response = client.get(
            f"/api/v1/onboarding/part-2/situations/{partner_id}",
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["partner_id"] == partner_id
        assert data["partner_name"] == "Clients"
        assert len(data["available_situations"]) == 2
    
    def test_select_situations_success(self, client, auth_headers, mock_dependencies):
        """Test selecting situations for a partner."""
        # This will FAIL initially
        partner_id = str(uuid4())
        situation_ids = [str(uuid4()), str(uuid4())]
        
        # Setup mock response
        mock_dependencies['service'].select_situations_for_partner = AsyncMock(
            return_value={
                "success": True,
                "partner_id": partner_id,
                "selected_count": 2,
                "situation_selections": []
            }
        )
        
        # Make request
        response = client.post(
            "/api/v1/onboarding/part-2/select-situations",
            headers=auth_headers,
            json={
                "partner_id": partner_id,
                "situation_ids": situation_ids
            }
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["partner_id"] == partner_id
        assert data["selected_count"] == 2
    
    def test_get_summary(self, client, auth_headers, mock_dependencies):
        """Test getting selections summary."""
        # This will FAIL initially
        # Setup mock response
        mock_dependencies['service'].get_user_selections_summary = AsyncMock(
            return_value={
                "total_partners_selected": 2,
                "total_situations_selected": 5,
                "selections": []
            }
        )
        
        # Make request
        response = client.get(
            "/api/v1/onboarding/part-2/summary",
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["total_partners_selected"] == 2
        assert data["total_situations_selected"] == 5
    
    def test_complete_part_2(self, client, auth_headers, mock_dependencies):
        """Test completing Part 2."""
        # This will FAIL initially
        # Setup mock response
        mock_dependencies['service'].complete_part_2 = AsyncMock(
            return_value={
                "success": True,
                "message": "Part 2 completed successfully",
                "next_step": "part_3"
            }
        )
        
        # Make request
        response = client.post(
            "/api/v1/onboarding/part-2/complete",
            headers=auth_headers
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["next_step"] == "part_3"
    
    def test_endpoints_require_authentication(self, client):
        """Test all endpoints require authentication."""
        # This will FAIL initially
        # Test each endpoint without auth headers
        endpoints = [
            ("GET", "/api/v1/onboarding/part-2/communication-partners"),
            ("POST", "/api/v1/onboarding/part-2/select-partners"),
            ("GET", f"/api/v1/onboarding/part-2/situations/{uuid4()}"),
            ("POST", "/api/v1/onboarding/part-2/select-situations"),
            ("GET", "/api/v1/onboarding/part-2/summary"),
            ("POST", "/api/v1/onboarding/part-2/complete")
        ]
        
        for method, endpoint in endpoints:
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint, json={})
            
            # Should get 403 Forbidden without auth
            assert response.status_code == 403, f"Endpoint {endpoint} should require auth"