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
from app.schemas.admin import (
    AdminUserUpdate,
    AdminUserCreate,
    AdminListingUpdate,
    AdminListingCreate,
    UserDeleteResponse,
    ListingDeleteResponse,
    AdminStats,
    AdminUserStats,
)
from app.schemas.reward import (
    RewardBase,
    RewardCreate,
    RewardUpdate,
    RewardResponse,
    RewardClaimBase,
    RewardClaimCreate,
    RewardClaimResponse,
    UserRewardClaimHistory,
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
    # Admin
    "AdminUserUpdate",
    "AdminUserCreate",
    "AdminListingUpdate",
    "AdminListingCreate",
    "UserDeleteResponse",
    "ListingDeleteResponse",
    "AdminStats",
    "AdminUserStats",
    # Rewards
    "RewardBase",
    "RewardCreate",
    "RewardUpdate",
    "RewardResponse",
    "RewardClaimBase",
    "RewardClaimCreate",
    "RewardClaimResponse",
    "UserRewardClaimHistory",
]

from .notification import NotificationBase, NotificationCreate, NotificationOut

