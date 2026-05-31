"""
Energy data and analytics routes.

ESP32 Authentication:
- DEVICE_API_KEY_REQUIRED=True (default, production): every POST to /api/energy/data
  must include the X-API-Key header matching settings.DEVICE_API_KEY.
- DEVICE_API_KEY_REQUIRED=False (development only): key check is skipped.
  A WARNING is logged at startup if this is used outside DEBUG mode.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi import APIRouter, Depends, HTTPException, status, Header
from database import get_db
from services.energy_service import EnergyService
from services.device_service import DeviceService
from services.hardware_status import mark_hardware_active
from ml.inference.energy_model import EnergyModel
from schemas import (
    EnergyDataCreate,
    EnergyDataResponse,
    AlertResponse,
    AlertCreate,
)
from routes.auth import get_current_user
from config import settings
from utils.logger import setup_logger

router = APIRouter(prefix="/api/energy", tags=["energy"])
logger = setup_logger(__name__)


def _check_device_api_key(x_api_key: str | None) -> None:
    """
    Validate the X-API-Key header from ESP32.
    Raises HTTP 401 if validation fails.
    Skipped only when DEVICE_API_KEY_REQUIRED=False (dev mode).
    """
    if not settings.DEVICE_API_KEY_REQUIRED:
        # Key enforcement is disabled — only allowed in DEBUG mode
        if not settings.DEBUG:
            logger.warning(
                "⚠️  ESP32 API key enforcement is DISABLED in a non-debug environment. "
                "Any client can POST energy data. Set DEVICE_API_KEY_REQUIRED=True in production."
            )
        return

    expected = settings.DEVICE_API_KEY
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "DEVICE_API_KEY is not configured on the server. "
                "Set it in environment variables."
            ),
        )

    if not x_api_key or x_api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key. ESP32 must send the correct device API key.",
        )


@router.post("/data", response_model=EnergyDataResponse)
async def save_energy_data(
    data: EnergyDataCreate,
    x_api_key: str | None = Header(None, alias="X-API-Key"),
):
    """
    Receive energy data from ESP32.

    Authentication:
    - Production: requires X-API-Key header matching DEVICE_API_KEY env var.
    - Development (DEVICE_API_KEY_REQUIRED=False): no key needed.
    """
    _check_device_api_key(x_api_key)

    # Signal that real hardware is sending data → demo seeder will auto-pause
    mark_hardware_active()

    db = get_db()
    energy_service = EnergyService(db)
    device_service = DeviceService(db)

    try:
        # Update device status to online
        await device_service.update_device_status(data.device_id, "online")

        # Save energy data
        energy_data = await energy_service.save_energy_data(
            data.device_id,
            data.dict(),
        )

        # Anomaly detection
        recent_data = await energy_service.get_device_energy_data(data.device_id, hours=1)
        model = EnergyModel(
            energy_price_per_unit=settings.ELECTRICITY_TARIFF_PKR,
            anomaly_threshold_sigma=settings.ANOMALY_THRESHOLD_SIGMA,
        )
        anomalies, _mean_power, _std_dev = model.detect_anomalies(recent_data)

        if anomalies and settings.ENABLE_AUTO_ALERTS:
            device = await device_service.get_device(data.device_id)
            await energy_service.create_alert(
                str(device["user_id"]),
                f"Anomaly in {device['name']}: Power {anomalies[-1]['power']:.0f}W",
                "warning",
            )

        # Non-critical: update RL agent with new reading
        try:
            from services.ai_service import AIService
            ai_service = AIService(db)
            await ai_service.update_rl_from_reading(
                data.device_id,
                energy_data.get("power", 0),
                energy_data.get("temperature", 25),
            )
        except Exception:
            pass

        return {
            "id": str(energy_data["_id"]),
            "device_id": str(energy_data["device_id"]),
            "current": energy_data["current"],
            "voltage": energy_data["voltage"],
            "power": energy_data["power"],
            "temperature": energy_data["temperature"],
            "humidity": energy_data["humidity"],
            "is_anomaly": len(anomalies) > 0,
            "timestamp": energy_data["timestamp"],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/device/{device_id}", response_model=list)
async def get_device_energy_data(
    device_id: str,
    hours: int = 24,
    user_id: str = Depends(get_current_user),
):
    """Get energy data for a device (last N hours). Requires device ownership."""
    db = get_db()
    energy_service = EnergyService(db)
    device_service = DeviceService(db)

    try:
        await device_service.get_device(device_id, user_id)  # ownership check
        data = await energy_service.get_device_energy_data(device_id, hours)
        return [
            {
                "id": str(d["_id"]),
                "device_id": str(d["device_id"]),
                "current": d["current"],
                "voltage": d["voltage"],
                "power": d["power"],
                "temperature": d["temperature"],
                "humidity": d["humidity"],
                "is_anomaly": d.get("is_anomaly", False),
                "timestamp": d["timestamp"],
            }
            for d in data
        ]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/alerts", response_model=AlertResponse)
async def create_alert(
    payload: AlertCreate,
    user_id: str = Depends(get_current_user),
):
    """Manually create an alert for the current user."""
    db = get_db()
    energy_service = EnergyService(db)

    try:
        alert = await energy_service.create_alert(
            user_id, payload.message, payload.alert_type
        )
        return {
            "id": str(alert["_id"]),
            "message": alert["message"],
            "alert_type": alert["alert_type"],
            "resolved": alert["resolved"],
            "created_at": alert["created_at"],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/alerts", response_model=list)
async def get_alerts(
    resolved: bool = False,
    user_id: str = Depends(get_current_user),
):
    """Get all alerts for the current user."""
    db = get_db()
    energy_service = EnergyService(db)

    alerts = await energy_service.get_user_alerts(user_id, resolved)
    return [
        {
            "id": str(a["_id"]),
            "message": a["message"],
            "alert_type": a.get("alert_type", "warning"),
            "resolved": a["resolved"],
            "created_at": a["created_at"],
        }
        for a in alerts
    ]


@router.put("/alerts/{alert_id}")
async def resolve_alert(
    alert_id: str,
    user_id: str = Depends(get_current_user),
):
    """Mark an alert as resolved."""
    db = get_db()
    energy_service = EnergyService(db)

    try:
        alert = await energy_service.resolve_alert(alert_id, user_id)
        return {
            "id": str(alert["_id"]),
            "message": alert["message"],
            "resolved": alert["resolved"],
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
