"""Pydantic schemas for request/response validation."""

from app.schemas.user_stats import (
    UserStatsBase,
    UserStatsCreate,
    UserStatsUpdate,
    UserStatsResponse,
)
from app.schemas.user_preferences import (
    UserPreferenceBase,
    UserPreferenceCreate,
    UserPreferenceBulkCreate,
    UserPreferenceResponse,
    UserPreferencesWithTagsResponse,
)
from app.schemas.listing_applicants import (
    ApplicantStatus,
    ListingApplicantBase,
    ListingApplicantCreate,
    ListingApplicantUpdate,
    ListingApplicantResponse,
    ListingApplicantWithDetailsResponse,
    ApplicantFilters,
)
from app.schemas.user import (
    UserRole,
    UserProfileBase,
    UserProfileCreate,
    UserProfileUpdate,
    UserProfileResponse,
    UserCreditsUpdate,
    UserLocationUpdate,
)

__all__ = [
    # User Stats
    "UserStatsBase",
    "UserStatsCreate",
    "UserStatsUpdate",
    "UserStatsResponse",
    # User Preferences
    "UserPreferenceBase",
    "UserPreferenceCreate",
    "UserPreferenceBulkCreate",
    "UserPreferenceResponse",
    "UserPreferencesWithTagsResponse",
    # Listing Applicants
    "ApplicantStatus",
    "ListingApplicantBase",
    "ListingApplicantCreate",
    "ListingApplicantUpdate",
    "ListingApplicantResponse",
    "ListingApplicantWithDetailsResponse",
    "ApplicantFilters",
    # User Profiles
    "UserRole",
    "UserProfileBase",
    "UserProfileCreate",
    "UserProfileUpdate",
    "UserProfileResponse",
    "UserCreditsUpdate",
    "UserLocationUpdate",
]
