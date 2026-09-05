from pydantic import BaseModel, Field
from typing import List, Optional


class AiEstimatorRequest(BaseModel):
    origin: str = Field(..., min_length=2, max_length=100)
    destination: str = Field(..., min_length=2, max_length=100)
    duration_days: int = Field(..., ge=1, le=365)
    travelers: int = Field(..., ge=1, le=50)
    travel_style: str
    accommodation_type: str
    interests: List[str]
    currency: str = Field(default="USD", pattern=r'^[A-Z]{3}$')
    additional_notes: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class AiEstimatorBreakdown(BaseModel):
    flights: float
    accommodation: float
    food: float
    activities: float
    transport: float
    misc: float


class AiEstimatorResponse(BaseModel):
    destination: str
    origin: str
    duration_days: int
    travelers: int
    currency: str
    total_estimated: float
    breakdown: AiEstimatorBreakdown
    notes: str
    travel_style: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None