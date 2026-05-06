from sqlalchemy.orm import Session
from app.core.exceptions import InvalidDateRangeError
from app.models.accommodation import Accommodation
from app.schemas.accommodation import AccommodationCreate, AccommodationUpdate
from typing import List, Optional
import uuid

class AccommodationService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_by_trip(self, trip_id: uuid.UUID) -> List[Accommodation]:
        return self.db.query(Accommodation).filter(
            Accommodation.trip_id == trip_id
        ).order_by(Accommodation.check_in_date).all()
    
    def get_by_id(self, accommodation_id: uuid.UUID) -> Accommodation:
        return self.db.query(Accommodation).filter(Accommodation.id == accommodation_id).first()
    
    def create(self, accommodation_data: AccommodationCreate, user_id: uuid.UUID) -> Accommodation:
        accommodation = Accommodation(
            id=uuid.uuid4(),
            created_by=user_id,
            **accommodation_data.model_dump()
        )
        
        self.db.add(accommodation)
        self.db.commit()
        self.db.refresh(accommodation)
        return accommodation
    
    def update(self, accommodation_id: uuid.UUID, accommodation_data: AccommodationUpdate) -> Optional[Accommodation]:
        accommodation = self.get_by_id(accommodation_id)
        if not accommodation:
            return None
        
        update_data = accommodation_data.model_dump(exclude_unset=True)

        new_start = update_data.get("check_in_date", accommodation.check_in_date)
        new_end = update_data.get("check_out_date", accommodation.check_out_date)
        
        if new_start and new_end and new_end <= new_start:
            raise InvalidDateRangeError("dates")
        
        for field, value in update_data.items():
            setattr(accommodation, field, value)
        
        self.db.commit()
        self.db.refresh(accommodation)
        return accommodation
    
    def delete(self, accommodation_id: uuid.UUID) -> bool:
        accommodation = self.get_by_id(accommodation_id)
        if not accommodation:
            return False
        
        self.db.delete(accommodation)
        self.db.commit()
        return True