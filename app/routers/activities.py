from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.database.db import get_db
from app.schemas.activity import ActivityCreate, ActivityUpdate, ActivityResponse
from app.services.activity_service import ActivityService
from app.services.trip_service import TripService
from app.auth.dependencies import get_current_active_user
from app.models.user import User
from app.models.activity import Activity
from app.core.exceptions import (
    ActivityNotFoundError,
    UnauthorizedError,
    InsufficientPermissionsError
)

router = APIRouter(prefix="/api/activities", tags=["activities"])


@router.get("/", response_model=List[ActivityResponse])
async def get_activities(
    trip_id: uuid.UUID,
    date: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[ActivityResponse]:
    trip_service = TripService(db)
    if not trip_service.has_view_permission(trip_id, current_user.id):
        raise UnauthorizedError("Not authorized to view this trip")
    
    service = ActivityService(db)
    
    if date:
        activities: List[Activity] = service.get_by_date(trip_id, date)
    else:
        activities: List[Activity] = service.get_all_by_trip(trip_id)
    
    return [ActivityResponse.model_validate(activity) for activity in activities]


@router.get("/{activity_id}", response_model=ActivityResponse)
async def get_activity(
    activity_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ActivityResponse:
    service = ActivityService(db)
    activity: Activity | None = service.get_by_id(activity_id)
    
    if not activity:
        raise ActivityNotFoundError()
    
    trip_service = TripService(db)
    if not trip_service.has_view_permission(activity.trip_id, current_user.id):
        raise UnauthorizedError("Not authorized to view this activity")
    
    return ActivityResponse.model_validate(activity)


@router.post("/", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
async def create_activity(
    activity_data: ActivityCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ActivityResponse:
    trip_service = TripService(db)
    if not trip_service.has_edit_permission(activity_data.trip_id, current_user.id):
        raise InsufficientPermissionsError("editor")
    
    service = ActivityService(db)
    activity: Activity = service.create(activity_data, current_user.id)
    
    return ActivityResponse.model_validate(activity)


@router.put("/{activity_id}", response_model=ActivityResponse)
async def update_activity(
    activity_id: uuid.UUID,
    activity_data: ActivityUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ActivityResponse:
    service = ActivityService(db)
    activity: Activity | None = service.get_by_id(activity_id)
    
    if not activity:
        raise ActivityNotFoundError()
    
    trip_service = TripService(db)
    if not trip_service.has_edit_permission(activity.trip_id, current_user.id):
        raise InsufficientPermissionsError("editor")
    
    updated: Activity | None = service.update(activity_id, activity_data)
    if not updated:
        raise ActivityNotFoundError()
    
    return ActivityResponse.model_validate(updated)


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_activity(
    activity_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> None:
    service = ActivityService(db)
    activity: Activity | None = service.get_by_id(activity_id)
    
    if not activity:
        raise ActivityNotFoundError()
    
    trip_service = TripService(db)
    if not trip_service.has_edit_permission(activity.trip_id, current_user.id):
        raise InsufficientPermissionsError("editor")
    
    service.delete(activity_id)