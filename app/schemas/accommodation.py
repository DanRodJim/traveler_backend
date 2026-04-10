from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional
from decimal import Decimal
from app.common.types import AccommodationType
import uuid


class AccommodationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    type: AccommodationType = AccommodationType.hotel
    address: Optional[str] = Field(None, max_length=500)
    check_in_date: date
    check_out_date: date
    booking_reference: Optional[str] = Field(None, max_length=100)
    cost: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    notes: Optional[str] = None

class AccommodationCreate(AccommodationBase):
    trip_id: uuid.UUID

class AccommodationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    type: Optional[AccommodationType] = None
    address: Optional[str] = Field(None, max_length=500)
    check_in_date: Optional[date] = None
    check_out_date: Optional[date] = None
    booking_reference: Optional[str] = Field(None, max_length=100)
    cost: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    notes: Optional[str] = None

class AccommodationResponse(AccommodationBase):
    id: uuid.UUID
    trip_id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True