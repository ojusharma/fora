"""
Dependencies for authentication and authorization.
"""

from fastapi import Depends, HTTPException, status, Header
from typing import Optional, Tuple
from uuid import UUID

from app.core.database import get_supabase_client
from app.schemas.user import UserRole
from supabase import Client


async def get_current_user(
    authorization: Optional[str] = Header(None),
    supabase: Client = Depends(get_supabase_client)
) -> Tuple[UUID, dict]:
    """
    Get current authenticated user from JWT token.
    
    Args:
        authorization: Authorization header with Bearer token
        supabase: Supabase client
        
    Returns:
        Tuple of (user_uid, user_data)
        
    Raises:
        HTTPException: If authentication fails
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Extract token from "Bearer <token>"
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify token with Supabase
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_uid = UUID(user_response.user.id)
        
        # Fetch user profile to get role and other data
        profile_response = supabase.table("user_profiles").select("*").eq("uid", str(user_uid)).execute()
        
        if not profile_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        user_profile = profile_response.data[0]
        
        return user_uid, user_profile
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def require_admin(
    current_user: Tuple[UUID, dict] = Depends(get_current_user)
) -> Tuple[UUID, dict]:
    """
    Require the current user to be an admin.
    
    Args:
        current_user: Current authenticated user from get_current_user
        
    Returns:
        Tuple of (user_uid, user_data) if user is admin
        
    Raises:
        HTTPException: If user is not an admin
    """
    user_uid, user_profile = current_user
    user_role = user_profile.get("role", "user")
    
    if user_role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return current_user


async def require_moderator_or_admin(
    current_user: Tuple[UUID, dict] = Depends(get_current_user)
) -> Tuple[UUID, dict]:
    """
    Require the current user to be a moderator or admin.
    
    Args:
        current_user: Current authenticated user from get_current_user
        
    Returns:
        Tuple of (user_uid, user_data) if user is moderator or admin
        
    Raises:
        HTTPException: If user is neither moderator nor admin
    """
    user_uid, user_profile = current_user
    user_role = user_profile.get("role", "user")
    
    if user_role not in [UserRole.ADMIN.value, UserRole.MODERATOR.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Moderator or admin privileges required"
        )
    
    return current_user
