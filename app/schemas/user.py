from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Optional, Literal
import uuid

EmailNotificationPreference = Literal["none", "invitations_only", "alerts_only", "all"]


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)

    model_config = ConfigDict(from_attributes=True)


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    password: Optional[str] = Field(None, min_length=6)
    email_notification_preference: Optional[EmailNotificationPreference] = None

    model_config = ConfigDict(from_attributes=True)


class PasswordChange(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6)


class NotificationPreferenceUpdate(BaseModel):
    email_notification_preference: EmailNotificationPreference


class UserResponse(UserBase):
    id: uuid.UUID
    is_active: bool
    email_notification_preference: EmailNotificationPreference
    created_at: datetime
    updated_at: Optional[datetime] = None


class UserInDB(UserResponse):
    hashed_password: str