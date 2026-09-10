from datetime import datetime, timezone
from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.core.exceptions import (
    InvalidDateRangeError,
    AccommodationNotFoundError,
    AccommodationSplitNotFoundError,
    UnauthorizedError,
)
from app.models.accommodation import Accommodation, AccommodationSplit
from app.schemas.accommodation import AccommodationCreate, AccommodationUpdate
from app.services.geocoding_service import geocode_address


class AccommodationService:
    def __init__(self, db: Session):
        self.db = db

    def _get_visible_accommodations_query(self, trip_id: uuid.UUID, current_user_id: uuid.UUID):
        public = self.db.query(Accommodation).filter(
            Accommodation.trip_id == trip_id, Accommodation.is_private == False
        )
        private = (
            self.db.query(Accommodation)
            .outerjoin(AccommodationSplit, AccommodationSplit.accommodation_id == Accommodation.id)
            .filter(
                Accommodation.trip_id == trip_id,
                Accommodation.is_private == True,
                or_(
                    Accommodation.paid_by == current_user_id,
                    Accommodation.created_by == current_user_id,
                    AccommodationSplit.user_id == current_user_id,
                ),
            )
        )
        return public, private

    def get_all_by_trip(self, trip_id: uuid.UUID, current_user_id: uuid.UUID) -> List[Accommodation]:
        public, private = self._get_visible_accommodations_query(trip_id, current_user_id)
        return sorted({a.id: a for a in public.all() + private.distinct().all()}.values(), key=lambda a: a.check_in_date)

    def _get_raw_by_id(self, accommodation_id: uuid.UUID) -> Optional[Accommodation]:
        return self.db.query(Accommodation).filter(Accommodation.id == accommodation_id).first()

    def get_by_id(self, accommodation_id: uuid.UUID, current_user_id: uuid.UUID) -> Optional[Accommodation]:
        acc = self._get_raw_by_id(accommodation_id)
        if not acc:
            return None
        if not acc.is_private:
            return acc

        is_visible = (
            acc.paid_by == current_user_id
            or acc.created_by == current_user_id
            or any(s.user_id == current_user_id for s in acc.splits)
        )
        return acc if is_visible else None

    async def create_with_splits(
        self, accommodation_data: AccommodationCreate, created_by: uuid.UUID
    ) -> Accommodation:
        accommodation_dict = accommodation_data.model_dump(exclude={'splits'})

        if accommodation_dict.get('address') and not accommodation_dict.get('latitude'):
                    coords = await geocode_address(accommodation_dict['address'])
                    if coords:
                        accommodation_dict['latitude'] = coords[0]
                        accommodation_dict['longitude'] = coords[1]

        accommodation = Accommodation(
            id=uuid.uuid4(),
            created_by=created_by,
            **accommodation_dict
        )

        self.db.add(accommodation)
        self.db.flush()

        if accommodation_data.splits:
            for split_data in accommodation_data.splits:
                is_payer = split_data.user_id == accommodation_data.paid_by

                split = AccommodationSplit(
                    accommodation_id=accommodation.id,
                    user_id=split_data.user_id,
                    amount=split_data.amount,
                    is_paid=is_payer,
                    paid_at=datetime.now(timezone.utc) if is_payer else None,
                )
                self.db.add(split)

        self.db.commit()
        self.db.refresh(accommodation)
        return accommodation

    async def create(self, accommodation_data: AccommodationCreate, created_by: uuid.UUID) -> Accommodation:
        return await self.create_with_splits(accommodation_data, created_by)

    async def update_with_splits(
        self, accommodation_id: uuid.UUID, accommodation_data: AccommodationUpdate
    ) -> Optional[Accommodation]:
        accommodation = self._get_raw_by_id(accommodation_id)
        if not accommodation:
            return None

        update_dict = accommodation_data.model_dump(exclude={'splits'}, exclude_unset=True)

        if 'address' in update_dict and update_dict['address'] and 'latitude' not in update_dict:
                    coords = await geocode_address(update_dict['address'])
                    if coords:
                        update_dict['latitude'] = coords[0]
                        update_dict['longitude'] = coords[1]

        new_start = update_dict.get("check_in_date", accommodation.check_in_date)
        new_end = update_dict.get("check_out_date", accommodation.check_out_date)
        if new_start and new_end and new_end <= new_start:
            raise InvalidDateRangeError("dates")

        for field, value in update_dict.items():
            setattr(accommodation, field, value)

        if accommodation_data.splits is not None:
            self.db.query(AccommodationSplit).filter(
                AccommodationSplit.accommodation_id == accommodation_id
            ).delete()

            paid_by = accommodation_data.paid_by or accommodation.paid_by

            for split_data in accommodation_data.splits:
                is_payer = split_data.user_id == paid_by

                split = AccommodationSplit(
                    accommodation_id=accommodation.id,
                    user_id=split_data.user_id,
                    amount=split_data.amount,
                    is_paid=is_payer,
                    paid_at=datetime.now(timezone.utc) if is_payer else None,
                )
                self.db.add(split)

        self.db.commit()
        self.db.refresh(accommodation)
        return accommodation

    async def update(self, accommodation_id: uuid.UUID, accommodation_data: AccommodationUpdate) -> Optional[Accommodation]:
        return await self.update_with_splits(accommodation_id, accommodation_data)

    def delete(self, accommodation_id: uuid.UUID) -> bool:
        accommodation = self._get_raw_by_id(accommodation_id)
        if not accommodation:
            return False

        self.db.delete(accommodation)
        self.db.commit()
        return True

    def mark_split_as_paid(
        self, accommodation_id: uuid.UUID, split_id: uuid.UUID, current_user_id: uuid.UUID
    ) -> AccommodationSplit:
        accommodation = self._get_raw_by_id(accommodation_id)
        if not accommodation:
            raise AccommodationNotFoundError()

        if accommodation.paid_by != current_user_id:
            raise UnauthorizedError("Only the payer can mark splits as paid")

        split = (
            self.db.query(AccommodationSplit)
            .filter(AccommodationSplit.id == split_id, AccommodationSplit.accommodation_id == accommodation_id)
            .first()
        )
        if not split:
            raise AccommodationSplitNotFoundError()

        split.is_paid = True
        split.paid_at = datetime.now(timezone.utc)
        split.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(split)
        return split

    def unmark_split_as_paid(
        self, accommodation_id: uuid.UUID, split_id: uuid.UUID, current_user_id: uuid.UUID
    ) -> AccommodationSplit:
        accommodation = self._get_raw_by_id(accommodation_id)
        if not accommodation:
            raise AccommodationNotFoundError()

        if accommodation.paid_by != current_user_id:
            raise UnauthorizedError("Only the payer can unmark splits as paid")

        split = (
            self.db.query(AccommodationSplit)
            .filter(AccommodationSplit.id == split_id, AccommodationSplit.accommodation_id == accommodation_id)
            .first()
        )
        if not split:
            raise AccommodationSplitNotFoundError()

        split.is_paid = False
        split.paid_at = None
        split.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(split)
        return split