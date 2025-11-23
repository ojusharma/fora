"""
Pydantic schemas for listing-related operations.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum


class ListingStatus(str, Enum):
    """Listing status enum."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING_CONFIRMATION = "pending_confirmation"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# ==================== BASE SCHEMAS ====================

class ListingBase(BaseModel):
    """Base schema for listing data."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    images: Optional[List[str]] = None
    tags: Optional[List[int]] = Field(default_factory=list)
    location_address: Optional[str] = Field(None, max_length=500)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    deadline: Optional[datetime] = None
    compensation: Optional[float] = Field(None, ge=0)


class ListingCreate(ListingBase):
    """Schema for creating a new listing."""
    pass


class ListingUpdate(BaseModel):
    """Schema for updating a listing."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    images: Optional[List[str]] = None
    tags: Optional[List[int]] = None
    location_address: Optional[str] = Field(None, max_length=500)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    deadline: Optional[datetime] = None
    compensation: Optional[float] = Field(None, ge=0)
    status: Optional[ListingStatus] = None


class ListingResponse(ListingBase):
    """Schema for listing response."""
    id: UUID
    poster_uid: UUID
    assignee_uid: Optional[UUID] = None
    applicants: List[UUID] = Field(default_factory=list)
    status: ListingStatus
    last_posted: datetime
    created_at: datetime
    updated_at: datetime
    poster_rating: Optional[float] = None
    assignee_rating: Optional[float] = None

    class Config:
        from_attributes = True


# ==================== QUERY SCHEMAS ====================

class ListingFilters(BaseModel):
    """Schema for filtering listings."""
    status: Optional[ListingStatus] = None
    exclude_status: Optional[ListingStatus] = None
    poster_uid: Optional[UUID] = None
    assignee_uid: Optional[UUID] = None
    tags: Optional[List[int]] = None
    min_compensation: Optional[float] = Field(None, ge=0)
    max_compensation: Optional[float] = Field(None, ge=0)
    has_deadline: Optional[bool] = None
    limit: int = Field(50, ge=1, le=100)
    offset: int = Field(0, ge=0)

    @field_validator('max_compensation')
    @classmethod
    def validate_compensation_range(cls, v, info):
        if v is not None and info.data.get('min_compensation') is not None:
            if v < info.data['min_compensation']:
                raise ValueError('max_compensation must be >= min_compensation')
        return v
