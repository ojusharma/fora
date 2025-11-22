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

__all__ = [
    "UserStatsBase",
    "UserStatsCreate",
    "UserStatsUpdate",
    "UserStatsResponse",
    "UserPreferenceBase",
    "UserPreferenceCreate",
    "UserPreferenceBulkCreate",
    "UserPreferenceResponse",
    "UserPreferencesWithTagsResponse",
    "ApplicantStatus",
    "ListingApplicantBase",
    "ListingApplicantCreate",
    "ListingApplicantUpdate",
    "ListingApplicantResponse",
    "ListingApplicantWithDetailsResponse",
    "ApplicantFilters",
]
