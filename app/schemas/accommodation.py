from pydantic import BaseModel, Field, model_validator, ConfigDict
from datetime import date, datetime
from typing import Optional, List
from decimal import Decimal
from app.common.types import AccommodationType
import uuid

from app.core.exceptions import InvalidDateRangeError


def validate_date_range(start: Optional[date], end: Optional[date]) -> None:
    if (start is not None and end is not None) and (end <= start):
        raise InvalidDateRangeError("dates")


# ── AccommodationSplit schemas ──────────────────────────────────────────────

class AccommodationSplitCreate(BaseModel):
    user_id: uuid.UUID
    amount: Decimal = Field(..., gt=0, decimal_places=2)


class AccommodationSplitResponse(BaseModel):
    id: uuid.UUID
    accommodation_id: uuid.UUID
    user_id: uuid.UUID
    amount: Decimal
    is_paid: bool = False
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ── Accommodation schemas ────────────────────────────────────────────────────

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
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    paid_by: Optional[uuid.UUID] = None
    is_private: bool = True

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='after')
    def check_dates(self):
        validate_date_range(self.check_in_date, self.check_out_date)
        return self


class AccommodationCreate(AccommodationBase):
    trip_id: uuid.UUID
    splits: Optional[List[AccommodationSplitCreate]] = None

    @model_validator(mode='after')
    def validate_paid_by_with_splits(self):
        if self.splits and not self.paid_by:
            raise ValueError("paid_by is required when splits are provided")
        return self


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
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    paid_by: Optional[uuid.UUID] = None
    is_private: Optional[bool] = None
    splits: Optional[List[AccommodationSplitCreate]] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='after')
    def check_dates(self):
        validate_date_range(self.check_in_date, self.check_out_date)
        return self

    @model_validator(mode='after')
    def validate_paid_by_with_splits(self):
        if self.splits and not self.paid_by:
            raise ValueError("paid_by is required when splits are provided")
        return self


class AccommodationResponse(AccommodationBase):
    id: uuid.UUID
    trip_id: uuid.UUID
    created_by: uuid.UUID
    splits: List[AccommodationSplitResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None