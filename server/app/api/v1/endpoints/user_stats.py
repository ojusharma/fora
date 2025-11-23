"""
API endpoints for user stats operations.
Stats are computed on-the-fly from source tables (listings, listing_applicants).
"""

from fastapi import APIRouter, Depends
from uuid import UUID

from app.core.database import get_supabase_client
from app.crud.user_stats import UserStatsCRUD
from app.schemas.user_stats import UserStatsResponse
from supabase import Client

router = APIRouter()


# ==================== DEPENDENCIES ====================

def get_user_stats_crud(supabase: Client = Depends(get_supabase_client)) -> UserStatsCRUD:
    """Dependency to get UserStatsCRUD instance."""
    return UserStatsCRUD(supabase)


# ==================== USER STATS ENDPOINTS ====================

@router.get(
    "/{user_id}/stats",
    response_model=UserStatsResponse,
    summary="Get user stats",
    description="Calculate and return user statistics from source data (listings, applications, etc.)",
)
async def get_user_stats(
    user_id: UUID,
    crud: UserStatsCRUD = Depends(get_user_stats_crud),
):
    """Get statistics for a specific user, computed on-the-fly."""
    result = await crud.get_user_stats(user_id)
    return result


@router.get(
    "/{user_id}/stats/or-create",
    response_model=UserStatsResponse,
    summary="Get user stats (alias)",
    description="Same as GET /{user_id}/stats - stats are always computed, never need creation.",
)
async def get_or_create_user_stats(
    user_id: UUID,
    crud: UserStatsCRUD = Depends(get_user_stats_crud),
):
    """Get user stats. Stats are computed on-the-fly, so they always 'exist'."""
    result = await crud.get_or_create_user_stats(user_id)
    return result
