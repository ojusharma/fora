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
    # attempt to attach sender display name to response
    try:
        prof_res = crud.supabase.table('user_profiles').select('*').eq('uid', str(user_uid)).execute()
        if prof_res and prof_res.data:
            p = prof_res.data[0]
            msg['sender_display_name'] = p.get('display_name') or p.get('full_name') or p.get('phone') or str(user_uid)[:8]
    except Exception:
        pass

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
