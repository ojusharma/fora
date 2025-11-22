"""
Background jobs for ML model training and maintenance.

This module contains tasks for:
- Computing user similarity matrices
- Updating engagement metrics
- Refreshing feature vectors
- Training collaborative filtering models
"""

from typing import Optional
from datetime import datetime, timedelta
import asyncio

from app.core.database import get_supabase_client
from app.ml.recommender import CollaborativeFilter
import logging

logger = logging.getLogger(__name__)


class MLTrainingService:
    """Service for training and updating ML models."""
    
    def __init__(self):
        self.collaborative_filter = CollaborativeFilter()
    
    async def compute_user_similarity_matrix(self):
        """
        Compute user-user similarity matrix for collaborative filtering.
        
        This should be run periodically (e.g., daily) to update recommendations.
        """
        logger.info("Starting user similarity matrix computation...")
        
        supabase = get_supabase_client()
        
        # Fetch recent interactions (last 90 days)
        since_date = (datetime.utcnow() - timedelta(days=90)).isoformat()
        
        interactions_response = (
            supabase.table("user_interactions")
            .select("user_uid, listing_id, interaction_type, interaction_time")
            .gte("interaction_time", since_date)
            .execute()
        )
        
        interactions = interactions_response.data if interactions_response.data else []
        
        if len(interactions) < 100:
            logger.warning("Not enough interactions to build similarity matrix")
            return
        
        # Build user-item matrix
        logger.info(f"Building matrix from {len(interactions)} interactions...")
        self.collaborative_filter.build_user_item_matrix(interactions)
        
        # Compute similarities
        logger.info("Computing user similarities...")
        similarity_matrix = self.collaborative_filter.calculate_user_similarity()
        
        # Store top similarities in database
        logger.info("Storing similarity scores...")
        stored_count = 0
        
        user_indices = list(self.collaborative_filter.user_index_map.items())
        
        for i, (user_a_uid, user_a_idx) in enumerate(user_indices):
            # Get top 50 similar users for this user
            similarities = similarity_matrix[user_a_idx].toarray()[0]
            top_similar_indices = similarities.argsort()[::-1][1:51]  # Exclude self
            
            for similar_idx in top_similar_indices:
                similarity_score = similarities[similar_idx]
                
                if similarity_score <= 0.1:  # Skip low similarities
                    continue
                
                # Find user UID from index
                user_b_uid = None
                for uid, idx in self.collaborative_filter.user_index_map.items():
                    if idx == similar_idx:
                        user_b_uid = uid
                        break
                
                if not user_b_uid:
                    continue
                
                # Ensure user_a < user_b (database constraint)
                if user_a_uid > user_b_uid:
                    user_a_uid, user_b_uid = user_b_uid, user_a_uid
                
                # Count common interactions
                user_a_items = set(self.collaborative_filter.user_item_matrix[user_a_idx].indices)
                user_b_items = set(self.collaborative_filter.user_item_matrix[similar_idx].indices)
                common_count = len(user_a_items & user_b_items)
                
                # Upsert to database
                try:
                    supabase.table("user_similarity_matrix").upsert({
                        "user_a_uid": user_a_uid,
                        "user_b_uid": user_b_uid,
                        "similarity_score": float(similarity_score),
                        "interaction_count": common_count,
                        "last_computed": datetime.utcnow().isoformat()
                    }).execute()
                    stored_count += 1
                except Exception as e:
                    logger.error(f"Error storing similarity: {e}")
        
        logger.info(f"User similarity matrix computation complete. Stored {stored_count} similarities.")
    
    async def update_engagement_scores(self):
        """
        Update engagement and trending scores for all listings.
        
        This should be run frequently (e.g., hourly).
        """
        logger.info("Updating engagement scores...")
        
        supabase = get_supabase_client()
        
        # Get all listings with metrics
        listings_response = (
            supabase.table("listing_engagement_metrics")
            .select("*")
            .execute()
        )
        
        metrics = listings_response.data if listings_response.data else []
        
        for metric in metrics:
            listing_id = metric["listing_id"]
            
            # Calculate engagement score
            engagement_score = (
                metric["apply_count"] * 10.0 +
                metric["save_count"] * 5.0 +
                metric["share_count"] * 3.0 +
                metric["click_count"] * 2.0 +
                metric["view_count"] * 1.0 -
                metric["dismiss_count"] * 5.0
            )
            engagement_score = max(0.0, engagement_score)
            
            # Calculate trending score (recent activity weighted more)
            # Get recent interactions (last 24 hours)
            since_24h = (datetime.utcnow() - timedelta(hours=24)).isoformat()
            
            recent_interactions = (
                supabase.table("user_interactions")
                .select("interaction_type")
                .eq("listing_id", listing_id)
                .gte("interaction_time", since_24h)
                .execute()
            )
            
            recent_count = len(recent_interactions.data) if recent_interactions.data else 0
            trending_score = engagement_score * 0.3 + recent_count * 10.0
            
            # Update metrics
            try:
                supabase.table("listing_engagement_metrics").update({
                    "engagement_score": engagement_score,
                    "trending_score": trending_score,
                    "last_updated": datetime.utcnow().isoformat()
                }).eq("listing_id", listing_id).execute()
            except Exception as e:
                logger.error(f"Error updating metrics for {listing_id}: {e}")
        
        logger.info(f"Updated engagement scores for {len(metrics)} listings")
    
    async def update_user_feature_vectors(self):
        """
        Update user preference feature vectors based on interaction history.
        
        This should be run periodically (e.g., daily).
        """
        logger.info("Updating user feature vectors...")
        
        supabase = get_supabase_client()
        
        # Get all active users (users with recent interactions)
        since_date = (datetime.utcnow() - timedelta(days=90)).isoformat()
        
        users_response = (
            supabase.table("user_interactions")
            .select("user_uid")
            .gte("interaction_time", since_date)
            .execute()
        )
        
        if not users_response.data:
            logger.warning("No active users found")
            return
        
        # Get unique users
        unique_users = {interaction["user_uid"] for interaction in users_response.data}
        
        logger.info(f"Updating feature vectors for {len(unique_users)} users...")
        
        for user_uid in unique_users:
            try:
                # Get user's interactions with listing details
                interactions = (
                    supabase.table("user_interactions")
                    .select("*, listings(*)")
                    .eq("user_uid", user_uid)
                    .gte("interaction_time", since_date)
                    .execute()
                )
                
                if not interactions.data:
                    continue
                
                # Calculate preference statistics
                tag_counts = {}
                compensation_values = []
                location_points = []
                interaction_count = len(interactions.data)
                
                for interaction in interactions.data:
                    listing = interaction.get("listings")
                    if not listing:
                        continue
                    
                    # Aggregate tags
                    if listing.get("tags"):
                        for tag in listing["tags"]:
                            tag_counts[tag] = tag_counts.get(tag, 0) + 1
                    
                    # Aggregate compensation
                    if listing.get("compensation"):
                        compensation_values.append(listing["compensation"])
                    
                    # Aggregate locations
                    if listing.get("latitude") and listing.get("longitude"):
                        location_points.append({
                            "lat": listing["latitude"],
                            "lon": listing["longitude"]
                        })
                
                # Calculate feature vector components
                tag_vector = [
                    tag_counts.get(tag_id, 0) / interaction_count
                    for tag_id in range(1, 51)  # Assuming max 50 tags
                ]
                
                compensation_mean = (
                    sum(compensation_values) / len(compensation_values)
                    if compensation_values else 0.0
                )
                
                compensation_std = 0.0
                if len(compensation_values) > 1:
                    mean = compensation_mean
                    variance = sum((x - mean) ** 2 for x in compensation_values) / len(compensation_values)
                    compensation_std = variance ** 0.5
                
                activity_level = min(interaction_count / 100.0, 1.0)
                
                # Store feature vector
                supabase.table("user_feature_vectors").upsert({
                    "user_uid": user_uid,
                    "tag_preference_vector": tag_vector,
                    "compensation_preference_mean": compensation_mean,
                    "compensation_preference_std": compensation_std,
                    "activity_level": activity_level,
                    "last_computed": datetime.utcnow().isoformat()
                }).execute()
                
            except Exception as e:
                logger.error(f"Error updating feature vector for user {user_uid}: {e}")
        
        logger.info("User feature vector update complete")
    
    async def refresh_trending_listings_view(self):
        """
        Refresh the materialized view for trending listings.
        
        This should be run frequently (e.g., every 15 minutes).
        """
        logger.info("Refreshing trending listings view...")
        
        supabase = get_supabase_client()
        
        try:
            # Execute SQL to refresh materialized view
            # Note: This requires PostgreSQL permissions
            supabase.rpc("refresh_materialized_view", {
                "view_name": "trending_listings"
            }).execute()
            
            logger.info("Trending listings view refreshed successfully")
        except Exception as e:
            logger.error(f"Error refreshing trending view: {e}")


