from typing import List, Dict
import uuid

from sqlalchemy.orm import Session

from app.models.trip import Trip
from app.models.activity import Activity
from app.models.flight import Flight
from app.models.accommodation import Accommodation


class CalendarService:
    def __init__(self, db: Session):
        self.db = db

    def get_events(self, trip_ids: List[uuid.UUID]) -> List[Dict]:
        events: List[Dict] = []

        trips = {
            t.id: t.title
            for t in self.db.query(Trip).filter(Trip.id.in_(trip_ids)).all()
        }

        # Flights
        flights = (
            self.db.query(Flight)
            .filter(Flight.trip_id.in_(trip_ids))
            .all()
        )
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

        # Accommodations — range event (check-in to check-out)
        accommodations = (
            self.db.query(Accommodation)
            .filter(Accommodation.trip_id.in_(trip_ids))
            .all()
        )
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

        # Activities
        activities = (
            self.db.query(Activity)
            .filter(Activity.trip_id.in_(trip_ids))
            .all()
        )
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