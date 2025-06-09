from supabase import Client
from typing import Dict, Any, Optional, List
import uuid

class SupabaseUserRepository:
    def __init__(self, client: Client):
        self.client = client
        self.table = "users"
    
    async def get_user_by_auth0_id(self, auth0_id: str) -> Optional[Dict[str, Any]]:
        """Get user by Auth0 ID"""
        try:
            result = self.client.table(self.table).select('*').eq('auth0_id', auth0_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error getting user by auth0_id: {e}")
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            result = self.client.table(self.table).select('*').eq('id', user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error getting user by id: {e}")
            return None
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user"""
        try:
            # Generate UUID if not provided
            if 'id' not in user_data:
                user_data['id'] = str(uuid.uuid4())
            
            # Convert date objects to string format for Supabase
            if 'date_of_birth' in user_data and user_data['date_of_birth']:
                if hasattr(user_data['date_of_birth'], 'isoformat'):
                    user_data['date_of_birth'] = user_data['date_of_birth'].isoformat()
            
            result = self.client.table(self.table).insert(user_data).execute()
            return result.data[0]
        except Exception as e:
            print(f"Error creating user: {e}")
            raise e
    
    async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile"""
        try:
            result = self.client.table(self.table).update(user_data).eq('id', user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error updating user: {e}")
            raise e
    
    async def get_all_users(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all users with pagination"""
        try:
            result = self.client.table(self.table).select('*').range(offset, offset + limit - 1).execute()
            return result.data
        except Exception as e:
            print(f"Error getting all users: {e}")
            return []