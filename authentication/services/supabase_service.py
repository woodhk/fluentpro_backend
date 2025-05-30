from supabase import create_client, Client
from django.conf import settings
from typing import Dict, Any, Optional
from datetime import datetime
import uuid


class SupabaseService:
    """
    Service class for interacting with Supabase
    """
    
    def __init__(self):
        self.client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_KEY
        )
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new user in Supabase
        """
        try:
            # Generate a unique ID if not provided
            if 'id' not in user_data:
                user_data['id'] = str(uuid.uuid4())
            
            # Ensure date_of_birth is in the correct format
            if isinstance(user_data.get('date_of_birth'), datetime):
                user_data['date_of_birth'] = user_data['date_of_birth'].strftime('%Y-%m-%d')
            
            # Add timestamp fields
            user_data['created_at'] = datetime.utcnow().isoformat()
            user_data['updated_at'] = datetime.utcnow().isoformat()
            
            # Insert user into Supabase
            response = self.client.table('users').insert(user_data).execute()
            
            if response.data:
                return response.data[0]
            else:
                raise Exception('Failed to create user in Supabase')
                
        except Exception as e:
            raise Exception(f'Supabase error: {str(e)}')
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get a user by email from Supabase
        """
        try:
            response = self.client.table('users').select('*').eq('email', email).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
            
        except Exception as e:
            raise Exception(f'Supabase error: {str(e)}')
    
    def get_user_by_auth0_id(self, auth0_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a user by Auth0 ID from Supabase
        """
        try:
            response = self.client.table('users').select('*').eq('auth0_id', auth0_id).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
            
        except Exception as e:
            raise Exception(f'Supabase error: {str(e)}')
    
    def update_user(self, user_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a user in Supabase
        """
        try:
            # Add updated timestamp
            update_data['updated_at'] = datetime.utcnow().isoformat()
            
            # Update user in Supabase
            response = self.client.table('users').update(update_data).eq('id', user_id).execute()
            
            if response.data:
                return response.data[0]
            else:
                raise Exception('Failed to update user in Supabase')
                
        except Exception as e:
            raise Exception(f'Supabase error: {str(e)}')
    
    def link_auth0_to_user(self, email: str, auth0_id: str) -> Dict[str, Any]:
        """
        Link an Auth0 ID to an existing user
        """
        try:
            user = self.get_user_by_email(email)
            if not user:
                raise Exception('User not found')
            
            return self.update_user(user['id'], {'auth0_id': auth0_id})
            
        except Exception as e:
            raise Exception(f'Failed to link Auth0 ID: {str(e)}')
    
    def delete_user(self, user_id: str) -> bool:
        """
        Delete a user from Supabase (soft delete by setting is_active to false)
        """
        try:
            response = self.client.table('users').update({
                'is_active': False,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', user_id).execute()
            
            return bool(response.data)
            
        except Exception as e:
            raise Exception(f'Supabase error: {str(e)}')