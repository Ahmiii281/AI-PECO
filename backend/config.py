"""
Configuration module for AI-PECO application.

All settings are loaded from environment variables (or .env file).
Call `settings` to access the singleton — never read os.getenv() directly
in application code; always use settings.<FIELD>.
"""
import os
import secrets
import logging
from pydantic_settings import BaseSettings
from pydantic import model_validator
from typing import Optional, List

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # ── Application ──────────────────────────────────────────────────────────
    APP_NAME: str = "AI-PECO"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ── Database ─────────────────────────────────────────────────────────────
    # CRITICAL: Must be set via environment variable in production
    MONGODB_URL: str = ""
    DATABASE_NAME: str = "aipeco_db"

    # ── JWT ───────────────────────────────────────────────────────────────────
    # CRITICAL: Must be a persistent, random 32+ character string in production.
    # Generate: python -c "import secrets; print(secrets.token_urlsafe(48))"
    # Must be set via environment variable in production — DO NOT commit defaults
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ── CORS — comma-separated origins ────────────────────────────────────────
    CORS_ORIGINS: str = (
        "http://localhost:3000,http://127.0.0.1:3000," \
        "http://localhost:5173,http://127.0.0.1:5173,https://ai-peco.vercel.app,https://ai-peco-frontend.vercel.app"
    )

    # ── ESP32 / Device API ───────────────────────────────────────────────────
    ESP32_POLLING_INTERVAL: int = 5          # seconds between readings
    DATA_RETENTION_DAYS: int = 30
    DEVICE_API_KEY: Optional[str] = None
    # Set to False only during local hardware development — always True in prod
    DEVICE_API_KEY_REQUIRED: bool = True

    # ── Energy & Billing ──────────────────────────────────────────────────────
    ELECTRICITY_TARIFF_PKR: float = 50.0    # PKR per kWh (FESCO default)
    ANOMALY_THRESHOLD_SIGMA: float = 2.0

    # ── Demo Mode ─────────────────────────────────────────────────────────────
    # When True, simulated ESP32 data is generated automatically.
    # Set to False when real hardware is connected.
    DEMO_MODE: bool = True

    # ── Server ────────────────────────────────────────────────────────────────
    PORT: int = 8080

    # ── Email (SMTP) ──────────────────────────────────────────────────────────
    # Leave SMTP_HOST empty to disable email and use log-only fallback.
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    SMTP_FROM: str = "no-reply@ai-peco.com"
    SMTP_USE_TLS: bool = True

    # ── Frontend ──────────────────────────────────────────────────────────────
    # Used to build password-reset links in emails.
    FRONTEND_URL: str = "https://ai-peco-frontend.vercel.app"

    # ── Features ─────────────────────────────────────────────────────────────
    ENABLE_AI_PREDICTIONS: bool = True
    ENABLE_AUTO_ALERTS: bool = True

    # ── Derived helpers ───────────────────────────────────────────────────────
    @property
    def cors_origins_list(self) -> List[str]:
        """Return CORS origins as a list."""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def ENERGY_PRICE_PER_UNIT(self) -> float:
        """Alias for ELECTRICITY_TARIFF_PKR — keeps legacy references working."""
        return self.ELECTRICITY_TARIFF_PKR

    @property
    def smtp_configured(self) -> bool:
        """True if all required SMTP fields are set."""
        return bool(self.SMTP_HOST and self.SMTP_USER and self.SMTP_PASS)

    # ── Validators ───────────────────────────────────────────────────────────
    @model_validator(mode="after")
    def validate_secrets(self) -> "Settings":
        """
        Validate SECRET_KEY and MONGODB_URL after all fields (including DEBUG) are loaded.

        Rules:
        - Production (DEBUG=False): SECRET_KEY and MONGODB_URL are mandatory
        - Development (DEBUG=True): Secrets can be auto-generated/mocked
        """
        if not self.DEBUG:
            # Production mode — strict validation
            if not self.SECRET_KEY or len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "CRITICAL: SECRET_KEY must be set in production via environment variable "
                    "and be at least 32 characters.\n"
                    "Generate with: python -c \"import secrets; print(secrets.token_urlsafe(48))\""
                )
            if not self.MONGODB_URL:
                raise ValueError(
                    "CRITICAL: MONGODB_URL must be set in production via environment variable.\n"
                    "This must point to MongoDB Atlas or a production database."
                )
            if self.MONGODB_URL.startswith("mongodb://localhost"):
                raise ValueError(
                    "CRITICAL: MONGODB_URL cannot use localhost in production.\n"
                    "Must connect to MongoDB Atlas or remote server."
                )
        else:
            # Development mode — auto-generate if needed
            if not self.SECRET_KEY:
                self.SECRET_KEY = "dev-" + "OfelwAclHvqGd51gRfM_D2WsSi3voTBalHZ5CYZwksOqYau7N-bu"
                logger.warning("⚠️  Using auto-generated SECRET_KEY for development (not secure)")
            if not self.MONGODB_URL:
                self.MONGODB_URL = "mongodb://localhost:27017"
                logger.warning("⚠️  Using localhost MongoDB for development")
        
        return self

    @model_validator(mode="after")
    def validate_additional_security(self) -> "Settings":
        """
        Additional security checks.
        """
        # Warn if ESP32 key auth is disabled outside DEBUG
        if not self.DEBUG and not self.DEVICE_API_KEY_REQUIRED:
            logger.warning(
                "DEVICE_API_KEY_REQUIRED=False in a non-debug environment. "
                "This means ANY client can POST energy data without authentication. "
                "Set DEVICE_API_KEY_REQUIRED=True and configure DEVICE_API_KEY."
            )

        return self

    class Config:
        env_file = ".env"
        extra = "ignore"


# Singleton — import `settings` everywhere; never re-instantiate.
settings = Settings()
