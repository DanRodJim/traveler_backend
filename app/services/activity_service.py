from sqlalchemy.orm import Session
from app.models.activity import Activity
from app.schemas.activity import ActivityCreate, ActivityUpdate
from typing import List, Optional
import uuid
from datetime import datetime

class ActivityService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_by_trip(self, trip_id: uuid.UUID) -> List[Activity]:
        return self.db.query(Activity).filter(
            Activity.trip_id == trip_id
        ).order_by(Activity.start_time).all()
    
    def get_by_date(self, trip_id: uuid.UUID, activity_date: str) -> List[Activity]:
        date_obj = datetime.fromisoformat(activity_date).date()
        
        return self.db.query(Activity).filter(
            Activity.trip_id == trip_id,
            Activity.activity_date == date_obj
        ).order_by(Activity.start_time).all()
    
    def get_by_id(self, activity_id: uuid.UUID) -> Optional[Activity]:
        """Obtener actividad por ID"""
        return self.db.query(Activity).filter(Activity.id == activity_id).first()
    
    def create(self, activity_data: ActivityCreate, user_id: uuid.UUID) -> Activity:
        activity = Activity(
            id=uuid.uuid4(),
            created_by=user_id,
            **activity_data.model_dump()
        )
        
        self.db.add(activity)
        self.db.commit()
        self.db.refresh(activity)
        return activity
    
    def update(self, activity_id: uuid.UUID, activity_data: ActivityUpdate) -> Optional[Activity]:
        activity = self.get_by_id(activity_id)
        if not activity:
            return None
        
        update_data = activity_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(activity, field, value)
        
        self.db.commit()
        self.db.refresh(activity)
        return activity
    
    def delete(self, activity_id: uuid.UUID) -> bool:
        activity = self.get_by_id(activity_id)
        if not activity:
            return False
        
        self.db.delete(activity)
        self.db.commit()
        return True