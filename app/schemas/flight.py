from pydantic import BaseModel, Field, ConfigDict, model_validator
from datetime import date, time, datetime
from typing import Optional, List
from decimal import Decimal
import uuid

PATTERN = r'^[A-Z]{3}$'

# ── FlightSplit schemas ─────────────────────────────────────────────────────

class FlightSplitCreate(BaseModel):
    user_id: uuid.UUID
    amount: Decimal = Field(..., gt=0, decimal_places=2)


class FlightSplitResponse(BaseModel):
    id: uuid.UUID
    flight_id: uuid.UUID
    user_id: uuid.UUID
    amount: Decimal
    is_paid: bool = False
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ── Flight schemas ───────────────────────────────────────────────────────────

class FlightBase(BaseModel):
    airline: Optional[str] = Field(None, max_length=100)
    flight_number: Optional[str] = Field(None, max_length=20)
    departure_airport: str = Field(..., min_length=3, max_length=3, pattern=PATTERN)
    arrival_airport: str = Field(..., min_length=3, max_length=3, pattern=PATTERN)
    departure_date: date
    departure_time: Optional[time] = None
    arrival_date: date
    arrival_time: Optional[time] = None
    booking_reference: Optional[str] = Field(None, max_length=50)
    cost: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    currency: Optional[str] = Field(default="USD", pattern=PATTERN)
    notes: Optional[str] = None
    paid_by: Optional[uuid.UUID] = None
    is_private: bool = True

    model_config = ConfigDict(from_attributes=True)


class FlightCreate(FlightBase):
    trip_id: uuid.UUID
    splits: Optional[List[FlightSplitCreate]] = None

    @model_validator(mode='after')
    def validate_paid_by_with_splits(self) -> 'FlightCreate':
        if self.splits and not self.paid_by:
            raise ValueError("paid_by is required when splits are provided")
        return self


class FlightUpdate(BaseModel):
    airline: Optional[str] = Field(None, max_length=100)
    flight_number: Optional[str] = Field(None, max_length=20)
    departure_airport: Optional[str] = Field(None, min_length=3, max_length=3, pattern=PATTERN)
    arrival_airport: Optional[str] = Field(None, min_length=3, max_length=3, pattern=PATTERN)
    departure_date: Optional[date] = None
    departure_time: Optional[time] = None
    arrival_date: Optional[date] = None
    arrival_time: Optional[time] = None
    booking_reference: Optional[str] = Field(None, max_length=50)
    cost: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    currency: Optional[str] = Field(None, pattern=PATTERN)
    notes: Optional[str] = None
    paid_by: Optional[uuid.UUID] = None
    is_private: Optional[bool] = None
    splits: Optional[List[FlightSplitCreate]] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='after')
    def validate_paid_by_with_splits(self) -> 'FlightUpdate':
        if self.splits and not self.paid_by:
            raise ValueError("paid_by is required when splits are provided")
        return self


class FlightResponse(FlightBase):
    id: uuid.UUID
    trip_id: uuid.UUID
    created_by: uuid.UUID
    splits: List[FlightSplitResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None