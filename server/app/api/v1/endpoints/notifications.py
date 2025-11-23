from fastapi import APIRouter, Depends
from supabase import Client

from app.core.database import get_supabase_client
from app.crud.notification import NotificationCRUD
from app.schemas.notification import NotificationCreate

router = APIRouter()

def get_notification_crud(
    supabase: Client = Depends(get_supabase_client)
) -> NotificationCRUD:
    return NotificationCRUD(supabase)


@router.post("/", summary="Create a notification")
async def create_notification(
    notif: NotificationCreate,
    crud: NotificationCRUD = Depends(get_notification_crud),
):
    return await crud.create_notification(notif)


@router.get("/{user_uid}", summary="List notifications for a user")
async def list_notifications(
    user_uid: str,
    crud: NotificationCRUD = Depends(get_notification_crud),
):
    return await crud.list_notifications(user_uid)


@router.post("/{notif_id}/read", summary="Mark notification as read")
async def mark_read(
    notif_id: int,
    crud: NotificationCRUD = Depends(get_notification_crud),
):
    return await crud.mark_as_read(notif_id)
