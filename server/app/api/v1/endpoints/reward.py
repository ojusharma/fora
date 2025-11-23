"""API endpoints for rewards system."""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional, Tuple
from uuid import UUID
import logging

from app.core.database import get_supabase_client, get_service_role_client
from app.core.deps import require_admin, get_current_user
from app.core.email import get_email_service
from app.crud.reward import RewardCRUD
from app.crud.user import UserCRUD
from app.schemas.reward import (
    RewardCreate,
    RewardUpdate,
    RewardResponse,
    RewardClaimCreate,
    RewardClaimResponse,
    UserRewardClaimHistory,
)
from supabase import Client

router = APIRouter()
logger = logging.getLogger(__name__)


# ==================== DEPENDENCIES ====================

def get_reward_crud(supabase: Client = Depends(get_supabase_client)) -> RewardCRUD:
    """Dependency to get RewardCRUD instance."""
    return RewardCRUD(supabase)


def get_user_crud(supabase: Client = Depends(get_supabase_client)) -> UserCRUD:
    """Dependency to get UserCRUD instance."""
    return UserCRUD(supabase)


# ==================== PUBLIC ENDPOINTS ====================

@router.get(
    "/",
    response_model=List[RewardResponse],
    summary="Get all active rewards",
    description="Get list of all active rewards available for claiming."
)
async def get_active_rewards(
    crud: RewardCRUD = Depends(get_reward_crud)
):
    """Get all active rewards."""
    try:
        rewards = await crud.get_active_rewards()
        return rewards
    except Exception as e:
        logger.error(f"Error fetching active rewards: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch rewards"
        )


@router.post(
    "/{reward_id}/claim",
    response_model=RewardClaimResponse,
    summary="Claim a reward",
    description="Claim a reward by spending credits. This will deduct credits from user's account."
)
async def claim_reward(
    reward_id: UUID,
    current_user: Tuple[UUID, dict] = Depends(get_current_user),
    reward_crud: RewardCRUD = Depends(get_reward_crud),
    user_crud: UserCRUD = Depends(get_user_crud),
    supabase: Client = Depends(get_supabase_client)
):
    """Claim a reward."""
    try:
        user_uid, user_profile = current_user
        user_id = user_uid
        
        # Get reward details
        reward = await reward_crud.get_reward(reward_id)
        if not reward:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reward not found"
            )
        
        if not reward.get("is_active", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This reward is no longer available"
            )
        
        # Get user's current credits
        user = await user_crud.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        user_credits = user.get("credits", 0)
        required_credits = reward.get("credits_required", 0)
        
        if user_credits < required_credits:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient credits. Required: {required_credits}, Available: {user_credits}"
            )
        
        # Create reward claim (database trigger will deduct credits)
        claim = await reward_crud.create_reward_claim(
            reward_id=reward_id,
            user_id=user_id,
            reward_title=reward.get("title", ""),
            credits_spent=required_credits
        )
        
        # Send email notification
        try:
            # Use service role client for admin operations (accessing user email)
            service_client = get_service_role_client()
            email_service = get_email_service(service_client)
            email_sent = await email_service.send_reward_claim_notification(
                user_id=user_id,
                reward_title=reward.get("title", ""),
                credits_spent=required_credits
            )
            
            if email_sent:
                # Mark email as sent
                await reward_crud.mark_email_sent(UUID(claim["id"]))
                logger.info(f"Email sent for reward claim {claim['id']}")
        except Exception as e:
            logger.error(f"Failed to send email for reward claim: {e}")
            # Don't fail the claim if email fails
        
        logger.info(f"User {user_id} claimed reward {reward_id}")
        
        return claim
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error claiming reward: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to claim reward: {str(e)}"
        )


@router.get(
    "/my-claims",
    response_model=UserRewardClaimHistory,
    summary="Get user's reward claim history",
    description="Get the claim history for the current user."
)
async def get_my_claims(
    skip: int = 0,
    limit: int = 100,
    current_user: Tuple[UUID, dict] = Depends(get_current_user),
    crud: RewardCRUD = Depends(get_reward_crud)
):
    """Get current user's reward claim history."""
    try:
        user_uid, user_profile = current_user
        user_id = user_uid
        
        # Get claims
        claims = await crud.get_user_claims(user_id, skip, limit)
        
        # Get stats
        stats = await crud.get_user_claim_stats(user_id)
        
        return {
            "claims": claims,
            "total_claims": stats["total_claims"],
            "total_credits_spent": stats["total_credits_spent"]
        }
    except Exception as e:
        logger.error(f"Error fetching user claims: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch claim history"
        )


