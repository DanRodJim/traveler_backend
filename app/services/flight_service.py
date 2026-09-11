from datetime import datetime, timezone, time
from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.models.flight import Flight, FlightSplit
from app.schemas.flight import FlightCreate, FlightUpdate
from app.core.exceptions import FlightNotFoundError, UnauthorizedError, FlightSplitNotFoundError


class FlightService:
    def __init__(self, db: Session):
        self.db = db

    def _get_visible_flights_query(self, trip_id: uuid.UUID, current_user_id: uuid.UUID):
        public = self.db.query(Flight).filter(
            Flight.trip_id == trip_id, Flight.is_private == False
        )
        private = (
            self.db.query(Flight)
            .outerjoin(FlightSplit, FlightSplit.flight_id == Flight.id)
            .filter(
                Flight.trip_id == trip_id,
                Flight.is_private == True,
                or_(
                    Flight.paid_by == current_user_id,
                    Flight.created_by == current_user_id,
                    FlightSplit.user_id == current_user_id,
                ),
            )
        )
        return public, private

    def get_all_by_trip(self, trip_id: uuid.UUID, current_user_id: uuid.UUID) -> List[Flight]:
        public, private = self._get_visible_flights_query(trip_id, current_user_id)
        flights = {f.id: f for f in public.all() + private.distinct().all()}.values()
        return sorted(
            flights,
            key=lambda f: (f.departure_date, f.departure_time or time.min)
        )

    def get_raw_by_id(self, flight_id: uuid.UUID) -> Optional[Flight]:
        """Unfiltered lookup by primary key. Only for internal/authorized use
        (create/update/delete, payer actions) where visibility filtering
        either doesn't apply or is enforced separately (edit permission,
        payer check). Do NOT use this to serve flight data to a viewer."""
        return self.db.query(Flight).filter(Flight.id == flight_id).first()

    def get_by_id(self, flight_id: uuid.UUID, current_user_id: uuid.UUID) -> Optional[Flight]:
        """Visibility-checked lookup. Returns None if the flight doesn't
        exist OR if it's private and the requesting user is not the
        creator, payer, or a split participant."""
        flight = self.get_raw_by_id(flight_id)
        if not flight:
            return None
        if not flight.is_private:
            return flight

        is_visible = (
            flight.paid_by == current_user_id
            or flight.created_by == current_user_id
            or any(s.user_id == current_user_id for s in flight.splits)
        )
        return flight if is_visible else None

    def create_with_splits(self, flight_data: FlightCreate, created_by: uuid.UUID) -> Flight:
        flight_dict = flight_data.model_dump(exclude={'splits'})
        flight = Flight(
            id=uuid.uuid4(),
            created_by=created_by,
            **flight_dict
        )

        self.db.add(flight)
        self.db.flush()

        if flight_data.splits:
            for split_data in flight_data.splits:
                is_payer = split_data.user_id == flight_data.paid_by

                split = FlightSplit(
                    flight_id=flight.id,
                    user_id=split_data.user_id,
                    amount=split_data.amount,
                    is_paid=is_payer,
                    paid_at=datetime.now(timezone.utc) if is_payer else None,
                )
                self.db.add(split)

        self.db.commit()
        self.db.refresh(flight)
        return flight

    def create(self, flight_data: FlightCreate, created_by: uuid.UUID) -> Flight:
        return self.create_with_splits(flight_data, created_by)

    def update_with_splits(
        self,
        flight_id: uuid.UUID,
        flight_data: FlightUpdate
    ) -> Optional[Flight]:
        flight = self.get_raw_by_id(flight_id)
        if not flight:
            return None

        update_dict = flight_data.model_dump(exclude={'splits'}, exclude_unset=True)
        for field, value in update_dict.items():
            setattr(flight, field, value)

        if flight_data.splits is not None:
            self.db.query(FlightSplit).filter(
                FlightSplit.flight_id == flight_id
            ).delete()

            paid_by = flight_data.paid_by or flight.paid_by

            for split_data in flight_data.splits:
                is_payer = split_data.user_id == paid_by

                split = FlightSplit(
                    flight_id=flight.id,
                    user_id=split_data.user_id,
                    amount=split_data.amount,
                    is_paid=is_payer,
                    paid_at=datetime.now(timezone.utc) if is_payer else None,
                )
                self.db.add(split)

        self.db.commit()
        self.db.refresh(flight)
        return flight

    def update(self, flight_id: uuid.UUID, flight_data: FlightUpdate) -> Optional[Flight]:
        return self.update_with_splits(flight_id, flight_data)

    def delete(self, flight_id: uuid.UUID) -> bool:
        flight = self.get_raw_by_id(flight_id)
        if not flight:
            return False

        self.db.delete(flight)
        self.db.commit()
        return True

    def mark_split_as_paid(
        self,
        flight_id: uuid.UUID,
        split_id: uuid.UUID,
        current_user_id: uuid.UUID
    ) -> FlightSplit:
        flight = self.get_raw_by_id(flight_id)
        if not flight:
            raise FlightNotFoundError()

        if flight.paid_by != current_user_id:
            raise UnauthorizedError("Only the payer can mark splits as paid")

        split = (
            self.db.query(FlightSplit)
            .filter(FlightSplit.id == split_id, FlightSplit.flight_id == flight_id)
            .first()
        )
        if not split:
            raise FlightSplitNotFoundError()

        split.is_paid = True
        split.paid_at = datetime.now(timezone.utc)
        split.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(split)
        return split

    def unmark_split_as_paid(
        self,
        flight_id: uuid.UUID,
        split_id: uuid.UUID,
        current_user_id: uuid.UUID
    ) -> FlightSplit:
        flight = self.get_raw_by_id(flight_id)
        if not flight:
            raise FlightNotFoundError()

        if flight.paid_by != current_user_id:
            raise UnauthorizedError("Only the payer can unmark splits as paid")

        split = (
            self.db.query(FlightSplit)
            .filter(FlightSplit.id == split_id, FlightSplit.flight_id == flight_id)
            .first()
        )
        if not split:
            raise FlightSplitNotFoundError()

        split.is_paid = False
        split.paid_at = None
        split.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(split)
        return split