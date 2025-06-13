import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock, AsyncMock
from uuid import uuid4
from src.main import app
from src.core.dependencies import get_current_user_auth0_id, get_db


@pytest.mark.integration
class TestPart2E2E:
    """End-to-end tests for Part 2 onboarding."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        return {"Authorization": "Bearer test-token"}
    
    @pytest.fixture
    def mock_all_dependencies(self):
        """Mock all external dependencies for E2E testing."""
        # Mock database
        mock_db = Mock()
        mock_db.table = Mock(return_value=mock_db)
        mock_db.select = Mock(return_value=mock_db)
        mock_db.insert = Mock(return_value=mock_db)
        mock_db.update = Mock(return_value=mock_db)
        mock_db.delete = Mock(return_value=mock_db)
        mock_db.eq = Mock(return_value=mock_db)
        mock_db.order = Mock(return_value=mock_db)
        mock_db.execute = Mock()
        
        # Override dependencies
        app.dependency_overrides[get_current_user_auth0_id] = lambda: "auth0|test123"
        app.dependency_overrides[get_db] = lambda: mock_db
        
        try:
            yield {'db': mock_db}
        finally:
            app.dependency_overrides.clear()
    
    def test_complete_part_2_user_journey(self, client, auth_headers, mock_all_dependencies):
        """Test complete user journey through Part 2."""
        # Setup test data
        user_id = str(uuid4())
        partner_ids = [str(uuid4()), str(uuid4())]
        situation_ids = [str(uuid4()), str(uuid4()), str(uuid4())]
        
        # Setup mock responses for the complete journey
        mock_all_dependencies['db'].execute.side_effect = [
            # Step 1: Get communication partners
            Mock(data=[
                {"id": partner_ids[0], "name": "Clients", "description": "External clients", "is_active": True},
                {"id": partner_ids[1], "name": "Colleagues", "description": "Team members", "is_active": True}
            ]),
            
            # Step 2: Select partners - get user
            Mock(data=[{"id": user_id, "auth0_id": "auth0|test123"}]),
            # - get available partners for validation
            Mock(data=[
                {"id": partner_ids[0], "name": "Clients"},
                {"id": partner_ids[1], "name": "Colleagues"}
            ]),
            # - delete existing selections
            Mock(data=[]),
            # - insert new selections
            Mock(data=[
                {"id": str(uuid4()), "priority": 1},
                {"id": str(uuid4()), "priority": 2}
            ]),
            
            # Step 3: Get situations for first partner
            Mock(data=[{"id": user_id}]),  # get user
            Mock(data=[  # get all situations
                {"id": situation_ids[0], "name": "Meetings"},
                {"id": situation_ids[1], "name": "Presentations"},
                {"id": situation_ids[2], "name": "Phone Calls"}
            ]),
            Mock(data=[]),  # get user's selections (empty)
            Mock(data=[{"id": partner_ids[0], "name": "Clients"}]),  # get partner info
            
            # Step 4: Select situations for first partner
            Mock(data=[{"id": user_id}]),  # get user
            Mock(data=[  # get available situations for validation
                {"id": situation_ids[0], "name": "Meetings"},
                {"id": situation_ids[1], "name": "Presentations"},
                {"id": situation_ids[2], "name": "Phone Calls"}
            ]),
            Mock(data=[]),  # delete existing
            Mock(data=[  # insert new
                {"id": str(uuid4()), "priority": 1},
                {"id": str(uuid4()), "priority": 2}
            ]),
            
            # Step 5: Get summary
            Mock(data=[{"id": user_id, "auth0_id": "auth0|test123"}]),  # get user by auth0_id
            Mock(data=[  # get user's selected partners with joins
                {
                    "communication_partner_id": partner_ids[0],
                    "priority": 1,
                    "communication_partners": {"id": partner_ids[0], "name": "Clients"}
                },
                {
                    "communication_partner_id": partner_ids[1],
                    "priority": 2,
                    "communication_partners": {"id": partner_ids[1], "name": "Colleagues"}
                }
            ]),
            Mock(data=[  # get situations for partner 1
                {
                    "unit_id": situation_ids[0],
                    "priority": 1,
                    "units": {"id": situation_ids[0], "name": "Meetings"}
                },
                {
                    "unit_id": situation_ids[1],
                    "priority": 2,
                    "units": {"id": situation_ids[1], "name": "Presentations"}
                }
            ]),
            Mock(data=[]),  # get situations for partner 2 (none selected)
            
            # Step 6: Complete Part 2
            Mock(data=[{"id": user_id, "auth0_id": "auth0|test123"}]),  # get user by auth0_id for complete_part_2
            # Get user again for summary
            Mock(data=[{"id": user_id, "auth0_id": "auth0|test123"}]),  # get user by auth0_id for get_user_selections_summary
            # Repeat summary queries
            Mock(data=[  # get partners
                {
                    "communication_partner_id": partner_ids[0],
                    "priority": 1,
                    "communication_partners": {"id": partner_ids[0], "name": "Clients"}
                }
            ]),
            Mock(data=[  # get situations
                {
                    "unit_id": situation_ids[0],
                    "priority": 1,
                    "units": {"id": situation_ids[0], "name": "Meetings"}
                }
            ]),
            Mock(data=[{"id": user_id, "onboarding_status": "personalisation"}])  # update status
        ]
        
        # Step 1: Get available partners
        response = client.get(
            "/api/v1/onboarding/part-2/communication-partners",
            headers=auth_headers
        )
        assert response.status_code == 200
        partners_data = response.json()
        assert len(partners_data["partners"]) == 2
        
        # Step 2: Select partners
        response = client.post(
            "/api/v1/onboarding/part-2/select-partners",
            headers=auth_headers,
            json={"partner_ids": partner_ids}
        )
        assert response.status_code == 200
        assert response.json()["selected_count"] == 2
        
        # Step 3: Get situations for first partner
        response = client.get(
            f"/api/v1/onboarding/part-2/situations/{partner_ids[0]}",
            headers=auth_headers
        )
        assert response.status_code == 200
        situations_data = response.json()
        assert len(situations_data["available_situations"]) == 3
        
        # Step 4: Select situations for first partner
        response = client.post(
            "/api/v1/onboarding/part-2/select-situations",
            headers=auth_headers,
            json={
                "partner_id": partner_ids[0],
                "situation_ids": [situation_ids[0], situation_ids[1]]
            }
        )
        assert response.status_code == 200
        assert response.json()["selected_count"] == 2
        
        # Step 5: Get summary
        response = client.get(
            "/api/v1/onboarding/part-2/summary",
            headers=auth_headers
        )
        assert response.status_code == 200
        summary = response.json()
        assert summary["total_partners_selected"] >= 1
        assert summary["total_situations_selected"] >= 1
        
        # Step 6: Complete Part 2
        response = client.post(
            "/api/v1/onboarding/part-2/complete",
            headers=auth_headers
        )
        assert response.status_code == 200
        complete_data = response.json()
        assert complete_data["success"] == True
        assert complete_data["next_step"] == "part_3"