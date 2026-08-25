from decimal import Decimal
from typing import Dict
import uuid

from sqlalchemy.orm import Session

from app.models.accommodation import Accommodation
from app.models.activity import Activity
from app.models.expense import Expense
from app.models.flight import Flight
from app.models.trip import Trip
from app.services.currency_service import get_exchange_rates, convert_currency


class BudgetService:
    def __init__(self, db: Session):
        self.db = db

    async def calculate_trip_spending(self, trip_id: uuid.UUID) -> Dict:
        trip = self.db.query(Trip).filter(Trip.id == trip_id).first()

        if not trip:
            return {
                "currency": "USD",
                "total_spent": 0.0,
                "breakdown": {
                    "expenses": 0.0,
                    "activities": 0.0,
                    "flights": 0.0,
                    "accommodations": 0.0,
                }
            }

        base_currency = trip.currency or "USD"
        rates = await get_exchange_rates(base_currency)

        all_expenses = (
            self.db.query(Expense)
            .filter(Expense.trip_id == trip_id, Expense.is_private == False)
            .all()
        )

        activities = (
            self.db.query(Activity)
            .filter(
                Activity.trip_id == trip_id,
                Activity.cost.isnot(None),
                Activity.is_private == False
            )
            .all()
        )

        flights = (
            self.db.query(Flight)
            .filter(
                Flight.trip_id == trip_id,
                Flight.cost.isnot(None),
                Flight.is_private == False
            )
            .all()
        )

        accommodations = (
            self.db.query(Accommodation)
            .filter(
                Accommodation.trip_id == trip_id,
                Accommodation.cost.isnot(None),
                Accommodation.is_private == False
            )
            .all()
        )

        expenses_total = sum(
            convert_currency(e.amount, e.currency, base_currency, rates)
            for e in all_expenses
        )

        activities_total = sum(
            convert_currency(a.cost, a.currency or base_currency, base_currency, rates)
            for a in activities if a.cost
        )

        flights_total = sum(
            convert_currency(f.cost, f.currency or base_currency, base_currency, rates)
            for f in flights if f.cost
        )

        accommodations_total = sum(
            convert_currency(a.cost, a.currency or base_currency, base_currency, rates)
            for a in accommodations if a.cost
        )

        total_spent = expenses_total + activities_total + flights_total + accommodations_total

        return {
            "currency": base_currency,
            "total_spent": float(total_spent),
            "breakdown": {
                "expenses": round(float(expenses_total), 2),
                "activities": round(float(activities_total), 2),
                "flights": round(float(flights_total), 2),
                "accommodations": round(float(accommodations_total), 2),
            }
        }

    async def get_trip_budget_summary(self, trip_id: uuid.UUID) -> Dict:
        trip = self.db.query(Trip).filter(Trip.id == trip_id).first()

        if not trip or not trip.budget:
            return {"has_budget": False}

        spending = await self.calculate_trip_spending(trip_id)

        base_currency = spending["currency"]
        total_spent = Decimal(str(spending["total_spent"]))
        budget = Decimal(str(trip.budget))
        remaining = budget - total_spent
        percentage = float(total_spent / budget * 100) if budget > 0 else 0

        return {
            "has_budget": True,
            "budget": float(budget),
            "currency": base_currency,
            "total_spent": round(float(total_spent), 2),
            "remaining": round(float(remaining), 2),
            "percentage": round(min(percentage, 100), 1),
            "is_over_budget": total_spent > budget,
            "breakdown": spending["breakdown"],
        }