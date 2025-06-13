import pytest
from unittest.mock import Mock, AsyncMock
from uuid import uuid4
from src.repositories.onboarding.communication_repository import CommunicationRepository


class TestCommunicationRepository:
    """Test communication repository."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock Supabase client."""
        mock = Mock()
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
    async def test_get_all_active_partners(self, mock_db):
        """Test getting all active communication partners."""
        # This will FAIL initially
        # Setup mock response
        mock_partners = [
            {
                "id": str(uuid4()),
                "name": "Clients",
                "description": "External clients",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": str(uuid4()),
                "name": "Colleagues",
                "description": "Team members",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z"
            }
        ]
        mock_db.execute.return_value = Mock(data=mock_partners)
        
        # Test the repository
        repo = CommunicationRepository(mock_db)
        result = await repo.get_all_active_partners()
        
        # Assertions
        assert len(result) == 2
        assert result[0]["name"] == "Clients"
        assert result[1]["name"] == "Colleagues"
        
        # Verify correct database calls
        mock_db.table.assert_called_with("communication_partners")
        mock_db.eq.assert_called_with("is_active", True)
        mock_db.order.assert_called_with("name")
    
    @pytest.mark.asyncio
    async def test_get_all_active_units(self, mock_db):
        """Test getting all active communication situations/units."""
        # This will FAIL initially
        mock_units = [
            {
                "id": str(uuid4()),
                "name": "Meetings",
                "description": "Formal meetings",
                "is_active": True
            },
            {
                "id": str(uuid4()),
                "name": "Phone Calls",
                "description": "Phone conversations",
                "is_active": True
            }
        ]
        mock_db.execute.return_value = Mock(data=mock_units)
        
        repo = CommunicationRepository(mock_db)
        result = await repo.get_all_active_units()
        
        assert len(result) == 2
        assert result[0]["name"] == "Meetings"
        
        # Verify it queries the units table
        mock_db.table.assert_called_with("units")
    
    @pytest.mark.asyncio
    async def test_save_user_partner_selections(self, mock_db):
        """Test saving user's partner selections with priority."""
        # This will FAIL initially
        user_id = str(uuid4())
        partner_ids = [str(uuid4()), str(uuid4()), str(uuid4())]
        
        # Mock the delete operation
        mock_db.execute.side_effect = [
            Mock(data=[]),  # Delete response
            Mock(data=[     # Insert response
                {"id": str(uuid4()), "user_id": user_id, "communication_partner_id": partner_ids[0], "priority": 1},
                {"id": str(uuid4()), "user_id": user_id, "communication_partner_id": partner_ids[1], "priority": 2},
                {"id": str(uuid4()), "user_id": user_id, "communication_partner_id": partner_ids[2], "priority": 3}
            ])
        ]
        
        repo = CommunicationRepository(mock_db)
        result = await repo.save_user_partner_selections(user_id, partner_ids)
        
        # Assertions
        assert len(result) == 3
        assert result[0]["priority"] == 1
        assert result[1]["priority"] == 2
        assert result[2]["priority"] == 3
        
        # Verify delete was called first
        mock_db.delete.assert_called_once()
        
        # Verify insert was called with correct data
        mock_db.insert.assert_called_once()
        insert_data = mock_db.insert.call_args[0][0]
        assert len(insert_data) == 3
        assert insert_data[0]["priority"] == 1
        assert insert_data[1]["priority"] == 2
        assert insert_data[2]["priority"] == 3
    
    @pytest.mark.asyncio
    async def test_get_user_selected_partners_with_joins(self, mock_db):
        """Test getting user's selected partners with join data."""
        # This will FAIL initially
        user_id = str(uuid4())
        
        # Mock response with nested join data (Supabase format)
        mock_response = [
            {
                "id": str(uuid4()),
                "user_id": user_id,
                "communication_partner_id": str(uuid4()),
                "priority": 1,
                "created_at": "2024-01-01T00:00:00Z",
                "communication_partners": {
                    "id": str(uuid4()),
                    "name": "Clients",
                    "description": "External clients"
                }
            },
            {
                "id": str(uuid4()),
                "user_id": user_id,
                "communication_partner_id": str(uuid4()),
                "priority": 2,
                "created_at": "2024-01-01T00:00:00Z",
                "communication_partners": {
                    "id": str(uuid4()),
                    "name": "Colleagues",
                    "description": "Team members"
                }
            }
        ]
        mock_db.execute.return_value = Mock(data=mock_response)
        
        repo = CommunicationRepository(mock_db)
        result = await repo.get_user_selected_partners(user_id)
        
        # Assertions
        assert len(result) == 2
        assert result[0]["priority"] == 1
        assert result[0]["communication_partners"]["name"] == "Clients"
        assert result[1]["priority"] == 2
        assert result[1]["communication_partners"]["name"] == "Colleagues"
        
        # Verify correct select with join
        mock_db.select.assert_called_with("*, communication_partners!inner(*)")
        mock_db.eq.assert_called_with("user_id", user_id)
        mock_db.order.assert_called_with("priority")
    
    @pytest.mark.asyncio
    async def test_save_user_partner_situations(self, mock_db):
        """Test saving situations for a specific partner."""
        # This will FAIL initially
        user_id = str(uuid4())
        partner_id = str(uuid4())
        unit_ids = [str(uuid4()), str(uuid4())]
        
        # Mock responses
        mock_db.execute.side_effect = [
            Mock(data=[]),  # Delete response
            Mock(data=[     # Insert response
                {
                    "id": str(uuid4()),
                    "user_id": user_id,
                    "communication_partner_id": partner_id,
                    "unit_id": unit_ids[0],
                    "priority": 1,
                    "is_custom": False
                },
                {
                    "id": str(uuid4()),
                    "user_id": user_id,
                    "communication_partner_id": partner_id,
                    "unit_id": unit_ids[1],
                    "priority": 2,
                    "is_custom": False
                }
            ])
        ]
        
        repo = CommunicationRepository(mock_db)
        result = await repo.save_user_partner_situations(user_id, partner_id, unit_ids)
        
        # Assertions
        assert len(result) == 2
        assert result[0]["priority"] == 1
        assert result[1]["priority"] == 2
        assert result[0]["is_custom"] == False
        
        # Verify table name
        mock_db.table.assert_any_call("user_partner_units")