from pydantic import BaseModel, Field, model_validator, ConfigDict # Importamos ConfigDict
from datetime import date, datetime
from typing import Optional
from decimal import Decimal
from app.common.types import AccommodationType
import uuid

from app.core.exceptions import InvalidDateRangeError

def validate_date_range(start: Optional[date], end: Optional[date]) -> None:
    if start is not None and end is not None:
        if end <= start:
            raise InvalidDateRangeError("dates")

class AccommodationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    type: AccommodationType = AccommodationType.HOTEL
    address: Optional[str] = Field(None, max_length=500)
    check_in_date: date
    check_out_date: date
    booking_reference: Optional[str] = Field(None, max_length=100)
    cost: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    currency: Optional[str] = Field(default="USD", pattern=r'^[A-Z]{3}$')
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='after')
    def check_dates(self):
        validate_date_range(self.check_in_date, self.check_out_date)
        return self

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
    currency: Optional[str] = Field(None, pattern=r'^[A-Z]{3}$')
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='after')
    def check_dates(self):
        validate_date_range(self.check_in_date, self.check_out_date)
        return self

class AccommodationResponse(AccommodationBase):
    id: uuid.UUID
    trip_id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None