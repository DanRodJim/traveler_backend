from pydantic import BaseModel, Field, ConfigDict
from datetime import date, time, datetime
from typing import Optional
from decimal import Decimal
import uuid

class FlightBase(BaseModel):
    airline: Optional[str] = Field(None, max_length=100)
    flight_number: Optional[str] = Field(None, max_length=20)
    departure_airport: str = Field(..., min_length=3, max_length=3, pattern=r'^[A-Z]{3}$')
    arrival_airport: str = Field(..., min_length=3, max_length=3, pattern=r'^[A-Z]{3}$')
    departure_date: date
    departure_time: Optional[time] = None
    arrival_date: date
    arrival_time: Optional[time] = None
    booking_reference: Optional[str] = Field(None, max_length=50)
    cost: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    currency: Optional[str] = Field(default="USD", pattern=r'^[A-Z]{3}$')
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class FlightCreate(FlightBase):
    trip_id: uuid.UUID

class FlightUpdate(BaseModel):
    airline: Optional[str] = Field(None, max_length=100)
    flight_number: Optional[str] = Field(None, max_length=20)
    departure_airport: Optional[str] = Field(None, min_length=3, max_length=3, pattern=r'^[A-Z]{3}$')
    arrival_airport: Optional[str] = Field(None, min_length=3, max_length=3, pattern=r'^[A-Z]{3}$')
    departure_date: Optional[date] = None
    departure_time: Optional[time] = None
    arrival_date: Optional[date] = None
    arrival_time: Optional[time] = None
    booking_reference: Optional[str] = Field(None, max_length=50)
    cost: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    currency: Optional[str] = Field(None, pattern=r'^[A-Z]{3}$')
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class FlightResponse(FlightBase):
    id: uuid.UUID
    trip_id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None