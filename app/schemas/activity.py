from pydantic import BaseModel, Field, model_validator, ConfigDict
from datetime import date, time, datetime
from typing import Optional, List
from decimal import Decimal
from app.common.types import ActivityCategory
import uuid

from app.core.exceptions import InvalidTimeRangeError


def validate_time_range(start: Optional[time], end: Optional[time]) -> None:
    if (start is not None and end is not None) and (end <= start):
        raise InvalidTimeRangeError("times")


# ── ActivitySplit schemas ────────────────────────────────────────────────────

class ActivitySplitCreate(BaseModel):
    user_id: uuid.UUID
    amount: Decimal = Field(..., gt=0, decimal_places=2)


class ActivitySplitResponse(BaseModel):
    id: uuid.UUID
    activity_id: uuid.UUID
    user_id: uuid.UUID
    amount: Decimal
    is_paid: bool = False
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ── Activity schemas ──────────────────────────────────────────────────────────

class ActivityBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    activity_date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    location: Optional[str] = Field(None, max_length=300)
    address: Optional[str] = Field(None, max_length=500)
    category: ActivityCategory = ActivityCategory.OTHER
    cost: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    currency: Optional[str] = Field(default="USD", pattern=r'^[A-Z]{3}$')
    notes: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    paid_by: Optional[uuid.UUID] = None
    is_private: bool = True

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='after')
    def check_times(self):
        validate_time_range(self.start_time, self.end_time)
        return self


class ActivityCreate(ActivityBase):
    trip_id: uuid.UUID
    splits: Optional[List[ActivitySplitCreate]] = None

    @model_validator(mode='after')
    def validate_paid_by_with_splits(self):
        if self.splits and not self.paid_by:
            raise ValueError("paid_by is required when splits are provided")
        return self


class ActivityUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    activity_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    location: Optional[str] = Field(None, max_length=300)
    address: Optional[str] = Field(None, max_length=500)
    category: Optional[ActivityCategory] = None
    cost: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    currency: Optional[str] = Field(None, pattern=r'^[A-Z]{3}$')
    notes: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    paid_by: Optional[uuid.UUID] = None
    is_private: Optional[bool] = None
    splits: Optional[List[ActivitySplitCreate]] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='after')
    def check_times(self):
        validate_time_range(self.start_time, self.end_time)
        return self

    @model_validator(mode='after')
    def validate_paid_by_with_splits(self):
        if self.splits and not self.paid_by:
            raise ValueError("paid_by is required when splits are provided")
        return self


class ActivityResponse(ActivityBase):
    id: uuid.UUID
    trip_id: uuid.UUID
    created_by: uuid.UUID
    splits: List[ActivitySplitResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None