"""
CRUD operations for listing_applicants table.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from app.crud.listing import ListingCRUD
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

    async def _send_notification(self, user_uid: str, message: str, redirect_url: str):
        from app.crud.notification import NotificationCRUD
        from app.schemas.notification import NotificationCreate

        notif = NotificationCRUD(self.supabase)

        await notif.create_notification(
            NotificationCreate(
                user_uid=user_uid,
                title=message,
                body=message,  # ← REQUIRED
                redirect_url=redirect_url,
            )
)


    async def create_application(
        self, application: ListingApplicantCreate
    ) -> Dict[str, Any]:
        """
        Create a new listing application or reactivate withdrawn/rejected application.
        
        Args:
            application: Application data
            
        Returns:
            Created/updated application data
            
        Raises:
            Exception if applicant is the poster (prevented by trigger)
        """
        application_data = application.model_dump()
        application_data["listing_id"] = str(application_data["listing_id"])
        application_data["applicant_uid"] = str(application_data["applicant_uid"])
        
        # Check if there's an existing application
        existing = await self.get_application(
            UUID(application_data["listing_id"]),
            UUID(application_data["applicant_uid"])
        )
        
        if existing:
            # If withdrawn or rejected, update to "applied" status
            if existing.get("status") in ["withdrawn", "rejected"]:
                application_data["status"] = "applied"
                application_data["applied_at"] = datetime.utcnow().isoformat()
                
                response = (
                    self.supabase.table("listing_applicants")
                    .update(application_data)
                    .eq("listing_id", application_data["listing_id"])
                    .eq("applicant_uid", application_data["applicant_uid"])
                    .execute()
                )
                return response.data[0] if response.data else None
            else:
                # Already has active application
                return existing
        
        # Create new application
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
        listing = await ListingCRUD(self.supabase).get_listing(listing_id)

        # Notify poster (listing owner)
        await self._send_notification(
            user_uid=str(listing["poster_uid"]),
            message=f"An applicant withdrew from your listing '{listing['name']}'.",
            redirect_url=f"/market/{listing_id}"
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
            List of applicants with user_rating
        """
        query = (
            self.supabase.table("listing_applicants")
            .select("*")
            .eq("listing_id", str(listing_id))
        )
        
        if status:
            query = query.eq("status", status.value)
        
        response = query.order("applied_at", desc=True).execute()
        applicants = response.data if response.data else []
        
        # Fetch user_rating for each applicant
        if applicants:
            applicant_uids = list({a.get("applicant_uid") for a in applicants if a.get("applicant_uid")})
            if applicant_uids:
                try:
                    profiles_response = (
                        self.supabase.table("user_profiles")
                        .select("uid, user_rating")
                        .in_("uid", [str(uid) for uid in applicant_uids])
                        .execute()
                    )
                    rating_by_uid = {p["uid"]: p.get("user_rating") for p in profiles_response.data} if profiles_response.data else {}
                    for applicant in applicants:
                        applicant_uid = applicant.get("applicant_uid")
                        if applicant_uid:
                            applicant["user_rating"] = rating_by_uid.get(str(applicant_uid))
                except Exception:
                    pass
        
        return applicants

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
        Check if a user has an active application to a listing.
        
        Args:
            listing_id: Listing ID
            applicant_uid: User ID
            
        Returns:
            True if has active application (not withdrawn/rejected), False otherwise
        """
        application = await self.get_application(listing_id, applicant_uid)
        if not application:
            return False
        
        # Allow reapplying if previously withdrawn or rejected
        status = application.get("status")
        return status not in ["withdrawn", "rejected"]

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

    async def shortlist_applicant(self, listing_id: UUID, applicant_uid: UUID):
        # Find existing application
        result = await self.get_application(listing_id, applicant_uid)
        if not result:
            return None

        # Update application status
        updated = (
            self.supabase.table("listing_applicants")
            .update({"status": "shortlisted"})
            .eq("listing_id", str(listing_id))
            .eq("applicant_uid", str(applicant_uid))
            .execute()
        )

        if not updated.data:
            return None

        # Update listing status to in_progress and set assignee_uid
        self.supabase.table("listings").update({
            "status": "in_progress",
            "assignee_uid": str(applicant_uid)
        }).eq("id", str(listing_id)).execute()

        # Load listing (title + poster)
        listing = await ListingCRUD(self.supabase).get_listing(listing_id)

        # Notify applicant
        await self._send_notification(
            user_uid=str(applicant_uid),
            message=f"Your application for '{listing['name']}' was shortlisted.",
            redirect_url=f"/market/{listing_id}"
        )

        return updated.data[0]


    async def reject_applicant(self, listing_id: UUID, applicant_uid: UUID):
        result = await self.get_application(listing_id, applicant_uid)
        if not result:
            return None

        updated = (
            self.supabase.table("listing_applicants")
            .update({"status": "rejected"})
            .eq("listing_id", str(listing_id))
            .eq("applicant_uid", str(applicant_uid))
            .execute()
        )

        if not updated.data:
            return None

        listing = await ListingCRUD(self.supabase).get_listing(listing_id)

        await self._send_notification(
            user_uid=str(applicant_uid),
            message=f"Your application for '{listing['name']}' was rejected.",
            redirect_url=f"/market/{listing_id}"
        )

        return updated.data[0]


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
