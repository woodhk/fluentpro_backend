from fastapi import APIRouter
from .v1.auth.auth import router as auth_router
from .v1.users.users import router as users_router

api_router = APIRouter()

# Include all v1 routes
api_router.include_router(auth_router, prefix="/v1")
api_router.include_router(users_router, prefix="/v1")