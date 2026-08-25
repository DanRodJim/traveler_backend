from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Literal
import uuid


class ChecklistItemCreate(BaseModel):
    list_type: Literal['tasks', 'packing']
    title: str = Field(..., min_length=1, max_length=200)
    is_private: bool = True


class ChecklistItemUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    is_private: Optional[bool] = None


class ChecklistItemToggle(BaseModel):
    is_completed: bool


class ChecklistItemResponse(BaseModel):
    id: uuid.UUID
    trip_id: uuid.UUID
    created_by: uuid.UUID
    list_type: str
    title: str
    is_completed: bool
    is_private: bool
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)