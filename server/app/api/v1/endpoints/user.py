"""
API endpoints for user operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional, Any, Dict
from uuid import UUID

from app.core.database import get_supabase_client
from app.crud.user import UserCRUD
from app.schemas.user import UserProfileResponse
from supabase import Client

router = APIRouter()


# ==================== DEPENDENCIES ====================

def get_user_crud(supabase: Client = Depends(get_supabase_client)) -> UserCRUD:
    """Dependency to get UserCRUD instance."""
    return UserCRUD(supabase)


# ==================== USER ENDPOINTS ====================


@router.get(
    "/{user_id}",
    response_model=Optional[UserProfileResponse],
    status_code=status.HTTP_200_OK,
    summary="Get user by ID",
)
async def get_user(user_id: UUID, crud: UserCRUD = Depends(get_user_crud)):
    """Get a user by their ID and return profile data.

    The CRUD layer returns a mapping from the DB. Normalize the key
    to `uid` if needed so the Pydantic model validates correctly.
    """
    result = await crud.get_user(user_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Supabase response keys might use 'uid' or 'id' depending on query; normalize.
    if isinstance(result, dict):
        if "id" in result and "uid" not in result:
            result["uid"] = result.pop("id")

    return result