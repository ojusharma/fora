"""Admin endpoints for ML model training, testing, and user/listing management."""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Literal, List, Tuple
from uuid import UUID
import logging

from app.ml.training import MLTrainingService
from app.ml.sample_data_generator import generate_sample_data
from app.core.database import get_supabase_client
from app.core.deps import require_admin
from app.crud.admin import AdminCRUD
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
from app.schemas.user import UserProfileResponse
from app.schemas.listing import ListingResponse
from supabase import Client

router = APIRouter()
logger = logging.getLogger(__name__)


class TrainingRequest(BaseModel):
    task_type: Literal["daily", "hourly", "frequent"]


class RoleChangeRequest(BaseModel):
    """Request to change a user's role."""
    new_role: Literal["user", "moderator", "admin"]


# ==================== DEPENDENCIES ====================

def get_admin_crud(supabase: Client = Depends(get_supabase_client)) -> AdminCRUD:
    """Dependency to get AdminCRUD instance."""
    return AdminCRUD(supabase)


@router.post("/train-ml")
async def trigger_ml_training(request: TrainingRequest):
    """
    Manually trigger ML training tasks.
    
    - **daily**: Computes user similarity matrices (normally runs at 2 AM)
    - **hourly**: Updates engagement metrics (normally runs every hour)
    - **frequent**: Refreshes trending listings (normally runs every 15 minutes)
    """
    try:
        training_service = MLTrainingService()
        
        if request.task_type == "daily":
            logger.info("Manually triggering daily training...")
            await training_service.compute_user_similarity_matrix()
            await training_service.update_user_feature_vectors()
            return {"status": "success", "message": "Daily training completed"}
        elif request.task_type == "hourly":
            logger.info("Manually triggering hourly update...")
            await training_service.update_engagement_scores()
            return {"status": "success", "message": "Hourly update completed"}
        elif request.task_type == "frequent":
            logger.info("Manually triggering frequent update...")
            await training_service.refresh_trending_listings_view()
            return {"status": "success", "message": "Frequent update completed"}
    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


@router.post("/generate-sample-data")
async def generate_sample_data_endpoint():
    """
    Generate sample listings and interactions for testing.
    
    Creates 20-30 sample listings with various tags and simulates user interactions.
    Useful for bootstrapping the ML system in development.
    """
    try:
        logger.info("Generating sample data...")
        
        # Get current user from database or use a default test user
        supabase = get_supabase_client()
        
        # Fetch existing users to use as poster_uid (from user_profiles which links to auth.users)
        users_response = supabase.table("user_profiles").select("uid").limit(10).execute()
        existing_user_uids = [u["uid"] for u in users_response.data] if users_response.data else []
        
        if not existing_user_uids:
            raise HTTPException(
                status_code=400,
                detail="No user profiles found in database. Please create a user account and profile first."
            )
        
        # Generate the sample data (we'll override poster_uid)
        _, listings, interactions = generate_sample_data(
            num_users=30,
            num_listings=25,
            interactions_per_user=30
        )
        
        # Use first existing user as the poster for all sample listings
        default_poster_uid = existing_user_uids[0]
        
        # Insert listings with valid poster_uid
        listings_to_insert = []
        for listing in listings:
            listings_to_insert.append({
                "id": listing["id"],
                "name": listing["name"],
                "description": listing["description"],
                "poster_uid": default_poster_uid,  # Use existing user
                "latitude": listing["latitude"],
                "longitude": listing["longitude"],
                "compensation": listing["compensation"],
                "status": listing["status"],
                "created_at": listing["created_at"].isoformat()
            })
        
        if listings_to_insert:
            result = supabase.table("listings").insert(listings_to_insert).execute()
            logger.info(f"Inserted {len(listings_to_insert)} listings")
        
        # Insert interactions using existing user UIDs
        interactions_to_insert = []
        for interaction in interactions:
            # Use random existing user for interactions
            import random
            user_uid = random.choice(existing_user_uids)
            
            interactions_to_insert.append({
                "user_uid": user_uid,  # Use existing user
                "listing_id": interaction["listing_id"],
                "interaction_type": interaction["interaction_type"],
                "interaction_time": interaction["interaction_time"].isoformat(),
                "time_spent_seconds": interaction.get("time_spent_seconds")
            })
        
        if interactions_to_insert:
            # Insert in batches to avoid size limits
            batch_size = 100
            for i in range(0, len(interactions_to_insert), batch_size):
                batch = interactions_to_insert[i:i + batch_size]
                supabase.table("user_interactions").insert(batch).execute()
            logger.info(f"Inserted {len(interactions_to_insert)} interactions")
        
        return {
            "status": "success",
            "users_used": len(existing_user_uids),
            "listings_created": len(listings),
            "interactions_created": len(interactions),
        }
    except Exception as e:
        logger.error(f"Sample data generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Sample data generation failed: {str(e)}"
        )


# ==================== USER MANAGEMENT ENDPOINTS ====================

@router.get("/users", response_model=List[UserProfileResponse])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    role: str = None,
    admin_user: Tuple[UUID, dict] = Depends(require_admin),
    crud: AdminCRUD = Depends(get_admin_crud),
):
    """
    Get all users with optional filtering by role.
    Requires admin privileges.
    """
    try:
        users = await crud.get_all_users(skip=skip, limit=limit, role=role)
        return users
    except Exception as e:
        logger.error(f"Failed to fetch users: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_uid}", response_model=UserProfileResponse)
