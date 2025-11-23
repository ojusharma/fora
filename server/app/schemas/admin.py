"""
Admin-specific schemas for user and listing management.
"""

from typing import Optional, List
from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel, Field

from app.schemas.user import UserRole
from app.schemas.listing import ListingStatus


# ==================== ADMIN USER MANAGEMENT ====================

class AdminUserUpdate(BaseModel):
    """Admin schema for updating any user profile."""
    dob: Optional[date] = None
    phone: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    display_name: Optional[str] = None
    role: Optional[UserRole] = None
    credits: Optional[int] = Field(None, ge=0)
    user_rating: Optional[float] = Field(None, ge=0, le=5)


class AdminUserCreate(BaseModel):
    """Admin schema for creating a user (bypassing normal signup)."""
    uid: UUID
    email: str
    dob: Optional[date] = None
    phone: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    display_name: Optional[str] = None
    role: Optional[UserRole] = UserRole.USER
    credits: Optional[int] = Field(default=0, ge=0)


class UserDeleteResponse(BaseModel):
    """Response for user deletion."""
    success: bool
    message: str
    deleted_uid: UUID


# ==================== ADMIN LISTING MANAGEMENT ====================

class AdminListingUpdate(BaseModel):
    """Admin schema for updating any listing."""
    name: Optional[str] = None
    description: Optional[str] = None
    images: Optional[dict] = None
    status: Optional[ListingStatus] = None
    location_address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    deadline: Optional[datetime] = None
    compensation: Optional[float] = Field(None, ge=0)
    poster_uid: Optional[UUID] = None  # Admin can change poster
    assignee_uid: Optional[UUID] = None  # Admin can assign/unassign
    poster_rating: Optional[float] = Field(None, ge=0, le=5)
    assignee_rating: Optional[float] = Field(None, ge=0, le=5)
    tags: Optional[List[int]] = None


class ListingDeleteResponse(BaseModel):
    """Response for listing deletion."""
    success: bool
    message: str
    deleted_id: UUID


class AdminListingCreate(BaseModel):
    """Admin schema for creating a listing on behalf of a user."""
    name: str
    description: Optional[str] = None
    images: Optional[dict] = None
    poster_uid: UUID  # Admin specifies the poster
    status: Optional[ListingStatus] = ListingStatus.OPEN
    location_address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    deadline: Optional[datetime] = None
    compensation: Optional[float] = Field(None, ge=0)
    tags: Optional[List[int]] = []


# ==================== ADMIN STATISTICS ====================

class AdminStats(BaseModel):
    """Overall platform statistics for admin dashboard."""
    total_users: int
    total_listings: int
    open_listings: int
    completed_listings: int
    total_applications: int
    admin_users: int
    moderator_users: int
    regular_users: int


class AdminUserStats(BaseModel):
    """Detailed statistics for a specific user."""
    uid: UUID
    display_name: Optional[str]
    email: Optional[str]
    role: str
    credits: int
    total_listings_posted: int
    total_listings_completed: int
    total_applications: int
    average_rating: Optional[float]
    account_created: Optional[datetime]
