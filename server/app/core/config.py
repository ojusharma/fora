"""
Core configuration module for Supabase and application settings.

This module handles all environment variables and application configuration.
"""

import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application Settings
    app_name: str = "Fora API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Supabase Configuration
    supabase_url: str
    supabase_key: str
    
    # API Settings
    api_v1_prefix: str = "/api/v1"
    
    # CORS Settings
    cors_origins: str = "http://localhost:3000,http://localhost:3001"
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Returns cached settings instance.
    
    The @lru_cache decorator ensures we only load settings once.
    """
    return Settings()
