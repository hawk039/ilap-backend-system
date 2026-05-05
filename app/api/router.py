from fastapi import APIRouter

from app.api.routes import admin, auth, conversations, legal_categories, support, users

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, tags=["users"])
api_router.include_router(legal_categories.router, prefix="/legal-categories", tags=["legal-categories"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
api_router.include_router(support.router, tags=["support"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
