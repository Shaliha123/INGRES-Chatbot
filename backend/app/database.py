import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient, ASCENDING, DESCENDING
from backend.app.config import settings

logger = logging.getLogger("ingres.database")

class Database:
    client: AsyncIOMotorClient = None
    db = None

db = Database()

def get_database():
    return db.db

async def connect_to_mongo():
    logger.info(f"Connecting to MongoDB Atlas database: {settings.DATABASE_NAME}...")
    db.client = AsyncIOMotorClient(settings.MONGODB_URI)
    db.db = db.client[settings.DATABASE_NAME]
    
    # Initialize collections and indexes synchronously via PyMongo client to ensure setup
    sync_client = MongoClient(settings.MONGODB_URI)
    sync_db = sync_client[settings.DATABASE_NAME]
    
    # Setup indexes as per 31_Database_Indexes.md
    try:
        # users collection
        sync_db.users.create_index([("email", ASCENDING)], unique=True)
        sync_db.users.create_index([("role", ASCENDING)])
        
        # chat_history collection
        sync_db.chat_history.create_index([("user_id", ASCENDING)])
        sync_db.chat_history.create_index([("timestamp", DESCENDING)])
        sync_db.chat_history.create_index([("conversation_id", ASCENDING)])
        
        # knowledge_base collection
        sync_db.knowledge_base.create_index([("title", ASCENDING)])
        sync_db.knowledge_base.create_index([("category", ASCENDING)])
        sync_db.knowledge_base.create_index([("keywords", ASCENDING)])
        sync_db.knowledge_base.create_index([("$**", "text")]) # Text index for search
        
        # documents collection
        sync_db.documents.create_index([("uploaded_by", ASCENDING)])
        sync_db.documents.create_index([("upload_date", DESCENDING)])
        
        # analytics collection
        sync_db.analytics.create_index([("last_updated", DESCENDING)])
        
        # logs collection
        sync_db.logs.create_index([("user_id", ASCENDING)])
        sync_db.logs.create_index([("timestamp", DESCENDING)])
        
        # settings collection
        sync_db.settings.create_index([("user_id", ASCENDING)], unique=True)
        
        logger.info("MongoDB Atlas connection established and indexes verified successfully.")
    except Exception as e:
        logger.error(f"Error setting up MongoDB indexes: {e}")
        raise e
    finally:
        sync_client.close()

async def close_mongo_connection():
    logger.info("Closing MongoDB Atlas connection...")
    if db.client:
        db.client.close()
