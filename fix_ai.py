push = "$push"
each = "$each"
set_ = "$set"

code = '''# ai_chat.py
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from app.mongo_database import get_ai_sessions, get_ai_messages
from app.mongo_models import AIMessageCreate, AIMessageResponse, AISession, AIMessage
from app.auth import verify_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter(prefix="/ai-chat", tags=["AI Chat"])
security = HTTPBearer(auto_error=False)


def get_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials and credentials.credentials:
        try:
            payload = verify_token(credentials.credentials)
            return str(payload.get("user_id"))
        except Exception:
            pass
    return None

@router.post("/message", response_model=AIMessageResponse)
async def send_ai_message(body: AIMessageCreate, user_id: str = Depends(get_user_id)):
    effective_user_id = user_id or body.guest_id or "guest_unknown"
    sessions = get_ai_sessions()
    session = None
    if body.session_id:
        session = await sessions.find_one({"session_id": body.session_id, "user_id": effective_user_id})
    if not session:
        new_session = AISession(user_id=effective_user_id)
        await sessions.insert_one(new_session.model_dump())
        session = new_session.model_dump()
    session_id = session["session_id"]
    history = session.get("messages", [])
    history_for_ai = [{"role": m["role"], "content": m["content"]} for m in history]
    ai_response_text = await call_ai(body.message, history_for_ai)
    now = datetime.utcnow()
    user_msg = AIMessage(role="user", content=body.message, timestamp=now)
    ai_msg = AIMessage(role="assistant", content=ai_response_text, timestamp=now)
    await sessions.update_one(
        {"session_id": session_id},
        {
            PUSH: {"messages": {EACH: [user_msg.model_dump(), ai_msg.model_dump()]}},
            SET: {"updated_at": now}
        }
    )
    return AIMessageResponse(
        session_id=session_id,
        user_message=body.message,
        ai_response=ai_response_text,
        timestamp=now,
    )


@router.get("/history/{session_id}")
async def get_session_history(session_id: str, user_id: str = Depends(get_user_id)):
    sessions = get_ai_sessions()
    session = await sessions.find_one({"session_id": session_id, "user_id": user_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/sessions")
async def get_user_sessions(user_id: str = Depends(get_user_id)):
    sessions = get_ai_sessions()
    cursor = sessions.find(
        {"user_id": user_id},
        {"_id": 0, "messages": 0}
    ).sort("updated_at", -1).limit(20)
    result = await cursor.to_list(length=20)
    return {"sessions": result}


@router.delete("/session/{session_id}")
async def delete_session(session_id: str, user_id: str = Depends(get_user_id)):
    sessions = get_ai_sessions()
    result = await sessions.delete_one({"session_id": session_id, "user_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session deleted"}


async def call_ai(user_message: str, history: list) -> str:
    try:
        import os
        from groq import Groq
        from app.vector_store import search_collection

        cols = ["creators", "profile_reviews", "general_reviews", "posts", "faq"]
        docs = []
        for col in cols:
            try:
                docs.extend(search_collection(col, user_message, n_results=3))
            except Exception:
                pass

        if docs:
            ctx = "\\n".join("- " + d for d in docs)
            sys_msg = (
                "You are Vestique AI. Use the real platform data below to answer "
                "questions about designers, tailors, reviews and posts on Vestique. "
                "Always prefer this data over general knowledge.\\n\\n"
                "VESTIQUE DATA:\\n" + ctx
            )
        else:
            sys_msg = "You are Vestique AI, a helpful assistant for the Vestique fashion platform."

        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        msgs = (
            [{"role": "system", "content": sys_msg}]
            + history
            + [{"role": "user", "content": user_message}]
        )
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=msgs,
            max_tokens=1024,
        )
        return response.choices[0].message.content

    except Exception as e:
        print(f"AI call error: {e}")
        return "Sorry, I could not process your request right now."
'''

code = code.replace("PUSH", '"%s"' % "$push")
code = code.replace("EACH", '"%s"' % "$each")
code = code.replace("SET", '"%s"' % "$set")

with open('/app/app/routers/ai_chat.py', 'w') as f:
    f.write(code)

print("Done!")