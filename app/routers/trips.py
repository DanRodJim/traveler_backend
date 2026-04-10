from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.database.db import get_db
from app.schemas.trip import (
    TripCreate, TripUpdate, TripResponse,
    TripMemberCreate, TripMemberUpdate, TripMemberResponse
)
from app.services.trip_service import TripService
from app.auth.dependencies import get_current_active_user
from app.models.user import User
from app.models.trip import Trip, TripMember
from app.core.exceptions import (
    TripNotFoundError,
    UnauthorizedError
)

router = APIRouter(prefix="/api/trips", tags=["trips"])

@router.get("/", response_model=List[TripResponse])
async def get_all_trips(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[TripResponse]:
    service = TripService(db)
    trips: List[Trip] = service.get_all_by_user(current_user.id)
    return [TripResponse.model_validate(trip) for trip in trips]


@router.get("/{trip_id}", response_model=TripResponse)
async def get_trip(
    trip_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> TripResponse:
    service = TripService(db)
    
    trip: Trip | None = service.get_by_id(trip_id)
    if not trip:
        raise TripNotFoundError()
    
    if not service.has_view_permission(trip_id, current_user.id):
        raise UnauthorizedError("Not authorized to view this trip")
    
    return TripResponse.model_validate(trip)


@router.post("/", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
async def create_trip(
    trip_data: TripCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> TripResponse:
    service = TripService(db)
    trip: Trip = service.create(trip_data, current_user.id)
    return TripResponse.model_validate(trip)


@router.put("/{trip_id}", response_model=TripResponse)
async def update_trip(
    trip_id: uuid.UUID,
    trip_data: TripUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> TripResponse:
    service = TripService(db)
    
    trip: Trip | None = service.update(trip_id, trip_data, current_user.id)
    if not trip:
        raise TripNotFoundError()
    
    return TripResponse.model_validate(trip)


@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trip(
    trip_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> None:
    service = TripService(db)
    
    if not service.delete(trip_id, current_user.id):
        raise TripNotFoundError()


# --- Trip Members ---

@router.get("/{trip_id}/members", response_model=List[TripMemberResponse])
async def get_trip_members(
    trip_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[TripMemberResponse]:
    service = TripService(db)
    
    if not service.has_view_permission(trip_id, current_user.id):
        raise UnauthorizedError("Not authorized to view this trip")
    
    members: List[TripMember] = service.get_members(trip_id)
    return [TripMemberResponse.model_validate(member) for member in members]


@router.post("/{trip_id}/members", response_model=TripMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_trip_member(
    trip_id: uuid.UUID,
    member_data: TripMemberCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> TripMemberResponse:
    service = TripService(db)
    
    member: TripMember = service.add_member(trip_id, member_data, current_user.id)
    return TripMemberResponse.model_validate(member)


@router.put("/{trip_id}/members/{user_id}", response_model=TripMemberResponse)
async def update_trip_member_role(
    trip_id: uuid.UUID,
    user_id: uuid.UUID,
    member_data: TripMemberUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> TripMemberResponse:
    service = TripService(db)
    
    member: TripMember = service.update_member_role(
        trip_id=trip_id,
        user_id=user_id,
        new_role=member_data.role,
        owner_id=current_user.id
    )
    
    return TripMemberResponse.model_validate(member)


@router.delete("/{trip_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_trip_member(
    trip_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> None:
    service = TripService(db)
    service.remove_member(trip_id, user_id, current_user.id)