import logging
from datetime import date, timedelta
import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.trip import Trip
from app.models.trip_member import TripMember
from app.models.trip_reminder_log import TripReminderLog
from app.models.user import User
from app.core.config import settings
from app.services.notification_service import NotificationService
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)

REMINDER_MILESTONES = [15, 7, 1]

_EMAIL_ENABLED_FOR_ALERTS = {"alerts_only", "all"}


class TripReminderService:
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService(db)
        self.email_service = EmailService()

    def send_due_reminders(self) -> int:
        """
        Revisa todos los trips activos y envía recordatorios a sus miembros
        para los milestones (15, 7, 1 días antes) que aún no se hayan enviado.
        Retorna la cantidad de recordatorios enviados en esta ejecución.
        """
        today = date.today()
        sent_count = 0

        for days_before in REMINDER_MILESTONES:
            target_date = today + timedelta(days=days_before)

            trips = (
                self.db.query(Trip)
                .filter(
                    Trip.start_date == target_date,
                    Trip.status.notin_(["cancelled", "completed"]),
                )
                .all()
            )

            for trip in trips:
                sent_count += self._notify_trip_members(trip, days_before)

        return sent_count

    def _notify_trip_members(self, trip: Trip, days_before: int) -> int:
        members = (
            self.db.query(TripMember)
            .join(User)
            .filter(TripMember.trip_id == trip.id)
            .all()
        )

        sent = 0
        for member in members:
            if self._already_sent(trip.id, member.user_id, days_before):
                continue

            if self._log_reminder(trip.id, member.user_id, days_before):
                self._send_reminder(trip, member.user, days_before)
                sent += 1

        return sent

    def _already_sent(self, trip_id: uuid.UUID, user_id: uuid.UUID, days_before: int) -> bool:
        return (
            self.db.query(TripReminderLog)
            .filter(
                TripReminderLog.trip_id == trip_id,
                TripReminderLog.user_id == user_id,
                TripReminderLog.days_before == days_before,
            )
            .first()
            is not None
        )

    def _log_reminder(self, trip_id: uuid.UUID, user_id: uuid.UUID, days_before: int) -> bool:
        """
        Intenta registrar el envío. Si otro proceso ya lo registró justo antes
        (condición de carrera), el UniqueConstraint lo rechaza y devolvemos False
        para no enviar el aviso duplicado.
        """
        log = TripReminderLog(
            id=uuid.uuid4(),
            trip_id=trip_id,
            user_id=user_id,
            days_before=days_before,
        )
        self.db.add(log)
        try:
            self.db.commit()
            return True
        except IntegrityError:
            self.db.rollback()
            return False

    def _send_reminder(self, trip: Trip, user: User, days_before: int) -> None:
        time_phrase = "tomorrow" if days_before == 1 else f"in {days_before} days"
        trip_url = f"/dashboard/trips/{trip.id}"

        self.notification_service.create(
            user_id=user.id,
            notif_type="trip_reminder",
            title="Upcoming trip",
            message=f"\"{trip.title}\" starts {time_phrase}!",
            link=trip_url,
        )

        if user.email_notification_preference in _EMAIL_ENABLED_FOR_ALERTS:
            full_trip_url = f"{settings.FRONTEND_URL}{trip_url}"
            self.email_service.send_trip_reminder_email(
                to_email=user.email,
                user_name=user.full_name,
                trip_title=trip.title,
                days_until=days_before,
                trip_url=full_trip_url,
            )