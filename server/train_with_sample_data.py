import asyncio
import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.ml.sample_data_generator import generate_sample_data
from app.ml.recommender import CollaborativeFilter, HybridRecommender

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SampleDataTrainer:
    def __init__(self):
        self.collaborative_filter = CollaborativeFilter()
        self.hybrid_recommender = HybridRecommender()
        
    def train_collaborative_filter(self, interactions):
        logger.info("Training collaborative filtering model...")
        
        if len(interactions) < 100:
            logger.warning("Not enough interactions for collaborative filtering")
            return
        
        logger.info(f"Building user-item matrix from {len(interactions)} interactions...")
        self.collaborative_filter.build_user_item_matrix(interactions)
        
        logger.info("Calculating user similarities...")
        similarity_matrix = self.collaborative_filter.calculate_user_similarity()
        
        num_users = len(self.collaborative_filter.user_index_map)
        num_items = len(self.collaborative_filter.item_index_map)
        logger.info(f"Built matrix: {num_users} users × {num_items} listings")
        logger.info(f"Matrix density: {len(interactions) / (num_users * num_items) * 100:.2f}%")
        
        logger.info("\nSample user similarities:")
        user_list = list(self.collaborative_filter.user_index_map.items())[:5]
        for user_uid, user_idx in user_list:
            similarities = similarity_matrix[user_idx].toarray()[0]
            top_similar = similarities.argsort()[::-1][1:4]
            
            similar_users = []
            for sim_idx in top_similar:
                score = similarities[sim_idx]
                if score > 0.1:
                    similar_users.append(f"{score:.3f}")
            
            if similar_users:
                logger.info(f"  User {user_uid[:8]}... → {', '.join(similar_users)}")
        
        logger.info("✓ Collaborative filtering model trained")
    
    def test_recommendations(self, users, listings, interactions):
        logger.info("\n" + "="*60)
        logger.info("Testing Recommendations")
        logger.info("="*60)
        
        user_interaction_counts = {}
        for interaction in interactions:
            uid = interaction["user_uid"]
            user_interaction_counts[uid] = user_interaction_counts.get(uid, 0) + 1
        
        test_user_uid = max(user_interaction_counts.items(), key=lambda x: x[1])[0]
        test_user = next(u for u in users if u["uid"] == test_user_uid)
        
        logger.info(f"\nTest User: {test_user_uid[:8]}...")
        logger.info(f"  Location: {test_user['location_name']}")
        logger.info(f"  Activity: {test_user['activity_level']}")
        logger.info(f"  Total interactions: {user_interaction_counts[test_user_uid]}")
        
        user_interactions = [i for i in interactions if i["user_uid"] == test_user_uid]
        interaction_summary = {}
        for interaction in user_interactions:
            int_type = interaction["interaction_type"]
            interaction_summary[int_type] = interaction_summary.get(int_type, 0) + 1
        logger.info(f"  Past interactions: {dict(sorted(interaction_summary.items()))}")
        
        if self.collaborative_filter.user_item_matrix is not None:
            logger.info(f"\nCollaborative Filtering Top 5:")
            interacted_listing_ids = {i["listing_id"] for i in user_interactions}
            candidate_listings = [l["id"] for l in listings if l["id"] not in interacted_listing_ids]
            
            cf_recommendations = self.collaborative_filter.get_recommendations(
                test_user_uid, candidate_listings[:50], top_k=10
            )
            
            if cf_recommendations:
                for i, (listing_id, score) in enumerate(cf_recommendations[:5], 1):
                    listing = next(l for l in listings if l["id"] == listing_id)
                    logger.info(f"  {i}. {listing['name']} (score: {score:.3f}, comp: ${listing['compensation'] or 0})")
        
        logger.info(f"\nHybrid Recommendations Top 5:")
        interacted_listing_ids = {i["listing_id"] for i in user_interactions}
        candidate_listings = [l for l in listings if l["id"] not in interacted_listing_ids][:50]
        
        user_data = {
            "latitude": test_user["latitude"],
            "longitude": test_user["longitude"],
            "preferred_tags": test_user["preferred_tags"],
            "max_distance_km": test_user["max_distance_km"]
        }
        
        ranked_listings = self.hybrid_recommender.rank_listings(
            test_user_uid, candidate_listings, user_data, top_n=5
        )
        
        for i, listing in enumerate(ranked_listings, 1):
            logger.info(f"  {i}. {listing['name']} (score: {listing['recommendation_score']:.3f})")
        
        logger.info("\n" + "="*60)
    
    def save_model_info(self, output_file: str = "model_info.txt"):
        with open(output_file, 'w') as f:
            f.write("ML Model Training Summary\n")
            f.write("="*60 + "\n\n")
            
            if self.collaborative_filter.user_item_matrix is not None:
                num_users = len(self.collaborative_filter.user_index_map)
                num_items = len(self.collaborative_filter.item_index_map)
                f.write(f"Collaborative Filtering Model:\n")
                f.write(f"  Users: {num_users}\n")
                f.write(f"  Listings: {num_items}\n")
                f.write(f"  Matrix shape: {self.collaborative_filter.user_item_matrix.shape}\n")
                f.write(f"  Matrix density: {self.collaborative_filter.user_item_matrix.nnz / (num_users * num_items) * 100:.2f}%\n")
            
            f.write("\nModel trained successfully!\n")
        logger.info(f"Model info saved to {output_file}")


async def main():
    parser = argparse.ArgumentParser(description="Train ML model with sample data")
    parser.add_argument("--users", type=int, default=100, help="Number of sample users")
    parser.add_argument("--listings", type=int, default=500, help="Number of sample listings")
    parser.add_argument("--interactions", type=int, default=50, help="Avg interactions per user")
    parser.add_argument("--test", action="store_true", help="Run recommendation tests")
    args = parser.parse_args()
    
    logger.info("="*60)
    logger.info("ML Model Training with Sample Data")
    logger.info(f"Users: {args.users} | Listings: {args.listings} | Interactions: {args.interactions}")
    logger.info("="*60 + "\n")
    
    logger.info("Generating sample data...")
    users, listings, interactions = generate_sample_data(
        num_users=args.users,
        num_listings=args.listings,
        interactions_per_user=args.interactions
    )
    
    logger.info("\nTraining models...")
    trainer = SampleDataTrainer()
    trainer.train_collaborative_filter(interactions)
    
    if args.test:
        trainer.test_recommendations(users, listings, interactions)
    
    trainer.save_model_info()
    
    logger.info("\n" + "="*60)
    logger.info("Training Complete! Check model_info.txt for details.")
    logger.info("="*60)


if __name__ == "__main__":
    asyncio.run(main())
