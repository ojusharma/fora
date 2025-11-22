"""CRUD operations for database tables."""

from app.crud.user_stats import UserStatsCRUD
from app.crud.user_preferences import UserPreferencesCRUD

__all__ = [
    "UserStatsCRUD",
    "UserPreferencesCRUD",
]
