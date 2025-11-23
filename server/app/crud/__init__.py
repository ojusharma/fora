"""CRUD operations for database tables."""

from app.crud.user_stats import UserStatsCRUD
from app.crud.user_preferences import UserPreferencesCRUD
from app.crud.listing_applicants import ListingApplicantsCRUD
from app.crud.reward import RewardCRUD

__all__ = [
    "UserStatsCRUD",
    "UserPreferencesCRUD",
    "ListingApplicantsCRUD",
    "RewardCRUD",
]
