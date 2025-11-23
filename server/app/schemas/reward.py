"""Pydantic schemas for rewards."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class RewardBase(BaseModel):
    """Base reward schema."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    credits_required: int = Field(..., gt=0)
    is_active: bool = True


class RewardCreate(RewardBase):
    """Schema for creating a new reward."""
    pass


class RewardUpdate(BaseModel):
    """Schema for updating a reward."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    credits_required: Optional[int] = Field(None, gt=0)
    is_active: Optional[bool] = None


class RewardResponse(RewardBase):
    """Schema for reward response."""
    id: str
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RewardClaimBase(BaseModel):
    """Base reward claim schema."""
    reward_id: str


class RewardClaimCreate(RewardClaimBase):
    """Schema for creating a reward claim."""
    pass


class RewardClaimResponse(BaseModel):
    """Schema for reward claim response."""
    id: str
    reward_id: str
    user_id: str
    credits_spent: int
    reward_title: str
    claimed_at: datetime
    email_sent: bool
    email_sent_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserRewardClaimHistory(BaseModel):
    """Schema for user's reward claim history."""
    claims: list[RewardClaimResponse]
    total_claims: int
    total_credits_spent: int
