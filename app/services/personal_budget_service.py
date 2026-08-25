from decimal import Decimal
from typing import Dict, List, Tuple
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.accommodation import Accommodation, AccommodationSplit
from app.models.activity import Activity, ActivitySplit
from app.models.expense import Expense, ExpenseSplit
from app.models.flight import Flight, FlightSplit
from app.models.trip import Trip
from app.models.trip_member import TripMember
from app.services.currency_service import get_exchange_rates, convert_currency


class PersonalBudgetService:
    def __init__(self, db: Session):
        self.db = db

    def get_my_expense_line_items(
        self, trip_id: uuid.UUID, user_id: uuid.UUID
    ) -> List[Tuple[Expense, Decimal, str]]:
        public_expenses = (
            self.db.query(Expense)
            .filter(Expense.trip_id == trip_id, Expense.is_private == False)
            .all()
        )
        private_expenses = (
            self.db.query(Expense)
            .outerjoin(ExpenseSplit, ExpenseSplit.expense_id == Expense.id)
            .filter(
                Expense.trip_id == trip_id,
                Expense.is_private == True,
                or_(
                    Expense.paid_by == user_id,
                    ExpenseSplit.user_id == user_id
                )
            )
            .distinct()
            .all()
        )
        all_expenses = list({e.id: e for e in public_expenses + private_expenses}.values())
        all_expenses.sort(key=lambda e: e.expense_date, reverse=True)

        items: List[Tuple[Expense, Decimal, str]] = []
        for expense in all_expenses:
            my_split = next((s for s in expense.splits if s.user_id == user_id), None)
            if my_split:
                items.append((expense, Decimal(str(my_split.amount)), expense.currency))
            elif expense.paid_by == user_id:
                items.append((expense, Decimal(str(expense.amount)), expense.currency))

        return items

    def get_my_flight_line_items(
        self, trip_id: uuid.UUID, user_id: uuid.UUID
    ) -> List[Tuple[Flight, Decimal, str]]:
        public_flights = (
            self.db.query(Flight)
            .filter(
                Flight.trip_id == trip_id,
                Flight.is_private == False,
                Flight.cost.isnot(None)
            )
            .all()
        )
        private_flights = (
            self.db.query(Flight)
            .outerjoin(FlightSplit, FlightSplit.flight_id == Flight.id)
            .filter(
                Flight.trip_id == trip_id,
                Flight.is_private == True,
                Flight.cost.isnot(None),
                or_(
                    Flight.paid_by == user_id,
                    Flight.created_by == user_id,
                    FlightSplit.user_id == user_id
                )
            )
            .distinct()
            .all()
        )
        all_flights = list({f.id: f for f in public_flights + private_flights}.values())
        all_flights.sort(key=lambda f: f.departure_date)

        items: List[Tuple[Flight, Decimal, str]] = []
        for flight in all_flights:
            my_split = next((s for s in flight.splits if s.user_id == user_id), None)
            payer_id = flight.paid_by or flight.created_by
            currency = flight.currency or "USD"

            if my_split:
                items.append((flight, Decimal(str(my_split.amount)), currency))
            elif payer_id == user_id and flight.cost:
                items.append((flight, Decimal(str(flight.cost)), currency))

        return items

    def get_my_accommodation_line_items(
        self, trip_id: uuid.UUID, user_id: uuid.UUID
    ) -> List[Tuple[Accommodation, Decimal, str]]:
        public_accommodations = (
            self.db.query(Accommodation)
            .filter(
                Accommodation.trip_id == trip_id,
                Accommodation.is_private == False,
                Accommodation.cost.isnot(None)
            )
            .all()
        )
        private_accommodations = (
            self.db.query(Accommodation)
            .outerjoin(AccommodationSplit, AccommodationSplit.accommodation_id == Accommodation.id)
            .filter(
                Accommodation.trip_id == trip_id,
                Accommodation.is_private == True,
                Accommodation.cost.isnot(None),
                or_(
                    Accommodation.paid_by == user_id,
                    Accommodation.created_by == user_id,
                    AccommodationSplit.user_id == user_id
                )
            )
            .distinct()
            .all()
        )
        all_accommodations = list(
            {a.id: a for a in public_accommodations + private_accommodations}.values()
        )
        all_accommodations.sort(key=lambda a: a.check_in_date)

        items: List[Tuple[Accommodation, Decimal, str]] = []
        for acc in all_accommodations:
            my_split = next((s for s in acc.splits if s.user_id == user_id), None)
            payer_id = acc.paid_by or acc.created_by
            currency = acc.currency or "USD"

            if my_split:
                items.append((acc, Decimal(str(my_split.amount)), currency))
            elif payer_id == user_id and acc.cost:
                items.append((acc, Decimal(str(acc.cost)), currency))

        return items

    def get_my_activity_line_items(
        self, trip_id: uuid.UUID, user_id: uuid.UUID
    ) -> List[Tuple[Activity, Decimal, str]]:
        public_activities = (
            self.db.query(Activity)
            .filter(
                Activity.trip_id == trip_id,
                Activity.is_private == False,
                Activity.cost.isnot(None)
            )
            .all()
        )
        private_activities = (
            self.db.query(Activity)
            .outerjoin(ActivitySplit, ActivitySplit.activity_id == Activity.id)
            .filter(
                Activity.trip_id == trip_id,
                Activity.is_private == True,
                Activity.cost.isnot(None),
                or_(
                    Activity.paid_by == user_id,
                    Activity.created_by == user_id,
                    ActivitySplit.user_id == user_id
                )
            )
            .distinct()
            .all()
        )
        all_activities = list(
            {a.id: a for a in public_activities + private_activities}.values()
        )
        all_activities.sort(key=lambda a: a.activity_date)

        items: List[Tuple[Activity, Decimal, str]] = []
        for act in all_activities:
            my_split = next((s for s in act.splits if s.user_id == user_id), None)
            payer_id = act.paid_by or act.created_by
            currency = act.currency or "USD"

            if my_split:
                items.append((act, Decimal(str(my_split.amount)), currency))
            elif payer_id == user_id and act.cost:
                items.append((act, Decimal(str(act.cost)), currency))

        return items

    async def calculate_personal_spending(
        self, trip_id: uuid.UUID, user_id: uuid.UUID
    ) -> Dict:
        trip = self.db.query(Trip).filter(Trip.id == trip_id).first()
        base_currency = (trip.currency if trip else None) or "USD"
        rates = await get_exchange_rates(base_currency)

        # ✅ Ahora cada item es (objeto, monto, moneda) — solo usamos monto y moneda aquí
        expense_items = self.get_my_expense_line_items(trip_id, user_id)
        flight_items = self.get_my_flight_line_items(trip_id, user_id)
        accommodation_items = self.get_my_accommodation_line_items(trip_id, user_id)
        activity_items = self.get_my_activity_line_items(trip_id, user_id)

        expenses_total = sum(
            convert_currency(amount, currency, base_currency, rates)
            for _, amount, currency in expense_items
        )
        flights_total = sum(
            convert_currency(amount, currency, base_currency, rates)
            for _, amount, currency in flight_items
        )
        accommodations_total = sum(
            convert_currency(amount, currency, base_currency, rates)
            for _, amount, currency in accommodation_items
        )
        activities_total = sum(
            convert_currency(amount, currency, base_currency, rates)
            for _, amount, currency in activity_items
        )

        total_spent = (
            expenses_total + flights_total + activities_total + accommodations_total
        )

        return {
            "currency": base_currency,
            "total_spent": float(total_spent),
            "breakdown": {
                "expenses": round(float(expenses_total), 2),
                "flights": round(float(flights_total), 2),
                "activities": round(float(activities_total), 2),
                "accommodations": round(float(accommodations_total), 2),
            }
        }

    async def get_personal_budget_summary(
        self,
        trip_id: uuid.UUID,
        current_user_id: uuid.UUID
    ) -> Dict:
        member = self.db.query(TripMember).filter(
            TripMember.trip_id == trip_id,
            TripMember.user_id == current_user_id
        ).first()

        if not member or not member.personal_budget:
            return {"has_budget": False}

        spending = await self.calculate_personal_spending(trip_id, current_user_id)

        base_currency = spending["currency"]
        total_spent = Decimal(str(spending["total_spent"]))
        budget = Decimal(str(member.personal_budget))
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