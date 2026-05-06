from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.database.db import get_db
from app.schemas.flight import FlightCreate, FlightUpdate, FlightResponse
from app.services.flight_service import FlightService
from app.services.trip_service import TripService
from app.auth.dependencies import get_current_active_user
from app.models import Flight, User
from app.core.exceptions import (
    FlightNotFoundError,
    UnauthorizedError,
    InsufficientPermissionsError
)

router = APIRouter(prefix="/api/flights", tags=["flights"])


@router.get("/", response_model=List[FlightResponse])
async def get_flights(
    trip_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[FlightResponse]:
    trip_service = TripService(db)
    if not trip_service.has_view_permission(trip_id, current_user.id):
        raise UnauthorizedError("Not authorized to view this trip")
    
    service = FlightService(db)
    flights: List[Flight] = service.get_all_by_trip(trip_id)
    
    return [FlightResponse.model_validate(flight) for flight in flights]


@router.get("/{flight_id}", response_model=FlightResponse)
async def get_flight(
    flight_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> FlightResponse:
    service = FlightService(db)
    flight: Flight | None = service.get_by_id(flight_id)
    
    if not flight:
        raise FlightNotFoundError()
    
    trip_service = TripService(db)
    if not trip_service.has_view_permission(flight.trip_id, current_user.id):
        raise UnauthorizedError("Not authorized to view this flight")
    
    return FlightResponse.model_validate(flight)


@router.post("/", response_model=FlightResponse, status_code=status.HTTP_201_CREATED)
async def create_flight(
    flight_data: FlightCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> FlightResponse:
    trip_service = TripService(db)
    if not trip_service.has_edit_permission(flight_data.trip_id, current_user.id):
        raise InsufficientPermissionsError("editor")
    
    service = FlightService(db)
    flight: Flight = service.create(flight_data, current_user.id)
    
    return FlightResponse.model_validate(flight)


@router.put("/{flight_id}", response_model=FlightResponse)
async def update_flight(
    flight_id: uuid.UUID,
    flight_data: FlightUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> FlightResponse:
    service = FlightService(db)
    flight: Flight | None = service.get_by_id(flight_id)
    
    if not flight:
        raise FlightNotFoundError()
    
    trip_service = TripService(db)
    if not trip_service.has_edit_permission(flight.trip_id, current_user.id):
        raise InsufficientPermissionsError("editor")
    
    updated: Flight | None = service.update(flight_id, flight_data)
    if not updated:
        raise FlightNotFoundError()
    
    return FlightResponse.model_validate(updated)


@router.delete("/{flight_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_flight(
    flight_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> None:
    service = FlightService(db)
    flight: Flight | None = service.get_by_id(flight_id)
    
    if not flight:
        raise FlightNotFoundError()
    
    trip_service = TripService(db)
    if not trip_service.has_edit_permission(flight.trip_id, current_user.id):
        raise InsufficientPermissionsError("editor")
    
    service.delete(flight_id)