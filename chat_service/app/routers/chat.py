from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.database import get_db
from app.models import ChatMessage
from app.schemas import MessageOut, ConversationItem
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from app.rag_service import get_rag_response


router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/history/{other_user_id}", response_model=list[MessageOut])
def get_chat_history(
    other_user_id: int,
    current_user_id: int = Query(...),
    limit: int = Query(50),
    db: Session = Depends(get_db),
):
    """Fetch message history between two users."""
    msgs = db.query(ChatMessage).filter(
        or_(
            and_(
                ChatMessage.sender_id == current_user_id,
                ChatMessage.receiver_id == other_user_id,
            ),
            and_(
                ChatMessage.sender_id == other_user_id,
                ChatMessage.receiver_id == current_user_id,
            ),
        )
    ).filter(ChatMessage.is_deleted == False).order_by(ChatMessage.created_at.asc()).limit(limit).all()
    return msgs


@router.get("/conversations/{user_id}", response_model=list[ConversationItem])
def get_conversations(user_id: int, db: Session = Depends(get_db)):
    """Get everyone this user has chatted with + last message + unread count."""
    messages = db.query(ChatMessage).filter(
        or_(
            ChatMessage.sender_id == user_id,
            ChatMessage.receiver_id == user_id,
        )
    ).order_by(ChatMessage.created_at.desc()).all()

    seen: dict[int, dict] = {}
    for msg in messages:
        other = msg.receiver_id if msg.sender_id == user_id else msg.sender_id
        if other not in seen:
            seen[other] = {
                "user_id": other,
                "last_message": msg.content,
                "last_message_time": msg.created_at.isoformat(),
                "unread_count": 0,
            }
        if msg.receiver_id == user_id and not msg.is_read:
            seen[other]["unread_count"] += 1

    return list(seen.values())



@router.delete("/message/{message_id}")
def delete_message(
    message_id: int,
    current_user_id: int = Query(...),
    delete_for_everyone: bool = Query(False),
    db: Session = Depends(get_db),
):
    msg = db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    if delete_for_everyone and msg.sender_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not allowed")

    if delete_for_everyone:
        msg.is_deleted = True
        db.commit()
        return {"deleted": True, "for_everyone": True, "message_id": message_id}
    else:
        db.delete(msg)
        db.commit()
        return {"deleted": True, "for_everyone": False, "message_id": message_id}    
    


class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str

@router.post("/ask")
async def ask_question(request: ChatRequest):
    answer = get_rag_response(request.question)
    return ChatResponse(answer=answer)    

