"""
CRUD operations for user_stats table.
"""

from typing import Optional, Dict, Any
from uuid import UUID
from supabase import Client

from app.schemas.user_stats import UserStatsCreate, UserStatsUpdate


class UserStatsCRUD:
    """CRUD operations for user stats."""

    def __init__(self, supabase: Client):
        """Initialize with Supabase client."""
        self.supabase = supabase

    # ==================== USER STATS OPERATIONS ====================

    async def create_user_stats(self, user_stats: UserStatsCreate) -> Dict[str, Any]:
        """
        Create user stats for a new user.
        
        Args:
            user_stats: User stats data
            
        Returns:
            Created user stats data
        """
        stats_data = user_stats.model_dump()
        stats_data["uid"] = str(stats_data["uid"])
        
        # Convert Decimal to float for JSON serialization
        if stats_data.get("avg_rating") is not None:
            stats_data["avg_rating"] = float(stats_data["avg_rating"])

        response = self.supabase.table("user_stats").insert(stats_data).execute()
        return response.data[0] if response.data else None

    async def get_user_stats(self, uid: UUID) -> Optional[Dict[str, Any]]:
        """
        Get user stats by user ID.
        
        Args:
            uid: User ID
            
        Returns:
            User stats data or None if not found
        """
        response = (
            self.supabase.table("user_stats")
            .select("*")
            .eq("uid", str(uid))
            .execute()
        )
        return response.data[0] if response.data else None

    async def update_user_stats(
        self, uid: UUID, user_stats: UserStatsUpdate
    ) -> Optional[Dict[str, Any]]:
        """
        Update user stats.
        
        Args:
            uid: User ID
            user_stats: User stats update data
            
        Returns:
            Updated user stats data or None if not found
        """
        stats_data = user_stats.model_dump(exclude_unset=True)
        
        # Convert Decimal to float for JSON serialization
        if "avg_rating" in stats_data and stats_data["avg_rating"] is not None:
            stats_data["avg_rating"] = float(stats_data["avg_rating"])

        response = (
            self.supabase.table("user_stats")
            .update(stats_data)
            .eq("uid", str(uid))
            .execute()
        )
        return response.data[0] if response.data else None

    async def delete_user_stats(self, uid: UUID) -> bool:
        """
        Delete user stats.
        
        Args:
            uid: User ID
            
        Returns:
            True if deleted, False if not found
        """
        response = (
            self.supabase.table("user_stats")
            .delete()
            .eq("uid", str(uid))
            .execute()
        )
        return len(response.data) > 0 if response.data else False

    async def increment_listings_posted(self, uid: UUID) -> Optional[Dict[str, Any]]:
        """
        Increment the number of listings posted by a user.
        
        Args:
            uid: User ID
            
        Returns:
            Updated user stats or None if not found
        """
        # Get current stats
        current_stats = await self.get_user_stats(uid)
        if not current_stats:
            return None
        
        # Increment and update
        new_count = current_stats.get("num_listings_posted", 0) + 1
        return await self.update_user_stats(
            uid, UserStatsUpdate(num_listings_posted=new_count)
        )

    async def increment_listings_applied(self, uid: UUID) -> Optional[Dict[str, Any]]:
        """
        Increment the number of listings a user has applied to.
        
        Args:
            uid: User ID
            
        Returns:
            Updated user stats or None if not found
        """
        current_stats = await self.get_user_stats(uid)
        if not current_stats:
            return None
        
        new_count = current_stats.get("num_listings_applied", 0) + 1
        return await self.update_user_stats(
            uid, UserStatsUpdate(num_listings_applied=new_count)
        )

    async def increment_listings_assigned(self, uid: UUID) -> Optional[Dict[str, Any]]:
        """
        Increment the number of listings assigned to a user.
        
        Args:
            uid: User ID
            
        Returns:
            Updated user stats or None if not found
        """
        current_stats = await self.get_user_stats(uid)
        if not current_stats:
            return None
        
        new_count = current_stats.get("num_listings_assigned", 0) + 1
        return await self.update_user_stats(
            uid, UserStatsUpdate(num_listings_assigned=new_count)
        )

    async def increment_listings_completed(self, uid: UUID) -> Optional[Dict[str, Any]]:
        """
        Increment the number of listings completed by a user.
        
        Args:
            uid: User ID
            
        Returns:
            Updated user stats or None if not found
        """
        current_stats = await self.get_user_stats(uid)
        if not current_stats:
            return None
        
        new_count = current_stats.get("num_listings_completed", 0) + 1
        return await self.update_user_stats(
            uid, UserStatsUpdate(num_listings_completed=new_count)
        )

    async def update_avg_rating(
        self, uid: UUID, new_rating: float
    ) -> Optional[Dict[str, Any]]:
        """
        Update the average rating for a user.
        
        Args:
            uid: User ID
            new_rating: New average rating value
            
        Returns:
            Updated user stats or None if not found
        """
        return await self.update_user_stats(
            uid, UserStatsUpdate(avg_rating=new_rating)
        )

    async def get_or_create_user_stats(self, uid: UUID) -> Dict[str, Any]:
        """
        Get user stats or create if they don't exist.
        
        Args:
            uid: User ID
            
        Returns:
            User stats data
        """
        stats = await self.get_user_stats(uid)
        if stats:
            return stats
        
        # Create new stats with default values
        new_stats = UserStatsCreate(uid=uid)
        return await self.create_user_stats(new_stats)
