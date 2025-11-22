"""
API endpoints for user preferences operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID

from app.core.database import get_supabase_client
from app.crud.user_preferences import UserPreferencesCRUD
from app.schemas.user_preferences import (
    UserPreferenceCreate,
    UserPreferenceBulkCreate,
    UserPreferenceResponse,
)
from supabase import Client

router = APIRouter()


# ==================== DEPENDENCIES ====================

def get_user_preferences_crud(
    supabase: Client = Depends(get_supabase_client)
) -> UserPreferencesCRUD:
    """Dependency to get UserPreferencesCRUD instance."""
    return UserPreferencesCRUD(supabase)


# ==================== USER PREFERENCES ENDPOINTS ====================

@router.post(
    "/",
    response_model=UserPreferenceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a single tag preference",
)
async def add_preference(
    preference: UserPreferenceCreate,
    crud: UserPreferencesCRUD = Depends(get_user_preferences_crud),
):
    """Add a single tag preference for a user."""
    result = await crud.add_preference(preference)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to add preference. May already exist or tag not found.",
        )
    return result


@router.post(
    "/bulk",
    response_model=List[UserPreferenceResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Add multiple tag preferences",
)
async def add_preferences_bulk(
    preferences: UserPreferenceBulkCreate,
    crud: UserPreferencesCRUD = Depends(get_user_preferences_crud),
):
    """Add multiple tag preferences for a user at once."""
    result = await crud.add_preferences_bulk(preferences)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to add preferences",
        )
    return result


@router.get(
    "/user/{user_id}",
    response_model=List[UserPreferenceResponse],
    summary="Get user preferences",
)
async def get_user_preferences(
    user_id: UUID,
    crud: UserPreferencesCRUD = Depends(get_user_preferences_crud),
):
    """Get all tag preferences for a user."""
    result = await crud.get_user_preferences(user_id)
    return result


@router.get(
    "/user/{user_id}/with-tags",
    response_model=List[dict],
    summary="Get user preferences with tag details",
)
async def get_user_preferences_with_tags(
    user_id: UUID,
    crud: UserPreferencesCRUD = Depends(get_user_preferences_crud),
):
    """Get all tag preferences for a user with full tag information."""
    result = await crud.get_user_preferences_with_tags(user_id)
    return result


@router.get(
    "/user/{user_id}/tag-ids",
    response_model=List[int],
    summary="Get user's preferred tag IDs",
)
async def get_user_tag_ids(
    user_id: UUID,
    crud: UserPreferencesCRUD = Depends(get_user_preferences_crud),
):
    """Get a list of tag IDs preferred by a user."""
    result = await crud.get_user_tag_ids(user_id)
    return result


@router.get(
    "/user/{user_id}/has/{tag_id}",
    response_model=bool,
    summary="Check if user has tag preference",
)
async def has_preference(
    user_id: UUID,
    tag_id: int,
    crud: UserPreferencesCRUD = Depends(get_user_preferences_crud),
):
    """Check if a user has a specific tag preference."""
    result = await crud.has_preference(user_id, tag_id)
    return result


@router.delete(
    "/user/{user_id}/tag/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a tag preference",
)
async def remove_preference(
    user_id: UUID,
    tag_id: int,
    crud: UserPreferencesCRUD = Depends(get_user_preferences_crud),
):
    """Remove a specific tag preference for a user."""
    success = await crud.remove_preference(user_id, tag_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preference not found",
        )


@router.delete(
    "/user/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove all user preferences",
)
async def remove_all_preferences(
    user_id: UUID,
    crud: UserPreferencesCRUD = Depends(get_user_preferences_crud),
):
    """Remove all tag preferences for a user."""
    success = await crud.remove_all_preferences(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No preferences found for user",
        )


@router.put(
    "/user/{user_id}",
    response_model=List[UserPreferenceResponse],
    summary="Set user preferences (replace all)",
)
async def set_preferences(
    user_id: UUID,
    tag_ids: List[int],
    crud: UserPreferencesCRUD = Depends(get_user_preferences_crud),
):
    """Replace all user preferences with a new set of tags."""
    result = await crud.set_preferences(user_id, tag_ids)
    return result


@router.get(
    "/tag/{tag_id}/users",
    response_model=List[UserPreferenceResponse],
    summary="Get users who prefer a tag",
)
async def get_users_by_tag_preference(
    tag_id: int,
    limit: int = 100,
    offset: int = 0,
    crud: UserPreferencesCRUD = Depends(get_user_preferences_crud),
):
    """Get all users who have a specific tag as a preference."""
    result = await crud.get_users_by_tag_preference(tag_id, limit, offset)
    return result


@router.get(
    "/tag/{tag_id}/count",
    response_model=int,
    summary="Count users with tag preference",
)
async def count_users_with_preference(
    tag_id: int,
    crud: UserPreferencesCRUD = Depends(get_user_preferences_crud),
):
    """Count how many users have a specific tag as a preference."""
    result = await crud.count_users_with_preference(tag_id)
    return result
