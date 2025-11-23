"""
CRUD operations for personalized feed and user interactions.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from supabase import Client

from app.ml.recommender import HybridRecommender


class FeedCRUD:
    """CRUD operations for personalized feed and interactions."""

    def __init__(self, supabase: Client):
        """Initialize with Supabase client."""
        self.supabase = supabase
        self.recommender = HybridRecommender()

    # ==================== INTERACTION TRACKING ====================

    async def track_interaction(
        self,
        user_uid: UUID,
        listing_id: UUID,
        interaction_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Track a user interaction with a listing.
        
        Args:
            user_uid: User ID
            listing_id: Listing ID
            interaction_type: Type of interaction (view, click, apply, save, share, dismiss)
            metadata: Additional metadata (time_spent, location, etc.)
            
        Returns:
            Created interaction record
        """
        interaction_data = {
            "user_uid": str(user_uid),
            "listing_id": str(listing_id),
            "interaction_type": interaction_type,
            "metadata": metadata or {}
        }
        
        # Add location if provided in metadata
        if metadata:
            if "latitude" in metadata:
                interaction_data["user_latitude"] = metadata["latitude"]
            if "longitude" in metadata:
                interaction_data["user_longitude"] = metadata["longitude"]
            if "time_spent_seconds" in metadata:
                interaction_data["time_spent_seconds"] = metadata["time_spent_seconds"]
            if "session_id" in metadata:
                interaction_data["session_id"] = metadata["session_id"]
            if "device_type" in metadata:
                interaction_data["device_type"] = metadata["device_type"]

        response = self.supabase.table("user_interactions").insert(interaction_data).execute()
        return response.data[0] if response.data else None

    async def get_user_interactions(
        self,
        user_uid: UUID,
        interaction_types: Optional[List[str]] = None,
        limit: int = 100,
        days: int = 90
    ) -> List[Dict[str, Any]]:
        """
        Get user's recent interactions.
        
        Args:
            user_uid: User ID
            interaction_types: Filter by interaction types
            limit: Maximum number of results
            days: Look back this many days
            
        Returns:
            List of interaction records
        """
        query = (
            self.supabase.table("user_interactions")
            .select("*")
            .eq("user_uid", str(user_uid))
            .gte("interaction_time", (datetime.utcnow() - timedelta(days=days)).isoformat())
            .order("interaction_time", desc=True)
            .limit(limit)
        )
        
        if interaction_types:
            query = query.in_("interaction_type", interaction_types)

        response = query.execute()
        return response.data if response.data else []

    async def get_listing_engagement_metrics(
        self,
        listing_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Get engagement metrics for a listing.
        
        Args:
            listing_id: Listing ID
            
        Returns:
            Engagement metrics or None
        """
        response = (
            self.supabase.table("listing_engagement_metrics")
            .select("*")
            .eq("listing_id", str(listing_id))
            .execute()
        )
        return response.data[0] if response.data else None

    # ==================== USER PREFERENCES ====================

    async def get_user_preferences(
        self,
        user_uid: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Get user's feed preferences.
        
        Args:
            user_uid: User ID
            
        Returns:
            User preferences or None
        """
        response = (
            self.supabase.table("user_feed_preferences")
            .select("*")
            .eq("user_uid", str(user_uid))
            .execute()
        )
        return response.data[0] if response.data else None

    async def update_user_preferences(
        self,
        user_uid: UUID,
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update user's feed preferences.
        
        Args:
            user_uid: User ID
            preferences: Preference updates
            
        Returns:
            Updated preferences
        """
        preferences["updated_at"] = datetime.utcnow().isoformat()
        
        response = (
            self.supabase.table("user_feed_preferences")
            .upsert({
                "user_uid": str(user_uid),
                **preferences
            })
            .execute()
        )
        return response.data[0] if response.data else None

    async def get_user_preferred_tags(
        self,
        user_uid: UUID,
        limit: int = 10
    ) -> List[int]:
        """
        Get user's preferred tags based on interaction history.
        
        Args:
            user_uid: User ID
            limit: Maximum number of tags
            
        Returns:
            List of tag IDs
        """
        try:
            # Try to call database function if it exists
            response = self.supabase.rpc(
                "get_user_preferred_tags",
                {
                    "user_uuid": str(user_uid),
                    "limit_count": limit
                }
            ).execute()
            
            return response.data if response.data else []
        except Exception as e:
            # Fallback: Get tags from recent interactions manually
            try:
                # Get user's recent interactions
                interactions = (
                    self.supabase.table("user_interactions")
                    .select("listing_id")
                    .eq("user_uid", str(user_uid))
                    .in_("interaction_type", ["view", "click", "apply", "save"])
                    .order("interaction_time", desc=True)
                    .limit(100)
                    .execute()
                )
                
                if not interactions.data:
                    return []
                
                # Get listing IDs
                listing_ids = [i["listing_id"] for i in interactions.data]
                
                # Fetch tags from these listings
                listings = (
                    self.supabase.table("listings")
                    .select("tags")
                    .in_("id", listing_ids)
                    .execute()
                )
                
                if not listings.data:
                    return []
                
                # Count tag occurrences
                tag_counts = {}
                for listing in listings.data:
                    if listing.get("tags"):
                        for tag in listing["tags"]:
                            tag_counts[tag] = tag_counts.get(tag, 0) + 1
                
                # Sort by frequency and return top tags
                sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
                return [tag_id for tag_id, count in sorted_tags[:limit]]
                
            except Exception as fallback_error:
                # If everything fails, return empty list
                print(f"Error fetching preferred tags: {fallback_error}")
                return []

    # ==================== PERSONALIZED FEED ====================

    async def get_personalized_feed(
        self,
        user_uid: UUID,
        limit: int = 50,
        offset: int = 0,
        exclude_seen: bool = True,
        exclude_applied: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get personalized feed for a user using ML recommendations.
        
        Args:
            user_uid: User ID
            limit: Number of listings to return
            offset: Pagination offset
            exclude_seen: Exclude recently viewed listings
            exclude_applied: Exclude listings user already applied to
            
        Returns:
            Ranked list of listings
        """
        # Get user profile and preferences
        user_profile = (
            self.supabase.table("user_profiles")
            .select("*")
            .eq("uid", str(user_uid))
            .execute()
        )
        user_profile = user_profile.data[0] if user_profile.data else {}
        
        user_prefs = await self.get_user_preferences(user_uid)
        if not user_prefs:
            user_prefs = {}
        
        preferred_tags = await self.get_user_preferred_tags(user_uid)
        
        # Combine user data
        user_data = {
            **user_profile,
            **user_prefs,
            "preferred_tags": preferred_tags
        }
        
        # Get candidate listings (open status)
        query = (
            self.supabase.table("listings")
            .select("*, listing_engagement_metrics(*)")
            .eq("status", "open")
        )
        
        # Exclude user's own listings
        query = query.neq("poster_uid", str(user_uid))
        
        # Apply user preference filters
        if user_prefs.get("max_distance_km") and user_profile.get("latitude"):
            # Note: PostgreSQL geography queries would be more efficient
            # For now, we fetch all and filter in Python
            pass
        
        if user_prefs.get("preferred_compensation_min"):
            query = query.gte("compensation", user_prefs["preferred_compensation_min"])
        
        if user_prefs.get("preferred_compensation_max"):
            query = query.lte("compensation", user_prefs["preferred_compensation_max"])
        
        # Fetch candidates (fetch more than needed for ranking)
        query = query.limit(limit * 3)
        response = query.execute()
        candidate_listings = response.data if response.data else []
        
        # Exclude already applied listings
        if exclude_applied:
            applied_listings = (
                self.supabase.table("listing_applicants")
                .select("listing_id")
                .eq("applicant_uid", str(user_uid))
                .execute()
            )
            applied_ids = {str(app["listing_id"]) for app in (applied_listings.data or [])}
            candidate_listings = [
                l for l in candidate_listings 
                if str(l["id"]) not in applied_ids
            ]
        
        # Exclude recently seen listings (within last 24 hours)
        if exclude_seen:
            recent_views = await self.get_user_interactions(
                user_uid,
                interaction_types=["view"],
                limit=100,
                days=1
            )
            seen_ids = {str(view["listing_id"]) for view in recent_views}
            candidate_listings = [
                l for l in candidate_listings 
                if str(l["id"]) not in seen_ids
            ]
        
        # Filter by blocked tags
        if user_prefs.get("blocked_tags"):
            blocked_tags = set(user_prefs["blocked_tags"])
            candidate_listings = [
                l for l in candidate_listings
                if not (set(l.get("tags", [])) & blocked_tags)
            ]
        
        # Filter by blocked users
        if user_prefs.get("blocked_users"):
            blocked_users = set(str(u) for u in user_prefs["blocked_users"])
            candidate_listings = [
                l for l in candidate_listings
                if str(l["poster_uid"]) not in blocked_users
            ]
        
        # Flatten engagement metrics
        for listing in candidate_listings:
            if listing.get("listing_engagement_metrics"):
                metrics = listing["listing_engagement_metrics"]
                if isinstance(metrics, list) and len(metrics) > 0:
                    metrics = metrics[0]
                listing.update({
                    "view_count": metrics.get("view_count", 0),
                    "click_count": metrics.get("click_count", 0),
                    "apply_count": metrics.get("apply_count", 0),
                    "save_count": metrics.get("save_count", 0),
                    "share_count": metrics.get("share_count", 0),
                    "dismiss_count": metrics.get("dismiss_count", 0),
                    "engagement_score": metrics.get("engagement_score", 0),
                })
        
        # Rank using ML algorithm
        if user_prefs.get("personalization_enabled", True):
            ranked_listings = self.recommender.rank_listings(
                str(user_uid),
                candidate_listings,
                user_data,
                top_n=limit + offset
            )
        else:
            # Fallback: sort by recency and engagement
            ranked_listings = sorted(
                candidate_listings,
                key=lambda x: (
                    x.get("engagement_score", 0) * 0.5 +
                    (datetime.utcnow() - datetime.fromisoformat(
                        x["created_at"].replace("Z", "+00:00")
                    )).total_seconds() / -86400  # Newer is better
                ),
                reverse=True
            )[:limit + offset]
        
        # Track feed impressions
        for idx, listing in enumerate(ranked_listings[offset:offset+limit], start=offset):
            await self.track_feed_impression(
                user_uid,
                UUID(listing["id"]),
                idx,
                listing.get("recommendation_score")
            )
        
        # Return paginated results
        return ranked_listings[offset:offset+limit]

    async def track_feed_impression(
        self,
        user_uid: UUID,
        listing_id: UUID,
        position: int,
        score: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Track that a listing was shown to user in their feed.
        
        Args:
            user_uid: User ID
            listing_id: Listing ID
            position: Position in feed
            score: Recommendation score
            
        Returns:
            Impression record
        """
        impression_data = {
            "user_uid": str(user_uid),
            "listing_id": str(listing_id),
            "position": position,
            "score": score,
            "algorithm_version": "hybrid_v1"
        }

        response = self.supabase.table("feed_impressions").insert(impression_data).execute()
        return response.data[0] if response.data else None

    # ==================== TRENDING & DISCOVERY ====================

    async def get_trending_listings(
        self,
        limit: int = 20,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get trending listings based on recent engagement.
        
        Args:
            limit: Number of listings
            hours: Time window in hours
            
        Returns:
            List of trending listings
        """
        since = datetime.utcnow() - timedelta(hours=hours)
        
        # Query listings with recent high engagement
        response = (
            self.supabase.table("listings")
            .select("*, listing_engagement_metrics(*)")
            .eq("status", "open")
            .gte("created_at", since.isoformat())
            .order("listing_engagement_metrics.trending_score", desc=True)
            .limit(limit)
            .execute()
        )
        
        return response.data if response.data else []

    async def get_nearby_listings(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 10.0,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get listings near a location.
        
        Args:
            latitude: Center latitude
            longitude: Center longitude
            radius_km: Search radius in kilometers
            limit: Number of listings
            
        Returns:
            List of nearby listings
        """
        # Note: This is a simplified version. For production, use PostGIS
        # ST_DWithin for efficient geographic queries
        
        response = (
            self.supabase.table("listings")
            .select("*")
            .eq("status", "open")
            .not_.is_("latitude", "null")
            .not_.is_("longitude", "null")
            .execute()
        )
        
        listings = response.data if response.data else []
        
        # Filter by distance in Python (inefficient, use PostGIS in production)
        nearby = []
        for listing in listings:
            if listing.get("latitude") and listing.get("longitude"):
                distance = self.recommender.recommendation_engine.calculate_location_distance(
                    latitude, longitude,
                    listing["latitude"], listing["longitude"]
                )
                if distance <= radius_km:
                    listing["distance_km"] = distance
                    nearby.append(listing)
        
        # Sort by distance
        nearby.sort(key=lambda x: x["distance_km"])
        
        return nearby[:limit]

    async def get_similar_listings(
        self,
        listing_id: UUID,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get listings similar to a given listing.
        
        Args:
            listing_id: Reference listing ID
            limit: Number of similar listings
            
        Returns:
            List of similar listings
        """
        # Get reference listing
        ref_listing = (
            self.supabase.table("listings")
            .select("*")
            .eq("id", str(listing_id))
            .execute()
        )
        
        if not ref_listing.data:
            return []
        
        ref_listing = ref_listing.data[0]
        ref_tags = set(ref_listing.get("tags", []))
        
        # Get candidate listings
        candidates = (
            self.supabase.table("listings")
            .select("*")
            .eq("status", "open")
            .neq("id", str(listing_id))
            .limit(100)
            .execute()
        )
        
        candidates = candidates.data if candidates.data else []
        
        # Calculate similarity scores
        for candidate in candidates:
            candidate_tags = set(candidate.get("tags", []))
            
            # Jaccard similarity for tags
            tag_similarity = (
                len(ref_tags & candidate_tags) / len(ref_tags | candidate_tags)
                if (ref_tags or candidate_tags) else 0.0
            )
            
            # Location similarity
            location_similarity = 0.5
            if (ref_listing.get("latitude") and ref_listing.get("longitude") and
                candidate.get("latitude") and candidate.get("longitude")):
                distance = self.recommender.recommendation_engine.calculate_location_distance(
                    ref_listing["latitude"], ref_listing["longitude"],
                    candidate["latitude"], candidate["longitude"]
                )
                location_similarity = max(0, 1 - distance / 50)  # Decay over 50km
            
            # Combined similarity
            candidate["similarity_score"] = (
                tag_similarity * 0.6 +
                location_similarity * 0.4
            )
        
        # Sort by similarity
        candidates.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        return candidates[:limit]
