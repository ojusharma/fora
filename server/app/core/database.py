"""
Database connection and Supabase client initialization.

This module provides the Supabase client instance for all database operations.
"""

from supabase import create_client, Client
from functools import lru_cache
from app.core.config import get_settings


@lru_cache()
def get_supabase_client() -> Client:
    """
    Returns cached Supabase client instance.
    
    The @lru_cache decorator ensures we only create one client instance.
    
    Returns:
        Client: The initialized Supabase client
        
    Raises:
        ValueError: If Supabase credentials are not set
    """
    settings = get_settings()
    
    if not settings.supabase_url or not settings.supabase_key:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_KEY must be set in .env file. "
            "Get them from: https://app.supabase.com/project/_/settings/api"
        )
    
    return create_client(settings.supabase_url, settings.supabase_key)
