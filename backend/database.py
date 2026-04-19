"""
Database initialization and connections
"""
import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from config import settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None

db_manager = DatabaseManager()

async def connect_db():
    """
    Connect to MongoDB with proper connection pooling and timeouts
    """
    try:
        logger.info("Connecting to MongoDB...")
        db_manager.client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            serverSelectionTimeoutMS=5000,
            maxPoolSize=50,
            minPoolSize=10
        )
        db_manager.db = db_manager.client[settings.DATABASE_NAME]
        await create_indexes()
        logger.info("Connected to MongoDB established successfully")
    except Exception as e:
        logger.error(f"Could not connect to MongoDB: {e}")
        raise e

async def close_db():
    """
    Close MongoDB connection
    """
    if db_manager.client:
        db_manager.client.close()
        logger.info("Disconnected from MongoDB")

async def create_indexes():
    """
    Create database indexes for performance
    """
    # Users collection
    await db_manager.db.users.create_index("email", unique=True)
    
    # Devices collection
    await db_manager.db.devices.create_index("user_id")
    
    # Energy data - compound index for time-series queries
    await db_manager.db.energy_data.create_index([("device_id", 1), ("timestamp", -1)])
    await db_manager.db.energy_data.create_index("device_id")
    
    # Alerts
    await db_manager.db.alerts.create_index("user_id")
    await db_manager.db.alerts.create_index("timestamp")
    
    # Recommendations
    await db_manager.db.recommendations.create_index("user_id")
    await db_manager.db.recommendations.create_index("timestamp")

async def get_db() -> AsyncIOMotorDatabase:
    """
    Get database instance using dependency injection pattern
    """
    if db_manager.db is None:
        raise Exception("Database is not initialized")
    return db_manager.db
