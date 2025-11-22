"""
Pydantic schemas for user_stats-related operations.
"""

from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal


# ==================== BASE SCHEMAS ====================

class UserStatsBase(BaseModel):
    """Base schema for user stats data."""
    num_listings_posted: int = Field(default=0, ge=0)
    num_listings_applied: int = Field(default=0, ge=0)
    num_listings_assigned: int = Field(default=0, ge=0)
    num_listings_completed: int = Field(default=0, ge=0)
    avg_rating: Optional[Decimal] = Field(None, ge=0, le=5)


class UserStatsCreate(UserStatsBase):
    """Schema for creating user stats."""
    uid: UUID


class UserStatsUpdate(BaseModel):
    """Schema for updating user stats."""
    num_listings_posted: Optional[int] = Field(None, ge=0)
    num_listings_applied: Optional[int] = Field(None, ge=0)
    num_listings_assigned: Optional[int] = Field(None, ge=0)
    num_listings_completed: Optional[int] = Field(None, ge=0)
    avg_rating: Optional[Decimal] = Field(None, ge=0, le=5)


class UserStatsResponse(UserStatsBase):
    """Schema for user stats response."""
    uid: UUID
    updated_at: datetime

    class Config:
        from_attributes = True
