"""
AI-PECO: AI-Powered Energy Consumption Optimizer
Main FastAPI application
"""
import os
import sys
# Add top-level folder to system path to import ml package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import connect_db, close_db, get_db
from routes import auth, devices, energy, dashboard, billing
from routes import predictions
from config import settings
from utils.logger import setup_logger
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse
from datetime import datetime

# Setup logger
logger = setup_logger(__name__)

# Demo mode flag
DEMO_MODE = settings.DEMO_MODE

# Keep reference to background tasks
_demo_task = None

# Lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _demo_task

    # Startup
    await connect_db()
    logger.info("AI-PECO Backend Started")

    # Start demo mode if enabled
    if DEMO_MODE:
        logger.info("DEMO_MODE is ON -- starting simulated data generation")
        try:
            from services.demo_seeder import start_demo_mode
            db = get_db()
            _demo_task = await start_demo_mode(db)
        except Exception as e:
            logger.error("Failed to start demo mode: %s", e)

    yield

    # Shutdown
    if _demo_task is not None:
        _demo_task.cancel()
    await close_db()
    logger.info("Disconnected from MongoDB")

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Energy Consumption Optimizer",
    lifespan=lifespan,
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Try again later."}
    )

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=3600,
)

# Include routes
app.include_router(auth.router)
app.include_router(devices.router)
app.include_router(energy.router)
app.include_router(dashboard.router)
app.include_router(billing.router)
app.include_router(predictions.router)

import traceback
@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    logger.error(f"Unexpected error: {exc}", exc_info=exc)
    try:
        os.makedirs("logs", exist_ok=True)
        with open("logs/fastapi_errors.log", "a") as f:
            f.write(f"\n{datetime.now().isoformat()} - Global error: {str(exc)}\n")
            traceback.print_exc(file=f)
    except Exception as log_error:
        logger.warning(f"Could not write to error log: {log_error}")
        
    return JSONResponse(
        status_code=500, 
        content={"detail": "Internal server error. Our team has been notified."}
    )

@app.get("/health")
async def health_check():
    from services.hardware_status import get_hardware_info
    hw = get_hardware_info()
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "data_source": hw["data_source"],
        "hardware_connected": hw["hardware_connected"],
        "hardware_last_seen": hw["last_seen"],
    }

@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "demo_mode": DEMO_MODE,
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.DEBUG
    )