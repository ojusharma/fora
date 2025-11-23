from typing import Optional
from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel, Field
from enum import Enum


class UserRole(str, Enum):
    """User role enum."""
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"


class UserProfileBase(BaseModel):
    """Base schema for user profile."""
    dob: Optional[date] = None
    phone: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    display_name: Optional[str] = None


class UserProfileCreate(UserProfileBase):
    """Schema for creating a user profile."""
    uid: UUID
    role: Optional[UserRole] = UserRole.USER
    credits: Optional[int] = Field(default=0, ge=0)


class UserProfileUpdate(BaseModel):
    """Schema for updating a user profile."""
    dob: Optional[date] = None
    phone: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    display_name: Optional[str] = None
    role: Optional[UserRole] = None


class UserProfileResponse(BaseModel):
    """Schema for user profile response."""
    uid: UUID
    dob: Optional[date] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    credits: Optional[int] = 0
    last_updated: Optional[datetime] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    display_name: Optional[str] = None
    user_rating: Optional[float] = None
    no_ratings: Optional[int] = 0

    class Config:
        orm_mode = True


class UserCreditsUpdate(BaseModel):
    """Schema for updating user credits."""
    credits: int = Field(..., description="New credit amount")


class UserLocationUpdate(BaseModel):
    """Schema for updating user location."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
