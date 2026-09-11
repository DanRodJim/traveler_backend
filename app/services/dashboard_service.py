import uuid
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Iterable, List, Dict, Any
from datetime import datetime, timedelta, time
from app.models import Accommodation, Activity, Expense, ExpenseSplit, Flight, Trip, TripMember
from app.models.accommodation import AccommodationSplit
from app.models.activity import ActivitySplit
from app.models.flight import FlightSplit
from app.services.accommodation_service import AccommodationService
from app.services.activity_service import ActivityService
from app.services.budget_service import BudgetService
from app.services.expense_service import ExpenseService
from app.services.flight_service import FlightService
from app.services.personal_budget_service import PersonalBudgetService


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    _SPLIT_SOURCES = [
        ("expense", Expense, ExpenseSplit, "expense_id", "title"),
        ("flight", Flight, FlightSplit, "flight_id", None),
        ("accommodation", Accommodation, AccommodationSplit, "accommodation_id", "name"),
        ("activity", Activity, ActivitySplit, "activity_id", "title"),
    ]
    
    def get_user_trip_ids(self, user_id: uuid.UUID) -> List[uuid.UUID]:
        trip_ids = self.db.query(TripMember.trip_id).filter(
            TripMember.user_id == user_id
        ).all()
        return [trip_id[0] for trip_id in trip_ids]
    
    def get_trips_by_status(self, trip_ids: List[uuid.UUID]) -> Dict[str, int]:
        trips_by_status = self.db.query(
            Trip.status,
            func.count(Trip.id)
        ).filter(
            Trip.id.in_(trip_ids)
        ).group_by(Trip.status).all()
        
        status_counts = {
            "planning": 0,
            "confirmed": 0,
            "in_progress": 0,
            "completed": 0,
            "cancelled": 0
        }
        
        for status, count in trips_by_status:
            status_counts[status] = count
        
        return status_counts
    
    async def get_total_expenses_by_currency(
        self, trip_ids: List[uuid.UUID], current_user_id: uuid.UUID
    ) -> Dict[str, float]:
        personal_budget_service = PersonalBudgetService(self.db)
        total_expenses_dict: Dict[str, float] = {}

        for trip_id in trip_ids:
            spending = await personal_budget_service.calculate_personal_spending(
                trip_id, current_user_id
            )
            currency = spending["currency"]
            total_expenses_dict[currency] = (
                total_expenses_dict.get(currency, 0) + spending["total_spent"]
            )

        return total_expenses_dict
    
    def get_expenses_by_category(
        self, trip_ids: List[uuid.UUID], current_user_id: uuid.UUID
    ) -> Dict[str, float]:
        expense_service = ExpenseService(self.db)
        category_totals: Dict[str, float] = {}

        for trip_id in trip_ids:
            visible_expenses = expense_service.get_all_by_trip(trip_id, current_user_id)
            for e in visible_expenses:
                category_totals[e.category] = category_totals.get(e.category, 0) + float(e.amount)

        return category_totals


    @staticmethod
    def _sum_cost(items: Iterable, attr: str) -> float:
        return sum(float(getattr(item, attr)) for item in items if getattr(item, attr))

    def get_expenses_by_type(
        self, trip_ids: List[uuid.UUID], current_user_id: uuid.UUID
    ) -> Dict[str, float]:
        expense_service = ExpenseService(self.db)
        activity_service = ActivityService(self.db)
        accommodation_service = AccommodationService(self.db)
        flight_service = FlightService(self.db)

        totals = {
            "Manual Expenses": 0.0,
            "Activities": 0.0,
            "Flights": 0.0,
            "Accommodations": 0.0,
        }

        for trip_id in trip_ids:
            totals["Manual Expenses"] += self._sum_cost(
                expense_service.get_all_by_trip(trip_id, current_user_id), "amount"
            )
            totals["Activities"] += self._sum_cost(
                activity_service.get_all_by_trip(trip_id, current_user_id), "cost"
            )
            totals["Accommodations"] += self._sum_cost(
                accommodation_service.get_all_by_trip(trip_id, current_user_id), "cost"
            )
            totals["Flights"] += self._sum_cost(
                flight_service.get_all_by_trip(trip_id, current_user_id), "cost"
            )

        return {k: v for k, v in totals.items() if v > 0}
    
    async def get_top_trips_by_spending(
        self, trip_ids: list, current_user_id: uuid.UUID, limit: int = 5
    ) -> list:
        trips = self.db.query(Trip).filter(Trip.id.in_(trip_ids)).all()

        personal_budget_service = PersonalBudgetService(self.db)
        results = []

        for trip in trips:
            spending = await personal_budget_service.calculate_personal_spending(
                trip.id, current_user_id
            )
            if spending["total_spent"] > 0:
                results.append({
                    "trip": trip.title,
                    "amount": round(spending["total_spent"], 2),
                })

        results.sort(key=lambda x: x["amount"], reverse=True)
        return results[:limit]
    
    def get_upcoming_activities(
        self,
        trip_ids: List[uuid.UUID],
        current_user_id: uuid.UUID,
        days: int = 7,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        today = datetime.now().date()
        end_date = today + timedelta(days=days)
        activity_service = ActivityService(self.db)
        upcoming_activities: List[Activity] = []
        for trip_id in trip_ids:
            for act in activity_service.get_all_by_trip(trip_id, current_user_id):
                if act.activity_date and today <= act.activity_date <= end_date:
                    upcoming_activities.append(act)

        upcoming_activities.sort(
            key=lambda a: (a.activity_date, a.start_time or time.min)
        )
        upcoming_activities = upcoming_activities[:limit]

        return [
            {
                "id": str(activity.id),
                "title": activity.title,
                "date": activity.activity_date.isoformat(),
                "time": activity.start_time.strftime("%H:%M") if activity.start_time else None,
                "trip_id": str(activity.trip_id),
                "category": activity.category
            }
            for activity in upcoming_activities
        ]
    
    def get_next_trip(self, trip_ids: List[uuid.UUID]) -> Dict[str, Any] | None:
        today = datetime.now().date()
        
        next_trip = self.db.query(Trip).filter(
            Trip.id.in_(trip_ids),
            Trip.start_date >= today,
            Trip.status.in_(['planning', 'confirmed'])
        ).order_by(Trip.start_date).first()
        
        if not next_trip:
            return None
        
        return {
            "id": str(next_trip.id),
            "title": next_trip.title,
            "destination": next_trip.destination,
            "start_date": next_trip.start_date.isoformat(),
            "days_until": (next_trip.start_date - today).days
        }
    
    def get_activities_by_category(
        self, trip_ids: List[uuid.UUID], current_user_id: uuid.UUID
    ) -> Dict[str, int]:
        activity_service = ActivityService(self.db)
        category_counts: Dict[str, int] = {}

        for trip_id in trip_ids:
            for act in activity_service.get_all_by_trip(trip_id, current_user_id):
                category_counts[act.category] = category_counts.get(act.category, 0) + 1

        return category_counts


    def get_accommodations_by_type(
        self, trip_ids: List[uuid.UUID], current_user_id: uuid.UUID
    ) -> Dict[str, int]:
        accommodation_service = AccommodationService(self.db)
        type_counts: Dict[str, int] = {}

        for trip_id in trip_ids:
            for acc in accommodation_service.get_all_by_trip(trip_id, current_user_id):
                type_counts[acc.type] = type_counts.get(acc.type, 0) + 1

        return type_counts

    def _describe_item(self, item_type: str, item) -> str:
        if item_type == "flight":
            return f"{item.departure_airport} → {item.arrival_airport}"
        if item_type == "accommodation":
            return item.name
        return item.title

    def get_pending_splits_owed_by_me(
        self, current_user_id: uuid.UUID, trip_ids: list
    ) -> list:
        results = []

        for item_type, model, split_model, fk_field, _ in self._SPLIT_SOURCES:
            rows = (
                self.db.query(split_model, model, Trip)
                .join(model, getattr(split_model, fk_field) == model.id)
                .join(Trip, model.trip_id == Trip.id)
                .filter(
                    model.trip_id.in_(trip_ids),
                    split_model.user_id == current_user_id,
                    split_model.is_paid == False,
                    model.paid_by != current_user_id,
                )
                .all()
            )

            for split, item, trip in rows:
                results.append({
                    "split_id": str(split.id),
                    "item_type": item_type,
                    "expense_title": self._describe_item(item_type, item),
                    "trip_id": str(trip.id),
                    "trip_title": trip.title,
                    "amount": float(split.amount),
                    "currency": item.currency or "USD",
                    "paid_by": str(item.paid_by),
                })

        return results


    def get_pending_splits_owed_to_me(
        self, current_user_id: uuid.UUID, trip_ids: list
    ) -> list:
        results = []

        for item_type, model, split_model, fk_field, _ in self._SPLIT_SOURCES:
            rows = (
                self.db.query(split_model, model, Trip)
                .join(model, getattr(split_model, fk_field) == model.id)
                .join(Trip, model.trip_id == Trip.id)
                .filter(
                    model.trip_id.in_(trip_ids),
                    model.paid_by == current_user_id,
                    split_model.user_id != current_user_id,
                    split_model.is_paid == False,
                )
                .all()
            )

            for split, item, trip in rows:
                results.append({
                    "split_id": str(split.id),
                    "item_type": item_type,
                    "expense_title": self._describe_item(item_type, item),
                    "trip_id": str(trip.id),
                    "trip_title": trip.title,
                    "amount": float(split.amount),
                    "currency": item.currency or "USD",
                    "owed_by": str(split.user_id),
                })

        return results

    async def get_budget_alerts(self, trip_ids: list) -> list:
        trips = (
            self.db.query(Trip)
            .filter(
                Trip.id.in_(trip_ids),
                Trip.budget.isnot(None),
                Trip.status.notin_(["completed", "cancelled"])
            )
            .all()
        )

        budget_service = BudgetService(self.db)
        alerts = []

        for trip in trips:
            summary = await budget_service.get_trip_budget_summary(trip.id)

            if not summary.get("has_budget"):
                continue

            percentage = summary["percentage"]
            if percentage >= 80:
                alerts.append({
                    "trip_id": str(trip.id),
                    "trip_title": trip.title,
                    "budget": summary["budget"],
                    "spent": summary["total_spent"],
                    "currency": summary["currency"],
                    "percentage": percentage,
                    "is_over_budget": summary["is_over_budget"],
                })

        return sorted(alerts, key=lambda x: x["percentage"], reverse=True)

    async def get_personal_budget_alerts(
        self,
        current_user_id: uuid.UUID,
        trip_ids: list
    ) -> list:
        trips = (
            self.db.query(Trip)
            .filter(
                Trip.id.in_(trip_ids),
                Trip.status.notin_(["completed", "cancelled"])
            )
            .all()
        )

        personal_budget_service = PersonalBudgetService(self.db)
        alerts = []

        for trip in trips:
            summary = await personal_budget_service.get_personal_budget_summary(
                trip.id, current_user_id
            )

            if not summary.get("has_budget"):
                continue

            percentage = summary["percentage"]
            if percentage >= 80:
                alerts.append({
                    "trip_id": str(trip.id),
                    "trip_title": trip.title,
                    "budget": summary["budget"],
                    "spent": summary["total_spent"],
                    "currency": summary["currency"],
                    "percentage": percentage,
                    "is_over_budget": summary["is_over_budget"],
                })

        return sorted(alerts, key=lambda x: x["percentage"], reverse=True)