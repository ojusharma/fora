from typing import List, Optional, Dict, Any
from supabase import Client
from app.schemas.notification import (
    NotificationCreate,
    NotificationUpdate,
)

class NotificationCRUD:
    """CRUD operations for notifications."""

    def __init__(self, supabase: Client):
        self.supabase = supabase

    # -----------------------------
    # Create Notification
    # -----------------------------
    async def create_notification(self, notif: NotificationCreate):
        data = notif.model_dump()
        return self.supabase.table("notifications").insert(data).execute()

    # -----------------------------
    # List Notifications for user
    # -----------------------------
    async def list_notifications(
        self, user_uid: str
    ) -> List[Dict[str, Any]]:

        response = (
            self.supabase.table("notifications")
            .select("*")
            .eq("user_uid", user_uid)
            .order("created_at", desc=True)
            .execute()
        )

        return response.data or []

    # -----------------------------
    # Mark Notification Read
    # -----------------------------
    async def mark_as_read(
        self, notif_id: int
    ) -> Optional[Dict[str, Any]]:

        response = (
            self.supabase.table("notifications")
            .update({"is_read": True})
            .eq("id", notif_id)
            .execute()
        )

        return response.data[0] if response.data else None

    # -----------------------------
    # Delete Notification
    # -----------------------------
    async def delete_notification(
        self, notif_id: int
    ) -> bool:

        response = (
            self.supabase.table("notifications")
            .delete()
            .eq("id", notif_id)
            .execute()
        )

        return bool(response.data)
