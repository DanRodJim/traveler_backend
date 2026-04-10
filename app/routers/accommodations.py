from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.database.db import get_db
from app.schemas.accommodation import AccommodationCreate, AccommodationUpdate, AccommodationResponse
from app.services.accommodation_service import AccommodationService
from app.services.trip_service import TripService
from app.auth.dependencies import get_current_active_user
from app.models.user import User
from app.models.accommodation import Accommodation
from app.core.exceptions import (
    AccommodationNotFoundError,
    UnauthorizedError,
    InsufficientPermissionsError
)

router = APIRouter(prefix="/api/accommodations", tags=["accommodations"])


@router.get("/", response_model=List[AccommodationResponse])
async def get_accommodations(
    trip_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[AccommodationResponse]:
    trip_service = TripService(db)
    if not trip_service.has_view_permission(trip_id, current_user.id):
        raise UnauthorizedError("Not authorized to view this trip")
    
    service = AccommodationService(db)
    accommodations: List[Accommodation] = service.get_all_by_trip(trip_id)
    
    return [
        AccommodationResponse.model_validate(accommodation)
        for accommodation in accommodations
    ]


@router.get("/{accommodation_id}", response_model=AccommodationResponse)
async def get_accommodation(
    accommodation_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> AccommodationResponse:
    service = AccommodationService(db)
    accommodation: Accommodation | None = service.get_by_id(accommodation_id)
    
    if not accommodation:
        raise AccommodationNotFoundError()
    
    trip_service = TripService(db)
    if not trip_service.has_view_permission(accommodation.trip_id, current_user.id):
        raise UnauthorizedError("Not authorized to view this accommodation")
    
    return AccommodationResponse.model_validate(accommodation)


@router.post("/", response_model=AccommodationResponse, status_code=status.HTTP_201_CREATED)
async def create_accommodation(
    accommodation_data: AccommodationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> AccommodationResponse:
    trip_service = TripService(db)
    if not trip_service.has_edit_permission(accommodation_data.trip_id, current_user.id):
        raise InsufficientPermissionsError("editor")
    
    service = AccommodationService(db)
    accommodation: Accommodation = service.create(accommodation_data, current_user.id)
    
    return AccommodationResponse.model_validate(accommodation)


@router.put("/{accommodation_id}", response_model=AccommodationResponse)
async def update_accommodation(
    accommodation_id: uuid.UUID,
    accommodation_data: AccommodationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> AccommodationResponse:
    service = AccommodationService(db)
    accommodation: Accommodation | None = service.get_by_id(accommodation_id)
    
    if not accommodation:
        raise AccommodationNotFoundError()
    
    trip_service = TripService(db)
    if not trip_service.has_edit_permission(accommodation.trip_id, current_user.id):
        raise InsufficientPermissionsError("editor")
    
    updated: Accommodation | None = service.update(accommodation_id, accommodation_data)
    if not updated:
        raise AccommodationNotFoundError()
    
    return AccommodationResponse.model_validate(updated)


@router.delete("/{accommodation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_accommodation(
    accommodation_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> None:
    service = AccommodationService(db)
    accommodation: Accommodation | None = service.get_by_id(accommodation_id)
    
    if not accommodation:
        raise AccommodationNotFoundError()
    
    trip_service = TripService(db)
    if not trip_service.has_edit_permission(accommodation.trip_id, current_user.id):
        raise InsufficientPermissionsError("editor")
    
    service.delete(accommodation_id)