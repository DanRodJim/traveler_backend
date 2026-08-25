import uuid
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any
from datetime import datetime, timedelta
from app.models import Accommodation, Activity, Expense, ExpenseSplit, Flight, Trip, TripMember
from app.services.budget_service import BudgetService
from app.services.personal_budget_service import PersonalBudgetService

class DashboardService:
    def __init__(self, db: Session):
        self.db = db
    
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
    
    def get_total_expenses_by_currency(self, trip_ids: List[uuid.UUID]) -> Dict[str, float]:
        total_expenses_dict = {}
        
        expenses_by_currency = self.db.query(
            Expense.currency,
            func.sum(Expense.amount)
        ).filter(
            Expense.trip_id.in_(trip_ids)
        ).group_by(Expense.currency).all()
        
        for currency, total in expenses_by_currency:
            total_expenses_dict[currency] = total_expenses_dict.get(currency, 0) + float(total)
        
        activities_by_currency = self.db.query(
            Activity.currency,
            func.sum(Activity.cost)
        ).filter(
            Activity.trip_id.in_(trip_ids),
            Activity.cost.isnot(None)
        ).group_by(Activity.currency).all()
        
        for currency, total in activities_by_currency:
            if currency:
                total_expenses_dict[currency] = total_expenses_dict.get(currency, 0) + float(total)
        
        flights_by_currency = self.db.query(
            Flight.currency,
            func.sum(Flight.cost)
        ).filter(
            Flight.trip_id.in_(trip_ids),
            Flight.cost.isnot(None)
        ).group_by(Flight.currency).all()
        
        for currency, total in flights_by_currency:
            if currency:
                total_expenses_dict[currency] = total_expenses_dict.get(currency, 0) + float(total)
        
        accommodations_by_currency = self.db.query(
            Accommodation.currency,
            func.sum(Accommodation.cost)
        ).filter(
            Accommodation.trip_id.in_(trip_ids),
            Accommodation.cost.isnot(None)
        ).group_by(Accommodation.currency).all()
        
        for currency, total in accommodations_by_currency:
            if currency:
                total_expenses_dict[currency] = total_expenses_dict.get(currency, 0) + float(total)
        
        return total_expenses_dict
    
    def get_expenses_by_category(self, trip_ids: List[uuid.UUID]) -> Dict[str, float]:
        expenses_by_category = self.db.query(
            Expense.category,
            func.sum(Expense.amount)
        ).filter(
            Expense.trip_id.in_(trip_ids)
        ).group_by(Expense.category).all()
        
        return {
            category: float(total) for category, total in expenses_by_category
        }
    
    def get_expenses_by_type(self, trip_ids: List[uuid.UUID]) -> Dict[str, float]:
        expense_type_totals = {}
        
        manual_total = self.db.query(
            func.sum(Expense.amount)
        ).filter(
            Expense.trip_id.in_(trip_ids)
        ).scalar() or 0
        
        if manual_total > 0:
            expense_type_totals['Manual Expenses'] = float(manual_total)
        
        activities_total = self.db.query(
            func.sum(Activity.cost)
        ).filter(
            Activity.trip_id.in_(trip_ids),
            Activity.cost.isnot(None)
        ).scalar() or 0
        
        if activities_total > 0:
            expense_type_totals['Activities'] = float(activities_total)
        
        flights_total = self.db.query(
            func.sum(Flight.cost)
        ).filter(
            Flight.trip_id.in_(trip_ids),
            Flight.cost.isnot(None)
        ).scalar() or 0
        
        if flights_total > 0:
            expense_type_totals['Flights'] = float(flights_total)
        
        accommodations_total = self.db.query(
            func.sum(Accommodation.cost)
        ).filter(
            Accommodation.trip_id.in_(trip_ids),
            Accommodation.cost.isnot(None)
        ).scalar() or 0
        
        if accommodations_total > 0:
            expense_type_totals['Accommodations'] = float(accommodations_total)
        
        return expense_type_totals
    
    async def get_top_trips_by_spending(self, trip_ids: list, limit: int = 5) -> list:
        trips = self.db.query(Trip).filter(Trip.id.in_(trip_ids)).all()

        budget_service = BudgetService(self.db)
        results = []

        for trip in trips:
            spending = await budget_service.calculate_trip_spending(trip.id)
            if spending["total_spent"] > 0:
                results.append({
                    "trip": trip.title,
                    "amount": round(spending["total_spent"], 2),
                })

        results.sort(key=lambda x: x["amount"], reverse=True)
        return results[:limit]
    
    def get_upcoming_activities(self, trip_ids: List[uuid.UUID], days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        today = datetime.now().date()
        
        upcoming_activities = self.db.query(Activity).join(
            Trip, Activity.trip_id == Trip.id
        ).filter(
            Trip.id.in_(trip_ids),
            Activity.activity_date >= today,
            Activity.activity_date <= today + timedelta(days=days)
        ).order_by(Activity.activity_date, Activity.start_time).limit(limit).all()
        
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
    
    def get_activities_by_category(self, trip_ids: List[uuid.UUID]) -> Dict[str, int]:
        activities_by_category = self.db.query(
            Activity.category,
            func.count(Activity.id)
        ).filter(
            Activity.trip_id.in_(trip_ids)
        ).group_by(Activity.category).all()
        
        return {
            category: count for category, count in activities_by_category
        }
    
    def get_accommodations_by_type(self, trip_ids: List[uuid.UUID]) -> Dict[str, int]:
        accommodations_by_type = self.db.query(
            Accommodation.type,
            func.count(Accommodation.id)
        ).filter(
            Accommodation.trip_id.in_(trip_ids)
        ).group_by(Accommodation.type).all()
        
        return {
            acc_type: count for acc_type, count in accommodations_by_type
        }

    def get_pending_splits_owed_by_me(
        self,
        current_user_id: uuid.UUID,
        trip_ids: list
    ) -> list:
        results = (
            self.db.query(ExpenseSplit, Expense, Trip)
            .join(Expense, ExpenseSplit.expense_id == Expense.id)
            .join(Trip, Expense.trip_id == Trip.id)
            .filter(
                Expense.trip_id.in_(trip_ids),
                ExpenseSplit.user_id == current_user_id,
                ExpenseSplit.is_paid == False,
                Expense.paid_by != current_user_id,
            )
            .all()
        )

        return [
            {
                "split_id": str(split.id),
                "expense_title": expense.title,
                "trip_id": str(trip.id),
                "trip_title": trip.title,
                "amount": float(split.amount),
                "currency": expense.currency,
                "paid_by": str(expense.paid_by),
            }
            for split, expense, trip in results
        ]

    def get_pending_splits_owed_to_me(
        self,
        current_user_id: uuid.UUID,
        trip_ids: list
    ) -> list:
        results = (
            self.db.query(ExpenseSplit, Expense, Trip)
            .join(Expense, ExpenseSplit.expense_id == Expense.id)
            .join(Trip, Expense.trip_id == Trip.id)
            .filter(
                Expense.trip_id.in_(trip_ids),
                Expense.paid_by == current_user_id,
                ExpenseSplit.user_id != current_user_id,
                ExpenseSplit.is_paid == False,
            )
            .all()
        )

        return [
            {
                "split_id": str(split.id),
                "expense_title": expense.title,
                "trip_id": str(trip.id),
                "trip_title": trip.title,
                "amount": float(split.amount),
                "currency": expense.currency,
                "owed_by": str(split.user_id),
            }
            for split, expense, trip in results
        ]

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