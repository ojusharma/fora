"""
CRUD operations for listing_applicants table.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from supabase import Client

from app.schemas.listing_applicants import (
    ListingApplicantCreate,
    ListingApplicantUpdate,
    ApplicantFilters,
    ApplicantStatus,
)


class ListingApplicantsCRUD:
    """CRUD operations for listing applicants."""

    def __init__(self, supabase: Client):
        """Initialize with Supabase client."""
        self.supabase = supabase

    # ==================== APPLICANT OPERATIONS ====================

    async def create_application(
        self, application: ListingApplicantCreate
    ) -> Dict[str, Any]:
        """
        Create a new listing application.
        
        Args:
            application: Application data
            
        Returns:
            Created application data
            
        Raises:
            Exception if applicant is the poster (prevented by trigger)
        """
        application_data = application.model_dump()
        application_data["listing_id"] = str(application_data["listing_id"])
        application_data["applicant_uid"] = str(application_data["applicant_uid"])
        application_data["status"] = "applied"

        response = (
            self.supabase.table("listing_applicants")
            .insert(application_data)
            .execute()
        )
        return response.data[0] if response.data else None

    async def get_application(
        self, listing_id: UUID, applicant_uid: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific application.
        
        Args:
            listing_id: Listing ID
            applicant_uid: Applicant user ID
            
        Returns:
            Application data or None if not found
        """
        response = (
            self.supabase.table("listing_applicants")
            .select("*")
            .eq("listing_id", str(listing_id))
            .eq("applicant_uid", str(applicant_uid))
            .execute()
        )
        return response.data[0] if response.data else None

    async def get_application_with_details(
        self, listing_id: UUID, applicant_uid: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Get application with listing and user details.
        
        Args:
            listing_id: Listing ID
            applicant_uid: Applicant user ID
            
        Returns:
            Application data with details or None if not found
        """
        response = (
            self.supabase.table("listing_applicants")
            .select("*, listings(*), user_profiles!applicant_uid(*)")
            .eq("listing_id", str(listing_id))
            .eq("applicant_uid", str(applicant_uid))
            .execute()
        )
        return response.data[0] if response.data else None

    async def update_application(
        self,
        listing_id: UUID,
        applicant_uid: UUID,
        update_data: ListingApplicantUpdate,
    ) -> Optional[Dict[str, Any]]:
        """
        Update an application.
        
        Args:
            listing_id: Listing ID
            applicant_uid: Applicant user ID
            update_data: Update data
            
        Returns:
            Updated application data or None if not found
        """
        update_dict = update_data.model_dump(exclude_unset=True)
        
        if "status" in update_dict:
            update_dict["status"] = update_dict["status"].value

        response = (
            self.supabase.table("listing_applicants")
            .update(update_dict)
            .eq("listing_id", str(listing_id))
            .eq("applicant_uid", str(applicant_uid))
            .execute()
        )
        return response.data[0] if response.data else None

    async def delete_application(
        self, listing_id: UUID, applicant_uid: UUID
    ) -> bool:
        """
        Delete an application (withdraw).
        
        Args:
            listing_id: Listing ID
            applicant_uid: Applicant user ID
            
        Returns:
            True if deleted, False if not found
        """
        response = (
            self.supabase.table("listing_applicants")
            .delete()
            .eq("listing_id", str(listing_id))
            .eq("applicant_uid", str(applicant_uid))
            .execute()
        )
        return len(response.data) > 0 if response.data else False

    async def get_listing_applicants(
        self, listing_id: UUID, status: Optional[ApplicantStatus] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all applicants for a listing, optionally filtered by status.
        
        Args:
            listing_id: Listing ID
            status: Optional status filter
            
        Returns:
            List of applicants
        """
        query = (
            self.supabase.table("listing_applicants")
            .select("*")
            .eq("listing_id", str(listing_id))
        )
        
        if status:
            query = query.eq("status", status.value)
        
        response = query.order("applied_at", desc=True).execute()
        return response.data if response.data else []

    async def get_listing_applicants_with_details(
        self, listing_id: UUID, status: Optional[ApplicantStatus] = None
    ) -> List[Dict[str, Any]]:
        """
        Get applicants with user profile details.
        
        Args:
            listing_id: Listing ID
            status: Optional status filter
            
        Returns:
            List of applicants with user details
        """
        query = (
            self.supabase.table("listing_applicants")
            .select("*, user_profiles!applicant_uid(*)")
            .eq("listing_id", str(listing_id))
        )
        
        if status:
            query = query.eq("status", status.value)
        
        response = query.order("applied_at", desc=True).execute()
        return response.data if response.data else []

    async def get_user_applications(
        self, applicant_uid: UUID, status: Optional[ApplicantStatus] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all applications by a user, optionally filtered by status.
        
        Args:
            applicant_uid: User ID
            status: Optional status filter
            
        Returns:
            List of applications
        """
        query = (
            self.supabase.table("listing_applicants")
            .select("*")
            .eq("applicant_uid", str(applicant_uid))
        )
        
        if status:
            query = query.eq("status", status.value)
        
        response = query.order("applied_at", desc=True).execute()
        return response.data if response.data else []

    async def get_user_applications_with_listings(
        self, applicant_uid: UUID, status: Optional[ApplicantStatus] = None
    ) -> List[Dict[str, Any]]:
        """
        Get user applications with listing details.
        
        Args:
            applicant_uid: User ID
            status: Optional status filter
            
        Returns:
            List of applications with listing details
        """
        query = (
            self.supabase.table("listing_applicants")
            .select("*, listings(*)")
            .eq("applicant_uid", str(applicant_uid))
        )
        
        if status:
            query = query.eq("status", status.value)
        
        response = query.order("applied_at", desc=True).execute()
        return response.data if response.data else []

    async def count_listing_applicants(
        self, listing_id: UUID, status: Optional[ApplicantStatus] = None
    ) -> int:
        """
        Count applicants for a listing.
        
        Args:
            listing_id: Listing ID
            status: Optional status filter
            
        Returns:
            Number of applicants
        """
        query = (
            self.supabase.table("listing_applicants")
            .select("*", count="exact")
            .eq("listing_id", str(listing_id))
        )
        
        if status:
            query = query.eq("status", status.value)
        
        response = query.execute()
        return response.count if hasattr(response, 'count') else 0

    async def count_user_applications(
        self, applicant_uid: UUID, status: Optional[ApplicantStatus] = None
    ) -> int:
        """
        Count applications by a user.
        
        Args:
            applicant_uid: User ID
            status: Optional status filter
            
        Returns:
            Number of applications
        """
        query = (
            self.supabase.table("listing_applicants")
            .select("*", count="exact")
            .eq("applicant_uid", str(applicant_uid))
        )
        
        if status:
            query = query.eq("status", status.value)
        
        response = query.execute()
        return response.count if hasattr(response, 'count') else 0

    async def has_applied(self, listing_id: UUID, applicant_uid: UUID) -> bool:
        """
        Check if a user has applied to a listing.
        
        Args:
            listing_id: Listing ID
            applicant_uid: User ID
            
        Returns:
            True if applied, False otherwise
        """
        application = await self.get_application(listing_id, applicant_uid)
        return application is not None

    async def update_status(
        self,
        listing_id: UUID,
        applicant_uid: UUID,
        status: ApplicantStatus,
    ) -> Optional[Dict[str, Any]]:
        """
        Update application status.
        
        Args:
            listing_id: Listing ID
            applicant_uid: Applicant user ID
            status: New status
            
        Returns:
            Updated application data or None if not found
        """
        return await self.update_application(
            listing_id,
            applicant_uid,
            ListingApplicantUpdate(status=status),
        )

    async def withdraw_application(
        self, listing_id: UUID, applicant_uid: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Withdraw an application by updating status to withdrawn.
        
        Args:
            listing_id: Listing ID
            applicant_uid: Applicant user ID
            
        Returns:
            Updated application data or None if not found
        """
        return await self.update_status(
            listing_id, applicant_uid, ApplicantStatus.WITHDRAWN
        )

    async def shortlist_applicant(
        self, listing_id: UUID, applicant_uid: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Shortlist an applicant.
        
        Args:
            listing_id: Listing ID
            applicant_uid: Applicant user ID
            
        Returns:
            Updated application data or None if not found
        """
        return await self.update_status(
            listing_id, applicant_uid, ApplicantStatus.SHORTLISTED
        )

    async def reject_applicant(
        self, listing_id: UUID, applicant_uid: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Reject an applicant.
        
        Args:
            listing_id: Listing ID
            applicant_uid: Applicant user ID
            
        Returns:
            Updated application data or None if not found
        """
        return await self.update_status(
            listing_id, applicant_uid, ApplicantStatus.REJECTED
        )

    async def get_applications_by_filters(
        self, filters: ApplicantFilters
    ) -> List[Dict[str, Any]]:
        """
        Get applications with advanced filtering.
        
        Args:
            filters: Filter criteria
            
        Returns:
            List of applications matching filters
        """
        query = self.supabase.table("listing_applicants").select("*")
        
        if filters.listing_id:
            query = query.eq("listing_id", str(filters.listing_id))
        
        if filters.applicant_uid:
            query = query.eq("applicant_uid", str(filters.applicant_uid))
        
        if filters.status:
            query = query.eq("status", filters.status.value)
        
        if filters.from_date:
            query = query.gte("applied_at", filters.from_date.isoformat())
        
        if filters.to_date:
            query = query.lte("applied_at", filters.to_date.isoformat())
        
        response = (
            query
            .order("applied_at", desc=True)
            .range(filters.offset, filters.offset + filters.limit - 1)
            .execute()
        )
        return response.data if response.data else []

    async def bulk_update_status(
        self,
        listing_id: UUID,
        applicant_uids: List[UUID],
        status: ApplicantStatus,
    ) -> List[Dict[str, Any]]:
        """
        Update status for multiple applicants at once.
        
        Args:
            listing_id: Listing ID
            applicant_uids: List of applicant user IDs
            status: New status
            
        Returns:
            List of updated applications
        """
        results = []
        for applicant_uid in applicant_uids:
            result = await self.update_status(listing_id, applicant_uid, status)
            if result:
                results.append(result)
        return results
