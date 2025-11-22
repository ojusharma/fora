"""
CRUD operations for User model.
"""

"""
CRUD operations for listings table.
"""

from typing import Optional, Dict, Any
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