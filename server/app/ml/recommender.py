"""
ML-based Recommendation Engine for Personalized Feed.

This module implements multiple recommendation algorithms:
1. Collaborative Filtering: Recommends based on similar users' behavior
2. Content-Based Filtering: Recommends based on listing features
3. Location-Based Filtering: Recommends based on geographic proximity
4. Hybrid Approach: Combines multiple algorithms with weighted scoring

Uses open-source algorithms from scikit-learn and scipy.
"""

import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.cluster import KMeans
from scipy.sparse import csr_matrix
from collections import defaultdict
import math


class RecommendationEngine:
    """
    Main recommendation engine that orchestrates different algorithms.
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.min_max_scaler = MinMaxScaler()
        
    def calculate_location_distance(
        self, 
        lat1: float, 
        lon1: float, 
        lat2: float, 
        lon2: float
    ) -> float:
        """
        Calculate distance between two geographic points using Haversine formula.
        
        Args:
            lat1, lon1: First location coordinates
            lat2, lon2: Second location coordinates
            
        Returns:
            Distance in kilometers
        """
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def calculate_location_score(
        self, 
        user_lat: Optional[float],
        user_lon: Optional[float],
        listing_lat: Optional[float],
        listing_lon: Optional[float],
        max_distance: float = 50.0
    ) -> float:
        """
        Calculate location-based score (1.0 = very close, 0.0 = far away).
        
        Args:
            user_lat, user_lon: User's location
            listing_lat, listing_lon: Listing's location
            max_distance: Maximum distance to consider (km)
            
        Returns:
            Score between 0.0 and 1.0
        """
        if not all([user_lat, user_lon, listing_lat, listing_lon]):
            return 0.5  # Neutral score if location unknown
        
        distance = self.calculate_location_distance(
            user_lat, user_lon, listing_lat, listing_lon
        )
        
        # Exponential decay: score decreases as distance increases
        score = math.exp(-distance / (max_distance / 3))
        return max(0.0, min(1.0, score))
    
    def calculate_tag_similarity(
        self, 
        user_tags: List[int], 
        listing_tags: List[int]
    ) -> float:
        """
        Calculate Jaccard similarity between user preferences and listing tags.
        
        Args:
            user_tags: List of user's preferred tag IDs
            listing_tags: List of listing's tag IDs
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not user_tags or not listing_tags:
            return 0.5  # Neutral score if no tags
        
        user_set = set(user_tags)
        listing_set = set(listing_tags)
        
        intersection = len(user_set & listing_set)
        union = len(user_set | listing_set)
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def calculate_engagement_score(
        self, 
        view_count: int,
        click_count: int,
        apply_count: int,
        save_count: int,
        share_count: int,
        dismiss_count: int
    ) -> float:
        """
        Calculate normalized engagement score for a listing.
        
        Args:
            view_count, click_count, apply_count, save_count, share_count, dismiss_count:
                Engagement metrics
            
        Returns:
            Normalized engagement score
        """
        # Weighted scoring
        score = (
            apply_count * 10.0 +
            save_count * 5.0 +
            share_count * 3.0 +
            click_count * 2.0 +
            view_count * 1.0 -
            dismiss_count * 5.0
        )
        
        # Apply logarithmic scaling to prevent viral posts from dominating
        if score > 0:
            score = math.log1p(score) * 10
        
        return max(0.0, score)
    
    def calculate_recency_score(
        self, 
        created_at: datetime,
        current_time: Optional[datetime] = None
    ) -> float:
        """
        Calculate recency score (newer listings get higher scores).
        
        Args:
            created_at: When the listing was created
            current_time: Current time (defaults to now)
            
        Returns:
            Score between 0.0 and 1.0
        """
        if current_time is None:
            current_time = datetime.utcnow()
        
        age_days = (current_time - created_at).total_seconds() / 86400
        
        # Exponential decay over 30 days
        score = math.exp(-age_days / 10)
        return max(0.0, min(1.0, score))
    
    def calculate_poster_quality_score(
        self,
        poster_rating: Optional[float],
        num_listings_posted: int,
        num_listings_completed: int
    ) -> float:
        """
        Calculate poster quality score based on history and ratings.
        
        Args:
            poster_rating: Average rating (1-5)
            num_listings_posted: Total listings posted
            num_listings_completed: Total listings completed
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        # Rating component (normalized to 0-1)
        rating_score = (poster_rating or 3.0) / 5.0
        
        # Completion rate
        completion_rate = (
            num_listings_completed / max(num_listings_posted, 1)
        ) if num_listings_posted > 0 else 0.5
        
        # Experience factor (logarithmic scaling)
        experience_factor = min(1.0, math.log1p(num_listings_posted) / 5)
        
        # Weighted combination
        quality_score = (
            rating_score * 0.5 +
            completion_rate * 0.3 +
            experience_factor * 0.2
        )
        
        return max(0.0, min(1.0, quality_score))


class CollaborativeFilter:
    """
    Collaborative Filtering implementation using user-user similarity.
    
    This uses the "Users who interacted with X also interacted with Y" approach.
    """
    
    def __init__(self):
        self.user_item_matrix = None
        self.user_similarity_matrix = None
        self.user_index_map = {}
        self.item_index_map = {}
    
    def build_user_item_matrix(
        self, 
        interactions: List[Dict[str, Any]]
    ) -> csr_matrix:
        """
        Build sparse user-item interaction matrix.
        
        Args:
            interactions: List of interaction records with user_uid, listing_id, 
                         and interaction_type
        
        Returns:
            Sparse CSR matrix
        """
        # Weight different interaction types
        interaction_weights = {
            'apply': 10.0,
            'save': 5.0,
            'share': 3.0,
            'click': 2.0,
            'view': 1.0,
            'dismiss': -5.0
        }
        
        # Build user and item indices
        users = set()
        items = set()
        for interaction in interactions:
            users.add(interaction['user_uid'])
            items.add(interaction['listing_id'])
        
        self.user_index_map = {user: idx for idx, user in enumerate(sorted(users))}
        self.item_index_map = {item: idx for idx, item in enumerate(sorted(items))}
        
        # Build matrix
        rows = []
        cols = []
        data = []
        
        user_item_scores = defaultdict(lambda: defaultdict(float))
        
        for interaction in interactions:
            user_idx = self.user_index_map[interaction['user_uid']]
            item_idx = self.item_index_map[interaction['listing_id']]
            weight = interaction_weights.get(
                interaction['interaction_type'], 1.0
            )
            
            user_item_scores[user_idx][item_idx] += weight
        
        for user_idx, items_dict in user_item_scores.items():
            for item_idx, score in items_dict.items():
                rows.append(user_idx)
                cols.append(item_idx)
                data.append(score)
        
        matrix = csr_matrix(
            (data, (rows, cols)),
            shape=(len(self.user_index_map), len(self.item_index_map))
        )
        
        self.user_item_matrix = matrix
        return matrix
    
    def calculate_user_similarity(self) -> np.ndarray:
        """
        Calculate user-user similarity using cosine similarity.
        
        Returns:
            User similarity matrix
        """
        if self.user_item_matrix is None:
            raise ValueError("User-item matrix not built yet")
        
        # Cosine similarity between users
        self.user_similarity_matrix = cosine_similarity(
            self.user_item_matrix, 
            dense_output=False
        )
        
        return self.user_similarity_matrix
    
    def get_recommendations(
        self,
        user_uid: str,
        candidate_listings: List[str],
        top_k: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Get collaborative filtering recommendations for a user.
        
        Args:
            user_uid: User ID
            candidate_listings: List of candidate listing IDs to score
            top_k: Number of similar users to consider
            
        Returns:
            List of (listing_id, score) tuples
        """
        if self.user_item_matrix is None or self.user_similarity_matrix is None:
            return []
        
        if user_uid not in self.user_index_map:
            return []  # Cold start: no data for this user
        
        user_idx = self.user_index_map[user_uid]
        
        # Get similar users
        user_similarities = self.user_similarity_matrix[user_idx].toarray()[0]
        similar_users = np.argsort(user_similarities)[::-1][1:top_k+1]  # Exclude self
        
        # Aggregate scores from similar users
        listing_scores = defaultdict(float)
        
        for similar_user_idx in similar_users:
            similarity = user_similarities[similar_user_idx]
            if similarity <= 0:
                continue
            
            # Get listings this similar user interacted with
            user_interactions = self.user_item_matrix[similar_user_idx].toarray()[0]
            
            for item_idx, interaction_score in enumerate(user_interactions):
                if interaction_score <= 0:
                    continue
                
                # Get listing ID from index
                listing_id = None
                for lid, idx in self.item_index_map.items():
                    if idx == item_idx:
                        listing_id = lid
                        break
                
                if listing_id and listing_id in candidate_listings:
                    listing_scores[listing_id] += similarity * interaction_score
        
        # Sort by score
        recommendations = sorted(
            listing_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return recommendations


class ContentBasedFilter:
    """
    Content-based filtering using listing features and user preferences.
    """
    
    def __init__(self):
        self.tag_vectorizer = None
    
    def create_listing_feature_vector(
        self,
        listing: Dict[str, Any],
        all_tags: List[int]
    ) -> np.ndarray:
        """
        Create feature vector for a listing.
        
        Args:
            listing: Listing data
            all_tags: List of all possible tag IDs
            
        Returns:
            Feature vector as numpy array
        """
        features = []
        
        # Tag one-hot encoding
        listing_tags = listing.get('tags', [])
        tag_vector = [1.0 if tag in listing_tags else 0.0 for tag in all_tags]
        features.extend(tag_vector)
        
        # Normalized compensation
        compensation = listing.get('compensation', 0) or 0
        features.append(min(compensation / 1000.0, 1.0))  # Normalize
        
        # Location features (if available)
        if listing.get('latitude') and listing.get('longitude'):
            features.append(listing['latitude'] / 90.0)  # Normalize
            features.append(listing['longitude'] / 180.0)  # Normalize
        else:
            features.extend([0.0, 0.0])
        
        # Engagement metrics (normalized)
        features.append(math.log1p(listing.get('view_count', 0)) / 10)
        features.append(math.log1p(listing.get('apply_count', 0)) / 5)
        
        return np.array(features)
    
    def create_user_preference_vector(
        self,
        user_interactions: List[Dict[str, Any]],
        all_tags: List[int]
    ) -> np.ndarray:
        """
        Create user preference vector based on interaction history.
        
        Args:
            user_interactions: List of user's past interactions with listings
            all_tags: List of all possible tag IDs
            
        Returns:
            User preference vector
        """
        if not user_interactions:
            # Return neutral preference vector
            return np.zeros(len(all_tags) + 5)
        
        # Aggregate weighted features from interacted listings
        feature_vectors = []
        weights = []
        
        interaction_weights = {
            'apply': 10.0,
            'save': 5.0,
            'share': 3.0,
            'click': 2.0,
            'view': 1.0,
            'dismiss': -3.0
        }
        
        for interaction in user_interactions:
            if 'listing' in interaction:
                listing = interaction['listing']
                feature_vector = self.create_listing_feature_vector(
                    listing, all_tags
                )
                feature_vectors.append(feature_vector)
                
                weight = interaction_weights.get(
                    interaction['interaction_type'], 1.0
                )
                weights.append(weight)
        
        if not feature_vectors:
            return np.zeros(len(all_tags) + 5)
        
        # Weighted average of feature vectors
        feature_matrix = np.array(feature_vectors)
        weight_array = np.array(weights).reshape(-1, 1)
        
        user_vector = np.average(feature_matrix, axis=0, weights=weights)
        
        return user_vector
    
    def calculate_content_similarity(
        self,
        user_vector: np.ndarray,
        listing_vector: np.ndarray
    ) -> float:
        """
        Calculate cosine similarity between user preferences and listing features.
        
        Args:
            user_vector: User preference vector
            listing_vector: Listing feature vector
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Cosine similarity
        dot_product = np.dot(user_vector, listing_vector)
        user_norm = np.linalg.norm(user_vector)
        listing_norm = np.linalg.norm(listing_vector)
        
        if user_norm == 0 or listing_norm == 0:
            return 0.5  # Neutral score
        
        similarity = dot_product / (user_norm * listing_norm)
        
        # Normalize to 0-1 range
        return (similarity + 1) / 2


class HybridRecommender:
    """
    Hybrid recommender that combines multiple algorithms.
    """
    
    def __init__(self):
        self.recommendation_engine = RecommendationEngine()
        self.collaborative_filter = CollaborativeFilter()
        self.content_based_filter = ContentBasedFilter()
    
    def calculate_hybrid_score(
        self,
        user_uid: str,
        listing: Dict[str, Any],
        user_data: Dict[str, Any],
        weights: Optional[Dict[str, float]] = None
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate hybrid recommendation score combining multiple signals.
        
        Args:
            user_uid: User ID
            listing: Listing data
            user_data: User profile and preference data
            weights: Custom weights for different components
            
        Returns:
            Tuple of (final_score, component_scores)
        """
        if weights is None:
            weights = {
                'location': 0.25,
                'tags': 0.20,
                'engagement': 0.15,
                'recency': 0.10,
                'poster_quality': 0.10,
                'collaborative': 0.10,
                'content': 0.10
            }
        
        component_scores = {}
        
        # Location-based score
        component_scores['location'] = self.recommendation_engine.calculate_location_score(
            user_data.get('latitude'),
            user_data.get('longitude'),
            listing.get('latitude'),
            listing.get('longitude'),
            user_data.get('max_distance_km', 50.0)
        )
        
        # Tag similarity score
        user_tags = user_data.get('preferred_tags', [])
        listing_tags = listing.get('tags', [])
        component_scores['tags'] = self.recommendation_engine.calculate_tag_similarity(
            user_tags, listing_tags
        )
        
        # Engagement score
        component_scores['engagement'] = self.recommendation_engine.calculate_engagement_score(
            listing.get('view_count', 0),
            listing.get('click_count', 0),
            listing.get('apply_count', 0),
            listing.get('save_count', 0),
            listing.get('share_count', 0),
            listing.get('dismiss_count', 0)
        ) / 100.0  # Normalize
        
        # Recency score
        created_at = listing.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        component_scores['recency'] = self.recommendation_engine.calculate_recency_score(
            created_at
        )
        
        # Poster quality score
        component_scores['poster_quality'] = self.recommendation_engine.calculate_poster_quality_score(
            listing.get('poster_rating'),
            listing.get('poster_num_listings', 0),
            listing.get('poster_num_completed', 0)
        )
        
        # Collaborative filtering score (placeholder - requires pre-computed matrix)
        component_scores['collaborative'] = 0.5  # Neutral
        
        # Content-based filtering score (placeholder)
        component_scores['content'] = 0.5  # Neutral
        
        # Calculate weighted sum
        final_score = sum(
            weights.get(component, 0) * score 
            for component, score in component_scores.items()
        )
        
        return final_score, component_scores
    
    def rank_listings(
        self,
        user_uid: str,
        listings: List[Dict[str, Any]],
        user_data: Dict[str, Any],
        top_n: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Rank listings for a user using hybrid approach.
        
        Args:
            user_uid: User ID
            listings: List of candidate listings
            user_data: User profile and preferences
            top_n: Return only top N results (None = all)
            
        Returns:
            Ranked list of listings with scores
        """
        ranked_listings = []
        
        for listing in listings:
            score, components = self.calculate_hybrid_score(
                user_uid, listing, user_data
            )
            
            ranked_listings.append({
                **listing,
                'recommendation_score': score,
                'score_components': components
            })
        
        # Sort by score
        ranked_listings.sort(
            key=lambda x: x['recommendation_score'], 
            reverse=True
        )
        
        if top_n:
            return ranked_listings[:top_n]
        
        return ranked_listings
