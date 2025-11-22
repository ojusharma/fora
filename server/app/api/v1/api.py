"""
API v1 router aggregation.

This module combines all v1 API endpoints.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import listings, tags

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(listings.router, prefix="/listings", tags=["listings"])
api_router.include_router(tags.router, prefix="/tags", tags=["tags"])

# Add more routers here as you create them:
# api_router.include_router(users.router, prefix="/users", tags=["users"])
