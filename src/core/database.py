from supabase import create_client, Client
from .config import settings

def get_supabase_client() -> Client:
    """Get Supabase client instance with service role key for backend operations"""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

# Dependency for FastAPI
async def get_db() -> Client:
    """FastAPI dependency to get database client"""
    return get_supabase_client()