import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.services.onboarding.job_matching_service import JobMatchingService

class TestJobMatchingService:
    """Test job matching service."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database client."""
        return Mock()
    
    @pytest.fixture
    def mock_dependencies(self):
        """Mock all service dependencies."""
        with patch('src.services.onboarding.job_matching_service.openai_client') as mock_openai, \
             patch('src.services.onboarding.job_matching_service.azure_search_client') as mock_azure:
            
            # Setup OpenAI mock
            mock_openai.generate_embedding = AsyncMock(
                return_value=[0.1] * 1536
            )
            
            # Setup Azure Search mock
            mock_azure.search_roles = AsyncMock(
                return_value=[
                    {
                        "id": "role1",
                        "title": "Software Engineer",
                        "description": "Develops software",
                        "industry_name": "Banking & Finance",
                        "confidence_score": 0.95
                    }
                ]
            )
            
            yield {
                'openai': mock_openai,
                'azure': mock_azure
            }
    
    @pytest.mark.asyncio
    async def test_search_roles_success(self, mock_db, mock_dependencies):
        """Test successful role search."""
        # Setup mock repositories
        service = JobMatchingService(mock_db)
        
        # Mock profile repo to return user with industry
        service.profile_repo.get_user_by_auth0_id = AsyncMock(
            return_value={
                "id": "user123",
                "industry_id": "ind123"
            }
        )
        
        # This should fail initially (RED)
        result = await service.search_roles(
            auth0_id="auth0|test",
            job_title="Software Developer",
            job_description="I write code and build applications"
        )
        
        assert "matches" in result
        assert len(result["matches"]) == 1
        assert result["matches"][0]["title"] == "Software Engineer"
        assert result["search_metadata"]["user_id"] == "user123"
        
        # Verify OpenAI was called
        mock_dependencies['openai'].generate_embedding.assert_called_once()
        
        # Verify Azure Search was called
        mock_dependencies['azure'].search_roles.assert_called_once_with(
            embedding=[0.1] * 1536,
            industry_id="ind123",
            top_k=5
        )
    
    @pytest.mark.asyncio
    async def test_search_roles_no_industry_set(self, mock_db):
        """Test role search when user has no industry set."""
        service = JobMatchingService(mock_db)
        
        # Mock profile repo to return user without industry
        service.profile_repo.get_user_by_auth0_id = AsyncMock(
            return_value={
                "id": "user123",
                "industry_id": None
            }
        )
        
        # This should fail initially (RED)
        with pytest.raises(Exception) as exc_info:
            await service.search_roles(
                auth0_id="auth0|test",
                job_title="Developer",
                job_description="I develop things"
            )
        
        assert "User industry not set" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_select_existing_role(self, mock_db):
        """Test selecting an existing role."""
        service = JobMatchingService(mock_db)
        
        # Mock profile repo
        service.profile_repo.get_user_by_auth0_id = AsyncMock(
            return_value={"id": "user123"}
        )
        
        # Mock job roles repo
        service.job_roles_repo.update_user_selected_role = AsyncMock(
            return_value={"id": "user123", "selected_role_id": "role123"}
        )
        
        # This should fail initially (RED)
        result = await service.select_role(
            auth0_id="auth0|test",
            role_id="role123"
        )
        
        assert result["success"] == True
        assert result["role_id"] == "role123"
        assert result["is_custom"] == False
        
        # Verify update was called
        service.job_roles_repo.update_user_selected_role.assert_called_once_with(
            user_id="user123",
            role_id="role123"
        )
    
    @pytest.mark.asyncio
    async def test_create_custom_role(self, mock_db, mock_dependencies):
        """Test creating a custom role."""
        service = JobMatchingService(mock_db)
        
        # Mock profile repo
        service.profile_repo.get_user_by_auth0_id = AsyncMock(
            return_value={
                "id": "user123",
                "industry_id": "ind123"
            }
        )
        
        # Mock job roles repo
        service.job_roles_repo.create_custom_role = AsyncMock(
            return_value={
                "id": "new-role-id",
                "title": "Custom Developer",
                "description": "Custom role description"
            }
        )
        
        service.job_roles_repo.update_user_selected_role = AsyncMock(
            return_value={"id": "user123", "selected_role_id": "new-role-id"}
        )
        
        # Mock Azure indexing
        service._index_single_role = AsyncMock()
        
        # This should fail initially (RED)
        result = await service.select_role(
            auth0_id="auth0|test",
            role_id=None,
            custom_title="Custom Developer",
            custom_description="I do custom development work"
        )
        
        assert result["success"] == True
        assert result["role_id"] == "new-role-id"
        assert result["is_custom"] == True
        
        # Verify embedding was generated
        mock_dependencies['openai'].generate_embedding.assert_called_once()
        
        # Verify custom role was created
        service.job_roles_repo.create_custom_role.assert_called_once()