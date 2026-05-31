"""
Pydantic schemas for API requests/responses
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime


# ─── Auth ─────────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    energy_limit: float = 50.0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Optional[UserResponse] = None
    message: Optional[str] = None


class PasswordResetRequest(BaseModel):
    email: EmailStr


class ForgotPasswordRequest(BaseModel):
    """Request body for the forgot-password endpoint."""
    email: EmailStr


class ResetPasswordWithToken(BaseModel):
    token: str = Field(..., min_length=10)
    new_password: str = Field(..., min_length=8, max_length=100)

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit.")
        return v


# ─── Devices ──────────────────────────────────────────────────────────────────

class DeviceCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    location: str = Field(..., min_length=2, max_length=100)
    relay_pin: int = Field(default=5, ge=0, le=39)  # Valid ESP32 GPIO range


class DeviceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    location: Optional[str] = Field(None, min_length=2, max_length=100)
    relay_pin: Optional[int] = Field(None, ge=0, le=39)


class DeviceResponse(BaseModel):
    id: str
    name: str
    location: str
    status: str
    is_relay_on: bool
    relay_pin: int
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Energy Data ──────────────────────────────────────────────────────────────

class EnergyDataCreate(BaseModel):
    device_id: str
    current: float = Field(..., ge=0)
    voltage: float = Field(..., ge=0)
    power: float = Field(..., ge=0)
    temperature: float = Field(..., ge=-40, le=85)   # DHT22 range
    humidity: float = Field(..., ge=0, le=100)


class EnergyDataResponse(BaseModel):
    id: str
    device_id: str
    current: float
    voltage: float
    power: float
    temperature: float
    humidity: float
    is_anomaly: bool
    timestamp: datetime

    class Config:
        from_attributes = True


# ─── Alerts ───────────────────────────────────────────────────────────────────

class AlertCreate(BaseModel):
    message: str = Field(..., min_length=5, max_length=500)
    alert_type: str = "warning"

    @field_validator("alert_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        allowed = {"info", "warning", "error", "critical"}
        if v not in allowed:
            raise ValueError(f"alert_type must be one of {allowed}")
        return v


class AlertResponse(BaseModel):
    id: str
    message: str
    alert_type: str
    resolved: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Recommendations ──────────────────────────────────────────────────────────

class RecommendationResponse(BaseModel):
    id: str
    message: str
    device_id: Optional[str]
    estimated_savings: float
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Dashboard ────────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_power: float
    avg_temperature: float
    avg_humidity: float
    alert_count: int
    device_count: int
    forecasted_power: Optional[float] = 0.0


class RelayCommand(BaseModel):
    device_id: str
    command: str

    @field_validator("command")
    @classmethod
    def validate_command(cls, v: str) -> str:
        if v not in ("ON", "OFF"):
            raise ValueError("command must be 'ON' or 'OFF'")
        return v


# ─── Smart Analysis ───────────────────────────────────────────────────────────

class SmartAnalysisRequest(BaseModel):
    """POST body for the smart analysis endpoint."""
    query: str = Field(..., min_length=2, max_length=500)
