from fastapi import FastAPI, WebSocket, Depends, Query, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.knowledge_base import load_knowledge 
from app.db_indexer import index_all
import asyncio

from app.database import get_db, create_tables
from app.auth import verify_token
from app.routers import chat, users
from app.routers import ai_chat 
from app.websocket.handler import handle_websocket
from app.mongo_database import connect_mongo, disconnect_mongo  

app = FastAPI(title="Vestique Chat Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(chat.router)
app.include_router(ai_chat.router) 



async def periodic_reindex(interval_seconds: int = 600):
    while True:
        await asyncio.sleep(interval_seconds)
        try:
            index_all()
        except Exception as e:
            print(f"[REINDEX] Error: {e}")

@app.on_event("startup")
async def startup():
    create_tables()
    load_knowledge()
    index_all()
    asyncio.create_task(periodic_reindex())
    await connect_mongo()


@app.on_event("shutdown")
async def shutdown():
    await disconnect_mongo()        


@app.get("/health")
def health():
    return {"status": "ok", "service": "vestique-chat"}


@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    # ✅ DO NOT call websocket.accept() here — manager.connect() does it inside handler
    try:
        payload = verify_token(token)
        user_id = int(payload.get("user_id"))  # ✅ Force int — JWT may return string "9"
    except Exception as e:
        print(f"[WS] Token error: {e}")
        await websocket.close(code=1008)
        return

    await handle_websocket(websocket, user_id, db)

