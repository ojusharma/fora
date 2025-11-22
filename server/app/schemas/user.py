from typing import Optional
from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel


class UserProfileResponse(BaseModel):
    uid: UUID
    dob: Optional[date] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    credits: Optional[int] = 0
    last_updated: Optional[datetime] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    display_name: Optional[str] = None

    class Config:
        orm_mode = True
