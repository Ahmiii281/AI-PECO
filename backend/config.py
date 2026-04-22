"""
Configuration module for AI-PECO application
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "AI-PECO"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Database
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "aipeco_db")
    
    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY")  # Must be set in .env
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost:3000,https://ai-peco.vercel.app").split(",")
    
    # ESP32 / device API
    ESP32_POLLING_INTERVAL: int = 5  # seconds
    DATA_RETENTION_DAYS: int = 30
    DEVICE_API_KEY: Optional[str] = os.getenv("DEVICE_API_KEY")
    
    # Energy Settings
    ENERGY_PRICE_PER_UNIT: float = 50  # PKR per unit
    ANOMALY_THRESHOLD_SIGMA: float = 2.0
    
    # Features
    ENABLE_AI_PREDICTIONS: bool = True
    ENABLE_AUTO_ALERTS: bool = True
    
    class Config:
        env_file = ".env"


# Validate critical settings
if not Settings().SECRET_KEY:
    raise ValueError("SECRET_KEY must be set in environment variables")

settings = Settings()