# ==================== ADMIN ENDPOINTS ====================

@router.get(
    "/admin/all",
    response_model=List[RewardResponse],
    summary="Get all rewards (admin only)",
    description="Get list of all rewards including inactive ones. Admin access required.",
    dependencies=[Depends(require_admin)]
)
async def get_all_rewards(
    skip: int = 0,
    limit: int = 100,
    include_inactive: bool = True,
    crud: RewardCRUD = Depends(get_reward_crud)
):
    """Get all rewards (admin only)."""
    try:
        rewards = await crud.get_rewards(
            skip=skip,
            limit=limit,
            include_inactive=include_inactive
        )
        return rewards
    except Exception as e:
        logger.error(f"Error fetching rewards: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch rewards"
        )


@router.post(
    "/admin",
    response_model=RewardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new reward (admin only)",
    description="Create a new reward. Admin access required.",
    dependencies=[Depends(require_admin)]
)
async def create_reward(
    reward: RewardCreate,
    current_user: Tuple[UUID, dict] = Depends(get_current_user),
    crud: RewardCRUD = Depends(get_reward_crud)
):
    """Create a new reward (admin only)."""
    try:
        user_uid, user_profile = current_user
        reward_data = reward.model_dump()
        reward_data["created_by"] = str(user_uid)
        
        created_reward = await crud.create_reward(reward_data)
        return created_reward
    except Exception as e:
        logger.error(f"Error creating reward: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create reward: {str(e)}"
        )


@router.get(
    "/admin/{reward_id}",
    response_model=RewardResponse,
    summary="Get reward by ID (admin only)",
    description="Get a specific reward by ID. Admin access required.",
    dependencies=[Depends(require_admin)]
)
async def get_reward(
    reward_id: UUID,
    crud: RewardCRUD = Depends(get_reward_crud)
):
    """Get a reward by ID (admin only)."""
    try:
        reward = await crud.get_reward(reward_id)
        if not reward:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reward not found"
            )
        return reward
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching reward: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch reward"
        )


@router.put(
    "/admin/{reward_id}",
    response_model=RewardResponse,
    summary="Update a reward (admin only)",
    description="Update an existing reward. Admin access required.",
    dependencies=[Depends(require_admin)]
)
async def update_reward(
    reward_id: UUID,
    reward: RewardUpdate,
    crud: RewardCRUD = Depends(get_reward_crud)
):
    """Update a reward (admin only)."""
    try:
        # Check if reward exists
        existing_reward = await crud.get_reward(reward_id)
        if not existing_reward:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reward not found"
            )
        
        # Update only provided fields
        reward_data = reward.model_dump(exclude_unset=True)
        updated_reward = await crud.update_reward(reward_id, reward_data)
        
        if not updated_reward:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update reward"
            )
        
        return updated_reward
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating reward: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update reward: {str(e)}"
        )


@router.delete(
    "/admin/{reward_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a reward (admin only)",
    description="Delete a reward. Admin access required.",
    dependencies=[Depends(require_admin)]
)
async def delete_reward(
    reward_id: UUID,
    crud: RewardCRUD = Depends(get_reward_crud)
):
    """Delete a reward (admin only)."""
    try:
        success = await crud.delete_reward(reward_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reward not found"
            )
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting reward: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete reward"
        )


@router.get(
    "/admin/{reward_id}/claims",
    response_model=List[RewardClaimResponse],
    summary="Get claims for a reward (admin only)",
    description="Get all claims for a specific reward. Admin access required.",
    dependencies=[Depends(require_admin)]
)
async def get_reward_claims(
    reward_id: UUID,
    skip: int = 0,
    limit: int = 100,
    crud: RewardCRUD = Depends(get_reward_crud)
):
    """Get all claims for a specific reward (admin only)."""
    try:
        claims = await crud.get_reward_claims(reward_id, skip, limit)
        return claims
    except Exception as e:
        logger.error(f"Error fetching reward claims: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch reward claims"
        )
