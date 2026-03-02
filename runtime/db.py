from motor.motor_asyncio import AsyncIOMotorClient
from .config import MONGODB_URI, DB_NAME

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
    return _db
