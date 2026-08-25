from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.database.db import get_db
from app.models.user import User
from app.schemas.checklist_item import (
    ChecklistItemCreate,
    ChecklistItemUpdate,
    ChecklistItemToggle,
    ChecklistItemResponse,
)
from app.services.checklist_service import ChecklistService
from app.auth.dependencies import get_current_active_user
from app.common.trip_utils import verify_trip_membership

router = APIRouter(prefix="/api/checklists", tags=["checklists"])


@router.get("/trip/{trip_id}", response_model=List[ChecklistItemResponse])
async def get_checklist_items(
    trip_id: uuid.UUID,
    list_type: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[ChecklistItemResponse]:
    verify_trip_membership(db, trip_id, current_user.id)
    service = ChecklistService(db)
    items = service.get_by_trip(trip_id, current_user.id, list_type)
    return [ChecklistItemResponse.model_validate(item) for item in items]


@router.post(
    "/trip/{trip_id}",
    response_model=ChecklistItemResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_checklist_item(
    trip_id: uuid.UUID,
    item_data: ChecklistItemCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ChecklistItemResponse:
    verify_trip_membership(db, trip_id, current_user.id)
    service = ChecklistService(db)
    item = service.create(trip_id, current_user.id, item_data)
    return ChecklistItemResponse.model_validate(item)


@router.put("/{item_id}", response_model=ChecklistItemResponse)
async def update_checklist_item(
    item_id: uuid.UUID,
    item_data: ChecklistItemUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ChecklistItemResponse:
    service = ChecklistService(db)
    item = service.update(item_id, current_user.id, item_data)
    return ChecklistItemResponse.model_validate(item)


@router.patch("/{item_id}/toggle", response_model=ChecklistItemResponse)
async def toggle_checklist_item(
    item_id: uuid.UUID,
    toggle_data: ChecklistItemToggle,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ChecklistItemResponse:
    service = ChecklistService(db)
    item = service.toggle(item_id, current_user.id, toggle_data.is_completed)
    return ChecklistItemResponse.model_validate(item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_checklist_item(
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> None:
    service = ChecklistService(db)
    service.delete(item_id, current_user.id)