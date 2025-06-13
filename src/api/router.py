from fastapi import APIRouter
from .v1.auth.auth import router as auth_router
from .v1.users.users import router as users_router
from .v1.onboarding.part_1 import router as onboarding_part_1_router
from .v1.admin import router as admin_router
from .v1.onboarding.part_2 import router as onboarding_part_2_router

api_router = APIRouter()

# Include all v1 routes
api_router.include_router(auth_router, prefix="/v1")
api_router.include_router(users_router, prefix="/v1")
api_router.include_router(onboarding_part_1_router, prefix="/v1/onboarding")
api_router.include_router(admin_router, prefix="/v1")
api_router.include_router(onboarding_part_2_router, prefix="/v1/onboarding")
