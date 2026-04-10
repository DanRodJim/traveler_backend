from sqlalchemy.orm import Session
from app.models.flight import Flight
from app.schemas.flight import FlightCreate, FlightUpdate
from typing import List, Optional
import uuid

class FlightService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_by_trip(self, trip_id: uuid.UUID) -> List[Flight]:
        return self.db.query(Flight).filter(
            Flight.trip_id == trip_id
        ).order_by(Flight.departure_date, Flight.departure_time).all()
    
    def get_by_id(self, flight_id: uuid.UUID) -> Optional[Flight]:
        return self.db.query(Flight).filter(Flight.id == flight_id).first()
    
    def create(self, flight_data: FlightCreate, user_id: uuid.UUID) -> Flight:
        flight = Flight(
            id=uuid.uuid4(),
            created_by=user_id,
            **flight_data.model_dump()
        )
        
        self.db.add(flight)
        self.db.commit()
        self.db.refresh(flight)
        return flight
    
    def update(self, flight_id: uuid.UUID, flight_data: FlightUpdate) -> Optional[Flight]:
        flight = self.get_by_id(flight_id)
        if not flight:
            return None
        
        update_data = flight_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(flight, field, value)
        
        self.db.commit()
        self.db.refresh(flight)
        return flight
    
    def delete(self, flight_id: uuid.UUID) -> bool:
        flight = self.get_by_id(flight_id)
        if not flight:
            return False
        
        self.db.delete(flight)
        self.db.commit()
        return True