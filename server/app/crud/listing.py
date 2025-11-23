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
        
        # Extract tags before inserting listing
        tags = listing_data.pop("tags", [])
        
        # Convert datetime to ISO string
        if listing_data.get("deadline"):
            listing_data["deadline"] = listing_data["deadline"].isoformat()

        response = self.supabase.table("listings").insert(listing_data).execute()
        created_listing = response.data[0] if response.data else None
        
        # Insert tags into listing_tags table
        if created_listing and tags:
            listing_id = created_listing["id"]
            tag_entries = [
                {"listing_id": listing_id, "tag_id": tag_id}
                for tag_id in tags
            ]
            self.supabase.table("listing_tags").insert(tag_entries).execute()
            created_listing["tags"] = tags
        
        return created_listing

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
        listing = response.data[0] if response.data else None
        
        # Fetch tags for this listing
        if listing:
            tags_response = (
                self.supabase.table("listing_tags")
                .select("tag_id")
                .eq("listing_id", str(listing_id))
                .execute()
            )
            listing["tags"] = [tag["tag_id"] for tag in tags_response.data] if tags_response.data else []
        
        return listing

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

