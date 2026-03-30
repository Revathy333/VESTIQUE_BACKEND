# chat_service/app/mongo_models.py
# Pydantic models for MongoDB documents

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Union
import uuid


class AIMessage(BaseModel):
    """A single message in an AI conversation"""
    role: str                    # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AISession(BaseModel):
    """
    A full AI chat session for one user.
    Stored as a single document in MongoDB.

    MongoDB document shape:
    {
        "session_id": "uuid",
        "user_id": 5,
        "messages": [
            { "role": "user", "content": "...", "timestamp": "..." },
            { "role": "assistant", "content": "...", "timestamp": "..." }
        ],
        "created_at": "...",
        "updated_at": "..."
    }
    """
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Union[str, int]
    messages: list[AIMessage] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AIMessageCreate(BaseModel):
    """Request body to send a message to AI"""
    message: str
    session_id: Optional[str] = None   # if None, creates a new session
    guest_id: Optional[str] = None


class AIMessageResponse(BaseModel):
    """Response from AI"""
    session_id: str
    user_message: str
    ai_response: str
    timestamp: datetime