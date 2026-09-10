"""
Script de desarrollo para disparar manualmente el job de recordatorios de
viaje, sin exponer nada por HTTP. Uso:

    python -m app.scripts.trigger_reminders

Solo debe ejecutarse localmente contra tu base de datos de desarrollo.
"""
import sys

from app.core.config import settings
from app.database.db import SessionLocal
from app.services.trip_reminder_service import TripReminderService


def main() -> None:
    if settings.is_production():
        print("Refusing to run: this script must not be used in production.")
        sys.exit(1)

    db = SessionLocal()
    try:
        service = TripReminderService(db)
        sent_count = service.send_due_reminders()
        print(f"Done. {sent_count} reminder(s) sent.")
    finally:
        db.close()


if __name__ == "__main__":
    main()