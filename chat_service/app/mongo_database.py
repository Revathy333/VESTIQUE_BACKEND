# chat_service/app/mongo_database.py
# MongoDB connection using Motor (async driver for FastAPI)

from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URL = os.getenv(
    "MONGO_URL",
    "mongodb://admin:mongo@123@vestique_mongo:27017/vestique_ai_chat?authSource=admin"
)

# Single client instance (reused across requests)
client: AsyncIOMotorClient = None
db = None

# Collections
ai_sessions_collection = None   # stores full AI chat sessions per user
ai_messages_collection = None   # stores individual messages (optional flat store)


async def connect_mongo():
    """Call this on FastAPI startup"""
    global client, db, ai_sessions_collection, ai_messages_collection

    client = AsyncIOMotorClient(MONGO_URL)
    db = client["vestique_ai_chat"]

    ai_sessions_collection = db["ai_sessions"]
    ai_messages_collection = db["ai_messages"]

    # Create indexes for fast lookup
    await ai_sessions_collection.create_index("user_id")
    await ai_sessions_collection.create_index("session_id", unique=True)
    await ai_messages_collection.create_index("session_id")
    await ai_messages_collection.create_index("user_id")

    print("✅ MongoDB connected")


async def disconnect_mongo():
    """Call this on FastAPI shutdown"""
    global client
    if client:
        client.close()
        print("MongoDB disconnected")


def get_ai_sessions():
    return ai_sessions_collection


def get_ai_messages():
    return ai_messages_collection