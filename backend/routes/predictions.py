"""
AI-PECO: Prediction API Routes
=================================
Endpoints for LSTM forecasting, NILM disaggregation, RL suggestions,
and smart analysis queries.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from database import get_db
from services.ai_service import AIService
from routes.auth import get_current_user

router = APIRouter(prefix="/api/predictions", tags=["predictions"])


@router.get("/forecast/{device_id}")
async def get_forecast(
    device_id: str,
    user_id: str = Depends(get_current_user),
):
    """
    Get AI-powered energy forecast for a specific device.
    Uses LSTM model when available, falls back to SMA.
    """
    db = get_db()
    ai_service = AIService(db)

    try:
        result = await ai_service.get_forecast(device_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/disaggregate/{device_id}")
async def get_disaggregation(
    device_id: str,
    user_id: str = Depends(get_current_user),
):
    """
    Get NILM-based power disaggregation for a device.
    Breaks down total power into appliance-level estimates.
    """
    db = get_db()
    ai_service = AIService(db)

    try:
        result = await ai_service.get_disaggregation(device_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/rl-suggestion")
async def get_rl_suggestion(
    user_id: str = Depends(get_current_user),
):
    """
    Get the RL agent's current optimization suggestion.
    The suggestion is based on time of day, power usage, temperature,
    and number of active devices.
    """
    db = get_db()
    ai_service = AIService(db)

    try:
        result = await ai_service.get_rl_suggestion(user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/smart-analysis")
async def smart_analysis(
    q: str = Query(..., description="Natural language query about energy usage"),
    user_id: str = Depends(get_current_user),
):
    """
    AI-powered analysis endpoint. Accepts a natural language question
    and returns a data-driven response with RL-based recommendations.
    """
    db = get_db()
    ai_service = AIService(db)

    try:
        result = await ai_service.process_smart_query(user_id, q)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
