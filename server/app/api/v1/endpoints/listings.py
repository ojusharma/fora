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
    exclude_status: Optional[ListingStatus] = None,
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
    - **exclude_status**: Exclude listings with this status
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
        exclude_status=exclude_status,
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


@router.post(
    "/{listing_id}/confirm-completion",
    response_model=ListingResponse,
    summary="Confirm task completion (poster only)",
)
async def confirm_task_completion(
    listing_id: UUID,
    user_uid: UUID = Depends(get_current_user_uid),
    crud: ListingCRUD = Depends(get_listing_crud),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Poster confirms that the task has been completed.
    Updates listing status to 'completed'.
    Updates assignee's application status to 'completed'.
    Adds credits to assignee's account.
    """
    # Get the listing to verify poster
    listing = await crud.get_listing(listing_id)
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found",
        )
    
    # Check if already completed to prevent double credit addition
    if listing.get("status") == "completed":
        print(f"[CONFIRM COMPLETION] Task already completed, skipping credit addition")
        return listing
    
    if listing["poster_uid"] != str(user_uid):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the poster can confirm completion",
        )
    
    assignee_uid = listing.get("assignee_uid")
    compensation = listing.get("compensation", 0)
    
    # Ensure compensation is a number
    try:
        compensation = float(compensation) if compensation else 0
    except (ValueError, TypeError):
        compensation = 0
    
    print(f"[CONFIRM COMPLETION] Listing ID: {listing_id}")
    print(f"[CONFIRM COMPLETION] Assignee UID: {assignee_uid}")
    print(f"[CONFIRM COMPLETION] Compensation: {compensation}")
    
    # Update listing status to completed
    result = await crud.update_listing(
        listing_id,
        ListingUpdate(status=ListingStatus.COMPLETED),
        user_uid
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update listing status",
        )
    
    # Update assignee's application status to completed
    if assignee_uid:
        print(f"[CONFIRM COMPLETION] Updating applicant status to completed...")
        applicant_update = supabase.table("listing_applicants").update({
            "status": "completed"
        }).eq("listing_id", str(listing_id)).eq("applicant_uid", assignee_uid).execute()
        
        print(f"[CONFIRM COMPLETION] Applicant update result: {applicant_update.data}")
        
        # Add credits to assignee's account
        print(f"[CONFIRM COMPLETION] Compensation check: {compensation} > 0 = {compensation > 0}")
        if compensation > 0:
            print(f"[CONFIRM COMPLETION] Adding {compensation} credits to assignee...")
            # Get current credits
            profile_response = supabase.table("user_profiles").select("credits").eq("uid", assignee_uid).execute()
            
            print(f"[CONFIRM COMPLETION] Profile response: {profile_response.data}")
            
            if profile_response.data and len(profile_response.data) > 0:
                current_credits = profile_response.data[0].get("credits", 0) or 0
                new_credits = int(current_credits + compensation)
                
                print(f"[CONFIRM COMPLETION] Current credits: {current_credits}, New credits: {new_credits}")
                
                # Update credits
                credit_update = supabase.table("user_profiles").update({
                    "credits": new_credits
                }).eq("uid", assignee_uid).execute()
                
                print(f"[CONFIRM COMPLETION] Credit update result: {credit_update.data}")
                
                # Notify assignee that task is complete and credits earned
                from app.crud.notification import NotificationCRUD
                from app.schemas.notification import NotificationCreate
                
                await NotificationCRUD(supabase).create_notification(
                    NotificationCreate(
                        user_uid=str(assignee_uid),
                        title="Task completed - credits earned!",
                        body=f"'{listing.get('name', 'Task')}' has been marked as complete. You earned {int(compensation)} credits!",
                        metadata={"redirect_url": f"/market/{listing_id}"}
                    )
                )
            else:
                print(f"[CONFIRM COMPLETION] ERROR: No profile found for assignee {assignee_uid}")
        else:
            print(f"[CONFIRM COMPLETION] Skipping credit addition - compensation is 0 or invalid")
    
    return result
