from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Literal
import uuid

NotificationType = Literal["invitation", "trip_reminder"]


class NotificationResponse(BaseModel):
    id: uuid.UUID
    type: NotificationType
    title: str
    message: str
    link: Optional[str] = None
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)