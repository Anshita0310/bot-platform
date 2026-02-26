from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "bot_builder")

_client = None
_db = None

async def get_client():
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(MONGODB_URI, uuidRepresentation="standard")
    return _client

async def get_db():
    global _db
    if _db is None:
        client = await get_client()
        _db = client[DB_NAME]
        # Ensure indexes once on first access
        await _db.flows.create_index(
            [("orgId", 1), ("projectId", 1), ("name", 1)], unique=True
        )
    return _db
