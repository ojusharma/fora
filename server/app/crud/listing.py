"""
CRUD operations for listings table.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from supabase import Client

from app.schemas.listing import (
    ListingCreate,
    ListingUpdate,
    ListingFilters,
    ApplicantCreate,
    ApplicantUpdate,
)


class ListingCRUD:
    """CRUD operations for listings."""

    def __init__(self, supabase: Client):
        """Initialize with Supabase client."""
        self.supabase = supabase

    # ==================== LISTING OPERATIONS ====================

    async def create_listing(
        self, listing: ListingCreate, poster_uid: UUID
    ) -> Dict[str, Any]:
        """
        Create a new listing.
        
        Args:
            listing: Listing data
            poster_uid: UID of the user creating the listing
            
        Returns:
            Created listing data
        """
        listing_data = listing.model_dump()
        listing_data["poster_uid"] = str(poster_uid)
        
        # Convert datetime to ISO string
        if listing_data.get("deadline"):
            listing_data["deadline"] = listing_data["deadline"].isoformat()

        response = self.supabase.table("listings").insert(listing_data).execute()
        return response.data[0] if response.data else None

    async def get_listing(self, listing_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get a listing by ID.
        
        Args:
            listing_id: The listing ID
            
        Returns:
            Listing data or None if not found
        """
        response = (
            self.supabase.table("listings")
            .select("*")
            .eq("id", str(listing_id))
            .execute()
        )
        return response.data[0] if response.data else None

    async def get_listings(self, filters: ListingFilters) -> List[Dict[str, Any]]:
        """
        Get listings with optional filters.
        
        Args:
            filters: Filter parameters
            
        Returns:
            List of listings
        """
        query = self.supabase.table("listings").select("*")

        # Apply filters
        if filters.status:
            query = query.eq("status", filters.status.value)
        if filters.poster_uid:
            query = query.eq("poster_uid", str(filters.poster_uid))
        if filters.assignee_uid:
            query = query.eq("assignee_uid", str(filters.assignee_uid))
        if filters.min_compensation is not None:
            query = query.gte("compensation", filters.min_compensation)
        if filters.max_compensation is not None:
            query = query.lte("compensation", filters.max_compensation)
        if filters.has_deadline is not None:
            if filters.has_deadline:
                query = query.not_.is_("deadline", "null")
            else:
                query = query.is_("deadline", "null")

        # Apply pagination
        query = query.order("created_at", desc=True)
        query = query.range(filters.offset, filters.offset + filters.limit - 1)

        response = query.execute()
        return response.data if response.data else []

    async def update_listing(
        self, listing_id: UUID, listing: ListingUpdate, user_uid: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Update a listing.
        
        Args:
            listing_id: The listing ID
            listing: Updated listing data
            user_uid: UID of the user updating (must be poster)
            
        Returns:
            Updated listing data or None if not found/unauthorized
        """
        # Check if user is the poster
        existing = await self.get_listing(listing_id)
        if not existing or existing["poster_uid"] != str(user_uid):
            return None

        # Filter out None values
        update_data = {
            k: v for k, v in listing.model_dump().items() if v is not None
        }
        
        if not update_data:
            return existing

        # Convert datetime to ISO string
        if update_data.get("deadline"):
            update_data["deadline"] = update_data["deadline"].isoformat()
        
        # Convert enum to string
        if update_data.get("status"):
            update_data["status"] = update_data["status"].value

        update_data["updated_at"] = datetime.utcnow().isoformat()

        response = (
            self.supabase.table("listings")
            .update(update_data)
            .eq("id", str(listing_id))
            .execute()
        )
        return response.data[0] if response.data else None

    async def delete_listing(
        self, listing_id: UUID, user_uid: UUID
    ) -> bool:
        """
        Delete a listing.
        
        Args:
            listing_id: The listing ID
            user_uid: UID of the user deleting (must be poster)
            
        Returns:
            True if deleted, False otherwise
        """
        # Check if user is the poster
        existing = await self.get_listing(listing_id)
        if not existing or existing["poster_uid"] != str(user_uid):
            return False

        response = (
            self.supabase.table("listings")
            .delete()
            .eq("id", str(listing_id))
            .execute()
        )
        return bool(response.data)

    # ==================== APPLICANT OPERATIONS ====================

    async def apply_to_listing(
        self, listing_id: UUID, applicant_uid: UUID, application: ApplicantCreate
    ) -> Optional[Dict[str, Any]]:
        """
        Apply to a listing.
        
        Args:
            listing_id: The listing ID
            applicant_uid: UID of the applicant
            application: Application data
            
        Returns:
            Application data or None if failed
        """
        # Check if listing exists and is open
        listing = await self.get_listing(listing_id)
        if not listing or listing["status"] != "open":
            return None

        # Check if already applied
        existing = (
            self.supabase.table("listing_applicants")
            .select("*")
            .eq("listing_id", str(listing_id))
            .eq("applicant_uid", str(applicant_uid))
            .execute()
        )
        if existing.data:
            return None

        application_data = {
            "listing_id": str(listing_id),
            "applicant_uid": str(applicant_uid),
            "message": application.message,
            "status": "applied",
        }

        response = (
            self.supabase.table("listing_applicants")
            .insert(application_data)
            .execute()
        )
        return response.data[0] if response.data else None

    async def get_listing_applicants(
        self, listing_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        Get all applicants for a listing.
        
        Args:
            listing_id: The listing ID
            
        Returns:
            List of applicants
        """
        response = (
            self.supabase.table("listing_applicants")
            .select("*")
            .eq("listing_id", str(listing_id))
            .order("applied_at", desc=True)
            .execute()
        )
        return response.data if response.data else []

    async def update_applicant_status(
        self,
        listing_id: UUID,
        applicant_uid: UUID,
        status_update: ApplicantUpdate,
        poster_uid: UUID,
    ) -> Optional[Dict[str, Any]]:
        """
        Update applicant status (poster only).
        
        Args:
            listing_id: The listing ID
            applicant_uid: UID of the applicant
            status_update: New status
            poster_uid: UID of the poster (for authorization)
            
        Returns:
            Updated applicant data or None if unauthorized
        """
        # Check if user is the poster
        listing = await self.get_listing(listing_id)
        if not listing or listing["poster_uid"] != str(poster_uid):
            return None

        update_data = {"status": status_update.status.value}

        response = (
            self.supabase.table("listing_applicants")
            .update(update_data)
            .eq("listing_id", str(listing_id))
            .eq("applicant_uid", str(applicant_uid))
            .execute()
        )
        
        # If accepted, update listing assignee
        if status_update.status.value == "accepted" and response.data:
            await self.supabase.table("listings").update({
                "assignee_uid": str(applicant_uid),
                "status": "in_progress"
            }).eq("id", str(listing_id)).execute()

        return response.data[0] if response.data else None

    async def get_user_applications(
        self, user_uid: UUID
    ) -> List[Dict[str, Any]]:
        """
        Get all applications by a user.
        
        Args:
            user_uid: UID of the user
            
        Returns:
            List of applications
        """
        response = (
            self.supabase.table("listing_applicants")
            .select("*, listings(*)")
            .eq("applicant_uid", str(user_uid))
            .order("applied_at", desc=True)
            .execute()
        )
        return response.data if response.data else []
