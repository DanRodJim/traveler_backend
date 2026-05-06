from pydantic import BaseModel, Field, model_validator, ConfigDict
from datetime import date, time, datetime
from typing import Optional
from decimal import Decimal
from app.common.types import ActivityCategory
import uuid

from app.core.exceptions import InvalidTimeRangeError

def validate_time_range(start: Optional[time], end: Optional[time]) -> None:
    if start is not None and end is not None:
        if end <= start:
            raise InvalidTimeRangeError("times")

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

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='after')
    def check_times(self):
        validate_time_range(self.start_time, self.end_time)
        return self

class ActivityCreate(ActivityBase):
    trip_id: uuid.UUID

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

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='after')
    def check_times(self):
        validate_time_range(self.start_time, self.end_time)
        return self

class ActivityResponse(ActivityBase):
    id: uuid.UUID
    trip_id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None