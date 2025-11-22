"""
Sample Data Generator for ML Model Training

This module generates realistic sample data for training the recommendation model
when there isn't enough real data in the database.

Generates:
- Sample users with preferences
- Sample listings with various attributes
- Sample user interactions (views, clicks, applies, saves, dismisses)
- Sample engagement metrics
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class SampleDataGenerator:
    """Generate realistic sample data for training."""
    
    # Sample tags by category
    TAG_CATEGORIES = {
        "skills": [
            "Programming", "Design", "Writing", "Marketing", "Sales",
            "Customer Service", "Data Analysis", "Project Management",
            "Teaching", "Translation", "Photography", "Video Editing",
            "Accounting", "Legal", "HR", "Research"
        ],
        "industries": [
            "Tech", "Healthcare", "Education", "Finance", "Retail",
            "Hospitality", "Manufacturing", "Real Estate", "Media",
            "Non-Profit", "Government", "Consulting", "Agriculture"
        ],
        "job_types": [
            "Remote", "On-Site", "Hybrid", "Part-Time", "Full-Time",
            "Contract", "Freelance", "Internship", "Temporary", "Permanent"
        ]
    }
    
    # Sample locations (major cities with coordinates)
    SAMPLE_LOCATIONS = [
        {"city": "New York", "lat": 40.7128, "lon": -74.0060},
        {"city": "Los Angeles", "lat": 34.0522, "lon": -118.2437},
        {"city": "Chicago", "lat": 41.8781, "lon": -87.6298},
        {"city": "Houston", "lat": 29.7604, "lon": -95.3698},
        {"city": "Phoenix", "lat": 33.4484, "lon": -112.0740},
        {"city": "San Francisco", "lat": 37.7749, "lon": -122.4194},
        {"city": "Seattle", "lat": 47.6062, "lon": -122.3321},
        {"city": "Boston", "lat": 42.3601, "lon": -71.0589},
        {"city": "Austin", "lat": 30.2672, "lon": -97.7431},
        {"city": "Denver", "lat": 39.7392, "lon": -104.9903},
        {"city": "Miami", "lat": 25.7617, "lon": -80.1918},
        {"city": "Portland", "lat": 45.5152, "lon": -122.6784},
    ]
    
    def __init__(self, num_users: int = 100, num_listings: int = 500):
        """
        Initialize the sample data generator.
        
        Args:
            num_users: Number of sample users to generate
            num_listings: Number of sample listings to generate
        """
        self.num_users = num_users
        self.num_listings = num_listings
        self.users = []
        self.listings = []
        self.interactions = []
        
        # Create tag mappings
        all_tags = []
        for category_tags in self.TAG_CATEGORIES.values():
            all_tags.extend(category_tags)
        self.tags = {i + 1: tag for i, tag in enumerate(all_tags)}
        
    def generate_users(self) -> List[Dict[str, Any]]:
        """
        Generate sample users with varying preferences.
        
        Returns:
            List of user dictionaries
        """
        logger.info(f"Generating {self.num_users} sample users...")
        
        users = []
        
        for i in range(self.num_users):
            # Random location
            location = random.choice(self.SAMPLE_LOCATIONS)
            
            # Random tag preferences (3-7 tags per user)
            num_preferences = random.randint(3, 7)
            preferred_tags = random.sample(list(self.tags.keys()), num_preferences)
            
            # Random activity level (some users more active than others)
            activity_level = random.choice([
                "low",      # 30%
                "low",
                "low",
                "medium",   # 40%
                "medium",
                "medium",
                "medium",
                "high",     # 30%
                "high",
                "high"
            ])
            
            user = {
                "uid": str(uuid.uuid4()),
                "latitude": location["lat"] + random.uniform(-0.5, 0.5),
                "longitude": location["lon"] + random.uniform(-0.5, 0.5),
                "location_name": location["city"],
                "preferred_tags": preferred_tags,
                "activity_level": activity_level,
                "max_distance_km": random.choice([25, 50, 100, 200]),
                "created_at": datetime.utcnow() - timedelta(days=random.randint(30, 365))
            }
            
            users.append(user)
        
        self.users = users
        logger.info(f"Generated {len(users)} users")
        return users
    
    def generate_listings(self) -> List[Dict[str, Any]]:
        """
        Generate sample listings with varying attributes.
        
        Returns:
            List of listing dictionaries
        """
        logger.info(f"Generating {self.num_listings} sample listings...")
        
        if not self.users:
            raise ValueError("Generate users first!")
        
        listings = []
        
        job_titles = [
            "Software Developer", "Graphic Designer", "Content Writer",
            "Marketing Manager", "Sales Representative", "Customer Support",
            "Data Analyst", "Project Manager", "Teacher", "Translator",
            "Photographer", "Video Editor", "Accountant", "Legal Assistant",
            "HR Coordinator", "Research Assistant", "Social Media Manager",
            "Web Developer", "UX Designer", "Copywriter"
        ]
        
        for i in range(self.num_listings):
            # Random poster
            poster = random.choice(self.users)
            
            # Random location (80% near poster, 20% anywhere)
            if random.random() < 0.8:
                location = {
                    "lat": poster["latitude"] + random.uniform(-0.3, 0.3),
                    "lon": poster["longitude"] + random.uniform(-0.3, 0.3)
                }
            else:
                rand_location = random.choice(self.SAMPLE_LOCATIONS)
                location = {
                    "lat": rand_location["lat"] + random.uniform(-0.5, 0.5),
                    "lon": rand_location["lon"] + random.uniform(-0.5, 0.5)
                }
            
            # Random tags (2-5 tags per listing)
            num_tags = random.randint(2, 5)
            listing_tags = random.sample(list(self.tags.keys()), num_tags)
            
            # Random compensation
            compensation = random.choice([
                None,  # 20% unpaid
                random.randint(15, 25) * 100,  # $1,500 - $2,500
                random.randint(25, 50) * 100,  # $2,500 - $5,000
                random.randint(50, 100) * 100, # $5,000 - $10,000
                random.randint(100, 200) * 100 # $10,000 - $20,000
            ])
            
            # Random creation date (last 60 days)
            created_at = datetime.utcnow() - timedelta(
                days=random.randint(1, 60),
                hours=random.randint(0, 23)
            )
            
            listing = {
                "id": str(uuid.uuid4()),
                "name": random.choice(job_titles),
                "description": f"Sample listing for {random.choice(job_titles)}",
                "poster_uid": poster["uid"],
                "tags": listing_tags,
                "latitude": location["lat"],
                "longitude": location["lon"],
                "compensation": compensation,
                "status": "open",
                "created_at": created_at,
                "view_count": 0,
                "click_count": 0,
                "apply_count": 0,
                "save_count": 0,
                "share_count": 0,
                "dismiss_count": 0
            }
            
            listings.append(listing)
        
        self.listings = listings
        logger.info(f"Generated {len(listings)} listings")
        return listings
    
    def generate_interactions(self, interactions_per_user: int = 50) -> List[Dict[str, Any]]:
        """
        Generate realistic user interactions.
        
        Args:
            interactions_per_user: Average number of interactions per user
            
        Returns:
            List of interaction dictionaries
        """
        logger.info(f"Generating user interactions...")
        
        if not self.users or not self.listings:
            raise ValueError("Generate users and listings first!")
        
        interactions = []
        
        interaction_types = ['view', 'click', 'apply', 'save', 'share', 'dismiss']
        
        # Interaction probabilities based on type
        # view -> click -> apply/save (funnel)
        interaction_funnel = {
            'view': 1.0,      # All interactions start with view
            'click': 0.3,     # 30% of views become clicks
            'apply': 0.05,    # 5% of views become applies
            'save': 0.08,     # 8% of views become saves
            'share': 0.02,    # 2% of views become shares
            'dismiss': 0.15   # 15% of views become dismisses
        }
        
        for user in self.users:
            # Number of interactions based on activity level
            if user["activity_level"] == "low":
                num_interactions = random.randint(10, 30)
            elif user["activity_level"] == "medium":
                num_interactions = random.randint(30, 70)
            else:  # high
                num_interactions = random.randint(70, 150)
            
            # Select listings this user will interact with
            # Users more likely to interact with listings matching their preferences
            candidate_listings = []
            
            for listing in self.listings:
                # Calculate relevance score
                score = 0.0
                
                # Tag overlap
                tag_overlap = len(set(user["preferred_tags"]) & set(listing["tags"]))
                score += tag_overlap * 2.0
                
                # Distance
                distance = self._calculate_distance(
                    user["latitude"], user["longitude"],
                    listing["latitude"], listing["longitude"]
                )
                if distance < user["max_distance_km"]:
                    score += (1.0 - distance / user["max_distance_km"]) * 3.0
                
                # Recency
                days_old = (datetime.utcnow() - listing["created_at"]).days
                recency_score = max(0, 1.0 - days_old / 60.0)
                score += recency_score * 2.0
                
                # Random factor
                score += random.uniform(0, 2)
                
                candidate_listings.append((listing, score))
            
            # Sort by relevance and select top candidates
            candidate_listings.sort(key=lambda x: x[1], reverse=True)
            top_listings = [l[0] for l in candidate_listings[:num_interactions * 2]]
            
            # Generate interactions
            interacted_listings = set()
            
            for _ in range(num_interactions):
                if not top_listings:
                    break
                
                # Select a listing
                listing = random.choice(top_listings)
                
                # Skip if already interacted with this listing
                if listing["id"] in interacted_listings:
                    continue
                
                interacted_listings.add(listing["id"])
                
                # Generate interaction sequence
                interaction_time = listing["created_at"] + timedelta(
                    hours=random.randint(0, (datetime.utcnow() - listing["created_at"]).days * 24)
                )
                
                # Always start with view
                interactions.append({
                    "user_uid": user["uid"],
                    "listing_id": listing["id"],
                    "interaction_type": "view",
                    "interaction_time": interaction_time,
                    "time_spent_seconds": random.randint(5, 120)
                })
                listing["view_count"] += 1
                
                # Subsequent interactions based on probabilities
                for int_type in ['click', 'save', 'apply', 'share', 'dismiss']:
                    if random.random() < interaction_funnel[int_type]:
                        interactions.append({
                            "user_uid": user["uid"],
                            "listing_id": listing["id"],
                            "interaction_type": int_type,
                            "interaction_time": interaction_time + timedelta(seconds=random.randint(5, 300))
                        })
                        
                        # Update listing counts
                        listing[f"{int_type}_count"] += 1
                        
                        # Stop after apply or dismiss
                        if int_type in ['apply', 'dismiss']:
                            break
        
        self.interactions = interactions
        logger.info(f"Generated {len(interactions)} interactions")
        return interactions
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in km (Haversine formula)."""
        import math
        
        R = 6371  # Earth's radius in km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics of generated data."""
        if not self.interactions:
            return {}
        
        interaction_counts = {}
        for interaction in self.interactions:
            int_type = interaction["interaction_type"]
            interaction_counts[int_type] = interaction_counts.get(int_type, 0) + 1
        
        return {
            "num_users": len(self.users),
            "num_listings": len(self.listings),
            "num_interactions": len(self.interactions),
            "interaction_breakdown": interaction_counts,
            "avg_interactions_per_user": len(self.interactions) / len(self.users),
            "avg_interactions_per_listing": len(self.interactions) / len(self.listings)
        }


def generate_sample_data(
    num_users: int = 100,
    num_listings: int = 500,
    interactions_per_user: int = 50
) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Convenience function to generate all sample data.
    
    Args:
        num_users: Number of users to generate
        num_listings: Number of listings to generate
        interactions_per_user: Average interactions per user
        
    Returns:
        Tuple of (users, listings, interactions)
    """
    generator = SampleDataGenerator(num_users, num_listings)
    
    users = generator.generate_users()
    listings = generator.generate_listings()
    interactions = generator.generate_interactions(interactions_per_user)
    
    summary = generator.get_summary()
    logger.info(f"Sample data generation complete:")
    logger.info(f"  Users: {summary['num_users']}")
    logger.info(f"  Listings: {summary['num_listings']}")
    logger.info(f"  Interactions: {summary['num_interactions']}")
    logger.info(f"  Breakdown: {summary['interaction_breakdown']}")
    
    return users, listings, interactions


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    users, listings, interactions = generate_sample_data(
        num_users=100,
        num_listings=500,
        interactions_per_user=50
    )
    
    print(f"\nGenerated {len(users)} users, {len(listings)} listings, {len(interactions)} interactions")
