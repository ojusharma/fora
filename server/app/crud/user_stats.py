"""
CRUD operations for user_stats - Computed on-the-fly from source tables.
"""

from typing import Dict, Any
from uuid import UUID
from supabase import Client
from datetime import datetime


class UserStatsCRUD:
    """CRUD operations for user stats - calculated from source data."""

    def __init__(self, supabase: Client):
        """Initialize with Supabase client."""
        self.supabase = supabase

    # ==================== COMPUTED STATS OPERATIONS ====================

    async def get_user_stats(self, uid: UUID) -> Dict[str, Any]:
        """
        Calculate user stats on-the-fly from source tables.
        
        Args:
            uid: User ID
            
        Returns:
            Computed user stats
        """
        user_id_str = str(uid)
        
        # 1. Count listings posted by this user
        listings_posted_response = (
            self.supabase.table("listings")
            .select("id", count="exact")
            .eq("poster_uid", user_id_str)
            .execute()
        )
        num_listings_posted = listings_posted_response.count or 0
        
        # 2. Count applications by this user
        listings_applied_response = (
            self.supabase.table("listing_applicants")
            .select("listing_id", count="exact")
            .eq("applicant_uid", user_id_str)
            .execute()
        )
        num_listings_applied = listings_applied_response.count or 0
        
        # 3. Count listings assigned to this user
        listings_assigned_response = (
            self.supabase.table("listings")
            .select("id", count="exact")
            .eq("assignee_uid", user_id_str)
            .execute()
        )
        num_listings_assigned = listings_assigned_response.count or 0
        
        # 4. Count completed listings where user was assignee
        listings_completed_response = (
            self.supabase.table("listings")
            .select("id", count="exact")
            .eq("assignee_uid", user_id_str)
            .eq("status", "completed")
            .execute()
        )
        num_listings_completed = listings_completed_response.count or 0
        
        # 5. Calculate average rating from listings where they were assignee
        # Get all assignee_rating values for this user
        ratings_response = (
            self.supabase.table("listings")
            .select("assignee_rating")
            .eq("assignee_uid", user_id_str)
            .not_.is_("assignee_rating", "null")
            .execute()
        )
        
        avg_rating = None
        if ratings_response.data:
            ratings = [float(r["assignee_rating"]) for r in ratings_response.data if r.get("assignee_rating")]
            if ratings:
                avg_rating = sum(ratings) / len(ratings)
        
        return {
            "uid": user_id_str,
            "num_listings_posted": num_listings_posted,
            "num_listings_applied": num_listings_applied,
            "num_listings_assigned": num_listings_assigned,
            "num_listings_completed": num_listings_completed,
            "avg_rating": avg_rating,
            "updated_at": datetime.utcnow().isoformat(),
        }

    async def get_or_create_user_stats(self, uid: UUID) -> Dict[str, Any]:
        """
        Get user stats (computed, so always "exists").
        
        Args:
            uid: User ID
            
        Returns:
            Computed user stats
        """
        # Since stats are computed, this is the same as get_user_stats
        return await self.get_user_stats(uid)
