"""
AI-PECO: Prediction API Routes
=================================
Endpoints for LSTM forecasting, NILM disaggregation, RL suggestions,
and smart analysis queries.

Smart Analysis uses POST (not GET) to keep the query out of URL logs
and server access logs, which is better for user privacy.
"""

from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from services.ai_service import AIService
from schemas import SmartAnalysisRequest
from routes.auth import get_current_user

router = APIRouter(prefix="/api/predictions", tags=["predictions"])


@router.get("/forecast/{device_id}")
async def get_forecast(
    device_id: str,
    user_id: str = Depends(get_current_user),
):
    """
    Get AI-powered energy forecast for a specific device.
    Uses LSTM model when available (requires ≥60 readings); falls back to SMA.
    Response always includes `method`, `confidence`, and a human-readable `message`.
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
    Uses trained CNN+LSTM model when available; falls back to estimated proportions.
    Response always includes `method`, `confidence`, and `is_estimate` flag.
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
    Uses tabular Q-learning pre-seeded with domain knowledge.
    Improves with every ESP32 sensor reading via online learning.
    """
    db = get_db()
    ai_service = AIService(db)

    try:
        result = await ai_service.get_rl_suggestion(user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/smart-analysis")
async def smart_analysis(
    body: SmartAnalysisRequest,
    user_id: str = Depends(get_current_user),
):
    """
    Data-driven energy assistant.

    Accepts a natural language question via POST body (not URL params —
    keeps queries private and out of access logs).
    Returns a structured analysis using real sensor data + RL suggestions.

    This is a rule/data-based assistant. It does NOT use a generative LLM
    for this endpoint — responses are deterministic and based on your actual
    energy readings.
    """
    db = get_db()
    ai_service = AIService(db)

    try:
        result = await ai_service.process_smart_query(user_id, body.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
