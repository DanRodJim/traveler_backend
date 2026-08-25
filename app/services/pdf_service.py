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
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)

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

    def _header(self, trip: Trip) -> list:
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

    # ── Itinerary PDF ────────────────────────────────────────

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

        if flights:
            elements.append(Paragraph("Flights", self.styles["SectionHeader"]))
            data = [["Route", "Departure", "Arrival", "Airline", "Ref"]]
            for f in sorted(flights, key=lambda x: x.departure_date):
                data.append([
                    f"{f.departure_airport} → {f.arrival_airport}",
                    f.departure_date.strftime("%b %d, %Y") + (f" {f.departure_time.strftime('%H:%M')}" if f.departure_time else ""),
                    f.arrival_date.strftime("%b %d, %Y") + (f" {f.arrival_time.strftime('%H:%M')}" if f.arrival_time else ""),
                    f.airline or "-",
                    f.booking_reference or "-",
                ])
            elements.append(self._build_table(data))

        if accommodations:
            elements.append(Paragraph("Accommodations", self.styles["SectionHeader"]))
            data = [["Name", "Type", "Check-in", "Check-out", "Ref"]]
            for a in sorted(accommodations, key=lambda x: x.check_in_date):
                data.append([
                    a.name,
                    a.type.capitalize(),
                    a.check_in_date.strftime("%b %d, %Y"),
                    a.check_out_date.strftime("%b %d, %Y"),
                    a.booking_reference or "-",
                ])
            elements.append(self._build_table(data))

        if activities:
            elements.append(Paragraph("Activities", self.styles["SectionHeader"]))
            data = [["Date", "Time", "Title", "Category", "Location"]]
            for act in activities:
                data.append([
                    act.activity_date.strftime("%b %d, %Y"),
                    act.start_time.strftime("%H:%M") if act.start_time else "-",
                    act.title,
                    act.category.capitalize(),
                    act.location or "-",
                ])
            elements.append(self._build_table(data))

        if not flights and not accommodations and not activities:
            elements.append(Paragraph("No itinerary items yet.", self.styles["Normal"]))

        doc.build(elements)
        buffer.seek(0)
        return buffer

    # ── Expenses PDF ───────────────────────────────────────────────────────

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

        totals: dict = {}
        for _, my_amount, currency in expense_items:
            totals[currency] = totals.get(currency, 0) + float(my_amount)
        for _, my_amount, currency in flight_items:
            totals[currency] = totals.get(currency, 0) + float(my_amount)
        for _, my_amount, currency in accommodation_items:
            totals[currency] = totals.get(currency, 0) + float(my_amount)
        for _, my_amount, currency in activity_items:
            totals[currency] = totals.get(currency, 0) + float(my_amount)

        if totals:
            elements.append(Paragraph("Summary", self.styles["SectionHeader"]))
            summary_text = " + ".join(f"{amt:,.2f} {cur}" for cur, amt in totals.items())
            elements.append(Paragraph(f"Total (your share): {summary_text}", self.styles["Normal"]))
            elements.append(Spacer(1, 0.1 * inch))

            base_currency = trip.currency or "USD"
            rates = await get_exchange_rates(base_currency)
            converted_total = sum(
                convert_currency(Decimal(str(amt)), cur, base_currency, rates)
                for cur, amt in totals.items()
            )
            today_str = datetime.now().strftime("%B %d, %Y")
            elements.append(Paragraph(
                f"Converted total: {float(converted_total):,.2f} {base_currency} "
                f"(exchange rates as of {today_str})",
                self.styles["Normal"]
            ))
            elements.append(Spacer(1, 0.15 * inch))

        # Manual Expenses
        if expense_items:
            elements.append(Paragraph("Manual Expenses (Your Share)", self.styles["SectionHeader"]))
            data = [["Date", "Title", "Category", "Paid by", "Your Share", "Private"]]
            for e, my_amount, currency in expense_items:
                paid_by_name = members.get(e.paid_by, "-") if e.paid_by else "-"
                data.append([
                    e.expense_date.strftime("%b %d, %Y"),
                    e.title,
                    e.category.capitalize(),
                    paid_by_name,
                    f"{float(my_amount):,.2f} {currency}",
                    "Yes" if e.is_private else "No",
                ])
            elements.append(self._build_table(data))
            elements.append(Spacer(1, 0.15 * inch))

        # Flights
        if flight_items:
            elements.append(Paragraph("Flights (Your Share)", self.styles["SectionHeader"]))
            data = [["Date", "Route", "Airline", "Your Share", "Private"]]
            for f, my_amount, currency in flight_items:
                data.append([
                    f.departure_date.strftime("%b %d, %Y"),
                    f"{f.departure_airport} → {f.arrival_airport}",
                    f.airline or "-",
                    f"{float(my_amount):,.2f} {currency}",
                    "Yes" if f.is_private else "No",
                ])
            elements.append(self._build_table(data))
            elements.append(Spacer(1, 0.15 * inch))

        # Accommodations
        if accommodation_items:
            elements.append(Paragraph("Accommodations (Your Share)", self.styles["SectionHeader"]))
            data = [["Check-in", "Name", "Type", "Your Share", "Private"]]
            for acc, my_amount, currency in accommodation_items:
                data.append([
                    acc.check_in_date.strftime("%b %d, %Y"),
                    acc.name,
                    acc.type.capitalize(),
                    f"{float(my_amount):,.2f} {currency}",
                    "Yes" if acc.is_private else "No",
                ])
            elements.append(self._build_table(data))
            elements.append(Spacer(1, 0.15 * inch))

        # Activities
        if activity_items:
            elements.append(Paragraph("Activities (Your Share)", self.styles["SectionHeader"]))
            data = [["Date", "Title", "Category", "Your Share", "Private"]]
            for act, my_amount, currency in activity_items:
                data.append([
                    act.activity_date.strftime("%b %d, %Y"),
                    act.title,
                    act.category.capitalize(),
                    f"{float(my_amount):,.2f} {currency}",
                    "Yes" if act.is_private else "No",
                ])
            elements.append(self._build_table(data))
            elements.append(Spacer(1, 0.15 * inch))

        if not expense_items and not flight_items and not accommodation_items and not activity_items:
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