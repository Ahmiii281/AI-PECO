"""
Database initialization and connections
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Global database instance
client: AsyncIOMotorClient = None
db: AsyncIOMotorDatabase = None


async def connect_db():
    """
    Connect to MongoDB with fallback to mock for local dev
    """
    global client, db
    
    try:
        # Use a short timeout for local detection
        client = AsyncIOMotorClient(
            settings.MONGODB_URL, 
            serverSelectionTimeoutMS=2000,
            connectTimeoutMS=2000
        )
        # Verify connection
        await client.admin.command('ping')
        db = client[settings.DATABASE_NAME]
        await create_indexes()
        logger.info("✓ Connected to MongoDB")
    except Exception as e:
        logger.warning(f"⚠️ Real MongoDB connection failed: {e}")
        logger.info("🔄 Falling back to Mock Database for development...")
        from mongomock_motor import AsyncMongoMockClient as MockClient
        client = MockClient()
        db = client[settings.DATABASE_NAME]
        await create_indexes()
        await seed_db()
        logger.info("✓ Using Mock MongoDB (Data will NOT persist)")


async def seed_db():
    """
    Seed database with default admin if using mock
    """
    from utils.password import hash_password
    admin_email = "admin@aipeco.com"
    existing = await db.users.find_one({"email": admin_email})
    if not existing:
        await db.users.insert_one({
            "name": "Demo Admin",
            "email": admin_email,
            "password_hash": hash_password("admin123"),
            "role": "admin",
            "energy_limit": 100.0,
            "is_active": True
        })
        logger.info(f"👤 Created default admin: {admin_email} / admin123")


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
