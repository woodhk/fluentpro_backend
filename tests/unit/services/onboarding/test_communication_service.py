import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4
from src.services.onboarding.communication_service import CommunicationService


class TestCommunicationService:
    """Test communication service."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database client."""
        return Mock()
    
    @pytest.fixture
    def mock_repositories(self):
        """Mock repository dependencies."""
        with patch('src.services.onboarding.communication_service.CommunicationRepository') as mock_comm_repo, \
             patch('src.services.onboarding.communication_service.ProfileRepository') as mock_profile_repo:
            
            # Create mock instances
            comm_instance = Mock()
            profile_instance = Mock()
            
            # Configure the classes to return the instances
            mock_comm_repo.return_value = comm_instance
            mock_profile_repo.return_value = profile_instance
            
            yield {
                'comm_repo': comm_instance,
                'profile_repo': profile_instance,
                'comm_class': mock_comm_repo,
                'profile_class': mock_profile_repo
            }
    
    @pytest.mark.asyncio
    async def test_get_available_partners_success(self, mock_db, mock_repositories):
        """Test getting available partners."""
        # This will FAIL initially
        # Setup mock data
        mock_partners = [
            {"id": str(uuid4()), "name": "Clients", "description": "External clients"},
            {"id": str(uuid4()), "name": "Colleagues", "description": "Team members"}
        ]
        mock_repositories['comm_repo'].get_all_active_partners = AsyncMock(
            return_value=mock_partners
        )
        
        # Test the service
        service = CommunicationService(mock_db)
        result = await service.get_available_partners()
        
        # Assertions
        assert result["total"] == 2
        assert len(result["partners"]) == 2
        assert result["partners"][0]["name"] == "Clients"
        
        # Verify repository was called
        mock_repositories['comm_repo'].get_all_active_partners.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_select_communication_partners_success(self, mock_db, mock_repositories):
        """Test selecting communication partners."""
        # This will FAIL initially
        auth0_id = "auth0|test123"
        user_id = str(uuid4())
        partner_ids = [str(uuid4()), str(uuid4())]
        
        # Mock user lookup
        mock_repositories['profile_repo'].get_user_by_auth0_id = AsyncMock(
            return_value={"id": user_id, "auth0_id": auth0_id}
        )
        
        # Mock available partners
        mock_repositories['comm_repo'].get_all_active_partners = AsyncMock(
            return_value=[
                {"id": partner_ids[0], "name": "Clients"},
                {"id": partner_ids[1], "name": "Colleagues"}
            ]
        )
        
        # Mock save operation
        mock_selections = [
            {"id": str(uuid4()), "user_id": user_id, "communication_partner_id": partner_ids[0], "priority": 1},
            {"id": str(uuid4()), "user_id": user_id, "communication_partner_id": partner_ids[1], "priority": 2}
        ]
        mock_repositories['comm_repo'].save_user_partner_selections = AsyncMock(
            return_value=mock_selections
        )
        
        # Test the service
        service = CommunicationService(mock_db)
        result = await service.select_communication_partners(auth0_id, partner_ids)
        
        # Assertions
        assert result["success"] == True
        assert result["selected_count"] == 2
        assert len(result["partner_selections"]) == 2
        
        # Verify calls
        mock_repositories['profile_repo'].get_user_by_auth0_id.assert_called_once_with(auth0_id)
        mock_repositories['comm_repo'].save_user_partner_selections.assert_called_once_with(
            user_id=user_id,
            partner_ids=partner_ids
        )
    
    @pytest.mark.asyncio
    async def test_select_partners_invalid_ids(self, mock_db, mock_repositories):
        """Test selecting partners with invalid IDs."""
        # This will FAIL initially
        auth0_id = "auth0|test123"
        user_id = str(uuid4())
        valid_id = str(uuid4())
        invalid_id = str(uuid4())
        
        # Mock user lookup
        mock_repositories['profile_repo'].get_user_by_auth0_id = AsyncMock(
            return_value={"id": user_id}
        )
        
        # Mock available partners (only one valid)
        mock_repositories['comm_repo'].get_all_active_partners = AsyncMock(
            return_value=[{"id": valid_id, "name": "Clients"}]
        )
        
        # Test with invalid partner ID
        service = CommunicationService(mock_db)
        
        with pytest.raises(ValueError) as exc_info:
            await service.select_communication_partners(
                auth0_id, 
                [valid_id, invalid_id]  # One invalid ID
            )
        
        assert "Invalid partner IDs" in str(exc_info.value)
        assert invalid_id in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_situations_for_partner(self, mock_db, mock_repositories):
        """Test getting situations for a specific partner."""
        # This will FAIL initially
        auth0_id = "auth0|test123"
        user_id = str(uuid4())
        partner_id = str(uuid4())
        
        # Mock user
        mock_repositories['profile_repo'].get_user_by_auth0_id = AsyncMock(
            return_value={"id": user_id}
        )
        
        # Mock all situations
        mock_situations = [
            {"id": str(uuid4()), "name": "Meetings"},
            {"id": str(uuid4()), "name": "Phone Calls"}
        ]
        mock_repositories['comm_repo'].get_all_active_units = AsyncMock(
            return_value=mock_situations
        )
        
        # Mock user's selections for this partner
        selected_id = mock_situations[0]["id"]
        mock_repositories['comm_repo'].get_user_situations_for_partner = AsyncMock(
            return_value=[
                {"unit_id": selected_id, "priority": 1}
            ]
        )
        
        # Mock partner info lookup  
        mock_repositories['comm_repo'].get_partner_by_id = AsyncMock(
            return_value={"id": partner_id, "name": "Clients"}
        )
        
        # Test the service
        service = CommunicationService(mock_db)
        result = await service.get_situations_for_partner(auth0_id, partner_id)
        
        # Assertions
        assert result["partner_id"] == partner_id
        assert result["partner_name"] == "Clients"
        assert len(result["available_situations"]) == 2
        assert len(result["selected_situations"]) == 1
        assert result["selected_situations"][0] == selected_id
    
    @pytest.mark.asyncio
    async def test_complete_part_2_success(self, mock_db, mock_repositories):
        """Test completing Part 2 of onboarding."""
        # This will FAIL initially
        auth0_id = "auth0|test123"
        user_id = str(uuid4())
        
        # Mock user
        mock_repositories['profile_repo'].get_user_by_auth0_id = AsyncMock(
            return_value={"id": user_id}
        )
        
        # Mock summary showing user has selections
        mock_repositories['comm_repo'].get_user_complete_selections = AsyncMock(
            return_value={
                "user_id": user_id,
                "partners": [
                    {
                        "partner": {"name": "Clients"},
                        "priority": 1,
                        "situations": [{"unit": {"name": "Meetings"}, "priority": 1}]
                    }
                ]
            }
        )
        
        # Mock profile update
        mock_repositories['profile_repo'].update = AsyncMock(
            return_value={"id": user_id, "onboarding_status": "personalisation"}
        )
        
        # Test the service
        service = CommunicationService(mock_db)
        # Need to mock the service's internal method
        service.get_user_selections_summary = AsyncMock(
            return_value={
                "total_partners_selected": 1,
                "total_situations_selected": 1,
                "selections": []
            }
        )
        
        result = await service.complete_part_2(auth0_id)
        
        # Assertions
        assert result["success"] == True
        assert result["next_step"] == "part_3"
        
        # Verify status update
        mock_repositories['profile_repo'].update.assert_called_once()
        update_args = mock_repositories['profile_repo'].update.call_args[0]
        assert update_args[0] == user_id
        assert update_args[1]["onboarding_status"] == "personalisation"
    
    @pytest.mark.asyncio
    async def test_complete_part_2_no_selections(self, mock_db, mock_repositories):
        """Test completing Part 2 without selections fails."""
        # This will FAIL initially
        auth0_id = "auth0|test123"
        user_id = str(uuid4())
        
        # Mock user
        mock_repositories['profile_repo'].get_user_by_auth0_id = AsyncMock(
            return_value={"id": user_id}
        )
        
        # Test the service
        service = CommunicationService(mock_db)
        # Mock empty selections
        service.get_user_selections_summary = AsyncMock(
            return_value={
                "total_partners_selected": 0,
                "total_situations_selected": 0,
                "selections": []
            }
        )
        
        # Should raise error
        with pytest.raises(ValueError) as exc_info:
            await service.complete_part_2(auth0_id)
        
        assert "No communication partners selected" in str(exc_info.value)