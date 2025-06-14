import pytest
from unittest.mock import Mock, patch
from src.services.users.user_service import UserService
from src.integrations.supabase import SupabaseUserRepository
from src.core.exceptions import UserNotFoundError

class TestSupabaseUserRepository:
    """Test Supabase user repository operations"""
    
    @pytest.mark.asyncio
    async def test_get_user_by_auth0_id_found(self, mock_supabase_client):
        """Test getting user by Auth0 ID when user exists"""
        # Setup mock response
        mock_result = Mock()
        mock_result.data = [{"id": "user123", "auth0_id": "auth0|test", "email": "test@example.com"}]
        mock_supabase_client.table_mock.select.return_value.eq.return_value.execute.return_value = mock_result
        
        repo = SupabaseUserRepository(mock_supabase_client)
        result = await repo.get_user_by_auth0_id("auth0|test")
        
        assert result is not None
        assert result["id"] == "user123"
        assert result["auth0_id"] == "auth0|test"
        mock_supabase_client.table_mock.select.assert_called_with('*')
    
    @pytest.mark.asyncio
    async def test_get_user_by_auth0_id_not_found(self, mock_supabase_client):
        """Test getting user by Auth0 ID when user doesn't exist"""
        # Setup mock response with empty data
        mock_result = Mock()
        mock_result.data = []
        mock_supabase_client.table_mock.select.return_value.eq.return_value.execute.return_value = mock_result
        
        repo = SupabaseUserRepository(mock_supabase_client)
        result = await repo.get_user_by_auth0_id("auth0|nonexistent")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, mock_supabase_client):
        """Test successful user creation"""
        # Setup mock response
        mock_result = Mock()
        mock_result.data = [{"id": "new-user-123", "email": "new@example.com"}]
        mock_supabase_client.table_mock.insert.return_value.execute.return_value = mock_result
        
        repo = SupabaseUserRepository(mock_supabase_client)
        user_data = {"email": "new@example.com", "auth0_id": "auth0|new"}
        
        result = await repo.create_user(user_data)
        
        assert result["id"] == "new-user-123"
        assert result["email"] == "new@example.com"
        mock_supabase_client.table_mock.insert.assert_called_with(user_data)
    
    @pytest.mark.asyncio
    async def test_update_user_success(self, mock_supabase_client):
        """Test successful user update"""
        # Setup mock response
        mock_result = Mock()
        mock_result.data = [{"id": "user123", "full_name": "Updated Name"}]
        mock_supabase_client.table_mock.update.return_value.eq.return_value.execute.return_value = mock_result
        
        repo = SupabaseUserRepository(mock_supabase_client)
        update_data = {"full_name": "Updated Name"}
        
        result = await repo.update_user("user123", update_data)
        
        assert result["full_name"] == "Updated Name"
        mock_supabase_client.table_mock.update.assert_called_with(update_data)

class TestUserService:
    """Test user service business logic"""
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_found(self, mock_supabase_client):
        """Test getting user by ID when user exists"""
        user_service = UserService(mock_supabase_client)
        
        with patch.object(user_service.user_repo, 'get_user_by_id') as mock_get:
            mock_get.return_value = {"id": "user123", "email": "test@example.com"}
            
            result = await user_service.get_user_by_id("user123")
            assert result["id"] == "user123"
            mock_get.assert_called_once_with("user123")
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, mock_supabase_client):
        """Test getting user by ID when user doesn't exist"""
        user_service = UserService(mock_supabase_client)
        
        with patch.object(user_service.user_repo, 'get_user_by_id') as mock_get:
            mock_get.return_value = None
            
            with pytest.raises(UserNotFoundError):
                await user_service.get_user_by_id("nonexistent")
    
    @pytest.mark.asyncio
    async def test_create_user_from_auth0_success(self, mock_supabase_client):
        """Test creating user from Auth0 data"""
        user_service = UserService(mock_supabase_client)
        
        auth0_data = {
            "sub": "auth0|test123",
            "email": "test@example.com",
            "name": "Test User"
        }
        
        with patch.object(user_service.user_repo, 'create_user') as mock_create:
            mock_create.return_value = {"id": "new-user", "email": "test@example.com"}
            
            result = await user_service.create_user_from_auth0(auth0_data)
            
            assert result["email"] == "test@example.com"
            mock_create.assert_called_once()
            call_args = mock_create.call_args[0][0]
            assert call_args["auth0_id"] == "auth0|test123"
            assert call_args["email"] == "test@example.com"
            assert call_args["full_name"] == "Test User"
            assert call_args["is_active"] is True
    
    @pytest.mark.asyncio
    async def test_update_user_profile_success(self, mock_supabase_client):
        """Test updating user profile"""
        from src.schemas.users.user import UserUpdate
        
        user_service = UserService(mock_supabase_client)
        update_data = UserUpdate(full_name="Updated Name", email="updated@example.com")
        
        with patch.object(user_service.user_repo, 'update_user') as mock_update:
            mock_update.return_value = {"id": "user123", "full_name": "Updated Name"}
            
            result = await user_service.update_user_profile("user123", update_data)
            
            assert result["full_name"] == "Updated Name"
            mock_update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sync_auth0_profile_existing_user(self, mock_supabase_client):
        """Test syncing Auth0 profile for existing user"""
        user_service = UserService(mock_supabase_client)
        
        with patch.object(user_service.user_repo, 'get_user_by_auth0_id') as mock_get, \
             patch.object(user_service.user_repo, 'update_user') as mock_update, \
             patch('src.integrations.auth0.auth0_client.get_user_profile') as mock_auth0:
            
            mock_get.return_value = {"id": "existing-user", "auth0_id": "auth0|test"}
            mock_auth0.return_value = {"email": "updated@example.com", "name": "Updated Name"}
            mock_update.return_value = {"id": "existing-user", "email": "updated@example.com"}
            
            result = await user_service.sync_auth0_profile("auth0|test")
            
            assert result["email"] == "updated@example.com"
            mock_update.assert_called_once()