async def get_user(
    user_uid: UUID,
    admin_user: Tuple[UUID, dict] = Depends(require_admin),
    crud: AdminCRUD = Depends(get_admin_crud),
):
    """
    Get a specific user by UID.
    Requires admin privileges.
    """
    try:
        user = await crud.get_user_by_id(user_uid)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/users/{user_uid}", response_model=UserProfileResponse)
async def update_user(
    user_uid: UUID,
    update_data: AdminUserUpdate,
    admin_user: Tuple[UUID, dict] = Depends(require_admin),
    crud: AdminCRUD = Depends(get_admin_crud),
):
    """
    Update a user's profile.
    Admin can update any field including role and credits.
    Requires admin privileges.
    """
    try:
        updated_user = await crud.update_user(user_uid, update_data)
        return updated_user
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/users/{user_uid}", response_model=UserDeleteResponse)
async def delete_user(
    user_uid: UUID,
    admin_user: Tuple[UUID, dict] = Depends(require_admin),
    crud: AdminCRUD = Depends(get_admin_crud),
):
    """
    Delete a user and all associated data.
    This will cascade delete all user's listings, applications, etc.
    Requires admin privileges.
    """
    try:
        success = await crud.delete_user(user_uid)
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        
        return UserDeleteResponse(
            success=True,
            message="User successfully deleted",
            deleted_uid=user_uid
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/users/{user_uid}/role", response_model=UserProfileResponse)
async def change_user_role(
    user_uid: UUID,
    role_data: RoleChangeRequest,
    admin_user: Tuple[UUID, dict] = Depends(require_admin),
    crud: AdminCRUD = Depends(get_admin_crud),
):
    """
    Change a user's role (user, moderator, admin).
    Requires admin privileges.
    """
    try:
        updated_user = await crud.change_user_role(user_uid, role_data.new_role)
        return updated_user
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to change user role: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== LISTING MANAGEMENT ENDPOINTS ====================

@router.get("/listings", response_model=List[ListingResponse])
async def get_all_listings(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    admin_user: Tuple[UUID, dict] = Depends(require_admin),
    crud: AdminCRUD = Depends(get_admin_crud),
):
    """
    Get all listings with optional filtering by status.
    Requires admin privileges.
    """
    try:
        listings = await crud.get_all_listings(skip=skip, limit=limit, status=status)
        return listings
    except Exception as e:
        logger.error(f"Failed to fetch listings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/listings/{listing_id}", response_model=ListingResponse)
async def get_listing(
    listing_id: UUID,
    admin_user: Tuple[UUID, dict] = Depends(require_admin),
    crud: AdminCRUD = Depends(get_admin_crud),
):
    """
    Get a specific listing by ID.
    Requires admin privileges.
    """
    try:
        listing = await crud.get_listing_by_id(listing_id)
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        return listing
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch listing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/listings", response_model=ListingResponse, status_code=status.HTTP_201_CREATED)
async def create_listing(
    listing_data: AdminListingCreate,
    admin_user: Tuple[UUID, dict] = Depends(require_admin),
    crud: AdminCRUD = Depends(get_admin_crud),
):
    """
    Create a listing on behalf of a user.
    Requires admin privileges.
    """
    try:
        created_listing = await crud.create_listing(listing_data)
        return created_listing
    except Exception as e:
        logger.error(f"Failed to create listing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/listings/{listing_id}", response_model=ListingResponse)
async def update_listing(
    listing_id: UUID,
    update_data: AdminListingUpdate,
    admin_user: Tuple[UUID, dict] = Depends(require_admin),
    crud: AdminCRUD = Depends(get_admin_crud),
):
    """
    Update a listing.
    Admin can update any field including poster, assignee, status.
    Requires admin privileges.
    """
    try:
        updated_listing = await crud.update_listing(listing_id, update_data)
        return updated_listing
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update listing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/listings/{listing_id}", response_model=ListingDeleteResponse)
async def delete_listing(
    listing_id: UUID,
    admin_user: Tuple[UUID, dict] = Depends(require_admin),
    crud: AdminCRUD = Depends(get_admin_crud),
):
    """
    Delete a listing.
    Requires admin privileges.
    """
    try:
        success = await crud.delete_listing(listing_id)
        if not success:
            raise HTTPException(status_code=404, detail="Listing not found")
        
        return ListingDeleteResponse(
            success=True,
            message="Listing successfully deleted",
            deleted_id=listing_id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete listing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== STATISTICS ENDPOINTS ====================

@router.get("/stats", response_model=AdminStats)
async def get_platform_stats(
    admin_user: Tuple[UUID, dict] = Depends(require_admin),
    crud: AdminCRUD = Depends(get_admin_crud),
):
    """
    Get overall platform statistics.
    Requires admin privileges.
    """
    try:
        stats = await crud.get_platform_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to fetch platform stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/users/{user_uid}", response_model=AdminUserStats)
async def get_user_stats(
    user_uid: UUID,
    admin_user: Tuple[UUID, dict] = Depends(require_admin),
    crud: AdminCRUD = Depends(get_admin_crud),
):
    """
    Get detailed statistics for a specific user.
    Requires admin privileges.
    """
    try:
        stats = await crud.get_user_stats(user_uid)
        return stats
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to fetch user stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

