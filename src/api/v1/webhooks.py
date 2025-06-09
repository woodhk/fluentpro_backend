from fastapi import APIRouter, Request, Depends, HTTPException
from supabase import Client
from ...core.database import get_db
from ...core.rate_limiting import limiter, WEBHOOK_RATE_LIMIT, STRICT_RATE_LIMIT
from ...services.user_service import UserService
import json

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/auth0")
@limiter.limit(WEBHOOK_RATE_LIMIT)
async def auth0_webhook(request: Request, db: Client = Depends(get_db)):
    """Handle Auth0 webhooks for user events"""
    try:
        payload = await request.json()
        event_type = payload.get("event")
        user_data = payload.get("data", {})
        
        user_service = UserService(db)
        
        if event_type == "user.created":
            # Handle new user registration
            await handle_user_created(user_service, user_data)
        
        elif event_type == "user.updated":
            # Handle user profile updates
            await handle_user_updated(user_service, user_data)
        
        elif event_type == "user.deleted":
            # Handle user deletion
            await handle_user_deleted(user_service, user_data)
        
        return {"status": "success", "message": f"Processed {event_type} event"}
    
    except Exception as e:
        print(f"Error processing Auth0 webhook: {e}")
        raise HTTPException(status_code=500, detail="Error processing webhook")

async def handle_user_created(user_service: UserService, user_data: dict):
    """Handle user creation from Auth0"""
    try:
        # Check if user already exists
        existing_user = await user_service.get_user_by_auth0_id(user_data.get("user_id"))
        
        if not existing_user:
            # Create new user in Supabase
            await user_service.create_user_from_auth0({
                "sub": user_data.get("user_id"),
                "email": user_data.get("email"),
                "name": user_data.get("name")
            })
            print(f"Created user from Auth0 webhook: {user_data.get('email')}")
    
    except Exception as e:
        print(f"Error creating user from webhook: {e}")

async def handle_user_updated(user_service: UserService, user_data: dict):
    """Handle user updates from Auth0"""
    try:
        auth0_id = user_data.get("user_id")
        existing_user = await user_service.get_user_by_auth0_id(auth0_id)
        
        if existing_user:
            # Sync user data with Auth0
            await user_service.sync_auth0_profile(auth0_id)
            print(f"Updated user from Auth0 webhook: {user_data.get('email')}")
    
    except Exception as e:
        print(f"Error updating user from webhook: {e}")

async def handle_user_deleted(user_service: UserService, user_data: dict):
    """Handle user deletion from Auth0"""
    try:
        # You might want to soft delete or handle this differently
        print(f"User deleted in Auth0: {user_data.get('email')}")
        # Implementation depends on your business logic
    
    except Exception as e:
        print(f"Error handling user deletion from webhook: {e}")