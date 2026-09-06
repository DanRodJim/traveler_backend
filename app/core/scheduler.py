import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.database.db import SessionLocal
from app.services.trip_reminder_service import TripReminderService

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def run_trip_reminders_job() -> None:
    db = SessionLocal()
    try:
        service = TripReminderService(db)
        sent_count = service.send_due_reminders()
        logger.info(f"Trip reminders job completed: {sent_count} reminder(s) sent.")
    except Exception:
        logger.exception("Trip reminders job failed")
    finally:
        db.close()


def start_scheduler() -> None:
    # Run every day at 08:00 (server time)
    scheduler.add_job(
        run_trip_reminders_job,
        trigger=CronTrigger(hour=8, minute=0),
        id="trip_reminders_job",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started: trip_reminders_job scheduled daily at 08:00")


def shutdown_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler shut down")