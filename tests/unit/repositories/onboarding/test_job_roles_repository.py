import pytest
from unittest.mock import Mock, AsyncMock
from src.repositories.onboarding.job_roles_repository import JobRolesRepository

class TestJobRolesRepository:
    """Test job roles repository."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock Supabase client."""
        mock = Mock()
        mock.table = Mock(return_value=mock)
        mock.select = Mock(return_value=mock)
        mock.insert = Mock(return_value=mock)
        mock.update = Mock(return_value=mock)
        mock.eq = Mock(return_value=mock)
        mock.execute = Mock()
        return mock
    
    @pytest.mark.asyncio
    async def test_get_roles_by_industry(self, mock_db):
        """Test getting roles by industry."""
        # Setup mock response
        mock_db.execute.return_value = Mock(
            data=[
                {"id": "role1", "title": "Software Engineer", "industry_id": "ind1"},
                {"id": "role2", "title": "Data Analyst", "industry_id": "ind1"}
            ]
        )
        
        # This should fail initially (RED)
        repo = JobRolesRepository(mock_db)
        result = await repo.get_roles_by_industry("ind1")
        
        assert len(result) == 2
        assert result[0]["title"] == "Software Engineer"
        
        # Verify database calls
        mock_db.table.assert_called_with("roles")
        mock_db.eq.assert_called_with("industry_id", "ind1")
    
    @pytest.mark.asyncio
    async def test_create_custom_role(self, mock_db):
        """Test creating a custom role."""
        # Setup mock response
        mock_db.execute.return_value = Mock(
            data=[{
                "id": "new-role-id",
                "title": "Custom Role",
                "description": "Custom Description",
                "industry_id": "ind1",
                "embedding_vector": [0.1, 0.2],
                "is_system_role": False
            }]
        )
        
        # This should fail initially (RED)
        repo = JobRolesRepository(mock_db)
        result = await repo.create_custom_role(
            title="Custom Role",
            description="Custom Description",
            industry_id="ind1",
            embedding=[0.1, 0.2]
        )
        
        assert result["id"] == "new-role-id"
        assert result["is_system_role"] == False
        
        # Verify insert was called
        mock_db.insert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_all_roles_for_indexing(self, mock_db):
        """Test getting all roles with industry information."""
        # Setup mock response
        mock_db.execute.return_value = Mock(
            data=[{
                "id": "role1",
                "title": "Software Engineer",
                "description": "Develops software",
                "industry_id": "ind1",
                "embedding_vector": [0.1, 0.2],
                "is_system_role": True,
                "industries": {"id": "ind1", "name": "Banking & Finance"}
            }]
        )
        
        # This should fail initially (RED)
        repo = JobRolesRepository(mock_db)
        result = await repo.get_all_roles_for_indexing()
        
        assert len(result) == 1
        assert result[0]["industry_name"] == "Banking & Finance"
        
        # Verify join query
        mock_db.select.assert_called_with(
            "id, title, description, industry_id, embedding_vector, is_system_role, industries!inner(id, name)"
        )
    
    @pytest.mark.asyncio
    async def test_update_user_selected_role(self, mock_db):
        """Test updating user's selected role."""
        # Setup mock response
        mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock(
            data=[{
                "id": "user1",
                "selected_role_id": "role1",
                "custom_role_title": None,
                "custom_role_description": None
            }]
        )
        
        # This should fail initially (RED)
        repo = JobRolesRepository(mock_db)
        result = await repo.update_user_selected_role(
            user_id="user1",
            role_id="role1"
        )
        
        assert result["selected_role_id"] == "role1"
        
        # Verify correct table was used
        mock_db.table.assert_any_call("users")