"""
CRUD operations for tags table.
"""

from typing import Optional, List, Dict, Any
from supabase import Client

from app.schemas.tag import TagCreate, TagUpdate


class TagCRUD:
    """CRUD operations for tags."""

    def __init__(self, supabase: Client):
        """Initialize with Supabase client."""
        self.supabase = supabase

    # ==================== TAG OPERATIONS ====================

    async def create_tag(self, tag: TagCreate) -> Dict[str, Any]:
        """
        Create a new tag.
        
        Args:
            tag: Tag data
            
        Returns:
            Created tag data
            
        Raises:
            Exception if tag with same name already exists
        """
        tag_data = tag.model_dump()
        
        response = self.supabase.table("tags").insert(tag_data).execute()
        return response.data[0] if response.data else None

    async def get_tag_by_id(self, tag_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a tag by ID.
        
        Args:
            tag_id: Tag ID
            
        Returns:
            Tag data or None if not found
        """
        response = self.supabase.table("tags").select("*").eq("id", tag_id).execute()
        return response.data[0] if response.data else None

    async def get_tag_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a tag by name.
        
        Args:
            name: Tag name
            
        Returns:
            Tag data or None if not found
        """
        response = self.supabase.table("tags").select("*").eq("name", name).execute()
        return response.data[0] if response.data else None

    async def get_all_tags(
        self,
        limit: int = 100,
        offset: int = 0,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all tags with optional search filter.
        
        Args:
            limit: Maximum number of tags to return
            offset: Number of tags to skip
            search: Optional search term to filter tags by name
            
        Returns:
            List of tags
        """
        query = self.supabase.table("tags").select("*")
        
        if search:
            query = query.ilike("name", f"%{search}%")
        
        query = query.order("name").range(offset, offset + limit - 1)
        
        response = query.execute()
        return response.data if response.data else []

    async def update_tag(self, tag_id: int, tag: TagUpdate) -> Optional[Dict[str, Any]]:
        """
        Update a tag.
        
        Args:
            tag_id: Tag ID
            tag: Updated tag data
            
        Returns:
            Updated tag data or None if not found
        """
        tag_data = tag.model_dump(exclude_unset=True)
        
        response = (
            self.supabase.table("tags")
            .update(tag_data)
            .eq("id", tag_id)
            .execute()
        )
        return response.data[0] if response.data else None

    async def delete_tag(self, tag_id: int) -> bool:
        """
        Delete a tag.
        
        Args:
            tag_id: Tag ID
            
        Returns:
            True if deleted successfully, False otherwise
        """
        response = self.supabase.table("tags").delete().eq("id", tag_id).execute()
        return len(response.data) > 0 if response.data else False

    async def get_tags_count(self, search: Optional[str] = None) -> int:
        """
        Get total count of tags.
        
        Args:
            search: Optional search term to filter tags by name
            
        Returns:
            Total count of tags
        """
        query = self.supabase.table("tags").select("id", count="exact")
        
        if search:
            query = query.ilike("name", f"%{search}%")
        
        response = query.execute()
        return response.count if response.count else 0
