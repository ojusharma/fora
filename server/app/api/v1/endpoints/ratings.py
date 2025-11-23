"""
API endpoints for rating operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from pydantic import BaseModel, Field

from app.core.database import get_supabase_client
from supabase import Client

router = APIRouter()


class SubmitPosterRating(BaseModel):
    """Schema for submitting a poster rating."""
    listing_id: UUID
    applicant_uid: UUID
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")


class SubmitAssigneeRating(BaseModel):
    """Schema for submitting an assignee rating."""
    listing_id: UUID
    assignee_uid: UUID
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")


@router.post(
    "/poster",
    status_code=status.HTTP_200_OK,
    summary="Submit a rating for a poster",
)
async def submit_poster_rating(
    rating_data: SubmitPosterRating,
    supabase: Client = Depends(get_supabase_client),
):
    """
    Submit a rating for a poster after completing a task.
    
    This will:
    1. Update the listing.poster_rating
    2. Increment the poster's user_profiles.no_ratings
    3. Recalculate the poster's user_profiles.user_rating
    """
    try:
        # Get the listing to find the poster_uid
        listing_response = (
            supabase.table("listings")
            .select("poster_uid, poster_rating")
            .eq("id", str(rating_data.listing_id))
            .execute()
        )
        
        if not listing_response.data or len(listing_response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Listing not found"
            )
        
        listing = listing_response.data[0]
        poster_uid = listing["poster_uid"]
        
        # Update the listing's poster_rating
        supabase.table("listings").update({
            "poster_rating": rating_data.rating
        }).eq("id", str(rating_data.listing_id)).execute()
        
        # Get current user profile data
        profile_response = (
            supabase.table("user_profiles")
            .select("user_rating, no_ratings")
            .eq("uid", poster_uid)
            .execute()
        )
        
        if not profile_response.data or len(profile_response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Poster profile not found"
            )
        
        profile = profile_response.data[0]
        current_rating = profile.get("user_rating") or 0
        current_no_ratings = profile.get("no_ratings") or 0
        
        # Calculate new rating
        # Formula: (current_user_rating * current_no_ratings + new_rating) / (current_no_ratings + 1)
        new_no_ratings = current_no_ratings + 1
        new_user_rating = ((current_rating * current_no_ratings) + rating_data.rating) / new_no_ratings
        
        # Update user profile
        supabase.table("user_profiles").update({
            "user_rating": round(new_user_rating, 2),
            "no_ratings": new_no_ratings
        }).eq("uid", poster_uid).execute()
        
        return {
            "message": "Rating submitted successfully",
            "new_user_rating": round(new_user_rating, 2),
            "total_ratings": new_no_ratings
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit rating: {str(e)}"
        )


@router.post(
    "/assignee",
    status_code=status.HTTP_200_OK,
    summary="Submit a rating for an assignee",
)
async def submit_assignee_rating(
    rating_data: SubmitAssigneeRating,
    supabase: Client = Depends(get_supabase_client),
):
    """
    Submit a rating for an assignee after they complete a task.
    
    This will:
    1. Update the listing.assignee_rating
    2. Increment the assignee's user_profiles.no_ratings
    3. Recalculate the assignee's user_profiles.user_rating
    """
    try:
        # Verify the listing exists
        listing_response = (
            supabase.table("listings")
            .select("id, assignee_uid")
            .eq("id", str(rating_data.listing_id))
            .execute()
        )
        
        if not listing_response.data or len(listing_response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Listing not found"
            )
        
        # Update the listing's assignee_rating
        supabase.table("listings").update({
            "assignee_rating": rating_data.rating
        }).eq("id", str(rating_data.listing_id)).execute()
        
        # Get current user profile data
        profile_response = (
            supabase.table("user_profiles")
            .select("user_rating, no_ratings")
            .eq("uid", str(rating_data.assignee_uid))
            .execute()
        )
        
        if not profile_response.data or len(profile_response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignee profile not found"
            )
        
        profile = profile_response.data[0]
        current_rating = profile.get("user_rating") or 0
        current_no_ratings = profile.get("no_ratings") or 0
        
        # Calculate new rating
        # Formula: (current_user_rating * current_no_ratings + new_rating) / (current_no_ratings + 1)
        new_no_ratings = current_no_ratings + 1
        new_user_rating = ((current_rating * current_no_ratings) + rating_data.rating) / new_no_ratings
        
        # Update user profile
        supabase.table("user_profiles").update({
            "user_rating": round(new_user_rating, 2),
            "no_ratings": new_no_ratings
        }).eq("uid", str(rating_data.assignee_uid)).execute()
        
        return {
            "message": "Rating submitted successfully",
            "new_user_rating": round(new_user_rating, 2),
            "total_ratings": new_no_ratings
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit rating: {str(e)}"
        )
