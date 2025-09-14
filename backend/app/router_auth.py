from fastapi import APIRouter
from .services.oauth import router as google_oauth_router

router = APIRouter()
router.include_router(google_oauth_router)
