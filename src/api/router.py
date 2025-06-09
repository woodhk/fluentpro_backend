from fastapi import APIRouter
from .v1 import auth, users, webhooks

api_router = APIRouter()

# Include all v1 routes
api_router.include_router(auth.router, prefix="/v1")
api_router.include_router(users.router, prefix="/v1")
api_router.include_router(webhooks.router, prefix="/v1")