"""
CRUD operations for user_preferences table.
"""

from typing import List, Dict, Any, Optional
from uuid import UUID
from supabase import Client

from app.schemas.user_preferences import (
    UserPreferenceCreate,
    UserPreferenceBulkCreate,
)


class UserPreferencesCRUD:
    """CRUD operations for user preferences."""

    def __init__(self, supabase: Client):
        """Initialize with Supabase client."""
        self.supabase = supabase

    # ==================== USER PREFERENCES OPERATIONS ====================

    async def add_preference(
        self, preference: UserPreferenceCreate
    ) -> Dict[str, Any]:
        """
        Add a single tag preference for a user.
        
        Args:
            preference: User preference data
            
        Returns:
            Created preference data
        """
        preference_data = preference.model_dump()
        preference_data["uid"] = str(preference_data["uid"])

        response = (
            self.supabase.table("user_preferences")
            .insert(preference_data)
            .execute()
        )
        return response.data[0] if response.data else None

    async def add_preferences_bulk(
        self, preferences: UserPreferenceBulkCreate
    ) -> List[Dict[str, Any]]:
        """
        Add multiple tag preferences for a user at once.
        
        Args:
            preferences: Bulk preference data with list of tag IDs
            
        Returns:
            List of created preferences
        """
        uid_str = str(preferences.uid)
        preference_records = [
            {"uid": uid_str, "tag_id": tag_id}
            for tag_id in preferences.tag_ids
        ]

        response = (
            self.supabase.table("user_preferences")
            .insert(preference_records)
            .execute()
        )
        return response.data if response.data else []

    async def get_user_preferences(self, uid: UUID) -> List[Dict[str, Any]]:
        """
        Get all tag preferences for a user.
        
        Args:
            uid: User ID
            
        Returns:
            List of user preferences
        """
        response = (
            self.supabase.table("user_preferences")
            .select("*")
            .eq("uid", str(uid))
            .execute()
        )
        return response.data if response.data else []

    async def get_user_preferences_with_tags(
        self, uid: UUID
    ) -> List[Dict[str, Any]]:
        """
        Get all tag preferences for a user with full tag details.
        
        Args:
            uid: User ID
            
        Returns:
            List of user preferences with tag information
        """
        response = (
            self.supabase.table("user_preferences")
            .select("*, tags(*)")
            .eq("uid", str(uid))
            .execute()
        )
        return response.data if response.data else []

    async def get_user_tag_ids(self, uid: UUID) -> List[int]:
        """
        Get list of tag IDs preferred by a user.
        
        Args:
            uid: User ID
            
        Returns:
            List of tag IDs
        """
        preferences = await self.get_user_preferences(uid)
        return [pref["tag_id"] for pref in preferences]

    async def has_preference(self, uid: UUID, tag_id: int) -> bool:
        """
        Check if a user has a specific tag preference.
        
        Args:
            uid: User ID
            tag_id: Tag ID
            
        Returns:
            True if preference exists, False otherwise
        """
        response = (
            self.supabase.table("user_preferences")
            .select("*")
            .eq("uid", str(uid))
            .eq("tag_id", tag_id)
            .execute()
        )
        return len(response.data) > 0 if response.data else False

    async def remove_preference(self, uid: UUID, tag_id: int) -> bool:
        """
        Remove a specific tag preference for a user.
        
        Args:
            uid: User ID
            tag_id: Tag ID to remove
            
        Returns:
            True if deleted, False if not found
        """
        response = (
            self.supabase.table("user_preferences")
            .delete()
            .eq("uid", str(uid))
            .eq("tag_id", tag_id)
            .execute()
        )
        return len(response.data) > 0 if response.data else False

    async def remove_all_preferences(self, uid: UUID) -> bool:
        """
        Remove all tag preferences for a user.
        
        Args:
            uid: User ID
            
        Returns:
            True if any preferences were deleted
        """
        response = (
            self.supabase.table("user_preferences")
            .delete()
            .eq("uid", str(uid))
            .execute()
        )
        return len(response.data) > 0 if response.data else False

    async def set_preferences(
        self, uid: UUID, tag_ids: List[int]
    ) -> List[Dict[str, Any]]:
        """
        Replace all user preferences with a new set of tags.
        This removes existing preferences and adds new ones.
        
        Args:
            uid: User ID
            tag_ids: List of tag IDs to set as preferences
            
        Returns:
            List of created preferences
        """
        # Remove existing preferences
        await self.remove_all_preferences(uid)
        
        # Add new preferences if any
        if not tag_ids:
            return []
        
        bulk_create = UserPreferenceBulkCreate(uid=uid, tag_ids=tag_ids)
        return await self.add_preferences_bulk(bulk_create)

    async def get_users_by_tag_preference(
        self, tag_id: int, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get all users who have a specific tag as a preference.
        
        Args:
            tag_id: Tag ID
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of user preferences for the tag
        """
        response = (
            self.supabase.table("user_preferences")
            .select("*")
            .eq("tag_id", tag_id)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return response.data if response.data else []

    async def count_users_with_preference(self, tag_id: int) -> int:
        """
        Count how many users have a specific tag as a preference.
        
        Args:
            tag_id: Tag ID
            
        Returns:
            Number of users with this preference
        """
        response = (
            self.supabase.table("user_preferences")
            .select("uid", count="exact")
            .eq("tag_id", tag_id)
            .execute()
        )
        return response.count if hasattr(response, 'count') else 0
