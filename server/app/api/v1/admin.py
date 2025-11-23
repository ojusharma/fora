"""Admin endpoints for ML model training and testing."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal
import logging

from app.ml.training import MLTrainingService
from app.ml.sample_data_generator import generate_sample_data
from app.core.database import get_supabase_client

router = APIRouter()
logger = logging.getLogger(__name__)


class TrainingRequest(BaseModel):
    task_type: Literal["daily", "hourly", "frequent"]


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
