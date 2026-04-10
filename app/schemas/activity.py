from pydantic import BaseModel, Field
from datetime import date, time, datetime
from typing import Optional
from decimal import Decimal
from app.common.types import ActivityCategory
import uuid

class ActivityBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    activity_date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    location: Optional[str] = Field(None, max_length=300)
    address: Optional[str] = Field(None, max_length=500)
    category: ActivityCategory = ActivityCategory.other
    cost: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    notes: Optional[str] = None

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
    notes: Optional[str] = None

class ActivityResponse(ActivityBase):
    id: uuid.UUID
    trip_id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True