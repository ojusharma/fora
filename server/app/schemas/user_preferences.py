"""
Pydantic schemas for user_preferences-related operations.
"""

from pydantic import BaseModel, Field
from typing import List
from uuid import UUID


# ==================== BASE SCHEMAS ====================

class UserPreferenceBase(BaseModel):
    """Base schema for user preference data."""
    tag_id: int = Field(..., gt=0)


class UserPreferenceCreate(UserPreferenceBase):
    """Schema for creating a user preference."""
    uid: UUID


class UserPreferenceBulkCreate(BaseModel):
    """Schema for creating multiple user preferences at once."""
    uid: UUID
    tag_ids: List[int] = Field(..., min_length=1)


class UserPreferenceResponse(UserPreferenceBase):
    """Schema for user preference response."""
    uid: UUID

    class Config:
        from_attributes = True


class UserPreferencesWithTagsResponse(BaseModel):
    """Schema for user preferences response with tag details."""
    uid: UUID
    tags: List[dict]  # List of tag objects with id and name

    class Config:
        from_attributes = True
