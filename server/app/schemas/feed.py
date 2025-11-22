"""
Pydantic schemas for feed and interaction operations.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


class InteractionType(str, Enum):
    """Interaction type enum."""
    VIEW = "view"
    CLICK = "click"
    APPLY = "apply"
    SAVE = "save"
    SHARE = "share"
    DISMISS = "dismiss"


# ==================== INTERACTION SCHEMAS ====================

class InteractionCreate(BaseModel):
    """Schema for creating an interaction."""
    interaction_type: InteractionType
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class InteractionResponse(BaseModel):
    """Schema for interaction response."""
    id: UUID
    user_uid: UUID
    listing_id: UUID
    interaction_type: InteractionType
    interaction_time: datetime
    session_id: Optional[str] = None
    time_spent_seconds: Optional[int] = None
    user_latitude: Optional[float] = None
    user_longitude: Optional[float] = None
    device_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# ==================== USER PREFERENCES SCHEMAS ====================

class UserPreferencesUpdate(BaseModel):
    """Schema for updating user feed preferences."""
    max_distance_km: Optional[float] = Field(None, ge=0, le=1000)
    preferred_compensation_min: Optional[float] = Field(None, ge=0)
    preferred_compensation_max: Optional[float] = Field(None, ge=0)
    preferred_tags: Optional[List[int]] = None
    blocked_tags: Optional[List[int]] = None
    blocked_users: Optional[List[UUID]] = None
    show_applied_listings: Optional[bool] = None
    show_completed_listings: Optional[bool] = None
    personalization_enabled: Optional[bool] = None


class UserPreferencesResponse(BaseModel):
    """Schema for user preferences response."""
    user_uid: UUID
    max_distance_km: Optional[float] = 50.0
    preferred_compensation_min: Optional[float] = None
    preferred_compensation_max: Optional[float] = None
    preferred_tags: Optional[List[int]] = Field(default_factory=list)
    blocked_tags: Optional[List[int]] = Field(default_factory=list)
    blocked_users: Optional[List[UUID]] = Field(default_factory=list)
    show_applied_listings: bool = False
    show_completed_listings: bool = False
    personalization_enabled: bool = True
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== FEED SCHEMAS ====================

class FeedFilters(BaseModel):
    """Schema for feed filters."""
    limit: int = Field(50, ge=1, le=100)
    offset: int = Field(0, ge=0)
    exclude_seen: bool = True
    exclude_applied: bool = True


class ListingWithScore(BaseModel):
    """Listing with recommendation score."""
    id: UUID
    name: str
    description: Optional[str] = None
    images: Optional[List[str]] = None
    poster_uid: UUID
    tags: Optional[List[int]] = Field(default_factory=list)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    deadline: Optional[datetime] = None
    compensation: Optional[float] = None
    status: str
    created_at: datetime
    recommendation_score: Optional[float] = None
    score_components: Optional[Dict[str, float]] = None
    distance_km: Optional[float] = None

    class Config:
        from_attributes = True


# ==================== ENGAGEMENT METRICS SCHEMAS ====================

class EngagementMetricsResponse(BaseModel):
    """Schema for listing engagement metrics."""
    listing_id: UUID
    view_count: int = 0
    click_count: int = 0
    apply_count: int = 0
    save_count: int = 0
    share_count: int = 0
    dismiss_count: int = 0
    avg_time_spent_seconds: float = 0.0
    engagement_score: float = 0.0
    trending_score: float = 0.0
    last_updated: datetime

    class Config:
        from_attributes = True


# ==================== FEED QUERY SCHEMAS ====================

class NearbyListingsQuery(BaseModel):
    """Schema for nearby listings query."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    radius_km: float = Field(10.0, ge=0.1, le=100)
    limit: int = Field(20, ge=1, le=100)


class TrendingListingsQuery(BaseModel):
    """Schema for trending listings query."""
    limit: int = Field(20, ge=1, le=100)
    hours: int = Field(24, ge=1, le=168)  # Max 1 week


class SimilarListingsQuery(BaseModel):
    """Schema for similar listings query."""
    limit: int = Field(10, ge=1, le=50)
