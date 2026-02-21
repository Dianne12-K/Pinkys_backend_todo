from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timezone

scheduler = BackgroundScheduler()


def start_scheduler(app):
    """Start APScheduler and register the reminder check job."""
    scheduler.add_job(
        func=lambda: check_reminders(app),
        trigger="interval",
        minutes=1,
        id="reminder_check",
        replace_existing=True,
    )
    scheduler.start()
    app.logger.info("Scheduler started — checking reminders every minute.")


def check_reminders(app):
    """Fire due reminders. Runs inside app context."""
    with app.app_context():
        from app.models import Reminder
        from app.extensions import db

        now = datetime.now(timezone.utc)
        due = Reminder.query.filter(
            Reminder.trigger_at <= now,
            Reminder.is_sent == False  # noqa: E712
        ).all()

        for reminder in due:
            _dispatch(reminder, app)
            reminder.is_sent = True

        db.session.commit()
        if due:
            app.logger.info(f"Dispatched {len(due)} reminder(s).")


def _dispatch(reminder, app):
    """Route reminder to the right channel."""
    channel = reminder.channel
    task = reminder.task
    app.logger.info(f"[{channel.upper()}] Reminder for task '{task.title}' (id={task.id})")

    if channel == "email":
        # TODO: plug in SendGrid / SMTP here
        pass
    elif channel == "sms":
        # TODO: plug in Twilio here
        pass
    elif channel == "push":
        # TODO: plug in Firebase FCM / Web Push here
        pass