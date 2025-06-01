from supabase import create_client, Client
from django.conf import settings
from typing import Dict, Any, Optional, List
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
    
    def update_user_native_language(self, auth0_id: str, native_language: str) -> Dict[str, Any]:
        """
        Update a user's native language based on their Auth0 ID
        """
        try:
            # Find user by Auth0 ID
            user = self.get_user_by_auth0_id(auth0_id)
            if not user:
                return {
                    'success': False,
                    'error': 'User not found'
                }
            
            # Update the native language
            update_data = {
                'native_language': native_language,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            response = self.client.table('users').update(update_data).eq('id', user['id']).execute()
            
            if response.data:
                return {
                    'success': True,
                    'user_id': user['id'],
                    'native_language': native_language
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to update native language'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Supabase error: {str(e)}'
            }
    
    def update_user_industry(self, auth0_id: str, industry_id: str) -> Dict[str, Any]:
        """
        Update a user's industry based on their Auth0 ID
        """
        try:
            # Find user by Auth0 ID
            user = self.get_user_by_auth0_id(auth0_id)
            if not user:
                return {
                    'success': False,
                    'error': 'User not found'
                }
            
            # Validate that the industry exists and is available
            industry_response = self.client.table('industries').select('*').eq('id', industry_id).execute()
            
            if not industry_response.data:
                return {
                    'success': False,
                    'error': 'Industry not found'
                }
            
            industry = industry_response.data[0]
            if industry.get('status') != 'available':
                return {
                    'success': False,
                    'error': 'Industry is not available for selection'
                }
            
            # Update the user's industry
            update_data = {
                'industry_id': industry_id,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            response = self.client.table('users').update(update_data).eq('id', user['id']).execute()
            
            if response.data:
                return {
                    'success': True,
                    'user_id': user['id'],
                    'industry_id': industry_id,
                    'industry_name': industry.get('name')
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to update industry'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Supabase error: {str(e)}'
            }
    
    def get_available_industries(self) -> list:
        """
        Get all available industries for selection
        """
        try:
            response = self.client.table('industries').select('*').eq('status', 'available').order('sort_order', desc=False).execute()
            
            if response.data:
                return [
                    {
                        'id': industry['id'],
                        'name': industry['name'],
                        'sort_order': industry.get('sort_order', 0)
                    }
                    for industry in response.data
                ]
            else:
                return []
                
        except Exception as e:
            raise Exception(f'Supabase error: {str(e)}')
    
    def get_all_roles_with_industry(self) -> List[Dict[str, Any]]:
        """
        Get all roles with their industry information for Azure AI Search indexing
        """
        try:
            response = self.client.table('roles').select(
                'id, title, description, hierarchy_level, search_keywords, industry_id, is_active, created_at, industries(name)'
            ).eq('is_active', True).execute()
            
            if response.data:
                roles_with_industry = []
                for role in response.data:
                    role_data = {
                        'id': role['id'],
                        'title': role['title'],
                        'description': role['description'],
                        'hierarchy_level': role['hierarchy_level'],
                        'search_keywords': role['search_keywords'],
                        'industry_id': role['industry_id'],
                        'industry_name': role['industries']['name'] if role['industries'] else '',
                        'is_active': role['is_active'],
                        'created_at': role['created_at']
                    }
                    roles_with_industry.append(role_data)
                return roles_with_industry
            else:
                return []
                
        except Exception as e:
            raise Exception(f'Supabase error: {str(e)}')
    
    def update_user_selected_role(self, auth0_id: str, role_id: str) -> Dict[str, Any]:
        """
        Update a user's selected role based on their Auth0 ID
        """
        try:
            # Find user by Auth0 ID
            user = self.get_user_by_auth0_id(auth0_id)
            if not user:
                return {
                    'success': False,
                    'error': 'User not found'
                }
            
            # Validate that the role exists and is active
            role_response = self.client.table('roles').select('*').eq('id', role_id).execute()
            
            if not role_response.data:
                return {
                    'success': False,
                    'error': 'Role not found'
                }
            
            role = role_response.data[0]
            if not role.get('is_active', True):
                return {
                    'success': False,
                    'error': 'Role is not available for selection'
                }
            
            # Update the user's selected role
            update_data = {
                'selected_role_id': role_id,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            response = self.client.table('users').update(update_data).eq('id', user['id']).execute()
            
            if response.data:
                return {
                    'success': True,
                    'user_id': user['id'],
                    'selected_role_id': role_id,
                    'role_title': role.get('title')
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to update selected role'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Supabase error: {str(e)}'
            }
    
    def get_user_full_profile(self, auth0_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a user's full profile including industry and selected role information
        """
        try:
            response = self.client.table('users').select(
                'id, full_name, email, date_of_birth, auth0_id, native_language, industry_id, selected_role_id, onboarding_status, hierarchy_level, industries(name), roles(title, description)'
            ).eq('auth0_id', auth0_id).execute()
            
            if response.data and len(response.data) > 0:
                user = response.data[0]
                # Flatten the nested relations for easier access
                user_profile = {
                    'id': user['id'],
                    'full_name': user['full_name'],
                    'email': user['email'],
                    'date_of_birth': user['date_of_birth'],
                    'auth0_id': user['auth0_id'],
                    'native_language': user['native_language'],
                    'industry_id': user['industry_id'],
                    'industry_name': user['industries']['name'] if user['industries'] else None,
                    'selected_role_id': user['selected_role_id'],
                    'role_title': user['roles']['title'] if user['roles'] else None,
                    'role_description': user['roles']['description'] if user['roles'] else None,
                    'onboarding_status': user['onboarding_status'],
                    'hierarchy_level': user['hierarchy_level']
                }
                return user_profile
            return None
            
        except Exception as e:
            raise Exception(f'Supabase error: {str(e)}')
    
    def create_new_role(self, title: str, description: str, industry_id: str, 
                       search_keywords: List[str], hierarchy_level: str = 'associate') -> Dict[str, Any]:
        """
        Create a new role in the roles table
        """
        try:
            # Generate a unique ID for the role
            role_id = str(uuid.uuid4())
            
            # Prepare role data
            role_data = {
                'id': role_id,
                'title': title,
                'description': description,
                'industry_id': industry_id,
                'hierarchy_level': hierarchy_level,
                'search_keywords': search_keywords,
                'is_active': True,
                'created_at': datetime.utcnow().isoformat()
            }
            
            # Insert role into Supabase
            response = self.client.table('roles').insert(role_data).execute()
            
            if response.data:
                created_role = response.data[0]
                return {
                    'success': True,
                    'role': created_role,
                    'role_id': role_id
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to create role in Supabase'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Supabase error: {str(e)}'
            }
    
    def get_role_with_industry(self, role_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a role by ID with industry information
        """
        try:
            response = self.client.table('roles').select(
                'id, title, description, hierarchy_level, search_keywords, industry_id, is_active, created_at, industries(name)'
            ).eq('id', role_id).execute()
            
            if response.data and len(response.data) > 0:
                role = response.data[0]
                # Flatten the nested relations for easier access
                role_data = {
                    'id': role['id'],
                    'title': role['title'],
                    'description': role['description'],
                    'hierarchy_level': role['hierarchy_level'],
                    'search_keywords': role['search_keywords'],
                    'industry_id': role['industry_id'],
                    'industry_name': role['industries']['name'] if role['industries'] else '',
                    'is_active': role['is_active'],
                    'created_at': role['created_at']
                }
                return role_data
            return None
            
        except Exception as e:
            raise Exception(f'Supabase error: {str(e)}')
    
    def update_user_session_role_source(self, auth0_id: str, role_source: str, role_details: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Update user session with role source information for onboarding tracking
        role_source: 'selected' for existing roles, 'created' for new roles
        """
        try:
            # Find user by Auth0 ID
            user = self.get_user_by_auth0_id(auth0_id)
            if not user:
                return {
                    'success': False,
                    'error': 'User not found'
                }
            
            # Get or create active user session
            session_response = self.client.table('user_sessions').select('*').eq('user_id', user['id']).eq('is_active', True).execute()
            
            session_data = {
                'role_source': role_source,
                'role_source_timestamp': datetime.utcnow().isoformat()
            }
            
            if role_details:
                session_data.update(role_details)
            
            if session_response.data and len(session_response.data) > 0:
                # Update existing session
                session = session_response.data[0]
                existing_data = session.get('session_data_json', {})
                existing_data.update(session_data)
                
                update_response = self.client.table('user_sessions').update({
                    'session_data_json': existing_data,
                    'updated_at': datetime.utcnow().isoformat()
                }).eq('id', session['id']).execute()
                
                if update_response.data:
                    return {
                        'success': True,
                        'session_id': session['id'],
                        'role_source': role_source
                    }
            else:
                # Create new session if none exists
                from datetime import timedelta
                session_data_full = {
                    'user_id': user['id'],
                    'session_data_json': session_data,
                    'phase': 'basic_info',
                    'expires_at': (datetime.utcnow() + timedelta(days=7)).isoformat(),
                    'is_active': True,
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                }
                
                create_response = self.client.table('user_sessions').insert(session_data_full).execute()
                
                if create_response.data:
                    return {
                        'success': True,
                        'session_id': create_response.data[0]['id'],
                        'role_source': role_source
                    }
            
            return {
                'success': False,
                'error': 'Failed to update session data'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Supabase error: {str(e)}'
            }
    
    def get_user_role_source(self, auth0_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the role source information for a user from their active session
        """
        try:
            # Find user by Auth0 ID
            user = self.get_user_by_auth0_id(auth0_id)
            if not user:
                return None
            
            # Get active user session
            session_response = self.client.table('user_sessions').select('*').eq('user_id', user['id']).eq('is_active', True).execute()
            
            if session_response.data and len(session_response.data) > 0:
                session = session_response.data[0]
                session_data = session.get('session_data_json', {})
                
                if 'role_source' in session_data:
                    return {
                        'role_source': session_data.get('role_source'),
                        'role_source_timestamp': session_data.get('role_source_timestamp'),
                        'session_id': session['id']
                    }
            
            return None
            
        except Exception as e:
            raise Exception(f'Supabase error: {str(e)}')