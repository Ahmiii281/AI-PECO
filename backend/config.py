"""
Configuration module for AI-PECO application
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "AI-PECO"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    MONGODB_URL: str = "mongodb+srv://username:password@cluster.mongodb.net"
    DATABASE_NAME: str = "aipeco_db"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: list = ["*", "https://ai-peco.vercel.app"]  # Explicitly added Vercel URL
                                                               # Allow all for debugging "Failed to fetch"
    
    
    # ESP32 / device API
    ESP32_POLLING_INTERVAL: int = 5  # seconds
    DATA_RETENTION_DAYS: int = 30
    DEVICE_API_KEY: Optional[str] = None
    
    # Energy Settings
    ENERGY_PRICE_PER_UNIT: float = 50  # PKR per unit
    ANOMALY_THRESHOLD_SIGMA: float = 2.0
    
    # Features
    ENABLE_AI_PREDICTIONS: bool = True
    ENABLE_AUTO_ALERTS: bool = True
    
    class Config:
        env_file = ".env"


settings = Settings()
