from typing import Dict, Optional
from pydantic import BaseModel
from datetime import datetime

class NotificationBase(BaseModel):
    user_uid: str
    message: str
    redirect_url: str | None = None

class NotificationCreate(BaseModel):
    user_uid: str
    title: str
    body: str
    metadata: Optional[Dict] = None

class NotificationOut(NotificationBase):
    id: int
    is_read: bool
    created_at: datetime

    class Config:
        orm_mode = True
class NotificationUpdate(BaseModel):
    is_read: bool
    class Config:
        orm_mode = True
        