"""
CRUD operations for User model.
"""

from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from supabase import Client


class UserCRUD:
    """CRUD operations for users."""

    def __init__(self, supabase: Client):
        """Initialize with Supabase client."""
        self.supabase = supabase

    # ==================== USER OPERATIONS ====================

    async def get_user(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get a user by ID.
        
        Args:
            user_id: The user ID
            
        Returns:
            User data or None if not found
        """
        response = self.supabase.table("user_profiles").select("*").eq("uid", str(user_id)).execute()
        return response.data[0] if response.data else None

    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new user profile.
        
        Args:
            user_data: User profile data
            
        Returns:
            Created user data
        """
        response = self.supabase.table("user_profiles").insert(user_data).execute()
        if not response.data:
            raise Exception("Failed to create user profile")
        return response.data[0]

    async def update_user(self, user_id: UUID, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a user profile.
        
        Args:
            user_id: The user ID
            user_data: User profile data to update
            
        Returns:
            Updated user data or None if not found
        """
        # Add last_updated timestamp
        user_data["last_updated"] = datetime.utcnow().isoformat()
        
        response = (
            self.supabase.table("user_profiles")
            .update(user_data)
            .eq("uid", str(user_id))
            .execute()
        )
        return response.data[0] if response.data else None

    async def delete_user(self, user_id: UUID) -> bool:
        """
        Delete a user profile.
        
        Args:
            user_id: The user ID
            
        Returns:
            True if deleted, False if not found
        """
        response = (
            self.supabase.table("user_profiles")
            .delete()
            .eq("uid", str(user_id))
            .execute()
        )
        return len(response.data) > 0 if response.data else False

    async def get_users(
        self,
        skip: int = 0,
        limit: int = 100,
        role: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get a list of users with optional filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            role: Optional role filter
            
        Returns:
            List of user data
        """
        query = self.supabase.table("user_profiles").select("*")
        
        if role:
            query = query.eq("role", role)
        
        response = query.range(skip, skip + limit - 1).execute()
        return response.data if response.data else []

    async def update_user_credits(self, user_id: UUID, credits: int) -> Optional[Dict[str, Any]]:
        """
        Update user credits.
        
        Args:
            user_id: The user ID
            credits: New credit amount
            
        Returns:
            Updated user data or None if not found
        """
        response = (
            self.supabase.table("user_profiles")
            .update({"credits": credits, "last_updated": datetime.utcnow().isoformat()})
            .eq("uid", str(user_id))
            .execute()
        )
        return response.data[0] if response.data else None

    async def add_user_credits(self, user_id: UUID, amount: int) -> Optional[Dict[str, Any]]:
        """
        Add credits to a user's account.
        
        Args:
            user_id: The user ID
            amount: Amount to add (can be negative to subtract)
            
        Returns:
            Updated user data or None if not found
        """
        # Get current credits
        user = await self.get_user(user_id)
        if not user:
            return None
        
        current_credits = user.get("credits", 0)
        new_credits = max(0, current_credits + amount)  # Prevent negative credits
        
        return await self.update_user_credits(user_id, new_credits)

    async def update_user_location(
        self,
        user_id: UUID,
        latitude: float,
        longitude: float
    ) -> Optional[Dict[str, Any]]:
        """
        Update user location coordinates.
        
        Args:
            user_id: The user ID
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Updated user data or None if not found
        """
        response = (
            self.supabase.table("user_profiles")
            .update({
                "latitude": latitude,
                "longitude": longitude,
                "last_updated": datetime.utcnow().isoformat()
            })
            .eq("uid", str(user_id))
            .execute()
        )
        return response.data[0] if response.data else None

    async def get_users_by_location(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 10.0,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get users near a location (simple distance calculation).
        
        Note: This is a simplified implementation. For production,
        consider using PostGIS for more accurate geospatial queries.
        
        Args:
            latitude: Center latitude
            longitude: Center longitude
            radius_km: Radius in kilometers
            limit: Maximum number of users to return
            
        Returns:
            List of nearby users
        """
        # Get all users with location data
        response = (
            self.supabase.table("user_profiles")
            .select("*")
            .not_.is_("latitude", "null")
            .not_.is_("longitude", "null")
            .limit(limit)
            .execute()
        )
        
        if not response.data:
            return []
        
        # Filter by distance (approximate using simple lat/lon difference)
        # For more accurate results, implement Haversine formula or use PostGIS
        nearby_users = []
        for user in response.data:
            lat_diff = abs(user["latitude"] - latitude)
            lon_diff = abs(user["longitude"] - longitude)
            # Rough approximation: 1 degree ≈ 111 km
            distance = ((lat_diff ** 2 + lon_diff ** 2) ** 0.5) * 111
            if distance <= radius_km:
                user["distance_km"] = round(distance, 2)
                nearby_users.append(user)
        
        # Sort by distance
        nearby_users.sort(key=lambda x: x["distance_km"])
        return nearby_users

    async def user_exists(self, user_id: UUID) -> bool:
        """
        Check if a user exists.
        
        Args:
            user_id: The user ID
            
        Returns:
            True if user exists, False otherwise
        """
        response = (
            self.supabase.table("user_profiles")
            .select("uid")
            .eq("uid", str(user_id))
            .execute()
        )
        return len(response.data) > 0 if response.data else False