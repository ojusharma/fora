"""
API endpoints for user stats operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from uuid import UUID

from app.core.database import get_supabase_client
from app.crud.user_stats import UserStatsCRUD
from app.schemas.user_stats import (
    UserStatsCreate,
    UserStatsUpdate,
    UserStatsResponse,
)
from supabase import Client

router = APIRouter()


# ==================== DEPENDENCIES ====================

def get_user_stats_crud(supabase: Client = Depends(get_supabase_client)) -> UserStatsCRUD:
    """Dependency to get UserStatsCRUD instance."""
    return UserStatsCRUD(supabase)


# ==================== USER STATS ENDPOINTS ====================

@router.post(
    "/",
    response_model=UserStatsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create user stats",
)
async def create_user_stats(
    user_stats: UserStatsCreate,
    crud: UserStatsCRUD = Depends(get_user_stats_crud),
):
    """Create stats for a new user."""
    result = await crud.create_user_stats(user_stats)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create user stats",
        )
    return result


@router.get(
    "/{user_id}",
    response_model=UserStatsResponse,
    summary="Get user stats by user ID",
)
async def get_user_stats(
    user_id: UUID,
    crud: UserStatsCRUD = Depends(get_user_stats_crud),
):
    """Get statistics for a specific user."""
    result = await crud.get_user_stats(user_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User stats not found",
        )
    return result


@router.get(
    "/{user_id}/or-create",
    response_model=UserStatsResponse,
    summary="Get user stats or create if not exists",
)
async def get_or_create_user_stats(
    user_id: UUID,
    crud: UserStatsCRUD = Depends(get_user_stats_crud),
):
    """Get user stats or create with default values if they don't exist."""
    result = await crud.get_or_create_user_stats(user_id)
    return result


@router.patch(
    "/{user_id}",
    response_model=UserStatsResponse,
    summary="Update user stats",
)
async def update_user_stats(
    user_id: UUID,
    user_stats: UserStatsUpdate,
    crud: UserStatsCRUD = Depends(get_user_stats_crud),
):
    """Update statistics for a user."""
    result = await crud.update_user_stats(user_id, user_stats)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User stats not found",
        )
    return result


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user stats",
)
async def delete_user_stats(
    user_id: UUID,
    crud: UserStatsCRUD = Depends(get_user_stats_crud),
):
    """Delete statistics for a user."""
    success = await crud.delete_user_stats(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User stats not found",
        )


@router.post(
    "/{user_id}/increment/listings-posted",
    response_model=UserStatsResponse,
    summary="Increment listings posted count",
)
async def increment_listings_posted(
    user_id: UUID,
    crud: UserStatsCRUD = Depends(get_user_stats_crud),
):
    """Increment the number of listings posted by a user."""
    result = await crud.increment_listings_posted(user_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User stats not found",
        )
    return result


@router.post(
    "/{user_id}/increment/listings-applied",
    response_model=UserStatsResponse,
    summary="Increment listings applied count",
)
async def increment_listings_applied(
    user_id: UUID,
    crud: UserStatsCRUD = Depends(get_user_stats_crud),
):
    """Increment the number of listings a user has applied to."""
    result = await crud.increment_listings_applied(user_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User stats not found",
        )
    return result


@router.post(
    "/{user_id}/increment/listings-assigned",
    response_model=UserStatsResponse,
    summary="Increment listings assigned count",
)
async def increment_listings_assigned(
    user_id: UUID,
    crud: UserStatsCRUD = Depends(get_user_stats_crud),
):
    """Increment the number of listings assigned to a user."""
    result = await crud.increment_listings_assigned(user_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User stats not found",
        )
    return result


@router.post(
    "/{user_id}/increment/listings-completed",
    response_model=UserStatsResponse,
    summary="Increment listings completed count",
)
async def increment_listings_completed(
    user_id: UUID,
    crud: UserStatsCRUD = Depends(get_user_stats_crud),
):
    """Increment the number of listings completed by a user."""
    result = await crud.increment_listings_completed(user_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User stats not found",
        )
    return result


@router.patch(
    "/{user_id}/rating",
    response_model=UserStatsResponse,
    summary="Update average rating",
)
async def update_avg_rating(
    user_id: UUID,
    new_rating: float,
    crud: UserStatsCRUD = Depends(get_user_stats_crud),
):
    """Update the average rating for a user."""
    if new_rating < 0 or new_rating > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be between 0 and 5",
        )
    
    result = await crud.update_avg_rating(user_id, new_rating)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User stats not found",
        )
    return result
