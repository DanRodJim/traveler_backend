from datetime import datetime
from io import BytesIO
from decimal import Decimal
import uuid

from sqlalchemy.orm import Session
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Flowable
)
from typing import List

from app.models.trip import Trip
from app.models.activity import Activity
from app.models.flight import Flight
from app.models.accommodation import Accommodation
from app.models.trip_member import TripMember
from app.models.user import User
from app.core.exceptions import ResourceNotFoundError
from app.services.personal_budget_service import PersonalBudgetService
from app.services.currency_service import get_exchange_rates, convert_currency


class PdfNotFoundError(ResourceNotFoundError):
    def __init__(self):
        super().__init__("Trip")


PRIMARY_COLOR = colors.HexColor("#2563eb")
LIGHT_GRAY = colors.HexColor("#f3f4f6")
DATE_FORMAT = "%b %d, %Y"
YOUR_SHARE = "Your Share"


class PdfService:
    def __init__(self, db: Session):
        self.db = db
        self.styles = getSampleStyleSheet()
        self.styles.add(ParagraphStyle(
            name="TripTitle", fontSize=22, spaceAfter=10, textColor=PRIMARY_COLOR, fontName="Helvetica-Bold"
        ))
        self.styles.add(ParagraphStyle(
            name="SectionHeader", fontSize=14, spaceBefore=18, spaceAfter=8,
            textColor=colors.HexColor("#111827"), fontName="Helvetica-Bold"
        ))
        self.styles.add(ParagraphStyle(
            name="MetaInfo", fontSize=10, textColor=colors.HexColor("#6b7280")
        ))

    def _get_trip(self, trip_id: uuid.UUID) -> Trip:
        trip = self.db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            raise PdfNotFoundError()
        return trip

    def _header(self, trip: Trip) -> List[Flowable]:
        return [
            Paragraph(trip.title, self.styles["TripTitle"]),
            Spacer(1, 4),
            Paragraph(f"{trip.destination}", self.styles["MetaInfo"]),
            Paragraph(
                f"{trip.start_date.strftime('%b %d, %Y')} — {trip.end_date.strftime('%b %d, %Y')}",
                self.styles["MetaInfo"]
            ),
            Spacer(1, 0.1 * inch),
        ]

    def _add_section(self, elements: List[Flowable], title: str, header_row: list, rows: list) -> None:
        if not rows:
            return
        elements.append(Paragraph(title, self.styles["SectionHeader"]))
        elements.append(self._build_table([header_row] + rows))
        elements.append(Spacer(1, 0.15 * inch))

    # ── Itinerary PDF ────────────────────────────────────────

    @staticmethod
    def _format_flight_row(f: Flight) -> list:
        departure = f.departure_date.strftime(DATE_FORMAT) + (
            f" {f.departure_time.strftime('%H:%M')}" if f.departure_time else ""
        )
        arrival = f.arrival_date.strftime(DATE_FORMAT) + (
            f" {f.arrival_time.strftime('%H:%M')}" if f.arrival_time else ""
        )
        return [
            f"{f.departure_airport} → {f.arrival_airport}",
            departure,
            arrival,
            f.airline or "-",
            f.booking_reference or "-",
        ]

    @staticmethod
    def _format_accommodation_itinerary_row(a: Accommodation) -> list:
        return [
            a.name,
            a.type.capitalize(),
            a.check_in_date.strftime(DATE_FORMAT),
            a.check_out_date.strftime(DATE_FORMAT),
            a.booking_reference or "-",
        ]

    @staticmethod
    def _format_activity_itinerary_row(act: Activity) -> list:
        return [
            act.activity_date.strftime(DATE_FORMAT),
            act.start_time.strftime("%H:%M") if act.start_time else "-",
            act.title,
            act.category.capitalize(),
            act.location or "-",
        ]

    def generate_itinerary_pdf(self, trip_id: uuid.UUID) -> BytesIO:
        trip = self._get_trip(trip_id)

        flights = self.db.query(Flight).filter(Flight.trip_id == trip_id).all()
        accommodations = self.db.query(Accommodation).filter(Accommodation.trip_id == trip_id).all()
        activities = (
            self.db.query(Activity)
            .filter(Activity.trip_id == trip_id)
            .order_by(Activity.activity_date, Activity.start_time)
            .all()
        )

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.6*inch, bottomMargin=0.6*inch)
        elements = self._header(trip)

        self._add_section(
            elements, "Flights",
            ["Route", "Departure", "Arrival", "Airline", "Ref"],
            [self._format_flight_row(f) for f in sorted(flights, key=lambda x: x.departure_date)],
        )
        self._add_section(
            elements, "Accommodations",
            ["Name", "Type", "Check-in", "Check-out", "Ref"],
            [self._format_accommodation_itinerary_row(a) for a in sorted(accommodations, key=lambda x: x.check_in_date)],
        )
        self._add_section(
            elements, "Activities",
            ["Date", "Time", "Title", "Category", "Location"],
            [self._format_activity_itinerary_row(act) for act in activities],
        )

        if not flights and not accommodations and not activities:
            elements.append(Paragraph("No itinerary items yet.", self.styles["Normal"]))

        doc.build(elements)
        buffer.seek(0)
        return buffer

    # ── Expenses PDF ───────────────────────────────────────────────────────

    @staticmethod
    def _format_expense_row(e, my_amount: Decimal, currency: str, members: dict) -> list:
        paid_by_name = members.get(e.paid_by, "-") if e.paid_by else "-"
        return [
            e.expense_date.strftime(DATE_FORMAT),
            e.title,
            e.category.capitalize(),
            paid_by_name,
            f"{float(my_amount):,.2f} {currency}",
            "Yes" if e.is_private else "No",
        ]

    @staticmethod
    def _format_flight_share_row(f: Flight, my_amount: Decimal, currency: str) -> list:
        return [
            f.departure_date.strftime(DATE_FORMAT),
            f"{f.departure_airport} → {f.arrival_airport}",
            f.airline or "-",
            f"{float(my_amount):,.2f} {currency}",
            "Yes" if f.is_private else "No",
        ]

    @staticmethod
    def _format_accommodation_share_row(acc: Accommodation, my_amount: Decimal, currency: str) -> list:
        return [
            acc.check_in_date.strftime(DATE_FORMAT),
            acc.name,
            acc.type.capitalize(),
            f"{float(my_amount):,.2f} {currency}",
            "Yes" if acc.is_private else "No",
        ]

    @staticmethod
    def _format_activity_share_row(act: Activity, my_amount: Decimal, currency: str) -> list:
        return [
            act.activity_date.strftime(DATE_FORMAT),
            act.title,
            act.category.capitalize(),
            f"{float(my_amount):,.2f} {currency}",
            "Yes" if act.is_private else "No",
        ]

    async def _build_summary_elements(self, trip: Trip, all_items: list) -> List[Flowable]:
        totals: dict = {}
        for _, my_amount, currency in all_items:
            totals[currency] = totals.get(currency, 0) + float(my_amount)

        if not totals:
            return []

        summary_elements: List[Flowable] = [Paragraph("Summary", self.styles["SectionHeader"])]
        summary_text = " + ".join(f"{amt:,.2f} {cur}" for cur, amt in totals.items())
        summary_elements.append(Paragraph(f"Total (your share): {summary_text}", self.styles["Normal"]))
        summary_elements.append(Spacer(1, 0.1 * inch))

        base_currency = trip.currency or "USD"
        rates = await get_exchange_rates(base_currency)
        converted_total = sum(
            convert_currency(Decimal(str(amt)), cur, base_currency, rates)
            for cur, amt in totals.items()
        )
        today_str = datetime.now().strftime("%B %d, %Y")
        summary_elements.append(Paragraph(
            f"Converted total: {float(converted_total):,.2f} {base_currency} "
            f"(exchange rates as of {today_str})",
            self.styles["Normal"]
        ))
        summary_elements.append(Spacer(1, 0.15 * inch))
        return summary_elements

    async def generate_expenses_pdf(self, trip_id: uuid.UUID, current_user_id: uuid.UUID) -> BytesIO:
        trip = self._get_trip(trip_id)

        personal_budget_service = PersonalBudgetService(self.db)
        expense_items = personal_budget_service.get_my_expense_line_items(trip_id, current_user_id)
        flight_items = personal_budget_service.get_my_flight_line_items(trip_id, current_user_id)
        accommodation_items = personal_budget_service.get_my_accommodation_line_items(trip_id, current_user_id)
        activity_items = personal_budget_service.get_my_activity_line_items(trip_id, current_user_id)

        members = {
            m.user_id: m.user.full_name
            for m in self.db.query(TripMember).join(User).filter(TripMember.trip_id == trip_id).all()
        }

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.6*inch, bottomMargin=0.6*inch)
        elements = self._header(trip)

        all_items = expense_items + flight_items + accommodation_items + activity_items
        elements.extend(await self._build_summary_elements(trip, all_items))

        self._add_section(
            elements, "Manual Expenses (Your Share)",
            ["Date", "Title", "Category", "Paid by", YOUR_SHARE, "Private"],
            [self._format_expense_row(e, amt, cur, members) for e, amt, cur in expense_items],
        )
        self._add_section(
            elements, "Flights (Your Share)",
            ["Date", "Route", "Airline", YOUR_SHARE, "Private"],
            [self._format_flight_share_row(f, amt, cur) for f, amt, cur in flight_items],
        )
        self._add_section(
            elements, "Accommodations (Your Share)",
            ["Check-in", "Name", "Type", YOUR_SHARE, "Private"],
            [self._format_accommodation_share_row(acc, amt, cur) for acc, amt, cur in accommodation_items],
        )
        self._add_section(
            elements, "Activities (Your Share)",
            ["Date", "Title", "Category", YOUR_SHARE, "Private"],
            [self._format_activity_share_row(act, amt, cur) for act, amt, cur in activity_items],
        )

        if not all_items:
            elements.append(Paragraph("No expenses visible to you yet.", self.styles["Normal"]))

        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph(
            "Note: All amounts shown represent your share only — either your split "
            "portion of a shared item, or the full amount if you paid alone with no "
            "split. Private items are only visible to you if you paid or are part of "
            "the split. The converted total may differ from the Trip Budget shown in "
            "the app, since Trip Budget only counts public items at full amount, not "
            "per-person shares.",
            self.styles["MetaInfo"]
        ))

        doc.build(elements)
        buffer.seek(0)
        return buffer

    # ── Helpers ────────────────────────────────────────────────────────────

    def _build_table(self, data: list) -> Table:
        table = Table(data, repeatRows=1, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_COLOR),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 1), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
        ]))
        return table