"""
Pydantic schemas for API requests/responses
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# Auth Schemas
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    energy_limit: float = 50.0
    created_at: datetime = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Optional[UserResponse] = None


# Device Schemas
class DeviceCreate(BaseModel):
    name: str
    location: str
    relay_pin: int = 5


class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    relay_pin: Optional[int] = None


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


# Energy Data Schemas
class EnergyDataCreate(BaseModel):
    device_id: str
    current: float
    voltage: float
    power: float
    temperature: float
    humidity: float


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


# Alert Schemas
class AlertResponse(BaseModel):
    id: str
    message: str
    alert_type: str
    resolved: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Recommendation Schemas
class RecommendationResponse(BaseModel):
    id: str
    message: str
    device_id: Optional[str]
    estimated_savings: float
    created_at: datetime

    class Config:
        from_attributes = True


class AlertCreate(BaseModel):
    message: str
    alert_type: str = "warning"


# Dashboard Schemas
class DashboardStats(BaseModel):
    total_power: float
    avg_temperature: float
    avg_humidity: float
    alert_count: int
    device_count: int
    forecasted_power: Optional[float] = 0.0


class RelayCommand(BaseModel):
    device_id: str
    command: str  # "ON" or "OFF"
