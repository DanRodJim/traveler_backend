from datetime import datetime, timezone
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.core.exceptions import (
    InvalidTimeRangeError,
    ActivityNotFoundError,
    ActivitySplitNotFoundError,
    UnauthorizedError,
)
from app.models.activity import Activity, ActivitySplit
from app.schemas.activity import ActivityCreate, ActivityUpdate


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
        return self.db.query(Activity).filter(Activity.id == activity_id).first()

    def create_with_splits(self, activity_data: ActivityCreate, created_by: uuid.UUID) -> Activity:
        activity_dict = activity_data.model_dump(exclude={'splits'})
        activity = Activity(
            id=uuid.uuid4(),
            created_by=created_by,
            **activity_dict
        )

        self.db.add(activity)
        self.db.flush()

        if activity_data.splits:
            for split_data in activity_data.splits:
                is_payer = split_data.user_id == activity_data.paid_by

                split = ActivitySplit(
                    activity_id=activity.id,
                    user_id=split_data.user_id,
                    amount=split_data.amount,
                    is_paid=is_payer,
                    paid_at=datetime.now(timezone.utc) if is_payer else None,
                )
                self.db.add(split)

        self.db.commit()
        self.db.refresh(activity)
        return activity

    def create(self, activity_data: ActivityCreate, created_by: uuid.UUID) -> Activity:
        return self.create_with_splits(activity_data, created_by)

    def update_with_splits(
        self, activity_id: uuid.UUID, activity_data: ActivityUpdate
    ) -> Optional[Activity]:
        activity = self.get_by_id(activity_id)
        if not activity:
            return None

        update_dict = activity_data.model_dump(exclude={'splits'}, exclude_unset=True)

        new_start = update_dict.get("start_time", activity.start_time)
        new_end = update_dict.get("end_time", activity.end_time)
        if new_start and new_end and new_end <= new_start:
            raise InvalidTimeRangeError("times")

        for field, value in update_dict.items():
            setattr(activity, field, value)

        if activity_data.splits is not None:
            self.db.query(ActivitySplit).filter(
                ActivitySplit.activity_id == activity_id
            ).delete()

            paid_by = activity_data.paid_by or activity.paid_by

            for split_data in activity_data.splits:
                is_payer = split_data.user_id == paid_by

                split = ActivitySplit(
                    activity_id=activity.id,
                    user_id=split_data.user_id,
                    amount=split_data.amount,
                    is_paid=is_payer,
                    paid_at=datetime.now(timezone.utc) if is_payer else None,
                )
                self.db.add(split)

        self.db.commit()
        self.db.refresh(activity)
        return activity

    def update(self, activity_id: uuid.UUID, activity_data: ActivityUpdate) -> Optional[Activity]:
        return self.update_with_splits(activity_id, activity_data)

    def delete(self, activity_id: uuid.UUID) -> bool:
        activity = self.get_by_id(activity_id)
        if not activity:
            return False

        self.db.delete(activity)
        self.db.commit()
        return True

    def mark_split_as_paid(
        self, activity_id: uuid.UUID, split_id: uuid.UUID, current_user_id: uuid.UUID
    ) -> ActivitySplit:
        activity = self.get_by_id(activity_id)
        if not activity:
            raise ActivityNotFoundError()

        if activity.paid_by != current_user_id:
            raise UnauthorizedError("Only the payer can mark splits as paid")

        split = (
            self.db.query(ActivitySplit)
            .filter(ActivitySplit.id == split_id, ActivitySplit.activity_id == activity_id)
            .first()
        )
        if not split:
            raise ActivitySplitNotFoundError()

        split.is_paid = True
        split.paid_at = datetime.now(timezone.utc)
        split.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(split)
        return split

    def unmark_split_as_paid(
        self, activity_id: uuid.UUID, split_id: uuid.UUID, current_user_id: uuid.UUID
    ) -> ActivitySplit:
        activity = self.get_by_id(activity_id)
        if not activity:
            raise ActivityNotFoundError()

        if activity.paid_by != current_user_id:
            raise UnauthorizedError("Only the payer can unmark splits as paid")

        split = (
            self.db.query(ActivitySplit)
            .filter(ActivitySplit.id == split_id, ActivitySplit.activity_id == activity_id)
            .first()
        )
        if not split:
            raise ActivitySplitNotFoundError()

        split.is_paid = False
        split.paid_at = None
        split.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(split)
        return split