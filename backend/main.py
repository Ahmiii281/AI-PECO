"""
AI-PECO: AI-Powered Energy Consumption Optimizer
Main FastAPI application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import connect_db, close_db
from routes import auth, devices, energy, dashboard, billing
from config import settings
from utils.logger import setup_logger
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse
from datetime import datetime

# Setup logger
logger = setup_logger(__name__)

# Lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_db()
    logger.info("✓ AI-PECO Backend Started")
    yield
    # Shutdown
    await close_db()
    logger.info("✓ Disconnected from MongoDB")

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
    allow_origins=settings.CORS_ORIGINS,
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

import traceback
@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    logger.error(f"Unexpected error: {exc}")
    try:
        with open("logs/fastapi_errors.log", "a") as f:
            f.write(f"\n{datetime.now().isoformat()} - Global error: {str(exc)}\n")
            traceback.print_exc(file=f)
    except:
        pass
        
    return JSONResponse(
        status_code=500, 
        content={"detail": "Internal server error. Our team has been notified."}
    )

@app.get("/health")
async def health_check():
    return {"status": "healthy", "app": settings.APP_NAME}

@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )