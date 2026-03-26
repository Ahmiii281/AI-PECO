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

# Lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_db()
    print("✓ AI-PECO Backend Started")
    yield
    # Shutdown
    await close_db()


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Energy Consumption Optimizer",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(auth.router)
app.include_router(devices.router)
app.include_router(energy.router)
app.include_router(dashboard.router)
app.include_router(billing.router)

from fastapi.responses import JSONResponse
import traceback
@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    with open("fastapi_errors.log", "a") as f:
        f.write("Global error:\n")
        traceback.print_exc(file=f)
    print("Caught:", exc)
    return JSONResponse(status_code=500, content={"detail": str(exc)})

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "app": settings.APP_NAME}


@app.get("/")
async def root():
    """
    Root endpoint
    """
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
