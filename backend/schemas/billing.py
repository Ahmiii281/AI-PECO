
from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class BillingRequest(BaseModel):
    consumer_type: str = Field(..., description="e.g., A-1, A-2, B")
    units: float = Field(0.0, description="Total units consumed")
    peak_units: float = Field(0.0, description="Peak units (for TOU)")
    offpeak_units: float = Field(0.0, description="Off-peak units (for TOU)")
    sanctioned_load: float = Field(1.0, description="Sanctioned load in kW")
    phase: int = Field(1, description="1 for Single Phase, 3 for Three Phase")
    is_protected: bool = Field(False, description="Whether the consumer is protected (Residential only)")

class SlabBreakdown(BaseModel):
    slab: str
    units: float
    rate: float
    cost: float

class BillingResponse(BaseModel):
    consumer_type: str
    total_units: float
    energy_charges: float
    fixed_charges: float
    total_bill: float
    breakdown: List[SlabBreakdown]
    optimization_suggestion: str
