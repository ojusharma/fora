"""
CRUD operations for Reward model.
"""

from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from supabase import Client


class RewardCRUD:
    """CRUD operations for rewards."""

    def __init__(self, supabase: Client):
        """Initialize with Supabase client."""
        self.supabase = supabase

    # ==================== REWARD OPERATIONS ====================

    async def get_reward(self, reward_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get a reward by ID.
        
        Args:
            reward_id: The reward ID
            
        Returns:
            Reward data or None if not found
        """
        response = (
            self.supabase.table("rewards")
            .select("*")
            .eq("id", str(reward_id))
            .execute()
        )
        return response.data[0] if response.data else None

    async def get_rewards(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get a list of rewards with optional filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            is_active: Filter by active status (None = all, True = active only, False = inactive only)
            include_inactive: If True and is_active is None, include inactive rewards
            
        Returns:
            List of rewards
        """
        query = self.supabase.table("rewards").select("*")
        
        if is_active is not None:
            query = query.eq("is_active", is_active)
        elif not include_inactive:
            query = query.eq("is_active", True)
        
        query = query.order("created_at", desc=True).range(skip, skip + limit - 1)
        
        response = query.execute()
        return response.data if response.data else []

    async def create_reward(self, reward_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new reward.
        
        Args:
            reward_data: Reward data
            
        Returns:
            Created reward data
        """
        response = self.supabase.table("rewards").insert(reward_data).execute()
        if not response.data:
            raise Exception("Failed to create reward")
        return response.data[0]

    async def update_reward(
        self, 
        reward_id: UUID, 
        reward_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update a reward.
        
        Args:
            reward_id: The reward ID
            reward_data: Reward data to update
            
        Returns:
            Updated reward data or None if not found
        """
        response = (
            self.supabase.table("rewards")
            .update(reward_data)
            .eq("id", str(reward_id))
            .execute()
        )
        return response.data[0] if response.data else None

    async def delete_reward(self, reward_id: UUID) -> bool:
        """
        Delete a reward.
        
        Args:
            reward_id: The reward ID
            
        Returns:
            True if deleted, False if not found
        """
        response = (
            self.supabase.table("rewards")
            .delete()
            .eq("id", str(reward_id))
            .execute()
        )
        return len(response.data) > 0 if response.data else False

    async def get_active_rewards(self) -> List[Dict[str, Any]]:
        """
        Get all active rewards.
        
        Returns:
            List of active rewards ordered by created_at descending
        """
        response = (
            self.supabase.table("rewards")
            .select("*")
            .eq("is_active", True)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data if response.data else []

    # ==================== REWARD CLAIM OPERATIONS ====================

    async def create_reward_claim(
        self, 
        reward_id: UUID,
        user_id: UUID,
        reward_title: str,
        credits_spent: int
    ) -> Dict[str, Any]:
        """
        Create a reward claim.
        
        Args:
            reward_id: The reward ID
            user_id: The user ID claiming the reward
            reward_title: Title of the reward at time of claim
            credits_spent: Number of credits spent
            
        Returns:
            Created reward claim data
        """
        claim_data = {
            "reward_id": str(reward_id),
            "user_id": str(user_id),
            "reward_title": reward_title,
            "credits_spent": credits_spent,
        }
        
        response = self.supabase.table("reward_claims").insert(claim_data).execute()
        if not response.data:
            raise Exception("Failed to create reward claim")
        return response.data[0]

    async def get_user_claims(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all claims made by a user.
        
        Args:
            user_id: The user ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of reward claims
        """
        response = (
            self.supabase.table("reward_claims")
            .select("*")
            .eq("user_id", str(user_id))
            .order("claimed_at", desc=True)
            .range(skip, skip + limit - 1)
            .execute()
        )
        return response.data if response.data else []

    async def get_reward_claims(
        self,
        reward_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all claims for a specific reward.
        
        Args:
            reward_id: The reward ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of reward claims
        """
        response = (
            self.supabase.table("reward_claims")
            .select("*")
            .eq("reward_id", str(reward_id))
            .order("claimed_at", desc=True)
            .range(skip, skip + limit - 1)
            .execute()
        )
        return response.data if response.data else []

    async def mark_email_sent(self, claim_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Mark a reward claim email as sent.
        
        Args:
            claim_id: The claim ID
            
        Returns:
            Updated claim data or None if not found
        """
        update_data = {
            "email_sent": True,
            "email_sent_at": datetime.utcnow().isoformat()
        }
        
        response = (
            self.supabase.table("reward_claims")
            .update(update_data)
            .eq("id", str(claim_id))
            .execute()
        )
        return response.data[0] if response.data else None

    async def get_user_claim_stats(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get statistics about a user's reward claims.
        
        Args:
            user_id: The user ID
            
        Returns:
            Dictionary with total_claims and total_credits_spent
        """
        response = (
            self.supabase.table("reward_claims")
            .select("credits_spent")
            .eq("user_id", str(user_id))
            .execute()
        )
        
        claims = response.data if response.data else []
        total_claims = len(claims)
        total_credits_spent = sum(claim.get("credits_spent", 0) for claim in claims)
        
        return {
            "total_claims": total_claims,
            "total_credits_spent": total_credits_spent
        }