class TestUserEndpoints:
    """Test user API endpoints"""
    
    def test_get_current_user_profile(self, client_with_auth, auth_headers):
        """Test getting current user profile"""
        response = client_with_auth.get("/api/v1/users/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-user-id-123"
        assert data["email"] == "test@example.com"
        assert data["full_name"] == "Test User"
        assert data["is_active"] is True
    
    def test_get_current_user_profile_unauthenticated(self, client_no_auth):
        """Test getting current user profile without authentication"""
        response = client_no_auth.get("/api/v1/users/me")
        
        assert response.status_code == 403
    
    def test_update_current_user_profile(self, client_with_auth, auth_headers, user_update_data):
        """Test updating current user profile"""
        with patch('src.services.user_service.UserService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.update_user_profile.return_value = {
                "id": "test-user-id-123",
                "email": "test@example.com",
                "full_name": "Updated Test User",
                "date_of_birth": "1990-05-15",
                "is_active": True
            }
            
            response = client_with_auth.put(
                "/api/v1/users/me",
                headers=auth_headers,
                json=user_update_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["full_name"] == "Updated Test User"
            assert data["date_of_birth"] == "1990-05-15"
    
    def test_update_current_user_profile_invalid_data(self, client_with_auth, auth_headers):
        """Test updating current user profile with invalid data"""
        invalid_data = {
            "email": "invalid-email",  # Invalid email format
            "date_of_birth": "invalid-date"  # Invalid date format
        }
        
        response = client_with_auth.put(
            "/api/v1/users/me",
            headers=auth_headers,
            json=invalid_data
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_get_user_by_id(self, client_with_auth, auth_headers):
        """Test getting user by ID"""
        user_id = "another-user-id"
        
        with patch('src.services.user_service.UserService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_user_by_id.return_value = {
                "id": user_id,
                "email": "other@example.com",
                "full_name": "Other User",
                "is_active": True
            }
            
            response = client_with_auth.get(f"/api/v1/users/{user_id}", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == user_id
            assert data["email"] == "other@example.com"
    
    def test_get_user_by_id_not_found(self, client_with_auth, auth_headers):
        """Test getting user by ID when user doesn't exist"""
        user_id = "nonexistent-user"
        
        with patch('src.services.user_service.UserService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.get_user_by_id.side_effect = UserNotFoundError(user_id)
            
            response = client_with_auth.get(f"/api/v1/users/{user_id}", headers=auth_headers)
            
            assert response.status_code == 404
    
    def test_get_user_by_id_unauthenticated(self, client_no_auth):
        """Test getting user by ID without authentication"""
        response = client_no_auth.get("/api/v1/users/some-user-id")
        
        assert response.status_code == 403

class TestUserValidation:
    """Test user data validation"""
    
    def test_user_response_schema_valid(self):
        """Test UserResponse schema with valid data"""
        from src.schemas.users.user import UserResponse
        from datetime import datetime
        
        data = {
            "id": "user123",
            "auth0_id": "auth0|test",
            "email": "test@example.com",
            "full_name": "Test User",
            "date_of_birth": "1990-01-01",
            "is_active": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        user = UserResponse(**data)
        assert user.id == "user123"
        assert user.email == "test@example.com"
    
    def test_user_update_schema_partial(self):
        """Test UserUpdate schema with partial data"""
        from src.schemas.users.user import UserUpdate
        
        # Should allow partial updates
        update = UserUpdate(full_name="New Name")
        assert update.full_name == "New Name"
        assert update.email is None
        assert update.date_of_birth is None
    
    def test_user_create_schema_required_fields(self):
        """Test UserCreate schema requires essential fields"""
        from src.schemas.users.user import UserCreate
        
        # Should require auth0_id and email
        with pytest.raises(ValueError):
            UserCreate(full_name="Test User")  # Missing required fields