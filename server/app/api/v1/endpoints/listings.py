"""
API endpoints for listing operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from uuid import UUID

from app.core.database import get_supabase_client
from app.crud.listing import ListingCRUD
from app.schemas.listing import (
    ListingCreate,
    ListingUpdate,
    ListingResponse,
    ListingFilters,
    ListingStatus,
    ApplicantCreate,
    ApplicantResponse,
    ApplicantUpdate,
)
from supabase import Client

router = APIRouter()


# ==================== DEPENDENCY ====================

def get_listing_crud(supabase: Client = Depends(get_supabase_client)) -> ListingCRUD:
    """Dependency to get ListingCRUD instance."""
    return ListingCRUD(supabase)


# TODO: Add authentication dependency to get current user
# For now, using user_uid as a query parameter
async def get_current_user_uid(user_uid: UUID = Query(..., description="Current user UID")) -> UUID:
    """Temporary: Get current user UID from query parameter."""
    return user_uid


# ==================== LISTING ENDPOINTS ====================

@router.post(
    "/",
    response_model=ListingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new listing",
)
async def create_listing(
    listing: ListingCreate,
    user_uid: UUID = Depends(get_current_user_uid),
    crud: ListingCRUD = Depends(get_listing_crud),
):
    """Create a new listing."""
    result = await crud.create_listing(listing, user_uid)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create listing",
        )
    return result


@router.get(
    "/",
    response_model=List[ListingResponse],
    summary="Get all listings with optional filters",
)
async def get_listings(
    status_filter: Optional[ListingStatus] = Query(None, alias="status"),
    poster_uid: Optional[UUID] = None,
    assignee_uid: Optional[UUID] = None,
    min_compensation: Optional[float] = None,
    max_compensation: Optional[float] = None,
    has_deadline: Optional[bool] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    crud: ListingCRUD = Depends(get_listing_crud),
):
    """
    Get listings with optional filters.
    
    - **status**: Filter by listing status
    - **poster_uid**: Filter by poster user ID
    - **assignee_uid**: Filter by assignee user ID
    - **min_compensation**: Minimum compensation
    - **max_compensation**: Maximum compensation
    - **has_deadline**: Filter by presence of deadline
    - **limit**: Number of results (max 100)
    - **offset**: Pagination offset
    """
    filters = ListingFilters(
        status=status_filter,
        poster_uid=poster_uid,
        assignee_uid=assignee_uid,
        min_compensation=min_compensation,
        max_compensation=max_compensation,
        has_deadline=has_deadline,
        limit=limit,
        offset=offset,
    )
    return await crud.get_listings(filters)


@router.get(
    "/{listing_id}",
    response_model=ListingResponse,
    summary="Get a specific listing",
)
async def get_listing(
    listing_id: UUID,
    crud: ListingCRUD = Depends(get_listing_crud),
):
    """Get a listing by ID."""
    result = await crud.get_listing(listing_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found",
        )
    return result


@router.patch(
    "/{listing_id}",
    response_model=ListingResponse,
    summary="Update a listing",
)
async def update_listing(
    listing_id: UUID,
    listing: ListingUpdate,
    user_uid: UUID = Depends(get_current_user_uid),
    crud: ListingCRUD = Depends(get_listing_crud),
):
    """Update a listing. Only the poster can update."""
    result = await crud.update_listing(listing_id, listing, user_uid)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found or unauthorized",
        )
    return result


@router.delete(
    "/{listing_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a listing",
)
async def delete_listing(
    listing_id: UUID,
    user_uid: UUID = Depends(get_current_user_uid),
    crud: ListingCRUD = Depends(get_listing_crud),
):
    """Delete a listing. Only the poster can delete."""
    success = await crud.delete_listing(listing_id, user_uid)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found or unauthorized",
        )
    return None


# ==================== APPLICANT ENDPOINTS ====================

@router.post(
    "/{listing_id}/apply",
    response_model=ApplicantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Apply to a listing",
)
async def apply_to_listing(
    listing_id: UUID,
    application: ApplicantCreate,
    user_uid: UUID = Depends(get_current_user_uid),
    crud: ListingCRUD = Depends(get_listing_crud),
):
    """Apply to a listing."""
    result = await crud.apply_to_listing(listing_id, user_uid, application)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot apply to this listing (not open or already applied)",
        )
    return result


@router.get(
    "/{listing_id}/applicants",
    response_model=List[ApplicantResponse],
    summary="Get all applicants for a listing",
)
async def get_listing_applicants(
    listing_id: UUID,
    crud: ListingCRUD = Depends(get_listing_crud),
):
    """Get all applicants for a listing."""
    return await crud.get_listing_applicants(listing_id)


@router.patch(
    "/{listing_id}/applicants/{applicant_uid}",
    response_model=ApplicantResponse,
    summary="Update applicant status",
)
async def update_applicant_status(
    listing_id: UUID,
    applicant_uid: UUID,
    status_update: ApplicantUpdate,
    user_uid: UUID = Depends(get_current_user_uid),
    crud: ListingCRUD = Depends(get_listing_crud),
):
    """Update applicant status. Only the poster can update."""
    result = await crud.update_applicant_status(
        listing_id, applicant_uid, status_update, user_uid
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found or unauthorized",
        )
    return result


@router.get(
    "/users/{user_uid}/applications",
    response_model=List[ApplicantResponse],
    summary="Get all applications by a user",
)
async def get_user_applications(
    user_uid: UUID,
    crud: ListingCRUD = Depends(get_listing_crud),
):
    """Get all applications by a user."""
    return await crud.get_user_applications(user_uid)
