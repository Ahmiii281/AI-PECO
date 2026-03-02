"""
Database initialization and connections
"""
from motor.motor_asyncio import AsyncClient, AsyncDatabase
from config import settings

# Global database instance
client: AsyncClient = None
db: AsyncDatabase = None


async def connect_db():
    """
    Connect to MongoDB
    """
    global client, db
    client = AsyncClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    
    # Create indexes
    await create_indexes()
    print("✓ Connected to MongoDB")


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


def get_db() -> AsyncDatabase:
    """
    Get database instance
    """
    return db
