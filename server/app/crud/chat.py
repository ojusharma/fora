from typing import Optional, List, Dict, Any
from uuid import UUID
from supabase import Client
from datetime import datetime


class ChatCRUD:
    def __init__(self, supabase: Client):
        self.supabase = supabase

    def get_room_by_listing(self, listing_id: UUID) -> Optional[Dict[str, Any]]:
        res = self.supabase.table("chat_rooms").select("*").eq("listing_id", str(listing_id)).execute()
        return res.data[0] if res.data else None

    def create_room_for_listing(self, listing_id: UUID, creator_uid: UUID) -> Optional[Dict[str, Any]]:
        # insert if not exists
        existing = self.get_room_by_listing(listing_id)
        if existing:
            return existing
        payload = {"listing_id": str(listing_id), "created_by": str(creator_uid)}
        res = self.supabase.table("chat_rooms").insert(payload).execute()
        return res.data[0] if res.data else None

    def ensure_room_for_listing(self, listing_id: UUID, creator_uid: UUID) -> Optional[Dict[str, Any]]:
        return self.create_room_for_listing(listing_id, creator_uid)

    def add_message_to_room(self, listing_id: UUID, sender_uid: Optional[UUID], content: str) -> Optional[Dict[str, Any]]:
        # ensure room exists
        room = self.get_room_by_listing(listing_id)
        if not room:
            return None

        room_id = room["id"]
        payload = {"room_id": room_id, "sender_uid": str(sender_uid) if sender_uid else None, "content": content}
        res = self.supabase.table("chat_messages").insert(payload).execute()
        msg = res.data[0] if res.data else None

        # update room preview
        try:
            self.supabase.table("chat_rooms").update({"last_message": content, "last_message_at": datetime.utcnow().isoformat()}).eq("id", room_id).execute()
        except Exception:
            pass

        return msg

    def get_messages_for_listing(self, listing_id: UUID, limit: int = 100) -> List[Dict[str, Any]]:
        room = self.get_room_by_listing(listing_id)
        if not room:
            return []
        room_id = room["id"]
        res = (
            self.supabase.table("chat_messages")
            .select("*")
            .eq("room_id", room_id)
            .order("created_at", desc=False)
            .limit(limit)
            .execute()
        )
        return res.data if res.data else []
