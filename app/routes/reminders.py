from flask import Blueprint, request, g
from app.extensions import db
from app.models import Task, Reminder
from app.middleware.auth import auth_required
from app.utils.helpers import success, error, parse_datetime, VALID_CHANNELS

reminders_bp = Blueprint("reminders", __name__, url_prefix="/api/tasks")


@reminders_bp.post("/<int:task_id>/reminders")
@auth_required
def add_reminder(task_id):
    """
    Add a reminder to a task.
    ---
    tags:
      - Reminders
    security:
      - Bearer: []
    parameters:
      - in: path
        name: task_id
        required: true
        schema:
          type: integer
          example: 1
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/definitions/ReminderRequest'
    responses:
      201:
        description: Reminder created
        content:
          application/json:
            schema:
              $ref: '#/definitions/ReminderResponse'
      400:
        description: Validation error
        content:
          application/json:
            schema:
              $ref: '#/definitions/ErrorResponse'
      404:
        description: Task not found
        content:
          application/json:
            schema:
              $ref: '#/definitions/ErrorResponse'
    """
    task = Task.query.filter_by(id=task_id, user_id=g.current_user.id).first()
    if not task:
        return error("Task not found", 404)
    data = request.get_json() or {}
    trigger_at = parse_datetime(data.get("trigger_at"))
    if not trigger_at:
        return error("trigger_at is required and must be a valid ISO datetime")
    channel = data.get("channel", "push")
    if channel not in VALID_CHANNELS:
        return error(f"channel must be one of {VALID_CHANNELS}")
    reminder = Reminder(task_id=task.id, trigger_at=trigger_at, channel=channel)
    db.session.add(reminder)
    db.session.commit()
    return success(reminder.to_dict(), "Reminder added", 201)


@reminders_bp.get("/<int:task_id>/reminders")
@auth_required
def list_reminders(task_id):
    """
    List all reminders for a task.
    ---
    tags:
      - Reminders
    security:
      - Bearer: []
    parameters:
      - in: path
        name: task_id
        required: true
        schema:
          type: integer
          example: 1
    responses:
      200:
        description: List of reminders
        content:
          application/json:
            schema:
              type: array
              items:
                $ref: '#/definitions/ReminderResponse'
      404:
        description: Task not found
        content:
          application/json:
            schema:
              $ref: '#/definitions/ErrorResponse'
    """
    task = Task.query.filter_by(id=task_id, user_id=g.current_user.id).first()
    if not task:
        return error("Task not found", 404)
    return success([r.to_dict() for r in task.reminders])


@reminders_bp.delete("/<int:task_id>/reminders/<int:reminder_id>")
@auth_required
def delete_reminder(task_id, reminder_id):
    """
    Delete a specific reminder.
    ---
    tags:
      - Reminders
    security:
      - Bearer: []
    parameters:
      - in: path
        name: task_id
        required: true
        schema:
          type: integer
          example: 1
      - in: path
        name: reminder_id
        required: true
        schema:
          type: integer
          example: 1
    responses:
      200:
        description: Reminder deleted
      404:
        description: Not found
        content:
          application/json:
            schema:
              $ref: '#/definitions/ErrorResponse'
    """
    task = Task.query.filter_by(id=task_id, user_id=g.current_user.id).first()
    if not task:
        return error("Task not found", 404)
    reminder = Reminder.query.filter_by(id=reminder_id, task_id=task_id).first()
    if not reminder:
        return error("Reminder not found", 404)
    db.session.delete(reminder)
    db.session.commit()
    return success(None, "Reminder deleted")


@reminders_bp.patch("/<int:task_id>/reminders/<int:reminder_id>/snooze")
@auth_required
def snooze_reminder(task_id, reminder_id):
    """
    Snooze a reminder by N minutes.
    ---
    tags:
      - Reminders
    security:
      - Bearer: []
    parameters:
      - in: path
        name: task_id
        required: true
        schema:
          type: integer
          example: 1
      - in: path
        name: reminder_id
        required: true
        schema:
          type: integer
          example: 1
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/definitions/SnoozeRequest'
    responses:
      200:
        description: Reminder snoozed
        content:
          application/json:
            schema:
              $ref: '#/definitions/ReminderResponse'
      404:
        description: Not found
        content:
          application/json:
            schema:
              $ref: '#/definitions/ErrorResponse'
    """
    from datetime import timedelta
    task = Task.query.filter_by(id=task_id, user_id=g.current_user.id).first()
    if not task:
        return error("Task not found", 404)
    reminder = Reminder.query.filter_by(id=reminder_id, task_id=task_id).first()
    if not reminder:
        return error("Reminder not found", 404)
    data = request.get_json() or {}
    minutes = data.get("minutes", 10)
    reminder.trigger_at = reminder.trigger_at + timedelta(minutes=int(minutes))
    reminder.is_sent = False
    db.session.commit()
    return success(reminder.to_dict(), f"Reminder snoozed by {minutes} minutes")