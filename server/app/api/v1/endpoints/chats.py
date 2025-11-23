from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from uuid import UUID

from app.core.database import get_supabase_client
from app.crud.chat import ChatCRUD
from app.schemas.chat import MessageCreate, MessageResponse, ChatRoomResponse
from supabase import Client

router = APIRouter()


def get_chat_crud(supabase: Client = Depends(get_supabase_client)) -> ChatCRUD:
    return ChatCRUD(supabase)


async def get_current_user_uid(user_uid: UUID = Query(..., description="Current user UID")) -> UUID:
    return user_uid


@router.post("/{listing_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def post_message_for_listing(
    listing_id: UUID,
    message: MessageCreate,
    user_uid: UUID = Depends(get_current_user_uid),
    crud: ChatCRUD = Depends(get_chat_crud),
):
    # ensure room exists
    room = crud.ensure_room_for_listing(listing_id, user_uid)
    if not room:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not create or find chat room")
    msg = crud.add_message_to_room(listing_id, user_uid, message.content)
    if not msg:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to persist message")
    
    # Get sender display name
    sender_name = None
    try:
        prof_res = crud.supabase.table('user_profiles').select('*').eq('uid', str(user_uid)).execute()
        if prof_res and prof_res.data:
            p = prof_res.data[0]
            sender_name = p.get('display_name') or p.get('full_name') or p.get('phone') or str(user_uid)[:8]
            msg['sender_display_name'] = sender_name
    except Exception:
        pass

    # Send notification to the other person in the chat
    try:
        from app.crud.notification import NotificationCRUD
        from app.schemas.notification import NotificationCreate
        from app.crud.listing import ListingCRUD
        
        # Get listing to find poster and assignee
        listing_crud = ListingCRUD(crud.supabase)
        listing = await listing_crud.get_listing(listing_id)
        
        if listing:
            poster_uid = listing.get("poster_uid")
            assignee_uid = listing.get("assignee_uid")
            
            # Determine who to notify (the person who didn't send the message)
            recipient_uid = None
            sender_uid_str = str(user_uid)
            
            if poster_uid and str(poster_uid) == sender_uid_str and assignee_uid:
                # Sender is poster, notify assignee
                recipient_uid = str(assignee_uid)
            elif assignee_uid and str(assignee_uid) == sender_uid_str and poster_uid:
                # Sender is assignee, notify poster
                recipient_uid = str(poster_uid)
            
            if recipient_uid:
                sender_display = sender_name or "Someone"
                message_preview = message.content[:50] + ('...' if len(message.content) > 50 else '')
                
                notif_crud = NotificationCRUD(crud.supabase)
                await notif_crud.create_notification(
                    NotificationCreate(
                        user_uid=recipient_uid,
                        title=f"New message from {sender_display}",
                        body=message_preview,
                        metadata={"redirect_url": f"/chats?listing={str(listing_id)}"}
                    )
                )
    except Exception as e:
        # Don't fail the message send if notification fails
        import traceback
        print(f"Failed to send chat notification: {e}")
        traceback.print_exc()

    return msg


@router.get("/{listing_id}/messages", response_model=List[MessageResponse])
async def get_messages_for_listing(listing_id: UUID, crud: ChatCRUD = Depends(get_chat_crud)):
    msgs = crud.get_messages_for_listing(listing_id)
    if not msgs:
        return []

    # collect unique sender uids
    sender_uids = list({m.get('sender_uid') for m in msgs if m.get('sender_uid')})
    name_by_uid = {}
    if sender_uids:
        # fetch profiles in batch
        try:
            profiles_res = crud.supabase.table('user_profiles').select('*').in_('uid', [str(u) for u in sender_uids]).execute()
        except Exception:
            profiles_res = None

        if profiles_res and profiles_res.data:
            for p in profiles_res.data:
                uid = p.get('uid') or p.get('id')
                if not uid:
                    continue
                name_by_uid[str(uid)] = p.get('display_name') or p.get('full_name') or p.get('phone') or str(uid)[:8]

    # attach display name to each message
    for m in msgs:
        suid = m.get('sender_uid')
        m['sender_display_name'] = name_by_uid.get(str(suid)) if suid else None

    return msgs
