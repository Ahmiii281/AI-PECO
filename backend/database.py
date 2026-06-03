"""
Database initialization and connection management.

Design:
- Production (DEBUG=False): fails fast if MongoDB is unreachable — no silent fallbacks.
- Development (DEBUG=True): falls back to an in-memory mock DB so the app
  starts without a real MongoDB instance.
- `get_db()` raises HTTP 503 if called before the DB is connected, preventing
  cryptic NoneType crashes deep in route handlers.
"""
import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from fastapi import HTTPException, status
from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

# ─── Module-level state ───────────────────────────────────────────────────────
_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None
_using_mock: bool = False


# ─── Lifecycle ────────────────────────────────────────────────────────────────

async def connect_db() -> None:
    """
    Connect to MongoDB on application startup.

    Production: raises SystemExit if the connection cannot be established.
    Development: falls back to mongomock-motor (in-memory, data not persisted).
    """
    global _client, _db, _using_mock

    try:
        _client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )
        # Verify the connection is actually reachable
        await _client.admin.command("ping")
        _db = _client[settings.DATABASE_NAME]
        _using_mock = False
        await _create_indexes()
        logger.info("✓ Connected to MongoDB at %s", settings.MONGODB_URL)

    except Exception as exc:
        if not settings.DEBUG:
            logger.critical(
                "MongoDB connection FAILED in production mode.\n"
                "URL: %s...\nError: %s\n\n"
                "Fix: Ensure MONGODB_URL is correct and the database is reachable.\n"
                "The application cannot start without a database connection.",
                settings.MONGODB_URL[:50] + "..." if settings.MONGODB_URL else "[not set]",
                exc,
            )
            # Re-raise to prevent app startup, but don't use SystemExit
            # FastAPI's lifespan will handle this and return error to client
            raise RuntimeError("Database connection failed in production") from exc

        # Development only: use in-memory mock
        logger.warning(
            "⚠️  MongoDB unavailable (%s). "
            "Falling back to in-memory mock database (data will NOT persist). "
            "This fallback is disabled in production.",
            exc,
        )
        try:
            from mongomock_motor import AsyncMongoMockClient  # type: ignore
            _client = AsyncMongoMockClient()
            _db = _client[settings.DATABASE_NAME]
            _using_mock = True
            await _create_indexes()
            await _seed_mock_db()
            logger.info("✓ Using mock MongoDB (development only)")
        except ImportError:
            logger.critical(
                "mongomock-motor is not installed and MongoDB is unavailable. "
                "Install it with: pip install mongomock-motor"
            )
            raise SystemExit(1) from exc


async def close_db() -> None:
    """Close the database connection on application shutdown."""
    global _client, _db, _using_mock
    if _client is not None:
        _client.close()
        logger.info("✓ Disconnected from MongoDB")
    _client = None
    _db = None
    _using_mock = False


# ─── Dependency ───────────────────────────────────────────────────────────────

def get_db() -> AsyncIOMotorDatabase:
    """
    FastAPI dependency — returns the active database handle.
    Raises HTTP 503 if the database is not connected, preventing NoneType crashes.
    """
    if _db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection is not available. Please try again later.",
        )
    return _db


def is_using_mock_db() -> bool:
    """Returns True if the application is running with the in-memory mock DB."""
    return _using_mock


# ─── Indexes ──────────────────────────────────────────────────────────────────

async def _create_indexes() -> None:
    """Create performance indexes. Safe to call on every startup (idempotent)."""
    assert _db is not None

    await _db.users.create_index("email", unique=True)
    await _db.devices.create_index("user_id")
    await _db.energy_data.create_index([("device_id", 1), ("timestamp", -1)])
    await _db.energy_data.create_index("device_id")
    await _db.alerts.create_index("user_id")
    await _db.alerts.create_index("timestamp")
    await _db.recommendations.create_index("user_id")
    await _db.recommendations.create_index("timestamp")
    logger.debug("Database indexes verified/created")


# ─── Mock seed (dev only) ─────────────────────────────────────────────────────

async def _seed_mock_db() -> None:
    """
    Seed the in-memory mock database with a default admin account.
    Only runs when using the mock DB in development mode.
    """
    import os
    from datetime import datetime
    from utils.password import hash_password

    admin_email = "admin@aipeco.com"
    existing = await _db.users.find_one({"email": admin_email})
    if not existing:
        admin_password = os.getenv("DEMO_ADMIN_PASSWORD", "Admin123!")
        await _db.users.insert_one({
            "name": "Demo Admin",
            "email": admin_email,
            "password_hash": hash_password(admin_password),
            "role": "admin",
            "energy_limit": 100.0,
            "is_active": True,
            "created_at": datetime.utcnow(),
        })
        logger.info(
            "Mock DB seeded — admin account: %s / %s",
            admin_email,
            admin_password,
        )
