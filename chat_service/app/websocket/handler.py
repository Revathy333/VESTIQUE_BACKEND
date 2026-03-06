# # import asyncio
# # import json
# # from fastapi import WebSocket, WebSocketDisconnect
# # from sqlalchemy.orm import Session
# # from sqlalchemy import or_, and_

# # from app.websocket.manager import manager
# # from app.redis_client import set_user_online, set_user_offline
# # from app.models import ChatMessage


# # def _heartbeat_sync(user_id: int):
# #     pass


# # async def heartbeat(user_id: int):
# #     while True:
# #         await asyncio.sleep(30)
# #         if manager.is_connected(user_id):
# #             set_user_online(user_id)
# #         else:
# #             break


# # async def handle_websocket(websocket: WebSocket, user_id: int, db: Session):
    
# #     await manager.connect(user_id, websocket)
# #     set_user_online(user_id)

# #     hb = asyncio.create_task(heartbeat(user_id))

# #     try:
# #         while True:
# #             raw = await websocket.receive_text()
# #             data = json.loads(raw)
# #             msg_type = data.get("type")

# #             # ── Heartbeat ──────────────────────────────────────────────
# #             if msg_type == "heartbeat":
# #                 set_user_online(user_id)

# #             # ── Send Message ───────────────────────────────────────────
# #             elif msg_type == "message":
# #                 to_id = data.get("to")
# #                 content = (data.get("content") or "").strip()
# #                 if not to_id or not content:
# #                     continue

# #                 msg = ChatMessage(
# #                     sender_id=user_id,
# #                     receiver_id=to_id,
# #                     content=content,
# #                 )
# #                 db.add(msg)
# #                 db.commit()
# #                 db.refresh(msg)

# #                 payload = {
# #                     "type": "message",
# #                     "id": msg.id,
# #                     "from": user_id,
# #                     "to": to_id,
# #                     "content": msg.content,
# #                     "created_at": msg.created_at.isoformat(),
# #                     "is_read": False,
# #                 }

# #                 await manager.send_to(to_id, payload)
# #                 await manager.send_to(user_id, payload)

# #             # ── Typing Indicator ───────────────────────────────────────
# #             elif msg_type == "typing":
# #                 to_id = data.get("to")
# #                 if to_id:
# #                     await manager.send_to(to_id, {
# #                         "type": "typing",
# #                         "from": user_id
# #                     })

# #             # ── Mark as Read ───────────────────────────────────────────
# #             elif msg_type == "read":
# #                 from_user = data.get("from_user")
# #                 if from_user:
# #                     msgs = db.query(ChatMessage).filter(
# #                         ChatMessage.sender_id == from_user,
# #                         ChatMessage.receiver_id == user_id,
# #                         ChatMessage.is_read == False,
# #                     ).all()
# #                     for m in msgs:
# #                         m.is_read = True
# #                     db.commit()

# #                     await manager.send_to(from_user, {
# #                         "type": "read",
# #                         "by": user_id
# #                     })

# #     except WebSocketDisconnect:
# #         pass
# #     except Exception:
# #         pass
# #     finally:
# #         hb.cancel()
# #         manager.disconnect(user_id)
# #         set_user_offline(user_id)

# import asyncio
# import json
# from fastapi import WebSocket, WebSocketDisconnect
# from sqlalchemy.orm import Session

# from app.websocket.manager import manager
# from app.redis_client import set_user_online, set_user_offline
# from app.models import ChatMessage


# async def heartbeat(user_id: int):
#     while True:
#         await asyncio.sleep(30)
#         if manager.is_connected(user_id):
#             set_user_online(user_id)
#         else:
#             break


# async def handle_websocket(websocket: WebSocket, user_id: int, db: Session):
#     user_id = int(user_id)  # ✅ Force int — safety cast

#     await manager.connect(user_id, websocket)
#     set_user_online(user_id)

#     print(f"[HANDLER] User {user_id} connected. All active: {list(manager.active.keys())}")

#     hb = asyncio.create_task(heartbeat(user_id))

#     try:
#         while True:
#             raw = await websocket.receive_text()
#             data = json.loads(raw)
#             msg_type = data.get("type")

#             # ── Heartbeat ──────────────────────────────────────────────
#             if msg_type == "heartbeat":
#                 set_user_online(user_id)

#             # ── Send Message ───────────────────────────────────────────
#             elif msg_type == "message":
#                 to_id = int(data.get("to"))  # ✅ Force int
#                 content = (data.get("content") or "").strip()

#                 print(f"[MSG] from={user_id} to={to_id} | active connections: {list(manager.active.keys())}")

#                 if not to_id or not content:
#                     continue

#                 msg = ChatMessage(
#                     sender_id=user_id,
#                     receiver_id=to_id,
#                     content=content,
#                 )
#                 db.add(msg)
#                 db.commit()
#                 db.refresh(msg)

#                 payload = {
#                     "type": "message",
#                     "id": msg.id,
#                     "from": user_id,
#                     "to": to_id,
#                     "content": msg.content,
#                     "created_at": msg.created_at.isoformat(),
#                     "is_read": False,
#                 }

