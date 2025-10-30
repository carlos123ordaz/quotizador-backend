from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

class Database:
    client: AsyncIOMotorClient = None
    db = None

db = Database()

async def connect_to_mongo():
    db.client = AsyncIOMotorClient(settings.MONGODB_URL)
    db.db = db.client[settings.MONGODB_DB_NAME]
    print("✅ Conectado a MongoDB")

async def close_mongo_connection():
    db.client.close()
    print("❌ Desconectado de MongoDB")

def get_database():
    return db.db