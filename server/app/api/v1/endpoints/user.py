"""
API endpoints for user operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, Any, Dict, List
from uuid import UUID

from app.core.database import get_supabase_client
from app.crud.user import UserCRUD
from app.schemas.user import (
    UserProfileResponse,
    UserProfileCreate,
    UserProfileUpdate,
    UserCreditsUpdate,
    UserLocationUpdate,
    UserRole,
)
from supabase import Client

router = APIRouter()


# ==================== DEPENDENCIES ====================

def get_user_crud(supabase: Client = Depends(get_supabase_client)) -> UserCRUD:
    """Dependency to get UserCRUD instance."""
    return UserCRUD(supabase)


# ==================== USER ENDPOINTS ====================


@router.get(
    "/{user_id}",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user by ID",
    description="Retrieve a user profile by their unique ID.",
)
async def get_user(user_id: UUID, crud: UserCRUD = Depends(get_user_crud)):
    """Get a user by their ID and return profile data."""
    result = await crud.get_user(user_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )

    # Normalize key to 'uid' if needed
    if isinstance(result, dict):
        if "id" in result and "uid" not in result:
            result["uid"] = result.pop("id")

    return result


@router.get(
    "/",
    response_model=List[UserProfileResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all users",
    description="Retrieve a list of users with optional filtering and pagination.",
)
async def get_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    role: Optional[UserRole] = Query(None, description="Filter by user role"),
    crud: UserCRUD = Depends(get_user_crud),
):
    """Get a list of users with optional filtering."""
    role_value = role.value if role else None
    users = await crud.get_users(skip=skip, limit=limit, role=role_value)
    
    # Normalize keys
    for user in users:
        if "id" in user and "uid" not in user:
            user["uid"] = user.pop("id")
    
    return users


@router.post(
    "/",
    response_model=UserProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create user profile",
    description="Create a new user profile.",
)
async def create_user(
    user: UserProfileCreate,
    crud: UserCRUD = Depends(get_user_crud),
):
    """Create a new user profile."""
    # Check if user already exists
    existing_user = await crud.get_user(user.uid)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with ID {user.uid} already exists"
        )
    
    # Convert to dict and handle enum
    user_data = user.model_dump()
    if "role" in user_data and hasattr(user_data["role"], "value"):
        user_data["role"] = user_data["role"].value
    
    try:
        result = await crud.create_user(user_data)
        
        # Normalize key
        if "id" in result and "uid" not in result:
            result["uid"] = result.pop("id")
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user profile: {str(e)}"
        )


@router.patch(
    "/{user_id}",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update user profile",
    description="Update an existing user profile with partial data.",
)
async def update_user(
    user_id: UUID,
    user_update: UserProfileUpdate,
    crud: UserCRUD = Depends(get_user_crud),
):
    """Update a user profile."""
    # Check if user exists
    existing_user = await crud.get_user(user_id)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Convert to dict and exclude unset values
    update_data = user_update.model_dump(exclude_unset=True)
    
    # Handle enum
    if "role" in update_data and hasattr(update_data["role"], "value"):
        update_data["role"] = update_data["role"].value
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    result = await crud.update_user(user_id, update_data)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Normalize key
    if "id" in result and "uid" not in result:
        result["uid"] = result.pop("id")
    
    return result


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user profile",
    description="Delete a user profile by ID.",
)
async def delete_user(
    user_id: UUID,
    crud: UserCRUD = Depends(get_user_crud),
):
    """Delete a user profile."""
    deleted = await crud.delete_user(user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    return None


@router.patch(
    "/{user_id}/credits",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update user credits",
    description="Update the credit balance for a user.",
)
async def update_user_credits(
    user_id: UUID,
    credits_update: UserCreditsUpdate,
    crud: UserCRUD = Depends(get_user_crud),
):
    """Update user credits."""
    result = await crud.update_user_credits(user_id, credits_update.credits)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Normalize key
    if "id" in result and "uid" not in result:
        result["uid"] = result.pop("id")
    
    return result


@router.post(
    "/{user_id}/credits/add",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Add credits to user",
    description="Add or subtract credits from a user's balance.",
)
async def add_user_credits(
    user_id: UUID,
    amount: int = Query(..., description="Amount to add (negative to subtract)"),
    crud: UserCRUD = Depends(get_user_crud),
):
    """Add credits to a user's account."""
    result = await crud.add_user_credits(user_id, amount)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Normalize key
    if "id" in result and "uid" not in result:
        result["uid"] = result.pop("id")
    
    return result


@router.patch(
    "/{user_id}/location",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update user location",
    description="Update a user's geographic coordinates.",
)
async def update_user_location(
    user_id: UUID,
    location: UserLocationUpdate,
    crud: UserCRUD = Depends(get_user_crud),
):
    """Update user location coordinates."""
    result = await crud.update_user_location(
        user_id,
        location.latitude,
        location.longitude
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Normalize key
    if "id" in result and "uid" not in result:
        result["uid"] = result.pop("id")
    
    return result


@router.get(
    "/nearby/search",
    response_model=List[UserProfileResponse],
    status_code=status.HTTP_200_OK,
    summary="Find nearby users",
    description="Find users near a specific location within a given radius.",
)
async def get_nearby_users(
    latitude: float = Query(..., ge=-90, le=90, description="Center latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="Center longitude"),
    radius_km: float = Query(10.0, gt=0, le=100, description="Search radius in kilometers"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of users to return"),
    crud: UserCRUD = Depends(get_user_crud),
):
    """Get users near a location."""
    users = await crud.get_users_by_location(
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        limit=limit
    )
    
    # Normalize keys
    for user in users:
        if "id" in user and "uid" not in user:
            user["uid"] = user.pop("id")
    
    return users


@router.get(
    "/{user_id}/exists",
    status_code=status.HTTP_200_OK,
    summary="Check if user exists",
    description="Check if a user profile exists by ID.",
)
async def check_user_exists(
    user_id: UUID,
    crud: UserCRUD = Depends(get_user_crud),
):
    """Check if a user exists."""
    exists = await crud.user_exists(user_id)
    return {"exists": exists, "user_id": str(user_id)}