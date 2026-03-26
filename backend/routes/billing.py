
from fastapi import APIRouter, HTTPException
from schemas.billing import BillingRequest, BillingResponse
from services.billing_service import billing_service

router = APIRouter(prefix="/api/billing", tags=["Billing"])

@router.post("/estimate", response_model=BillingResponse)
async def estimate_bill(request: BillingRequest):
    try:
        result = billing_service.calculate_bill(
            consumer_type=request.consumer_type,
            units=request.units,
            peak_units=request.peak_units,
            offpeak_units=request.offpeak_units,
            sanctioned_load=request.sanctioned_load,
            phase=request.phase,
            is_protected=request.is_protected
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred during bill calculation.")

@router.get("/categories")
async def get_categories():
    return [
        {"id": "A-1", "name": "Residential"},
        {"id": "A-2", "name": "Commercial"},
        {"id": "A-3", "name": "General Services"},
        {"id": "B", "name": "Industrial"}
    ]
