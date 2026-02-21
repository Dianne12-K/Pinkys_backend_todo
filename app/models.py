from datetime import datetime, timezone
from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    tasks = db.relationship("Task", backref="owner", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {"id": self.id, "email": self.email, "username": self.username}


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    due_date = db.Column(db.DateTime, nullable=True)
    priority = db.Column(db.String(10), default="medium")  # low | medium | high
    status = db.Column(db.String(20), default="pending")   # pending | completed | archived
    is_recurring = db.Column(db.Boolean, default=False)
    recurrence_rule = db.Column(db.String(50), nullable=True)  # daily | weekly | monthly
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    reminders = db.relationship("Reminder", backref="task", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "priority": self.priority,
            "status": self.status,
            "is_recurring": self.is_recurring,
            "recurrence_rule": self.recurrence_rule,
            "reminders": [r.to_dict() for r in self.reminders],
            "created_at": self.created_at.isoformat(),
        }


class Reminder(db.Model):
    __tablename__ = "reminders"

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"), nullable=False)
    trigger_at = db.Column(db.DateTime, nullable=False)
    channel = db.Column(db.String(20), default="push")  # push | email | sms
    is_sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "task_id": self.task_id,
            "trigger_at": self.trigger_at.isoformat(),
            "channel": self.channel,
            "is_sent": self.is_sent,
        }


class Note(db.Model):
    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"), nullable=True)  # optional - link to a task
    title = db.Column(db.String(200), default="")
    content = db.Column(db.Text, nullable=False)
    color = db.Column(db.String(20), default="yellow")  # yellow | blue | green | pink | white
    is_pinned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "task_id": self.task_id,
            "title": self.title,
            "content": self.content,
            "color": self.color,
            "is_pinned": self.is_pinned,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }