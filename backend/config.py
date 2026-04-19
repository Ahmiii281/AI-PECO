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
    
    # Database (No hardcoded credentials)
    MONGODB_URL: str
    DATABASE_NAME: str = "aipeco_db"
    
    # JWT (No hardcoded secret)
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS (Strict production domains)
    CORS_ORIGINS: list[str] = ["https://ai-peco.vercel.app"]
    
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
