"""
Pydantic schemas for listing_applicants-related operations.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum


class ApplicantStatus(str, Enum):
    """Applicant status enum."""
    APPLIED = "applied"
    SHORTLISTED = "shortlisted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    PENDING_CONFIRMATION = "pending_confirmation"
    COMPLETED = "completed"


# ==================== BASE SCHEMAS ====================

class ListingApplicantBase(BaseModel):
    """Base schema for listing applicant data."""
    message: Optional[str] = Field(None, max_length=1000)
    status: ApplicantStatus = ApplicantStatus.APPLIED


class ListingApplicantCreate(BaseModel):
    """Schema for creating a listing application."""
    listing_id: UUID
    applicant_uid: UUID
    message: Optional[str] = Field(None, max_length=1000)


class ListingApplicantUpdate(BaseModel):
    """Schema for updating applicant status."""
    status: ApplicantStatus
    message: Optional[str] = Field(None, max_length=1000)


class ListingApplicantResponse(BaseModel):
    """Schema for listing applicant response."""
    listing_id: UUID
    applicant_uid: UUID
    applied_at: datetime
    status: ApplicantStatus
    message: Optional[str] = None

    class Config:
        from_attributes = True


class ListingApplicantWithDetailsResponse(ListingApplicantResponse):
    """Schema for applicant response with listing and user details."""
    listing: Optional[dict] = None
    applicant: Optional[dict] = None

    class Config:
        from_attributes = True


class ApplicantFilters(BaseModel):
    """Schema for filtering applicants."""
    status: Optional[ApplicantStatus] = None
    listing_id: Optional[UUID] = None
    applicant_uid: Optional[UUID] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    limit: int = Field(50, ge=1, le=100)
    offset: int = Field(0, ge=0)
