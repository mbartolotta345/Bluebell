"""Daily reminder job - finds thirsty plants and sends a grouped digest.

Runnable two ways:
  1. Standalone, e.g. via cron:      python scheduler.py
  2. Embedded in the Flask app via APScheduler: call start_scheduler(app)
"""
import os
from datetime import date

from dotenv import load_dotenv

load_dotenv()

from models import ContactSettings, NotificationsLog, Plant, User, db  # noqa: E402
from services.notifications import (  # noqa: E402
    build_email_digest,
    build_sms_digest,
    new_digest_id,
    send_email,
    send_sms,
)
from utils import is_thirsty, plant_with_schedule  # noqa: E402

REALERT_INTERVAL_DAYS = int(os.environ.get("REALERT_INTERVAL_DAYS", "3"))


def _needs_alert(plant, user):
    """True if thirsty and this user hasn't already been alerted recently
    for this overdue stretch. Plants are shared, but each logged-in user
    who has set up reminders is alerted independently."""
    last_notification = (
        NotificationsLog.query.filter(NotificationsLog.plant_id == plant.id)
        .filter(NotificationsLog.user_id == user.id)
        .filter(NotificationsLog.sent_at >= plant.last_watered_at)
        .order_by(NotificationsLog.sent_at.desc())
        .first()
    )
    if last_notification is None:
        return True
    days_since = (date.today() - last_notification.sent_at.date()).days
    return days_since >= REALERT_INTERVAL_DAYS


def _run_daily_check_for_user(user, plants):
    """Finds which of the shared plants this user needs alerting about, and
    sends them a digest via their own reminder contact settings.

    Safe to call with no contact info configured - it simply does nothing.
    """
    thirsty = [p for p in plants if is_thirsty(p)]
    to_alert = [p for p in thirsty if _needs_alert(p, user)]

    if not to_alert:
        return

    settings = ContactSettings.query.filter_by(user_id=user.id).first()
    if settings is None or (not settings.phone_number and not settings.email):
        return

    digest_id = new_digest_id()
    plant_summaries = [plant_with_schedule(p) for p in to_alert]

    if settings.phone_number:
        message = build_sms_digest(plant_summaries)
        send_sms(settings.phone_number, message)
        for p in to_alert:
            db.session.add(
                NotificationsLog(plant_id=p.id, user_id=user.id, channel="sms", digest_id=digest_id)
            )

    if settings.email:
        subject = f"{len(to_alert)} plant(s) need watering"
        body = build_email_digest(plant_summaries)
        send_email(settings.email, subject, body)
        for p in to_alert:
            db.session.add(
                NotificationsLog(plant_id=p.id, user_id=user.id, channel="email", digest_id=digest_id)
            )

    db.session.commit()
    print(f"Sent reminders to {user.email} for {len(to_alert)} plant(s), digest {digest_id}.")


def run_daily_check():
    """Runs the reminder check for every registered user against the
    shared plant list - anyone can use the tracker without an account,
    but reminders are opt-in per logged-in user."""
    users = User.query.all()
    if not users:
        print("No users have signed up for reminders yet.")
        return

    plants = Plant.query.filter_by(active=True).all()
    for user in users:
        _run_daily_check_for_user(user, plants)


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
