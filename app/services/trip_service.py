from sqlalchemy.orm import Session
from app.models.trip import Trip, TripMember, MemberRole
from app.schemas.trip import TripCreate, TripUpdate, TripMemberCreate
from typing import List, Optional
import uuid
from app.core.exceptions import (
    NotTripOwnerError,
    DuplicateResourceError,
    ResourceNotFoundError
)

class TripService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_by_user(self, user_id: uuid.UUID) -> List[Trip]:
        owned_trips = self.db.query(Trip).filter(Trip.owner_id == user_id).all()
        
        memberships = self.db.query(TripMember).filter(TripMember.user_id == user_id).all()
        member_trips = [m.trip for m in memberships]
        
        # Owner + members, no duplicates
        all_trips = {trip.id: trip for trip in owned_trips + member_trips}
        return list(all_trips.values())
    
    def get_by_id(self, trip_id: uuid.UUID) -> Optional[Trip]:
        return self.db.query(Trip).filter(Trip.id == trip_id).first()
    
    def create(self, trip_data: TripCreate, owner_id: uuid.UUID) -> Trip:
        trip = Trip(
            id=uuid.uuid4(),
            owner_id=owner_id,
            **trip_data.model_dump()
        )
        
        self.db.add(trip)
        self.db.commit()
        self.db.refresh(trip)
        return trip
    
    # Only owner or editor
    def update(self, trip_id: uuid.UUID, trip_data: TripUpdate, user_id: uuid.UUID) -> Optional[Trip]:
        trip = self.get_by_id(trip_id)
        if not trip:
            return None
        
        if not self.has_edit_permission(trip_id, user_id):
            return None
        
        update_data = trip_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(trip, field, value)
        
        self.db.commit()
        self.db.refresh(trip)
        return trip
    
    # Only owner
    def delete(self, trip_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        trip = self.get_by_id(trip_id)
        if not trip:
            return False
        
        if trip.owner_id != user_id:
            return False
        
        self.db.delete(trip)
        self.db.commit()
        return True
    

    # Trip Members

    # Only owner
    def add_member(self, trip_id: uuid.UUID, member_data: TripMemberCreate, owner_id: uuid.UUID) -> TripMember:
        trip = self.get_by_id(trip_id)
        
        if not trip or trip.owner_id != owner_id:
            raise NotTripOwnerError()
        
        existing = self.db.query(TripMember).filter(
            TripMember.trip_id == trip_id,
            TripMember.user_id == member_data.user_id
        ).first()
        
        if existing:
            raise DuplicateResourceError("Member")
        
        member = TripMember(
            id=uuid.uuid4(),
            trip_id=trip_id,
            **member_data.model_dump()
        )
        
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member

    def update_member_role(
        self,
        trip_id: uuid.UUID,
        user_id: uuid.UUID,
        new_role: MemberRole,
        owner_id: uuid.UUID
    ) -> TripMember:
        trip = self.get_by_id(trip_id)
        
        if not trip or trip.owner_id != owner_id:
            raise NotTripOwnerError()
        
        if user_id == owner_id:
            raise NotTripOwnerError()
        
        member = self.db.query(TripMember).filter(
            TripMember.trip_id == trip_id,
            TripMember.user_id == user_id
        ).first()
        
        if not member:
            raise ResourceNotFoundError("Member")
        
        member.role = new_role
        
        self.db.commit()
        self.db.refresh(member)
        return member

    def remove_member(self, trip_id: uuid.UUID, user_id: uuid.UUID, owner_id: uuid.UUID) -> bool:
        trip = self.get_by_id(trip_id)
        
        if not trip or trip.owner_id != owner_id:
            raise NotTripOwnerError()
        
        member = self.db.query(TripMember).filter(
            TripMember.trip_id == trip_id,
            TripMember.user_id == user_id
        ).first()
        
        if not member:
            raise ResourceNotFoundError("Member")
        
        self.db.delete(member)
        self.db.commit()
        return True
    
    def get_members(self, trip_id: uuid.UUID) -> List[TripMember]:
        return self.db.query(TripMember).filter(TripMember.trip_id == trip_id).all()
    

    # Permissions

    def has_edit_permission(self, trip_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        trip = self.get_by_id(trip_id)
        if not trip:
            return False
        
        if trip.owner_id == user_id:
            return True
        
        member = self.db.query(TripMember).filter(
            TripMember.trip_id == trip_id,
            TripMember.user_id == user_id
        ).first()
        
        if member is None:
            return False
        
        return member.role == MemberRole.editor
    
    def has_view_permission(self, trip_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        trip = self.get_by_id(trip_id)
        if not trip:
            return False
        
        if trip.owner_id == user_id:
            return True
        
        member = self.db.query(TripMember).filter(
            TripMember.trip_id == trip_id,
            TripMember.user_id == user_id
        ).first()
        
        return member is not None