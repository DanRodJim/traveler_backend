from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import Literal
import uuid

from app.common.types import InvitationStatus, MemberRole


class TripInvitationCreate(BaseModel):
    email: EmailStr
    role: MemberRole = MemberRole.VIEWER


class TripInvitationResponse(BaseModel):
    id: uuid.UUID
    trip_id: uuid.UUID
    invited_email: str
    invited_by: uuid.UUID
    role: MemberRole
    status: InvitationStatus
    expires_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MyInvitationResponse(BaseModel):
    id: uuid.UUID
    trip_id: uuid.UUID
    trip_title: str
    trip_destination: str
    inviter_name: str
    role: MemberRole
    status: InvitationStatus
    token: str
    expires_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)