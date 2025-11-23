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
from app.crud.notification import NotificationCRUD
from app.schemas.notification import NotificationCreate
from app.crud.listing import ListingCRUD
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
    "/{listing_id}/applicants/{applicant_uid}/apply",
    response_model=ListingApplicantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Apply to a listing",
)
async def apply_to_listing(
    listing_id: UUID,
    applicant_uid: UUID,
    message: Optional[str] = None,
    crud: ListingApplicantsCRUD = Depends(get_listing_applicants_crud),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Apply to a listing.
    
    Note: The poster cannot apply to their own listing (prevented by database trigger).
    TODO: Add authentication to get current user ID instead of accepting it in request.
    """
    from app.schemas.listing_applicants import ListingApplicantCreate
    
    application_data = ListingApplicantCreate(
        listing_id=listing_id,
        applicant_uid=applicant_uid,
        message=message,
    )
    
    try:
        result = await crud.create_application(application_data)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create application",
            )
        listing = await ListingCRUD(supabase).get_listing(listing_id)
        notif_crud = NotificationCRUD(supabase)
        await NotificationCRUD(supabase).create_notification(
            NotificationCreate(
                user_uid=listing["poster_uid"],
                title="New application received",
                body=f"Someone applied to your listing '{listing['name']}'",
                metadata={"redirect_url": f"/market/{listing_id}"}
            )
        )


        return result
    except Exception as e:
        # Handle database trigger errors (e.g., poster applying to own listing)
        error_msg = str(e)
        if "poster_cannot_apply" in error_msg.lower() or "cannot apply to own listing" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Poster cannot apply to their own listing",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to apply: {error_msg}",
        )


@router.get(
    "/{listing_id}/applicants/{applicant_uid}",
    response_model=ListingApplicantResponse,
    summary="Get a specific application",
)
async def get_application(
    listing_id: UUID,
    applicant_uid: UUID,
    crud: ListingApplicantsCRUD = Depends(get_listing_applicants_crud),
):
    """Get a specific application by listing ID and applicant UID."""
    result = await crud.get_application(listing_id, applicant_uid)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )
    return result


@router.get(
    "/{listing_id}/applicants/{applicant_uid}/details",
    response_model=dict,
    summary="Get application with details",
)
async def get_application_with_details(
    listing_id: UUID,
    applicant_uid: UUID,
    crud: ListingApplicantsCRUD = Depends(get_listing_applicants_crud),
):
    """Get application with listing and user profile details."""
    result = await crud.get_application_with_details(listing_id, applicant_uid)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )
    return result


@router.patch(
    "/{listing_id}/applicants/{applicant_uid}",
    response_model=ListingApplicantResponse,
    summary="Update an application",
)
async def update_application(
    listing_id: UUID,
    applicant_uid: UUID,
    update_data: ListingApplicantUpdate,
    crud: ListingApplicantsCRUD = Depends(get_listing_applicants_crud),
    supabase: Client = Depends(get_supabase_client),
):
    """Update an application (e.g., change status or message)."""
    result = await crud.update_application(listing_id, applicant_uid, update_data)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )
    
    # If applicant status is being set to pending_confirmation, update listing status too
    if update_data.status == ApplicantStatus.PENDING_CONFIRMATION:
        supabase.table("listings").update({
            "status": "pending_confirmation"
        }).eq("id", str(listing_id)).execute()
        
        # Notify poster that assignee marked task as complete
        from app.crud.listing import ListingCRUD
        from app.crud.notification import NotificationCRUD
        from app.schemas.notification import NotificationCreate
        
        listing = await ListingCRUD(supabase).get_listing(listing_id)
        if listing and listing.get("poster_uid"):
            # Get assignee name
            assignee_profile = supabase.table("user_profiles").select("display_name, phone").eq("uid", str(applicant_uid)).execute()
            assignee_name = "Assignee"
            if assignee_profile.data and len(assignee_profile.data) > 0:
                profile = assignee_profile.data[0]
                assignee_name = profile.get("display_name") or profile.get("phone") or "Assignee"
            
            await NotificationCRUD(supabase).create_notification(
                NotificationCreate(
                    user_uid=listing["poster_uid"],
                    title=f"{assignee_name} marked task as complete",
                    body=f"{assignee_name} has completed '{listing.get('name', 'your task')}' and is waiting for your review.",
                    metadata={"redirect_url": f"/market/{listing_id}"}
                )
            )
    
    return result


@router.get(
    "/{listing_id}/applicants",
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
    "/{listing_id}/applicants/details",
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
    "/{listing_id}/applicants/count",
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
    "/{listing_id}/applicants/check/{user_uid}",
    response_model=bool,
    summary="Check if user has applied",
)
async def has_applied(
    listing_id: UUID,
    user_uid: UUID,
    crud: ListingApplicantsCRUD = Depends(get_listing_applicants_crud),
):
    """Check if a user has applied to a specific listing."""
    result = await crud.has_applied(listing_id, user_uid)
    return result


@router.post(
    "/{listing_id}/applicants/{applicant_uid}/withdraw",
    response_model=ListingApplicantResponse,
    summary="Withdraw an application",
)
async def withdraw_application(
    listing_id: UUID,
    applicant_uid: UUID,
    crud: ListingApplicantsCRUD = Depends(get_listing_applicants_crud),
):
    """Withdraw an application by updating status to withdrawn."""
    result = await crud.withdraw_application(listing_id, applicant_uid)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )
    return result


@router.post(
    "/{listing_id}/applicants/{applicant_uid}/shortlist",
    response_model=ListingApplicantResponse,
    summary="Shortlist an applicant",
)
async def shortlist_applicant(
    listing_id: UUID,
    applicant_uid: UUID,
    crud: ListingApplicantsCRUD = Depends(get_listing_applicants_crud),
):
    """Shortlist an applicant for a listing."""
    result = await crud.shortlist_applicant(listing_id, applicant_uid)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )
    return result


@router.post(
    "/{listing_id}/applicants/{applicant_uid}/reject",
    response_model=ListingApplicantResponse,
    summary="Reject an applicant",
)
async def reject_applicant(
    listing_id: UUID,
    applicant_uid: UUID,
    crud: ListingApplicantsCRUD = Depends(get_listing_applicants_crud),
):
    """Reject an applicant for a listing."""
    result = await crud.reject_applicant(listing_id, applicant_uid)
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
