import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4
from src.services.onboarding.communication_service import CommunicationService
from src.repositories.onboarding.communication_repository import CommunicationRepository


@pytest.mark.integration
class TestPart2Integration:
    """Integration tests for Part 2 onboarding."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database with realistic responses."""
        mock = Mock()
        
        # Make it chainable
        mock.table = Mock(return_value=mock)
        mock.select = Mock(return_value=mock)
        mock.insert = Mock(return_value=mock)
        mock.update = Mock(return_value=mock)
        mock.delete = Mock(return_value=mock)
        mock.eq = Mock(return_value=mock)
        mock.order = Mock(return_value=mock)
        mock.execute = Mock()
        
        return mock
    
    @pytest.mark.asyncio
    async def test_complete_partner_selection_flow(self, mock_db):
        """Test complete flow of selecting partners."""
        # Setup test data
        user_id = str(uuid4())
        partner_ids = [str(uuid4()), str(uuid4())]
        
        # Mock the profile lookup
        with patch('src.services.onboarding.communication_service.ProfileRepository') as mock_profile_class:
            mock_profile = Mock()
            mock_profile_class.return_value = mock_profile
            mock_profile.get_user_by_auth0_id = AsyncMock(
                return_value={"id": user_id}
            )
            
            # Mock CommunicationRepository
            with patch('src.services.onboarding.communication_service.CommunicationRepository') as mock_comm_class:
                mock_comm_repo = Mock()
                mock_comm_class.return_value = mock_comm_repo
                
                # Mock get_all_active_partners - called twice (once for listing, once for validation)
                mock_comm_repo.get_all_active_partners = AsyncMock(
                    return_value=[
                        {"id": partner_ids[0], "name": "Clients"},
                        {"id": partner_ids[1], "name": "Colleagues"}
                    ]
                )
                
                # Mock save_user_partner_selections
                mock_comm_repo.save_user_partner_selections = AsyncMock(
                    return_value=[
                        {"id": str(uuid4()), "user_id": user_id, "communication_partner_id": partner_ids[0], "priority": 1},
                        {"id": str(uuid4()), "user_id": user_id, "communication_partner_id": partner_ids[1], "priority": 2}
                    ]
                )
                
                # Test the complete flow
                service = CommunicationService(mock_db)
                
                # Step 1: Get available partners
                available = await service.get_available_partners()
                assert available["total"] == 2
                
                # Step 2: Select partners
                result = await service.select_communication_partners(
                    auth0_id="auth0|test",
                    partner_ids=partner_ids
                )
                
                assert result["success"] == True
                assert result["selected_count"] == 2
    
    @pytest.mark.asyncio
    async def test_complete_situation_selection_flow(self, mock_db):
        """Test complete flow of selecting situations for a partner."""
        # Setup test data
        user_id = str(uuid4())
        partner_id = str(uuid4())
        situation_ids = [str(uuid4()), str(uuid4())]
        
        # Mock the profile lookup
        with patch('src.services.onboarding.communication_service.ProfileRepository') as mock_profile_class:
            mock_profile = Mock()
            mock_profile_class.return_value = mock_profile
            mock_profile.get_user_by_auth0_id = AsyncMock(
                return_value={"id": user_id}
            )
            
            # Mock CommunicationRepository
            with patch('src.services.onboarding.communication_service.CommunicationRepository') as mock_comm_class:
                mock_comm_repo = Mock()
                mock_comm_class.return_value = mock_comm_repo
                
                # Mock get_all_active_units - called twice (once for listing, once for validation)
                mock_comm_repo.get_all_active_units = AsyncMock(
                    return_value=[
                        {"id": situation_ids[0], "name": "Meetings"},
                        {"id": situation_ids[1], "name": "Phone Calls"}
                    ]
                )
                
                # Mock get_user_situations_for_partner
                mock_comm_repo.get_user_situations_for_partner = AsyncMock(
                    return_value=[]
                )
                
                # Mock get_partner_by_id
                mock_comm_repo.get_partner_by_id = AsyncMock(
                    return_value={"id": partner_id, "name": "Clients"}
                )
                
                # Mock save_user_partner_situations
                mock_comm_repo.save_user_partner_situations = AsyncMock(
                    return_value=[
                        {
                            "id": str(uuid4()),
                            "user_id": user_id,
                            "communication_partner_id": partner_id,
                            "unit_id": situation_ids[0],
                            "priority": 1
                        },
                        {
                            "id": str(uuid4()),
                            "user_id": user_id,
                            "communication_partner_id": partner_id,
                            "unit_id": situation_ids[1],
                            "priority": 2
                        }
                    ]
                )
                
                # Test the complete flow
                service = CommunicationService(mock_db)
                
                # Step 1: Get situations for partner
                situations = await service.get_situations_for_partner(
                    auth0_id="auth0|test",
                    partner_id=partner_id
                )
                
                assert situations["partner_name"] == "Clients"
                assert len(situations["available_situations"]) == 2
                
                # Step 2: Select situations
                result = await service.select_situations_for_partner(
                    auth0_id="auth0|test",
                    partner_id=partner_id,
                    situation_ids=situation_ids
                )
                
                assert result["success"] == True
                assert result["selected_count"] == 2
    
    @pytest.mark.asyncio
    async def test_complete_onboarding_part_2_flow(self, mock_db):
        """Test the complete Part 2 onboarding flow."""
        # Setup comprehensive test data
        user_id = str(uuid4())
        partner1_id = str(uuid4())
        partner2_id = str(uuid4())
        situations = [str(uuid4()), str(uuid4()), str(uuid4())]
        
        # Mock profile repository
        with patch('src.services.onboarding.communication_service.ProfileRepository') as mock_profile_class:
            mock_profile = Mock()
            mock_profile_class.return_value = mock_profile
            mock_profile.get_user_by_auth0_id = AsyncMock(
                return_value={"id": user_id}
            )
            mock_profile.update = AsyncMock(
                return_value={"id": user_id, "onboarding_status": "personalisation"}
            )
            
            # Mock communication repository for summary
            with patch.object(CommunicationRepository, 'get_user_complete_selections') as mock_get_selections:
                mock_get_selections.return_value = {
                    "user_id": user_id,
                    "partners": [
                        {
                            "partner": {"id": partner1_id, "name": "Clients"},
                            "priority": 1,
                            "situations": [
                                {"unit": {"name": "Meetings"}, "priority": 1},
                                {"unit": {"name": "Presentations"}, "priority": 2}
                            ]
                        },
                        {
                            "partner": {"id": partner2_id, "name": "Colleagues"},
                            "priority": 2,
                            "situations": [
                                {"unit": {"name": "Team Discussions"}, "priority": 1}
                            ]
                        }
                    ]
                }
                
                # Test completing Part 2
                service = CommunicationService(mock_db)
                
                # Get summary first
                summary = await service.get_user_selections_summary("auth0|test")
                assert summary["total_partners_selected"] == 2
                assert summary["total_situations_selected"] == 3
                
                # Complete Part 2
                result = await service.complete_part_2("auth0|test")
                assert result["success"] == True
                assert result["next_step"] == "part_3"
                
                # Verify status was updated
                mock_profile.update.assert_called_once()
                update_call = mock_profile.update.call_args[0]
                assert update_call[1]["onboarding_status"] == "personalisation"