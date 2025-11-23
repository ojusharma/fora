"""
API v1 router aggregation.

This module combines all v1 API endpoints.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    listings,
    feed,
    tags,
    user,
    user_stats,
    user_preferences,
    listing_applicants,
)
from app.api.v1 import admin

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(listings.router, prefix="/listings", tags=["listings"])
api_router.include_router(feed.router, prefix="/feed", tags=["feed"])
api_router.include_router(tags.router, prefix="/tags", tags=["tags"])
api_router.include_router(user.router, prefix="/users", tags=["users"])
api_router.include_router(user_stats.router, prefix="/user-stats", tags=["user-stats"])
api_router.include_router(
    user_preferences.router, prefix="/user-preferences", tags=["user-preferences"]
)
api_router.include_router(
    listing_applicants.router, prefix="/applicants", tags=["applicants"]
)
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
