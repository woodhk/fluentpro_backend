import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.services.onboarding.job_matching_service import JobMatchingService

@pytest.mark.integration
class TestRoleSearchIntegration:
    """Integration tests for role search feature."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database with realistic data."""
        mock = Mock()
        
        # Create a chain-able mock
        mock.table = Mock(return_value=mock)
        mock.select = Mock(return_value=mock)
        mock.insert = Mock(return_value=mock)
        mock.update = Mock(return_value=mock)
        mock.eq = Mock(return_value=mock)
        mock.execute = Mock()
        
        return mock
    
    @pytest.mark.asyncio
    async def test_full_role_search_flow(self, mock_db):
        """Test complete role search flow from input to results."""
        # Setup the execute mock to return proper data structure
        mock_result = Mock()
        mock_result.data = [{
            "id": "user123",
            "auth0_id": "auth0|test",
            "industry_id": "ind-banking"
        }]
        mock_db.execute.return_value = mock_result
        
        # Mock OpenAI and Azure Search where they're used
        with patch('src.services.onboarding.job_matching_service.openai_client') as mock_openai_client, \
             patch('src.services.onboarding.job_matching_service.azure_search_client') as mock_azure_client:
            
            # Mock embedding response
            mock_openai_client.generate_embedding = AsyncMock(return_value=[0.1] * 1536)
            
            # Mock search results
            mock_search_results = [
                {
                    "id": "role1",
                    "title": "Software Engineer",
                    "description": "Develops banking software",
                    "industry_name": "Banking & Finance",
                    "confidence_score": 0.95
                },
                {
                    "id": "role2",
                    "title": "Senior Developer",
                    "description": "Leads development teams",
                    "industry_name": "Banking & Finance",
                    "confidence_score": 0.88
                }
            ]
            mock_azure_client.search_roles = AsyncMock(return_value=mock_search_results)
            
            # Test the service
            service = JobMatchingService(mock_db)
            
            result = await service.search_roles(
                auth0_id="auth0|test",
                job_title="Software Developer",
                job_description="I develop web applications for financial institutions"
            )
            
            assert "matches" in result
            assert len(result["matches"]) == 2
            assert result["matches"][0]["confidence_score"] == 0.95
            assert result["search_metadata"]["industry_id"] == "ind-banking"
            
            # Verify OpenAI was called
            mock_openai_client.generate_embedding.assert_called_once()
            
            # Verify Azure Search was called
            mock_azure_client.search_roles.assert_called_once_with(
                embedding=[0.1] * 1536,
                industry_id="ind-banking",
                top_k=5
            )
    
    @pytest.mark.asyncio
    async def test_custom_role_creation_and_indexing(self, mock_db):
        """Test custom role creation with Azure indexing."""
        # Create different mock results for different calls
        user_result = Mock()
        user_result.data = [{
            "id": "user123",
            "auth0_id": "auth0|test",
            "industry_id": "ind-shipping"
        }]
        
        role_result = Mock()
        role_result.data = [{
            "id": "new-custom-role",
            "title": "Logistics Coordinator",
            "description": "Manages shipping operations",
            "industry_id": "ind-shipping",
            "embedding_vector": [0.1] * 1536,
            "is_system_role": False
        }]
        
        update_result = Mock()
        update_result.data = [{
            "id": "user123",
            "selected_role_id": "new-custom-role"
        }]
        
        industry_result = Mock()
        industry_result.data = [{"name": "Shipping & Logistics"}]
        
        # The execute method on mock_db should be used for role creation (job_roles table)
        mock_db.execute.return_value = role_result
        
        # Create a proper mock for the industries table that can be awaited
        mock_industries_table = Mock()
        mock_industries_table.select = Mock(return_value=mock_industries_table)
        mock_industries_table.eq = Mock(return_value=mock_industries_table)
        # Make execute an async function that returns the industry result
        async def async_execute():
            return industry_result
        mock_industries_table.execute = async_execute
        
        # Create a mock for the users table update
        mock_users_table = Mock()
        mock_users_table.update = Mock(return_value=mock_users_table)
        mock_users_table.eq = Mock(return_value=mock_users_table)
        # Make execute an async function that returns the update result
        async def async_update_execute():
            return update_result
        mock_users_table.execute = async_update_execute
        
        # Create a comprehensive mock for the users table that handles both select and update operations
        mock_users_comprehensive = Mock()
        
        # For select operations (get_user_by_auth0_id)
        mock_users_comprehensive.select = Mock(return_value=mock_users_comprehensive)
        mock_users_comprehensive.eq = Mock(return_value=mock_users_comprehensive)
        mock_users_comprehensive.execute = Mock(return_value=user_result)
        
        # For update operations (update_user_selected_role) - return sync mock
        mock_update_chain = Mock()
        mock_update_chain.eq = Mock(return_value=mock_update_chain)
        mock_update_chain.execute = Mock(return_value=update_result)
        mock_users_comprehensive.update = Mock(return_value=mock_update_chain)
        
        # Create mock for job_roles table operations
        mock_job_roles_table = Mock()
        mock_job_roles_table.insert = Mock(return_value=mock_job_roles_table)
        mock_job_roles_table.execute = Mock(return_value=role_result)
        
        # Setup table side effect to return appropriate mock
        def table_side_effect(table_name):
            if table_name == "industries":
                return mock_industries_table
            elif table_name == "users":
                return mock_users_comprehensive
            elif table_name == "job_roles":
                return mock_job_roles_table  # For role creation
            # For the default table, return the regular mock
            return mock_db
        
        mock_db.table.side_effect = table_side_effect
        
        # Mock OpenAI and Azure Search where they're used
        with patch('src.services.onboarding.job_matching_service.openai_client') as mock_openai_client, \
             patch('src.services.onboarding.job_matching_service.azure_search_client') as mock_azure_client:
            
            mock_openai_client.generate_embedding = AsyncMock(return_value=[0.2] * 1536)
            mock_azure_client.upload_documents = AsyncMock()
            
            # Test the service
            service = JobMatchingService(mock_db)
            
            result = await service.select_role(
                auth0_id="auth0|test",
                role_id=None,
                custom_title="Logistics Coordinator",
                custom_description="I manage shipping operations and coordinate logistics"
            )
            
            assert result["success"] == True
            assert result["is_custom"] == True
            assert result["role_id"] == "new-custom-role"
            
            # Verify Azure indexing was called
            mock_azure_client.upload_documents.assert_called_once()
            upload_call = mock_azure_client.upload_documents.call_args[0]
            documents = upload_call[0]
            
            assert len(documents) == 1
            assert documents[0]["id"] == "new-custom-role"
            assert documents[0]["industry_name"] == "Shipping & Logistics"
    
    @pytest.mark.asyncio
    async def test_error_handling_cascade(self, mock_db):
        """Test error handling through the integration."""
        # Setup user without industry
        mock_result = Mock()
        mock_result.data = [{
            "id": "user123",
            "auth0_id": "auth0|test",
            "industry_id": None  # No industry set
        }]
        mock_db.execute.return_value = mock_result
        
        service = JobMatchingService(mock_db)
        
        with pytest.raises(Exception) as exc_info:
            await service.search_roles(
                auth0_id="auth0|test",
                job_title="Developer",
                job_description="I develop software applications"
            )
        
        assert "User industry not set" in str(exc_info.value)