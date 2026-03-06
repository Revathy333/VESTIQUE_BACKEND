from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class MessageOut(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    content: str
    is_read: bool
    created_at: datetime
    is_deleted: bool = False

    class Config:
        from_attributes = True


class OnlineUser(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    role: str
    profile_picture: Optional[str] = None
    business_name: Optional[str] = None
    is_online: bool = False


class ConversationItem(BaseModel):
    user_id: int
    last_message: str
    last_message_time: str
    unread_count: int