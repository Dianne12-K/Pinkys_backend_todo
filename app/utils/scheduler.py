from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timezone

scheduler = BackgroundScheduler()


def start_scheduler(app):
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
    with app.app_context():
        from app.models import Reminder
        from app.extensions import db

        now = datetime.now(timezone.utc)
        due = Reminder.query.filter(
            Reminder.trigger_at <= now,
            Reminder.is_sent == False
        ).all()

        for reminder in due:
            _dispatch(reminder, app)
            reminder.is_sent = True

        db.session.commit()
        if due:
            app.logger.info(f"Dispatched {len(due)} reminder(s).")


def _dispatch(reminder, app):
    channel = reminder.channel
    task = reminder.task
    user = task.owner

    app.logger.info(f"[{channel.upper()}] Reminder for task '{task.title}' → {user.email}")

    if channel == "email":
        _send_email(
            to_email=user.email,
            task_title=task.title,
            task_description=task.description,
            due_date=task.due_date,
            app=app
        )
    elif channel == "sms":
        _send_sms(
            task_title=task.title,
            due_date=task.due_date,
            app=app
        )
    elif channel == "push":
        app.logger.info(f"[PUSH] Push notification for '{task.title}' — wire up FCM here")


def _send_email(to_email, task_title, task_description, due_date, app):
    import os
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail

    due = due_date.strftime("%d %b %Y at %H:%M") if due_date else "No due date"

    message = Mail(
        from_email=os.getenv("MAIL_FROM"),
        to_emails=to_email,
        subject=f"⏰ Reminder: {task_title}",
        html_content=f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto;">
                <h2 style="color: #e91e8c;">📌 Task Reminder</h2>
                <p>This is a reminder for your task:</p>
                <h3 style="color: #333;">{task_title}</h3>
                <p>{task_description or 'No description provided.'}</p>
                <p><strong>Due:</strong> {due}</p>
                <hr/>
                <small style="color: #999;">Pinky's Todo App</small>
            </div>
        """
    )

    try:
        sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        response = sg.send(message)
        app.logger.info(f"[EMAIL] Sent to {to_email} — status {response.status_code}")
    except Exception as e:
        app.logger.error(f"[EMAIL] Failed to send to {to_email}: {e}")


def _send_sms(task_title, due_date, app):
    import os
    from twilio.rest import Client

    due = due_date.strftime("%d %b %Y at %H:%M") if due_date else "No due date"
    body = f"⏰ Pinky's Reminder: '{task_title}' is due {due}"

    try:
        client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )
        message = client.messages.create(
            body=body,
            from_=os.getenv("TWILIO_FROM_NUMBER"),
            to="+254700000000"  # TODO: store user phone number in User model
        )
        app.logger.info(f"[SMS] Sent — SID: {message.sid}")
    except Exception as e:
        app.logger.error(f"[SMS] Failed: {e}")