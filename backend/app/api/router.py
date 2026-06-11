from fastapi import APIRouter

from app.api.routes import ai, auth, finance, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(finance.router, prefix="/finance")
api_router.include_router(ai.router)
