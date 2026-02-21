from flask import Blueprint, request, g
from app.extensions import db
from app.models import Task
from app.middleware.auth import auth_required
from app.utils.helpers import success, error, paginate, parse_datetime, validate_task_payload

tasks_bp = Blueprint("tasks", __name__, url_prefix="/api/tasks")


@tasks_bp.get("/")
@auth_required
def list_tasks():
    """
    Get all tasks for the current user.
    ---
    tags:
      - Tasks
    security:
      - Bearer: []
    parameters:
      - in: query
        name: status
        schema:
          type: string
          enum: [pending, completed, archived]
      - in: query
        name: priority
        schema:
          type: string
          enum: [low, medium, high]
      - in: query
        name: page
        schema:
          type: integer
          default: 1
      - in: query
        name: per_page
        schema:
          type: integer
          default: 20
    responses:
      200:
        description: Paginated list of tasks
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                data:
                  type: object
                  properties:
                    tasks:
                      type: array
                      items:
                        $ref: '#/definitions/TaskResponse'
                    meta:
                      type: object
                      properties:
                        page:     { type: integer, example: 1 }
                        per_page: { type: integer, example: 20 }
                        total:    { type: integer, example: 5 }
                        pages:    { type: integer, example: 1 }
    """
    query = Task.query.filter_by(user_id=g.current_user.id)
    if status := request.args.get("status"):
        query = query.filter_by(status=status)
    if priority := request.args.get("priority"):
        query = query.filter_by(priority=priority)
    query = query.order_by(Task.due_date.asc())
    items, meta = paginate(query)
    return success({"tasks": [t.to_dict() for t in items], "meta": meta})


@tasks_bp.post("/")
@auth_required
def create_task():
    """
    Create a new task.
    ---
    tags:
      - Tasks
    security:
      - Bearer: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/definitions/TaskRequest'
    responses:
      201:
        description: Task created
        content:
          application/json:
            schema:
              $ref: '#/definitions/TaskResponse'
      400:
        description: Validation error
        content:
          application/json:
            schema:
              $ref: '#/definitions/ErrorResponse'
    """
    data = request.get_json() or {}
    errs = validate_task_payload(data)
    if errs:
        return error("Validation failed", detail=errs)
    task = Task(
        user_id=g.current_user.id,
        title=data["title"].strip(),
        description=data.get("description", ""),
        due_date=parse_datetime(data.get("due_date")),
        priority=data.get("priority", "medium"),
        is_recurring=data.get("is_recurring", False),
        recurrence_rule=data.get("recurrence_rule"),
    )
    db.session.add(task)
    db.session.commit()
    return success(task.to_dict(), "Task created", 201)


@tasks_bp.get("/<int:task_id>")
@auth_required
def get_task(task_id):
    """
    Get a single task by ID.
    ---
    tags:
      - Tasks
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
        description: Task found
        content:
          application/json:
            schema:
              $ref: '#/definitions/TaskResponse'
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
    return success(task.to_dict())


@tasks_bp.put("/<int:task_id>")
@auth_required
def update_task(task_id):
    """
    Update a task.
    ---
    tags:
      - Tasks
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
            $ref: '#/definitions/TaskUpdateRequest'
    responses:
      200:
        description: Task updated
        content:
          application/json:
            schema:
              $ref: '#/definitions/TaskResponse'
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
    errs = validate_task_payload({**{"title": task.title}, **data})
    if errs:
        return error("Validation failed", detail=errs)
    task.title = data.get("title", task.title).strip()
    task.description = data.get("description", task.description)
    task.priority = data.get("priority", task.priority)
    task.status = data.get("status", task.status)
    task.is_recurring = data.get("is_recurring", task.is_recurring)
    task.recurrence_rule = data.get("recurrence_rule", task.recurrence_rule)
    if "due_date" in data:
        task.due_date = parse_datetime(data["due_date"])
    db.session.commit()
    return success(task.to_dict(), "Task updated")


@tasks_bp.patch("/<int:task_id>/complete")
@auth_required
def complete_task(task_id):
    """
    Mark a task as completed.
    ---
    tags:
      - Tasks
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
        description: Task marked complete
        content:
          application/json:
            schema:
              $ref: '#/definitions/TaskResponse'
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
    task.status = "completed"
    db.session.commit()
    return success(task.to_dict(), "Task completed")


@tasks_bp.delete("/<int:task_id>")
@auth_required
def delete_task(task_id):
    """
    Delete a task and all its reminders.
    ---
    tags:
      - Tasks
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
        description: Task deleted
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
    db.session.delete(task)
    db.session.commit()
    return success(None, "Task deleted")