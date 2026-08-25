from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from app.common.types import MemberRole
import uuid

from app.schemas.user import UserBase

class TripMemberBase(BaseModel):
    user_id: uuid.UUID
    role: MemberRole = MemberRole.VIEWER
    
    model_config = ConfigDict(from_attributes=True)

class TripMemberCreate(BaseModel):
    email: EmailStr
    role: MemberRole = MemberRole.VIEWER

class TripMemberUpdate(BaseModel):
    role: MemberRole

class TripMemberBudgetUpdate(BaseModel):
    personal_budget: Optional[Decimal] = None

class TripMemberResponse(TripMemberBase):
    id: uuid.UUID
    trip_id: uuid.UUID
    joined_at: datetime
    personal_budget: Optional[Decimal] = None
    user: Optional[UserBase] = None
    
    model_config = ConfigDict(from_attributes=True)