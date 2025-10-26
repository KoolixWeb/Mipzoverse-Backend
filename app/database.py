from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

client = AsyncIOMotorClient(settings.mongodb_uri)
db = client["mipzoverse"]

users_collection = db["users"]
email_templates_collection  = db["email_templates"]

async def get_db():
    return db