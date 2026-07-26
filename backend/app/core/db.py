from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import get_settings

settings = get_settings()

client = None
db = None

if settings.mongodb_uri:
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_database]

def get_database():
    return db
