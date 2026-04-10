from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional
from decimal import Decimal
from app.common.types import TripStatus, MemberRole
import uuid

class TripBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    destination: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    start_date: date
    end_date: date
    budget: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    currency: str = Field(default="USD", pattern=r'^[A-Z]{3}$')
    status: TripStatus = TripStatus.planning

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

class TripResponse(TripBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Trip Members
class TripMemberBase(BaseModel):
    user_id: uuid.UUID
    role: MemberRole = MemberRole.viewer

class TripMemberCreate(TripMemberBase):
    pass

class TripMemberUpdate(BaseModel):
    role: MemberRole

class TripMemberResponse(TripMemberBase):
    id: uuid.UUID
    trip_id: uuid.UUID
    joined_at: datetime
    
    class Config:
        from_attributes = True