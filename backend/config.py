"""
Configuration module for AI-PECO application
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional, List
import os


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "AI-PECO"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "ba341914_db_users"
    
    # JWT - CRITICAL: Must be set from environment in production
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS — stored as comma-separated string in .env
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,https://ai-peco.vercel.app"
    
    # ESP32 / device API
    ESP32_POLLING_INTERVAL: int = 5  # seconds
    DATA_RETENTION_DAYS: int = 30
    DEVICE_API_KEY: Optional[str] = None
    
    # Energy Settings
    ENERGY_PRICE_PER_UNIT: float = 50  # PKR per unit
    ANOMALY_THRESHOLD_SIGMA: float = 2.0
    
    # Demo mode (when ESP32 hardware is not connected)
    DEMO_MODE: bool = True

    # Server port (overridden by Render/Railway via PORT env var)
    PORT: int = 8080

    # Features
    ENABLE_AI_PREDICTIONS: bool = True
    ENABLE_AUTO_ALERTS: bool = True

    @property
    def cors_origins_list(self) -> List[str]:
        """Return CORS origins as a list."""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
    
    @field_validator("SECRET_KEY", mode="after")
    @classmethod
    def validate_secret_key(cls, v):
        """Ensure SECRET_KEY is configured properly."""
        import os
        
        # In production (when PORT or other env vars are set), SECRET_KEY is mandatory
        is_production = not os.getenv("DEBUG", "false").lower() == "true"
        
        if not v:
            if is_production:
                raise ValueError(
                    "SECRET_KEY must be set in environment variables for production. "
                    "Generate one: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
                )
            # For development, generate a temporary key
            import secrets
            return secrets.token_urlsafe(32)
        
        if v == "change_me_in_production":
            raise ValueError(
                "SECRET_KEY is using unsafe default value 'change_me_in_production'. "
                "Please set a strong random value in environment variables."
            )
        
        return v
    
    class Config:
        env_file = ".env"
        extra = "ignore"


# Initialize and validate settings once
settings = Settings()
