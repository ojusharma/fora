"""
API endpoints for personalized feed and recommendations.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.core.database import get_supabase_client
from app.crud.feed import FeedCRUD
from app.schemas.feed import (
    InteractionCreate,
    InteractionResponse,
    UserPreferencesUpdate,
    UserPreferencesResponse,
    FeedFilters,
    ListingWithScore,
    EngagementMetricsResponse,
    NearbyListingsQuery,
    TrendingListingsQuery,
    SimilarListingsQuery,
)
from supabase import Client

router = APIRouter()


# ==================== DEPENDENCY ====================

def get_feed_crud(supabase: Client = Depends(get_supabase_client)) -> FeedCRUD:
    """Dependency to get FeedCRUD instance."""
    return FeedCRUD(supabase)


# TODO: Replace with proper authentication
async def get_current_user_uid(
    user_uid: UUID = Query(..., description="Current user UID")
) -> UUID:
    """Temporary: Get current user UID from query parameter."""
    return user_uid


# ==================== INTERACTION TRACKING ENDPOINTS ====================

@router.post(
    "/interactions/{listing_id}",
    response_model=InteractionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Track user interaction with a listing",
)
async def track_interaction(
    listing_id: UUID,
    interaction: InteractionCreate,
    user_uid: UUID = Depends(get_current_user_uid),
    crud: FeedCRUD = Depends(get_feed_crud),
):
    """
    Track user interaction with a listing.
    
    Interaction types:
    - **view**: User viewed the listing
    - **click**: User clicked on the listing
    - **apply**: User applied to the listing
    - **save**: User saved/bookmarked the listing
    - **share**: User shared the listing
    - **dismiss**: User dismissed/hid the listing
    """
    result = await crud.track_interaction(
        user_uid,
        listing_id,
        interaction.interaction_type.value,
        interaction.metadata
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to track interaction",
        )
    
    return result


@router.get(
    "/interactions",
    response_model=List[InteractionResponse],
    summary="Get user's interaction history",
)
async def get_user_interactions(
    interaction_types: Optional[List[str]] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    days: int = Query(90, ge=1, le=365),
    user_uid: UUID = Depends(get_current_user_uid),
    crud: FeedCRUD = Depends(get_feed_crud),
):
    """Get user's interaction history."""
    return await crud.get_user_interactions(
        user_uid,
        interaction_types=interaction_types,
        limit=limit,
        days=days
    )


# ==================== USER PREFERENCES ENDPOINTS ====================

@router.get(
    "/preferences",
    response_model=UserPreferencesResponse,
    summary="Get user's feed preferences",
)
async def get_preferences(
    user_uid: UUID = Depends(get_current_user_uid),
    crud: FeedCRUD = Depends(get_feed_crud),
):
    """Get user's feed preferences."""
    result = await crud.get_user_preferences(user_uid)
    
    if not result:
        # Return default preferences
        return UserPreferencesResponse(
            user_uid=user_uid,
            updated_at=datetime.utcnow()
        )
    
    return result


@router.patch(
    "/preferences",
    response_model=UserPreferencesResponse,
    summary="Update user's feed preferences",
)
async def update_preferences(
    preferences: UserPreferencesUpdate,
    user_uid: UUID = Depends(get_current_user_uid),
    crud: FeedCRUD = Depends(get_feed_crud),
):
    """Update user's feed preferences."""
    # Filter out None values
    update_data = {
        k: v for k, v in preferences.model_dump().items() if v is not None
    }
    
    result = await crud.update_user_preferences(user_uid, update_data)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update preferences",
        )
    
    return result


@router.get(
    "/preferences/tags",
    response_model=List[int],
    summary="Get user's preferred tags based on behavior",
)
async def get_preferred_tags(
    limit: int = Query(10, ge=1, le=50),
    user_uid: UUID = Depends(get_current_user_uid),
    crud: FeedCRUD = Depends(get_feed_crud),
):
    """Get user's preferred tags learned from interaction history."""
    return await crud.get_user_preferred_tags(user_uid, limit)


# ==================== PERSONALIZED FEED ENDPOINTS ====================

@router.get(
    "/",
    response_model=List[ListingWithScore],
    summary="Get personalized feed",
)
async def get_personalized_feed(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    exclude_seen: bool = Query(True),
    exclude_applied: bool = Query(True),
    user_uid: UUID = Depends(get_current_user_uid),
    crud: FeedCRUD = Depends(get_feed_crud),
):
    """
    Get personalized feed using ML recommendations.
    
    The feed is ranked using a hybrid algorithm that considers:
    - **Location proximity**: Listings closer to user get higher scores
    - **Tag matching**: Listings matching user's interests get higher scores
    - **Engagement history**: Popular and trending listings get boosted
    - **Recency**: Newer listings get priority
    - **Poster quality**: Listings from reputable posters rank higher
    - **Collaborative filtering**: "Users like you also viewed" recommendations
    - **Content similarity**: Listings similar to what you've interacted with
    
    Parameters:
    - **limit**: Number of listings to return (1-100)
    - **offset**: Pagination offset
    - **exclude_seen**: Don't show recently viewed listings
    - **exclude_applied**: Don't show listings you've already applied to
    """
    return await crud.get_personalized_feed(
        user_uid,
        limit=limit,
        offset=offset,
        exclude_seen=exclude_seen,
        exclude_applied=exclude_applied
    )


# ==================== DISCOVERY ENDPOINTS ====================

@router.get(
    "/trending",
    response_model=List[ListingWithScore],
    summary="Get trending listings",
)
async def get_trending_listings(
    limit: int = Query(20, ge=1, le=100),
    hours: int = Query(24, ge=1, le=168),
    crud: FeedCRUD = Depends(get_feed_crud),
):
    """
    Get trending listings based on recent engagement.
    
    - **limit**: Number of listings (1-100)
    - **hours**: Time window in hours (1-168)
    """
    return await crud.get_trending_listings(limit=limit, hours=hours)


@router.post(
    "/nearby",
    response_model=List[ListingWithScore],
    summary="Get nearby listings",
)
async def get_nearby_listings(
    query: NearbyListingsQuery,
    crud: FeedCRUD = Depends(get_feed_crud),
):
    """
    Get listings near a specific location.
    
    - **latitude**: Center latitude (-90 to 90)
    - **longitude**: Center longitude (-180 to 180)
    - **radius_km**: Search radius in kilometers (0.1 to 100)
    - **limit**: Number of listings (1-100)
    """
    return await crud.get_nearby_listings(
        query.latitude,
        query.longitude,
        query.radius_km,
        query.limit
    )


@router.get(
    "/similar/{listing_id}",
    response_model=List[ListingWithScore],
    summary="Get similar listings",
)
async def get_similar_listings(
    listing_id: UUID,
    limit: int = Query(10, ge=1, le=50),
    crud: FeedCRUD = Depends(get_feed_crud),
):
    """
    Get listings similar to a given listing.
    
    Similarity is based on:
    - Matching tags
    - Geographic proximity
    - Similar compensation range
    """
    return await crud.get_similar_listings(listing_id, limit)


# ==================== ENGAGEMENT METRICS ENDPOINTS ====================

@router.get(
    "/metrics/{listing_id}",
    response_model=EngagementMetricsResponse,
    summary="Get engagement metrics for a listing",
)
async def get_engagement_metrics(
    listing_id: UUID,
    crud: FeedCRUD = Depends(get_feed_crud),
):
    """Get engagement metrics (views, clicks, applies, etc.) for a listing."""
    result = await crud.get_listing_engagement_metrics(listing_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Engagement metrics not found",
        )
    
    return result
