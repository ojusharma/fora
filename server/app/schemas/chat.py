from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: UUID
    room_id: UUID
    sender_uid: Optional[UUID]
    sender_display_name: Optional[str] = None
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatRoomResponse(BaseModel):
    id: UUID
    listing_id: UUID
    created_by: UUID
    created_at: datetime
    last_message: Optional[str] = None
    last_message_at: Optional[datetime] = None

    class Config:
        from_attributes = True