#                 print(f"[SEND] Delivering to receiver {to_id}: {to_id in manager.active}")
#                 await manager.send_to(to_id, payload)
#                 await manager.send_to(user_id, payload)

#             # ── Typing Indicator ───────────────────────────────────────
#             elif msg_type == "typing":
#                 to_id = int(data.get("to"))  # ✅ Force int
#                 if to_id:
#                     await manager.send_to(to_id, {
#                         "type": "typing",
#                         "from": user_id,
#                     })

#             # ── Mark as Read ───────────────────────────────────────────
#             elif msg_type == "read":
#                 from_user = int(data.get("from_user"))  # ✅ Force int
#                 if from_user:
#                     msgs = db.query(ChatMessage).filter(
#                         ChatMessage.sender_id == from_user,
#                         ChatMessage.receiver_id == user_id,
#                         ChatMessage.is_read == False,
#                     ).all()
#                     for m in msgs:
#                         m.is_read = True
#                     db.commit()

#                     await manager.send_to(from_user, {
#                         "type": "read",
#                         "by": user_id,
#                     })

#     except WebSocketDisconnect:
#         pass
#     except Exception as e:
#         print(f"[WS ERROR] user={user_id} error={e}")
#     finally:
#         hb.cancel()
#         manager.disconnect(user_id)
#         set_user_offline(user_id)
#         print(f"[HANDLER] User {user_id} disconnected. Remaining: {list(manager.active.keys())}")

import asyncio
import json
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.websocket.manager import manager
from app.redis_client import set_user_online, set_user_offline
from app.models import ChatMessage


async def heartbeat(user_id: int):
    while True:
        await asyncio.sleep(30)
        if manager.is_connected(user_id):
            set_user_online(user_id)
        else:
            break


async def handle_websocket(websocket: WebSocket, user_id: int, db: Session):
    user_id = int(user_id)  # ✅ Force int — safety cast

    await manager.connect(user_id, websocket)
    set_user_online(user_id)

    print(f"[HANDLER] User {user_id} connected. All active: {list(manager.active.keys())}")

    hb = asyncio.create_task(heartbeat(user_id))

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            msg_type = data.get("type")

            # ── Heartbeat ──────────────────────────────────────────────
            if msg_type == "heartbeat":
                set_user_online(user_id)

            # ── Send Message ───────────────────────────────────────────
            elif msg_type == "message":
                to_id = int(data.get("to"))  # ✅ Force int
                content = (data.get("content") or "").strip()

                print(f"[MSG] from={user_id} to={to_id} | active connections: {list(manager.active.keys())}")

                if not to_id or not content:
                    continue

                msg = ChatMessage(
                    sender_id=user_id,
                    receiver_id=to_id,
                    content=content,
                )
                db.add(msg)
                db.commit()
                db.refresh(msg)

                payload = {
                    "type": "message",
                    "id": msg.id,
                    "from": user_id,
                    "to": to_id,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat(),
                    "is_read": False,
                }

                print(f"[SEND] Delivering to receiver {to_id}: {to_id in manager.active}")
                await manager.send_to(to_id, payload)
                await manager.send_to(user_id, payload)

            # ── Typing Indicator ───────────────────────────────────────
            elif msg_type == "typing":
                to_id = int(data.get("to"))  # ✅ Force int
                if to_id:
                    await manager.send_to(to_id, {
                        "type": "typing",
                        "from": user_id,
                    })

            # ── Mark as Read ───────────────────────────────────────────
            elif msg_type == "read":
                from_user = int(data.get("from_user"))  # ✅ Force int
                if from_user:
                    msgs = db.query(ChatMessage).filter(
                        ChatMessage.sender_id == from_user,
                        ChatMessage.receiver_id == user_id,
                        ChatMessage.is_read == False,
                    ).all()
                    for m in msgs:
                        m.is_read = True
                    db.commit()

                    await manager.send_to(from_user, {
                        "type": "read",
                        "by": user_id,
                    })

            # ── Delete Message ─────────────────────────────────────────
            elif msg_type == "delete_message":
                message_id = data.get("message_id")
                for_everyone = data.get("for_everyone", False)

                if message_id:
                    target_msg = db.query(ChatMessage).filter(
                        ChatMessage.id == message_id
                    ).first()

                    if target_msg:
                        if for_everyone and target_msg.sender_id == user_id:
                            target_msg.is_deleted = True
                            db.commit()
                            payload = {
                                "type": "message_deleted",
                                "message_id": message_id,
                            }
                            await manager.send_to(user_id, payload)
                            await manager.send_to(target_msg.receiver_id, payload)

                        elif not for_everyone:
                            db.delete(target_msg)
                            db.commit()

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[WS ERROR] user={user_id} error={e}")
    finally:
        hb.cancel()
        manager.disconnect(user_id)
        set_user_offline(user_id)
        print(f"[HANDLER] User {user_id} disconnected. Remaining: {list(manager.active.keys())}")
