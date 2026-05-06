from pydantic import BaseModel, Field, model_validator, ConfigDict
from datetime import date, datetime
from typing import Optional
from decimal import Decimal
from app.common.types import TripStatus
import uuid

from app.core.exceptions import InvalidDateRangeError

def validate_date_range(start: Optional[date], end: Optional[date]) -> None:
    if start is not None and end is not None:
        if end <= start:
            raise InvalidDateRangeError("dates")

class TripBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    destination: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    start_date: date
    end_date: date
    budget: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    currency: Optional[str] = Field(default="USD", pattern=r'^[A-Z]{3}$')
    status: TripStatus = TripStatus.PLANNING

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='after')
    def check_dates(self):
        validate_date_range(self.start_date, self.end_date)
        return self

class TripCreate(TripBase):
    pass

class TripUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    destination: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    currency: Optional[str] = Field(None, pattern=r'^[A-Z]{3}$')
    status: Optional[TripStatus] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='after')
    def check_dates(self):
        validate_date_range(self.start_date, self.end_date)
        return self

class TripResponse(TripBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None