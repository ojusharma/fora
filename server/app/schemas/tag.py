"""
Pydantic schemas for tag-related operations.
"""

from pydantic import BaseModel, Field
from typing import Optional


# ==================== BASE SCHEMAS ====================

class TagBase(BaseModel):
    """Base schema for tag data."""
    name: str = Field(..., min_length=1, max_length=50)


class TagCreate(TagBase):
    """Schema for creating a new tag."""
    pass


class TagUpdate(BaseModel):
    """Schema for updating a tag."""
    name: str = Field(..., min_length=1, max_length=50)


class TagResponse(TagBase):
    """Schema for tag response."""
    id: int

    class Config:
        from_attributes = True
