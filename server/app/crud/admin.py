"""
Admin CRUD operations for managing users and listings.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from supabase import Client

from app.schemas.admin import (
    AdminUserUpdate,
    AdminListingUpdate,
    AdminListingCreate,
)


class AdminCRUD:
    """CRUD operations for admin user and listing management."""

    def __init__(self, supabase: Client):
        """Initialize with Supabase client."""
        self.supabase = supabase

    # ==================== USER MANAGEMENT ====================

    async def get_all_users(
        self,
        skip: int = 0,
        limit: int = 100,
        role: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all users with optional filtering by role.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            role: Filter by user role
            
        Returns:
            List of user profiles
        """
        query = self.supabase.table("user_profiles").select("*")
        
        if role:
            query = query.eq("role", role)
        
        response = query.range(skip, skip + limit - 1).execute()
        return response.data if response.data else []

    async def get_user_by_id(self, user_uid: UUID) -> Optional[Dict[str, Any]]:
        """
        Get a specific user by UID.
        
        Args:
            user_uid: User UID
            
        Returns:
            User profile or None if not found
        """
        response = (
            self.supabase.table("user_profiles")
            .select("*")
            .eq("uid", str(user_uid))
            .execute()
        )
        return response.data[0] if response.data else None

    async def update_user(
        self,
        user_uid: UUID,
        update_data: AdminUserUpdate
    ) -> Dict[str, Any]:
        """
        Update a user's profile (admin can update any field including role).
        
        Args:
            user_uid: User UID to update
            update_data: Updated user data
            
        Returns:
            Updated user profile
        """
        update_dict = update_data.model_dump(exclude_unset=True)
        
        # Convert role enum to string if present
        if "role" in update_dict and update_dict["role"]:
            update_dict["role"] = update_dict["role"].value
        
        response = (
            self.supabase.table("user_profiles")
            .update(update_dict)
            .eq("uid", str(user_uid))
            .execute()
        )
        
        if not response.data:
            raise ValueError(f"User with UID {user_uid} not found")
        
        return response.data[0]

    async def delete_user(self, user_uid: UUID) -> bool:
        """
        Delete a user and all associated data.
        
        Args:
            user_uid: User UID to delete
            
        Returns:
            True if deletion was successful
            
        Note:
            This will cascade delete all user's listings, applications, etc.
            due to foreign key constraints in the database.
        """
        # Delete from user_profiles (which references auth.users with CASCADE)
        response = (
            self.supabase.table("user_profiles")
            .delete()
            .eq("uid", str(user_uid))
            .execute()
        )
        
        # Also delete from Supabase auth
        try:
            # Note: This requires service role key
            self.supabase.auth.admin.delete_user(str(user_uid))
        except Exception as e:
            # Log the error but continue - profile is already deleted
            print(f"Warning: Could not delete auth user: {e}")
        
        return bool(response.data)

    async def change_user_role(
        self,
        user_uid: UUID,
        new_role: str
    ) -> Dict[str, Any]:
        """
        Change a user's role.
        
        Args:
            user_uid: User UID
            new_role: New role (user, moderator, admin)
            
        Returns:
            Updated user profile
        """
        response = (
            self.supabase.table("user_profiles")
            .update({"role": new_role})
            .eq("uid", str(user_uid))
            .execute()
        )
        
        if not response.data:
            raise ValueError(f"User with UID {user_uid} not found")
        
        return response.data[0]

    # ==================== LISTING MANAGEMENT ====================

    async def get_all_listings(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all listings with optional filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Filter by listing status
            
        Returns:
            List of listings
        """
        query = self.supabase.table("listings").select("*")
        
        if status:
            query = query.eq("status", status)
        
        response = query.range(skip, skip + limit - 1).execute()
        return response.data if response.data else []

    async def get_listing_by_id(self, listing_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get a specific listing by ID.
        
        Args:
            listing_id: Listing ID
            
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
        
        # Fetch tags
        if listing:
            tags_response = (
                self.supabase.table("listing_tags")
                .select("tag_id")
                .eq("listing_id", str(listing_id))
                .execute()
            )
            listing["tags"] = [tag["tag_id"] for tag in tags_response.data] if tags_response.data else []
        
        return listing

    async def create_listing(
        self,
        listing_data: AdminListingCreate
    ) -> Dict[str, Any]:
        """
        Create a listing on behalf of a user.
        
        Args:
            listing_data: Listing data
            
        Returns:
            Created listing
        """
        listing_dict = listing_data.model_dump(exclude={"tags"})
        
        # Convert UUIDs to strings
        if listing_dict.get("poster_uid"):
            listing_dict["poster_uid"] = str(listing_dict["poster_uid"])
        
        # Convert datetime to ISO string
        if listing_dict.get("deadline"):
            listing_dict["deadline"] = listing_dict["deadline"].isoformat()
        
        # Convert status enum to string
        if listing_dict.get("status"):
            listing_dict["status"] = listing_dict["status"].value
        
        response = self.supabase.table("listings").insert(listing_dict).execute()
        created_listing = response.data[0] if response.data else None
        
        # Insert tags
        if created_listing and listing_data.tags:
            listing_id = created_listing["id"]
            tag_entries = [
                {"listing_id": listing_id, "tag_id": tag_id}
                for tag_id in listing_data.tags
            ]
            self.supabase.table("listing_tags").insert(tag_entries).execute()
            created_listing["tags"] = listing_data.tags
        
        return created_listing

    async def update_listing(
        self,
        listing_id: UUID,
        update_data: AdminListingUpdate
    ) -> Dict[str, Any]:
        """
        Update a listing (admin can update any field).
        
        Args:
            listing_id: Listing ID to update
            update_data: Updated listing data
            
        Returns:
            Updated listing
        """
        update_dict = update_data.model_dump(exclude_unset=True, exclude={"tags"})
        
        # Convert status enum to string if present
        if "status" in update_dict and update_dict["status"]:
            update_dict["status"] = update_dict["status"].value
        
        # Convert UUIDs to strings
        if "poster_uid" in update_dict and update_dict["poster_uid"]:
            update_dict["poster_uid"] = str(update_dict["poster_uid"])
        if "assignee_uid" in update_dict and update_dict["assignee_uid"]:
            update_dict["assignee_uid"] = str(update_dict["assignee_uid"])
        
        # Convert datetime to ISO string
        if "deadline" in update_dict and update_dict["deadline"]:
            update_dict["deadline"] = update_dict["deadline"].isoformat()
        
        response = (
            self.supabase.table("listings")
            .update(update_dict)
            .eq("id", str(listing_id))
            .execute()
        )
        
        if not response.data:
            raise ValueError(f"Listing with ID {listing_id} not found")
        
        updated_listing = response.data[0]
        
        # Update tags if provided
        if update_data.tags is not None:
            # Delete existing tags
            self.supabase.table("listing_tags").delete().eq("listing_id", str(listing_id)).execute()
            
            # Insert new tags
            if update_data.tags:
                tag_entries = [
                    {"listing_id": str(listing_id), "tag_id": tag_id}
                    for tag_id in update_data.tags
                ]
                self.supabase.table("listing_tags").insert(tag_entries).execute()
            
            updated_listing["tags"] = update_data.tags
        
        return updated_listing

    async def delete_listing(self, listing_id: UUID) -> bool:
        """
        Delete a listing.
        
        Args:
            listing_id: Listing ID to delete
            
        Returns:
            True if deletion was successful
        """
        # Delete tags first
        self.supabase.table("listing_tags").delete().eq("listing_id", str(listing_id)).execute()
        
        # Delete listing
        response = (
            self.supabase.table("listings")
            .delete()
            .eq("id", str(listing_id))
            .execute()
        )
        
        return bool(response.data)

    # ==================== STATISTICS ====================

    async def get_platform_stats(self) -> Dict[str, Any]:
        """
        Get overall platform statistics.
        
        Returns:
            Dictionary with various platform statistics
        """
        # Count users
        users_response = self.supabase.table("user_profiles").select("role", count="exact").execute()
        total_users = users_response.count if hasattr(users_response, 'count') else 0
        
        # Count users by role
        admin_count = len([u for u in users_response.data if u.get("role") == "admin"]) if users_response.data else 0
        moderator_count = len([u for u in users_response.data if u.get("role") == "moderator"]) if users_response.data else 0
        regular_users = total_users - admin_count - moderator_count
        
        # Count listings
        listings_response = self.supabase.table("listings").select("status", count="exact").execute()
        total_listings = listings_response.count if hasattr(listings_response, 'count') else 0
        
        # Count by status
        open_listings = len([l for l in listings_response.data if l.get("status") == "open"]) if listings_response.data else 0
        completed_listings = len([l for l in listings_response.data if l.get("status") == "completed"]) if listings_response.data else 0
        
        # Count applications
        apps_response = self.supabase.table("listing_applicants").select("*", count="exact").execute()
        total_applications = apps_response.count if hasattr(apps_response, 'count') else 0
        
        return {
            "total_users": total_users,
            "total_listings": total_listings,
            "open_listings": open_listings,
            "completed_listings": completed_listings,
            "total_applications": total_applications,
            "admin_users": admin_count,
            "moderator_users": moderator_count,
            "regular_users": regular_users,
        }

    async def get_user_stats(self, user_uid: UUID) -> Dict[str, Any]:
        """
        Get detailed statistics for a specific user.
        
        Args:
            user_uid: User UID
            
        Returns:
            Dictionary with user statistics
        """
        # Get user profile
        user = await self.get_user_by_id(user_uid)
        if not user:
            raise ValueError(f"User with UID {user_uid} not found")
        
        # Count listings posted
        posted_response = (
            self.supabase.table("listings")
            .select("*", count="exact")
            .eq("poster_uid", str(user_uid))
            .execute()
        )
        total_posted = posted_response.count if hasattr(posted_response, 'count') else 0
        completed_posted = len([l for l in posted_response.data if l.get("status") == "completed"]) if posted_response.data else 0
        
        # Count applications
        apps_response = (
            self.supabase.table("listing_applicants")
            .select("*", count="exact")
            .eq("applicant_uid", str(user_uid))
            .execute()
        )
        total_applications = apps_response.count if hasattr(apps_response, 'count') else 0
        
        return {
            "uid": user_uid,
            "display_name": user.get("display_name"),
            "role": user.get("role", "user"),
            "credits": user.get("credits", 0),
            "total_listings_posted": total_posted,
            "total_listings_completed": completed_posted,
            "total_applications": total_applications,
            "average_rating": user.get("user_rating"),
            "account_created": user.get("last_updated"),
        }
