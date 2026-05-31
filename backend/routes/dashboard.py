"""
Dashboard and relay control routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from database import get_db
from services.device_service import DeviceService
from services.energy_service import EnergyService
from ml.inference.energy_model import EnergyModel
from schemas import DashboardStats, RelayCommand
from routes.auth import get_current_user
from config import settings

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(user_id: str = Depends(get_current_user)):
    """
    Get dashboard statistics
    """
    db = get_db()
    energy_service = EnergyService(db)

    try:
        stats = await energy_service.get_dashboard_stats(user_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/relay/{device_id}")
async def control_relay(
    device_id: str,
    command: RelayCommand,
    user_id: str = Depends(get_current_user)
):
    """
    Control relay (turn ON/OFF)
    """
    db = get_db()
    device_service = DeviceService(db)

    try:
        # Verify ownership
        device = await device_service.get_device(device_id, user_id)

        # Set relay command
        result = await device_service.set_relay_command(device_id, command.command)

        return {
            "device_id": str(result["_id"]),
            "name": result["name"],
            "command": command.command,
            "status": "success"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/recommendation/{device_id}")
async def get_recommendation(
    device_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Get AI recommendation for device.
    Combines anomaly-based and RL-based suggestions.
    """
    db = get_db()
    device_service = DeviceService(db)
    energy_service = EnergyService(db)

    try:
        # Verify ownership
        device = await device_service.get_device(device_id, user_id)

        # Get recent energy data
        recent_data = await energy_service.get_device_energy_data(device_id, hours=24)

        if len(recent_data) < 3:
            return {
                "message": "Insufficient data for recommendations",
                "confidence": "low",
                "estimated_savings": 0
            }

        # Analyze with anomaly-based AI model
        model = EnergyModel(
            energy_price_per_unit=settings.ELECTRICITY_TARIFF_PKR,
            anomaly_threshold_sigma=settings.ANOMALY_THRESHOLD_SIGMA
        )

        anomalies, mean_power, std_dev = model.detect_anomalies(recent_data)
        recommendation = model.generate_recommendation(anomalies, mean_power)

        daily_cost = model.forecast_daily_cost(mean_power)

        # Get RL-based suggestion
        rl_suggestion = None
        try:
            from services.ai_service import AIService
            ai_service = AIService(db)
            rl_suggestion = await ai_service.get_rl_suggestion(user_id)
        except Exception:
            pass

        result = {
            **recommendation,
            "device_name": device["name"],
            "current_daily_cost": daily_cost,
            "all_readings_count": len(recent_data),
            "anomaly_count": len(anomalies),
        }

        if rl_suggestion:
            result["rl_recommendation"] = {
                "title": rl_suggestion.get("title", ""),
                "description": rl_suggestion.get("description", ""),
                "estimated_savings_pkr": rl_suggestion.get("estimated_savings_pkr", 0),
                "confidence": rl_suggestion.get("confidence", "low"),
                "source": "reinforcement_learning",
            }

        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/device-command/{device_id}")
async def get_device_command(device_id: str):
    """
    Get relay command for device (polled by ESP32)
    """
    db = get_db()
    device_service = DeviceService(db)

    try:
        command = await device_service.get_relay_command(device_id)
        return {
            "device_id": command["device_id"],
            "command": command["command"],
            "relay_pin": command["relay_pin"]
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
