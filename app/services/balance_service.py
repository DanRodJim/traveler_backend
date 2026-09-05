from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime, timezone
import uuid

from app.models.accommodation import Accommodation, AccommodationSplit
from app.models.activity import Activity, ActivitySplit
from app.models.expense import Expense, ExpenseSplit
from app.models.flight import Flight, FlightSplit
from app.models.trip_member import TripMember
from app.models.user import User


class BalanceService:
    def __init__(self, db: Session):
        self.db = db

    def _get_visible_expenses(self, trip_id: uuid.UUID, current_user_id: uuid.UUID) -> List[Expense]:
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
                    Expense.paid_by == current_user_id,
                    ExpenseSplit.user_id == current_user_id
                )
            )
            .distinct()
            .all()
        )
        return list({e.id: e for e in public_expenses + private_expenses}.values())

    def _get_visible_flights(self, trip_id: uuid.UUID, current_user_id: uuid.UUID) -> List[Flight]:
        public_flights = (
            self.db.query(Flight)
            .filter(Flight.trip_id == trip_id, Flight.is_private == False)
            .all()
        )
        private_flights = (
            self.db.query(Flight)
            .outerjoin(FlightSplit, FlightSplit.flight_id == Flight.id)
            .filter(
                Flight.trip_id == trip_id,
                Flight.is_private == True,
                or_(
                    Flight.paid_by == current_user_id,
                    FlightSplit.user_id == current_user_id
                )
            )
            .distinct()
            .all()
        )
        return list({f.id: f for f in public_flights + private_flights}.values())

    def _get_visible_accommodations(self, trip_id: uuid.UUID, current_user_id: uuid.UUID) -> List[Accommodation]:
        public_accommodations = (
            self.db.query(Accommodation)
            .filter(Accommodation.trip_id == trip_id, Accommodation.is_private == False)
            .all()
        )
        private_accommodations = (
            self.db.query(Accommodation)
            .outerjoin(AccommodationSplit, AccommodationSplit.accommodation_id == Accommodation.id)
            .filter(
                Accommodation.trip_id == trip_id,
                Accommodation.is_private == True,
                or_(
                    Accommodation.paid_by == current_user_id,
                    AccommodationSplit.user_id == current_user_id
                )
            )
            .distinct()
            .all()
        )
        return list({a.id: a for a in public_accommodations + private_accommodations}.values())

    def _get_visible_activities(self, trip_id: uuid.UUID, current_user_id: uuid.UUID) -> List[Activity]:
        public_activities = (
            self.db.query(Activity)
            .filter(Activity.trip_id == trip_id, Activity.is_private == False)
            .all()
        )
        private_activities = (
            self.db.query(Activity)
            .outerjoin(ActivitySplit, ActivitySplit.activity_id == Activity.id)
            .filter(
                Activity.trip_id == trip_id,
                Activity.is_private == True,
                or_(
                    Activity.paid_by == current_user_id,
                    ActivitySplit.user_id == current_user_id
                )
            )
            .distinct()
            .all()
        )
        return list({a.id: a for a in public_activities + private_activities}.values())

    def _ensure_currency(
        self,
        currency: str,
        members: List[TripMember],
        balances_by_currency: Dict[str, Dict[str, Decimal]],
        paid_by_currency: Dict[str, Dict[str, Decimal]],
        owes_by_currency: Dict[str, Dict[str, Decimal]],
    ) -> None:
        if currency not in balances_by_currency:
            balances_by_currency[currency] = {str(m.user_id): Decimal('0') for m in members}
            paid_by_currency[currency] = {str(m.user_id): Decimal('0') for m in members}
            owes_by_currency[currency] = {str(m.user_id): Decimal('0') for m in members}

    def _apply_pending_splits(
        self,
        currency: str,
        payer_id: Optional[uuid.UUID],
        pending_splits: list,
        members: List[TripMember],
        balances_by_currency: Dict[str, Dict[str, Decimal]],
        paid_by_currency: Dict[str, Dict[str, Decimal]],
        owes_by_currency: Dict[str, Dict[str, Decimal]],
    ) -> None:
        self._ensure_currency(currency, members, balances_by_currency, paid_by_currency, owes_by_currency)
        if not pending_splits:
            return

        pending_total = sum(Decimal(str(s.amount)) for s in pending_splits)

        if payer_id:
            payer_str = str(payer_id)
            if payer_str in paid_by_currency[currency]:
                paid_by_currency[currency][payer_str] += pending_total
                balances_by_currency[currency][payer_str] += pending_total

        for split in pending_splits:
            user_id = str(split.user_id)
            split_amount = Decimal(str(split.amount))
            if user_id not in owes_by_currency[currency]:
                continue
            owes_by_currency[currency][user_id] += split_amount
            balances_by_currency[currency][user_id] -= split_amount

    def _collect_pending_items(
        self, trip_id: uuid.UUID, current_user_id: uuid.UUID
    ) -> list[tuple[str, Optional[uuid.UUID], list]]:
        expenses = self._get_visible_expenses(trip_id, current_user_id)
        flights = self._get_visible_flights(trip_id, current_user_id)
        accommodations = self._get_visible_accommodations(trip_id, current_user_id)
        activities = self._get_visible_activities(trip_id, current_user_id)

        items: list[tuple[str, Optional[uuid.UUID], list]] = []

        for expense in expenses:
            pending = [s for s in (expense.splits or []) if not s.is_paid]
            items.append((expense.currency, expense.paid_by, pending))

        for flight in flights:
            pending = [s for s in (flight.splits or []) if not s.is_paid]
            items.append((flight.currency or "USD", flight.paid_by or flight.created_by, pending))

        for acc in accommodations:
            pending = [s for s in (acc.splits or []) if not s.is_paid]
            items.append((acc.currency or "USD", acc.paid_by or acc.created_by, pending))

        for act in activities:
            pending = [s for s in (act.splits or []) if not s.is_paid]
            items.append((act.currency or "USD", act.paid_by or act.created_by, pending))

        return items

    def calculate_trip_balances(self, trip_id: uuid.UUID, current_user_id: uuid.UUID) -> Dict:
        members = self.db.query(TripMember).join(User).filter(
            TripMember.trip_id == trip_id
        ).all()

        member_map = {
            str(member.user_id): {
                'id': str(member.user_id),
                'name': member.user.full_name,
                'email': member.user.email
            }
            for member in members
        }

        balances_by_currency: Dict[str, Dict[str, Decimal]] = {}
        paid_by_currency: Dict[str, Dict[str, Decimal]] = {}
        owes_by_currency: Dict[str, Dict[str, Decimal]] = {}

        pending_items = self._collect_pending_items(trip_id, current_user_id)
        for currency, payer_id, pending_splits in pending_items:
            self._apply_pending_splits(
                currency, payer_id, pending_splits,
                members, balances_by_currency, paid_by_currency, owes_by_currency,
            )

        settlements_by_currency = {
            currency: self._calculate_settlements(balances_by_currency[currency], member_map)
            for currency in balances_by_currency
        }

        return {
            'members': list(member_map.values()),
            'balances_by_currency': {
                currency: [
                    {
                        'user_id': user_id,
                        'user_name': member_map[user_id]['name'],
                        'balance': float(balance),
                        'paid': float(paid_by_currency[currency][user_id]),
                        'owes': float(owes_by_currency[currency][user_id])
                    }
                    for user_id, balance in balances.items()
                ]
                for currency, balances in balances_by_currency.items()
            },
            'settlements_by_currency': settlements_by_currency
        }

    def _calculate_settlements(
        self,
        balances: Dict[str, Decimal],
        member_map: Dict[str, Dict]
    ) -> List[Dict]:
        debtors = []
        creditors = []

        for user_id, balance in balances.items():
            if balance < 0:
                debtors.append({'user_id': user_id, 'amount': abs(balance)})
            elif balance > 0:
                creditors.append({'user_id': user_id, 'amount': balance})

        settlements = []
        debtors.sort(key=lambda x: x['amount'], reverse=True)
        creditors.sort(key=lambda x: x['amount'], reverse=True)

        i = 0
        j = 0

        while i < len(debtors) and j < len(creditors):
            debtor = debtors[i]
            creditor = creditors[j]
            amount = min(debtor['amount'], creditor['amount'])

            if amount > Decimal('0.01'):
                settlements.append({
                    'from_user_id': debtor['user_id'],
                    'from_user_name': member_map[debtor['user_id']]['name'],
                    'to_user_id': creditor['user_id'],
                    'to_user_name': member_map[creditor['user_id']]['name'],
                    'amount': float(amount)
                })

            debtor['amount'] -= amount
            creditor['amount'] -= amount

            if debtor['amount'] < Decimal('0.01'):
                i += 1
            if creditor['amount'] < Decimal('0.01'):
                j += 1

        return settlements

    def calculate_user_balance_in_trip(
        self,
        trip_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Dict:
        all_balances = self.calculate_trip_balances(trip_id, user_id)
        user_id_str = str(user_id)

        user_balances = {}
        for currency, balances_list in all_balances['balances_by_currency'].items():
            user_balance = next(
                (b for b in balances_list if b['user_id'] == user_id_str),
                None
            )
            if user_balance:
                user_balances[currency] = user_balance

        user_settlements = {}
        for currency, settlements in all_balances['settlements_by_currency'].items():
            relevant_settlements = [
                s for s in settlements
                if s['from_user_id'] == user_id_str or s['to_user_id'] == user_id_str
            ]
            if relevant_settlements:
                user_settlements[currency] = relevant_settlements

        return {
            'user_id': user_id_str,
            'balances_by_currency': user_balances,
            'settlements_by_currency': user_settlements
        }

    def settle_between_users(
        self,
        trip_id: uuid.UUID,
        from_user_id: uuid.UUID,
        to_user_id: uuid.UUID,
        currency: str
    ) -> int:
        now = datetime.now(timezone.utc)
        settled_count = 0

        expense_splits = (
            self.db.query(ExpenseSplit)
            .join(Expense, ExpenseSplit.expense_id == Expense.id)
            .filter(
                Expense.trip_id == trip_id,
                Expense.paid_by == to_user_id,
                Expense.currency == currency,
                ExpenseSplit.user_id == from_user_id,
                ExpenseSplit.is_paid.is_(False)
            )
            .all()
        )
        for split in expense_splits:
            split.is_paid = True
            split.paid_at = now
            split.updated_at = now
            settled_count += 1

        flight_splits = (
            self.db.query(FlightSplit)
            .join(Flight, FlightSplit.flight_id == Flight.id)
            .filter(
                Flight.trip_id == trip_id,
                or_(Flight.paid_by == to_user_id, Flight.created_by == to_user_id),
                Flight.currency == currency,
                FlightSplit.user_id == from_user_id,
                FlightSplit.is_paid.is_(False)
            )
            .all()
        )
        for split in flight_splits:
            split.is_paid = True
            split.paid_at = now
            split.updated_at = now
            settled_count += 1

        self.db.commit()
        return settled_count