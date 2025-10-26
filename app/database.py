from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

client = AsyncIOMotorClient(settings.mongodb_uri)
db = client["mipzoverse"]

users_collection = db["users"]

async def get_db():
    return db