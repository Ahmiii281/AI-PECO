"""
Energy data and analytics routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from database import get_db
from motor.motor_asyncio import AsyncIOMotorDatabase
from services.energy_service import EnergyService
from services.device_service import DeviceService
from ai.energy_model import EnergyModel
from schemas import (
    EnergyDataCreate,
    EnergyDataResponse,
    AlertResponse,
    RecommendationResponse,
    AlertCreate,
)
from routes.auth import get_current_user
from config import settings

router = APIRouter(prefix="/api/energy", tags=["energy"])


@router.post("/data", response_model=EnergyDataResponse)
async def save_energy_data(
    data: EnergyDataCreate,
    x_api_key: str = Header(None)
):
    """
    Receive energy data from ESP32.
    - In development (`DEBUG=True`), requests are accepted without a device API key.
    - In non-development environments, a valid `X-API-Key` matching `DEVICE_API_KEY`
      is required; otherwise a 401 is returned.
    """
    is_dev = settings.DEBUG
    expected_key = settings.DEVICE_API_KEY

    if not is_dev:
        if not x_api_key or not expected_key or x_api_key != expected_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing device API key",
            )

    energy_service = EnergyService(db)
    device_service = DeviceService(db)

    try:
        # Update device status to online
        await device_service.update_device_status(data.device_id, "online")

        # Save energy data
        energy_data = await energy_service.save_energy_data(
            data.device_id,
            data.dict()
        )

        # Check for anomalies
        recent_data = await energy_service.get_device_energy_data(data.device_id, hours=1)
        model = EnergyModel(
            energy_price_per_unit=settings.ENERGY_PRICE_PER_UNIT,
            anomaly_threshold_sigma=settings.ANOMALY_THRESHOLD_SIGMA
        )

        detection_result = model.detect_anomalies(recent_data)
        anomalies = detection_result.get("anomalies", [])
        mean_power = detection_result.get("mean_power", 0.0)

        if anomalies and settings.ENABLE_AUTO_ALERTS:
            # Get device owner
            device = await device_service.get_device(data.device_id)
            # Create alert
            await energy_service.create_alert(
                str(device["user_id"]),
                f"Anomaly in {device['name']}: Power {anomalies[-1]['power']:.0f}W",
                "warning"
            )

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

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/device/{device_id}", response_model=list)
async def get_device_energy_data(
    device_id: str,
    hours: int = 24,
    user_id: str = Depends(get_current_user)
):
    """
    Get energy data for a device (last N hours)
    """
    energy_service = EnergyService(db)
    device_service = DeviceService(db)

    try:
        # Verify ownership
        await device_service.get_device(device_id, user_id)

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
    """
    Manually create an alert
    """
    energy_service = EnergyService(db)

    try:
        alert = await energy_service.create_alert(
            user_id,
            payload.message,
            payload.alert_type,
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
    user_id: str = Depends(get_current_user)
):
    """
    Get user alerts
    """
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
    user_id: str = Depends(get_current_user)
):
    """
    Mark alert as resolved
    """
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
