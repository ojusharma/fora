"""
API endpoints for listing applicants operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.core.database import get_supabase_client
from app.crud.listing_applicants import ListingApplicantsCRUD
from app.schemas.listing_applicants import (
    ListingApplicantCreate,
    ListingApplicantUpdate,
    ListingApplicantResponse,
    ListingApplicantWithDetailsResponse,
    ApplicantFilters,
    ApplicantStatus,
)
from supabase import Client

router = APIRouter()


# ==================== DEPENDENCIES ====================

def get_listing_applicants_crud(
    supabase: Client = Depends(get_supabase_client)
) -> ListingApplicantsCRUD:
    """Dependency to get ListingApplicantsCRUD instance."""
    return ListingApplicantsCRUD(supabase)


# ==================== APPLICATION ENDPOINTS ====================

@router.post(
    "/",
    response_model=ListingApplicantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Apply to a listing",
)
async def create_application(
    application: ListingApplicantCreate,
    crud: ListingApplicantsCRUD = Depends(get_listing_applicants_crud),
):
    """
    Apply to a listing.
    
    Note: The poster cannot apply to their own listing (prevented by database trigger).
    """
    result = await crud.create_application(application)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create application. You may have already applied or the listing poster cannot apply to their own listing.",
        )
    return result


@router.get(
    "/{listing_id}/{applicant_id}",
    response_model=ListingApplicantResponse,
    summary="Get a specific application",
)
async def get_application(
    listing_id: UUID,
    applicant_id: UUID,
    crud: ListingApplicantsCRUD = Depends(get_listing_applicants_crud),
):
    """Get a specific application by listing ID and applicant ID."""
    result = await crud.get_application(listing_id, applicant_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )
    return result


@router.get(
    "/{listing_id}/{applicant_id}/details",
    response_model=dict,
    summary="Get application with details",
)
async def get_application_with_details(
    listing_id: UUID,
    applicant_id: UUID,
    crud: ListingApplicantsCRUD = Depends(get_listing_applicants_crud),
):
    """Get application with listing and user profile details."""
    result = await crud.get_application_with_details(listing_id, applicant_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )
    return result


@router.patch(
    "/{listing_id}/{applicant_id}",
    response_model=ListingApplicantResponse,
    summary="Update an application",
)
async def update_application(
    listing_id: UUID,
    applicant_id: UUID,
    update_data: ListingApplicantUpdate,
    crud: ListingApplicantsCRUD = Depends(get_listing_applicants_crud),
):
    """Update an application (e.g., change status or message)."""
    result = await crud.update_application(listing_id, applicant_id, update_data)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )
    return result


@router.delete(
    "/{listing_id}/{applicant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an application",
)
async def delete_application(
    listing_id: UUID,
    applicant_id: UUID,
    crud: ListingApplicantsCRUD = Depends(get_listing_applicants_crud),
):
    """Delete (withdraw) an application."""
    success = await crud.delete_application(listing_id, applicant_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )


@router.get(
    "/listing/{listing_id}",
    response_model=List[ListingApplicantResponse],
    summary="Get all applicants for a listing",
)
async def get_listing_applicants(
    listing_id: UUID,
    status_filter: Optional[ApplicantStatus] = Query(None, alias="status"),
    crud: ListingApplicantsCRUD = Depends(get_listing_applicants_crud),
):
    """Get all applicants for a listing, optionally filtered by status."""
    result = await crud.get_listing_applicants(listing_id, status_filter)
    return result


@router.get(
    "/listing/{listing_id}/details",
    response_model=List[dict],
    summary="Get applicants with user details",
)
async def get_listing_applicants_with_details(
    listing_id: UUID,
    status_filter: Optional[ApplicantStatus] = Query(None, alias="status"),
    crud: ListingApplicantsCRUD = Depends(get_listing_applicants_crud),
):
    """Get applicants for a listing with user profile details."""
    result = await crud.get_listing_applicants_with_details(listing_id, status_filter)
    return result


@router.get(
    "/user/{user_id}",
    response_model=List[ListingApplicantResponse],
    summary="Get all applications by a user",
)
async def get_user_applications(
    user_id: UUID,
    status_filter: Optional[ApplicantStatus] = Query(None, alias="status"),
    crud: ListingApplicantsCRUD = Depends(get_listing_applicants_crud),
):
    """Get all applications submitted by a user, optionally filtered by status."""
    result = await crud.get_user_applications(user_id, status_filter)
    return result


@router.get(
    "/user/{user_id}/with-listings",
    response_model=List[dict],
    summary="Get user applications with listing details",
)
async def get_user_applications_with_listings(
    user_id: UUID,
    status_filter: Optional[ApplicantStatus] = Query(None, alias="status"),
    crud: ListingApplicantsCRUD = Depends(get_listing_applicants_crud),
):
    """Get user applications with full listing details."""
    result = await crud.get_user_applications_with_listings(user_id, status_filter)
    return result


@router.get(
    "/listing/{listing_id}/count",
    response_model=int,
    summary="Count applicants for a listing",
)
async def count_listing_applicants(
    listing_id: UUID,
    status_filter: Optional[ApplicantStatus] = Query(None, alias="status"),
    crud: ListingApplicantsCRUD = Depends(get_listing_applicants_crud),
):
    """Count applicants for a listing, optionally filtered by status."""
    result = await crud.count_listing_applicants(listing_id, status_filter)
    return result


@router.get(
    "/user/{user_id}/count",
    response_model=int,
    summary="Count applications by a user",
)
async def count_user_applications(
    user_id: UUID,
    status_filter: Optional[ApplicantStatus] = Query(None, alias="status"),
    crud: ListingApplicantsCRUD = Depends(get_listing_applicants_crud),
):
    """Count applications submitted by a user, optionally filtered by status."""
    result = await crud.count_user_applications(user_id, status_filter)
    return result


@router.get(
    "/check/{listing_id}/{user_id}",
    response_model=bool,
    summary="Check if user has applied",
)
async def has_applied(
    listing_id: UUID,
    user_id: UUID,
    crud: ListingApplicantsCRUD = Depends(get_listing_applicants_crud),
):
    """Check if a user has applied to a specific listing."""
    result = await crud.has_applied(listing_id, user_id)
    return result


@router.patch(
    "/{listing_id}/{applicant_id}/status",
    response_model=ListingApplicantResponse,
    summary="Update application status",
)
async def update_status(
    listing_id: UUID,
    applicant_id: UUID,
    status: ApplicantStatus,
    crud: ListingApplicantsCRUD = Depends(get_listing_applicants_crud),
):
    """Update the status of an application."""
    result = await crud.update_status(listing_id, applicant_id, status)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )
    return result


@router.post(
    "/{listing_id}/{applicant_id}/withdraw",
    response_model=ListingApplicantResponse,
    summary="Withdraw an application",
)
async def withdraw_application(
    listing_id: UUID,
    applicant_id: UUID,
    crud: ListingApplicantsCRUD = Depends(get_listing_applicants_crud),
):
    """Withdraw an application by updating status to withdrawn."""
    result = await crud.withdraw_application(listing_id, applicant_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )
    return result


@router.post(
    "/{listing_id}/{applicant_id}/shortlist",
    response_model=ListingApplicantResponse,
    summary="Shortlist an applicant",
)
async def shortlist_applicant(
    listing_id: UUID,
    applicant_id: UUID,
    crud: ListingApplicantsCRUD = Depends(get_listing_applicants_crud),
):
    """Shortlist an applicant for a listing."""
    result = await crud.shortlist_applicant(listing_id, applicant_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )
    return result


@router.post(
    "/{listing_id}/{applicant_id}/reject",
    response_model=ListingApplicantResponse,
    summary="Reject an applicant",
)
async def reject_applicant(
    listing_id: UUID,
    applicant_id: UUID,
    crud: ListingApplicantsCRUD = Depends(get_listing_applicants_crud),
):
    """Reject an applicant for a listing."""
    result = await crud.reject_applicant(listing_id, applicant_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )
    return result


@router.post(
    "/search",
    response_model=List[ListingApplicantResponse],
    summary="Search applications with filters",
)
async def search_applications(
    filters: ApplicantFilters,
    crud: ListingApplicantsCRUD = Depends(get_listing_applicants_crud),
):
    """Search applications with advanced filtering."""
    result = await crud.get_applications_by_filters(filters)
    return result


@router.post(
    "/{listing_id}/bulk-update",
    response_model=List[ListingApplicantResponse],
    summary="Bulk update applicant status",
)
async def bulk_update_status(
    listing_id: UUID,
    applicant_ids: List[UUID],
    status: ApplicantStatus,
    crud: ListingApplicantsCRUD = Depends(get_listing_applicants_crud),
):
    """Update status for multiple applicants at once."""
    result = await crud.bulk_update_status(listing_id, applicant_ids, status)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No applications updated",
        )
    return result
