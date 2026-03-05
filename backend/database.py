"""
Database initialization and connections
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from config import settings

# Global database instance
client: AsyncIOMotorClient = None
db: AsyncIOMotorDatabase = None


async def connect_db():
    """
    Connect to MongoDB
    """
    global client, db
    
    # Create indexes and DB connect
    try:
        # Prevent DNS timeout hang / configuration error on fake srv strings for demo
        client = AsyncIOMotorClient(settings.MONGODB_URL, serverSelectionTimeoutMS=2000)
        db = client[settings.DATABASE_NAME]
        await create_indexes()
        print("✓ Connected to MongoDB")
    except Exception as e:
        print(f"⚠ Could not connect to real MongoDB (running in offline/demo mode): {e}")


async def close_db():
    """
    Close MongoDB connection
    """
    global client
    if client:
        client.close()
        print("✓ Disconnected from MongoDB")


async def create_indexes():
    """
    Create database indexes for performance
    """
    # Users collection
    await db.users.create_index("email", unique=True)
    
    # Devices collection
    await db.devices.create_index("user_id")
    
    # Energy data - compound index for time-series queries
    await db.energy_data.create_index([("device_id", 1), ("timestamp", -1)])
    await db.energy_data.create_index("device_id")
    
    # Alerts
    await db.alerts.create_index("user_id")
    await db.alerts.create_index("timestamp")
    
    # Recommendations
    await db.recommendations.create_index("user_id")
    await db.recommendations.create_index("timestamp")


def get_db() -> AsyncIOMotorDatabase:
    """
    Get database instance
    """
    return db
