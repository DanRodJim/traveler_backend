from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.trip_member import TripMember
import uuid


def verify_trip_membership(
    db: Session,
    trip_id: uuid.UUID,
    user_id: uuid.UUID
) -> None:
    membership = db.query(TripMember).filter(
        TripMember.trip_id == trip_id,
        TripMember.user_id == user_id
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this trip"
        )