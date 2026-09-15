"""Daily reminder job - finds thirsty plants and sends a grouped digest.

Runnable two ways:
  1. Standalone, e.g. via cron:      python scheduler.py
  2. Embedded in the Flask app via APScheduler: call start_scheduler(app)
"""
import os
from datetime import date

from dotenv import load_dotenv

load_dotenv()

from models import ContactSettings, NotificationsLog, Plant, db  # noqa: E402
from services.notifications import (  # noqa: E402
    build_email_digest,
    build_sms_digest,
    new_digest_id,
    send_email,
    send_sms,
)
from utils import is_thirsty, plant_with_schedule  # noqa: E402

REALERT_INTERVAL_DAYS = int(os.environ.get("REALERT_INTERVAL_DAYS", "3"))


def _needs_alert(plant):
    """True if thirsty and not already alerted recently for this overdue stretch."""
    last_notification = (
        NotificationsLog.query.filter(NotificationsLog.plant_id == plant.id)
        .filter(NotificationsLog.sent_at >= plant.last_watered_at)
        .order_by(NotificationsLog.sent_at.desc())
        .first()
    )
    if last_notification is None:
        return True
    days_since = (date.today() - last_notification.sent_at.date()).days
    return days_since >= REALERT_INTERVAL_DAYS


def run_daily_check():
    """Finds thirsty plants, builds digests, and sends reminders.

    Safe to call with no contact info configured - it simply does nothing.
    """
    plants = Plant.query.filter_by(active=True).all()
    thirsty = [p for p in plants if is_thirsty(p)]
    to_alert = [p for p in thirsty if _needs_alert(p)]

    if not to_alert:
        print("No plants need a new reminder today.")
        return

    settings = ContactSettings.query.first()
    if settings is None or (not settings.phone_number and not settings.email):
        print("No contact info configured - skipping reminders.")
        return

    digest_id = new_digest_id()
    plant_summaries = [plant_with_schedule(p) for p in to_alert]

    if settings.phone_number:
        message = build_sms_digest(plant_summaries)
        send_sms(settings.phone_number, message)
        for p in to_alert:
            db.session.add(NotificationsLog(plant_id=p.id, channel="sms", digest_id=digest_id))

    if settings.email:
        subject = f"{len(to_alert)} plant(s) need watering"
        body = build_email_digest(plant_summaries)
        send_email(settings.email, subject, body)
        for p in to_alert:
            db.session.add(NotificationsLog(plant_id=p.id, channel="email", digest_id=digest_id))

    db.session.commit()
    print(f"Sent reminders for {len(to_alert)} plant(s), digest {digest_id}.")


def start_scheduler(app):
    """Registers the daily job with APScheduler, to run inside the Flask app process."""
    from apscheduler.schedulers.background import BackgroundScheduler

    scheduler = BackgroundScheduler()
    hour = int(os.environ.get("REMINDER_HOUR", "8"))
    minute = int(os.environ.get("REMINDER_MINUTE", "0"))

    def job():
        with app.app_context():
            run_daily_check()

    scheduler.add_job(job, "cron", hour=hour, minute=minute)
    scheduler.start()
    return scheduler


if __name__ == "__main__":
    from app import create_app

    app = create_app()
    with app.app_context():
        run_daily_check()
