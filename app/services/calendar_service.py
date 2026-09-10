from typing import List, Dict
import uuid

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.trip import Trip
from app.models.activity import Activity, ActivitySplit
from app.models.flight import Flight, FlightSplit
from app.models.accommodation import Accommodation, AccommodationSplit


class CalendarService:
    def __init__(self, db: Session):
        self.db = db

    def _visible(self, model, split_model, split_fk, trip_ids: List[uuid.UUID], current_user_id: uuid.UUID):
        public = self.db.query(model).filter(
            model.trip_id.in_(trip_ids), model.is_private == False
        )
        private = (
            self.db.query(model)
            .outerjoin(split_model, getattr(split_model, split_fk) == model.id)
            .filter(
                model.trip_id.in_(trip_ids),
                model.is_private == True,
                or_(
                    model.paid_by == current_user_id,
                    model.created_by == current_user_id,
                    split_model.user_id == current_user_id,
                ),
            )
        )
        return list({item.id: item for item in public.all() + private.distinct().all()}.values())

    def get_events(self, trip_ids: List[uuid.UUID], current_user_id: uuid.UUID) -> List[Dict]:
        events: List[Dict] = []

        trips = {
            t.id: t.title
            for t in self.db.query(Trip).filter(Trip.id.in_(trip_ids)).all()
        }

        flights = self._visible(Flight, FlightSplit, "flight_id", trip_ids, current_user_id)
        for flight in flights:
            events.append({
                "id": f"flight-{flight.id}",
                "type": "flight",
                "title": f"{flight.departure_airport} → {flight.arrival_airport}",
                "date": flight.departure_date.isoformat(),
                "end_date": None,
                "time": flight.departure_time.strftime("%H:%M") if flight.departure_time else None,
                "trip_id": str(flight.trip_id),
                "trip_title": trips.get(flight.trip_id, ""),
                "item_id": str(flight.id),
            })

        accommodations = self._visible(Accommodation, AccommodationSplit, "accommodation_id", trip_ids, current_user_id)
        for acc in accommodations:
            events.append({
                "id": f"accommodation-{acc.id}",
                "type": "accommodation",
                "title": acc.name,
                "date": acc.check_in_date.isoformat(),
                "end_date": acc.check_out_date.isoformat(),
                "time": None,
                "trip_id": str(acc.trip_id),
                "trip_title": trips.get(acc.trip_id, ""),
                "item_id": str(acc.id),
            })

        activities = self._visible(Activity, ActivitySplit, "activity_id", trip_ids, current_user_id)
        for activity in activities:
            events.append({
                "id": f"activity-{activity.id}",
                "type": "activity",
                "title": activity.title,
                "date": activity.activity_date.isoformat(),
                "end_date": None,
                "time": activity.start_time.strftime("%H:%M") if activity.start_time else None,
                "trip_id": str(activity.trip_id),
                "trip_title": trips.get(activity.trip_id, ""),
                "item_id": str(activity.id),
            })

        return events