# ==================== SCHEDULED TASK RUNNERS ====================

async def run_daily_training():
    """Run daily training tasks."""
    logger.info("=== Starting daily ML training tasks ===")
    
    service = MLTrainingService()
    
    try:
        await service.compute_user_similarity_matrix()
        await service.update_user_feature_vectors()
    except Exception as e:
        logger.error(f"Error in daily training: {e}")
    
    logger.info("=== Daily ML training tasks complete ===")


async def run_hourly_updates():
    """Run hourly update tasks."""
    logger.info("=== Starting hourly update tasks ===")
    
    service = MLTrainingService()
    
    try:
        await service.update_engagement_scores()
    except Exception as e:
        logger.error(f"Error in hourly updates: {e}")
    
    logger.info("=== Hourly update tasks complete ===")


async def run_frequent_updates():
    """Run frequent update tasks (every 15 minutes)."""
    logger.info("=== Starting frequent update tasks ===")
    
    service = MLTrainingService()
    
    try:
        await service.refresh_trending_listings_view()
    except Exception as e:
        logger.error(f"Error in frequent updates: {e}")
    
    logger.info("=== Frequent update tasks complete ===")


# ==================== MANUAL TRIGGER ====================

if __name__ == "__main__":
    """
    Run training tasks manually.
    
    Usage:
        python -m app.ml.training
    """
    import sys
    
    async def main():
        if len(sys.argv) < 2:
            print("Usage: python -m app.ml.training [daily|hourly|frequent]")
            sys.exit(1)
        
        task_type = sys.argv[1]
        
        if task_type == "daily":
            await run_daily_training()
        elif task_type == "hourly":
            await run_hourly_updates()
        elif task_type == "frequent":
            await run_frequent_updates()
        else:
            print(f"Unknown task type: {task_type}")
            sys.exit(1)
    
    asyncio.run(main())
