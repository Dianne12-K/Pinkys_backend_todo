import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///todo.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 1 day in seconds

    SWAGGER = {
        "title": "Todo & Reminder API",
        "uiversion": 3,
        "version": "1.0.0",
        "description": "Full stack To-Do and Reminder API built with Flask",
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT token. Format: **Bearer &lt;token&gt;**"
            }
        },
        "security": [{"Bearer": []}],
        "definitions": {

            # ── Auth ──────────────────────────────────────────────────────────
            "RegisterRequest": {
                "type": "object",
                "required": ["email", "username", "password"],
                "properties": {
                    "email":    {"type": "string", "example": "diana@example.com"},
                    "username": {"type": "string", "example": "diana_k"},
                    "password": {"type": "string", "example": "MySecret123!"}
                }
            },
            "LoginRequest": {
                "type": "object",
                "required": ["email", "password"],
                "properties": {
                    "email":    {"type": "string", "example": "diana@example.com"},
                    "password": {"type": "string", "example": "MySecret123!"}
                }
            },
            "UserResponse": {
                "type": "object",
                "properties": {
                    "id":       {"type": "integer", "example": 1},
                    "email":    {"type": "string",  "example": "diana@example.com"},
                    "username": {"type": "string",  "example": "diana_k"}
                }
            },
            "AuthResponse": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": True},
                    "message": {"type": "string",  "example": "Login successful"},
                    "data": {
                        "type": "object",
                        "properties": {
                            "user":  {"$ref": "#/definitions/UserResponse"},
                            "token": {"type": "string", "example": "eyJhbGciOiJIUzI1NiJ9..."}
                        }
                    }
                }
            },

            # ── Tasks ─────────────────────────────────────────────────────────
            "TaskRequest": {
                "type": "object",
                "required": ["title"],
                "properties": {
                    "title":          {"type": "string",  "example": "Submit project report"},
                    "description":    {"type": "string",  "example": "Final report for Q1 2026"},
                    "due_date":       {"type": "string",  "format": "date-time", "example": "2026-03-15T09:00:00"},
                    "priority":       {"type": "string",  "enum": ["low", "medium", "high"], "example": "high"},
                    "is_recurring":   {"type": "boolean", "example": False},
                    "recurrence_rule":{"type": "string",  "enum": ["daily", "weekly", "monthly"], "example": "weekly"}
                }
            },
            "TaskUpdateRequest": {
                "type": "object",
                "properties": {
                    "title":          {"type": "string",  "example": "Updated task title"},
                    "description":    {"type": "string",  "example": "Updated description"},
                    "due_date":       {"type": "string",  "format": "date-time", "example": "2026-04-01T10:00:00"},
                    "priority":       {"type": "string",  "enum": ["low", "medium", "high"], "example": "low"},
                    "status":         {"type": "string",  "enum": ["pending", "completed", "archived"], "example": "completed"},
                    "is_recurring":   {"type": "boolean", "example": False},
                    "recurrence_rule":{"type": "string",  "enum": ["daily", "weekly", "monthly"]}
                }
            },
            "TaskResponse": {
                "type": "object",
                "properties": {
                    "id":             {"type": "integer", "example": 1},
                    "title":          {"type": "string",  "example": "Submit project report"},
                    "description":    {"type": "string",  "example": "Final report for Q1 2026"},
                    "due_date":       {"type": "string",  "format": "date-time", "example": "2026-03-15T09:00:00"},
                    "priority":       {"type": "string",  "example": "high"},
                    "status":         {"type": "string",  "example": "pending"},
                    "is_recurring":   {"type": "boolean", "example": False},
                    "recurrence_rule":{"type": "string",  "example": None},
                    "reminders":      {"type": "array", "items": {"$ref": "#/definitions/ReminderResponse"}},
                    "created_at":     {"type": "string",  "example": "2026-02-21T10:00:00"}
                }
            },

            # ── Reminders ─────────────────────────────────────────────────────
            "ReminderRequest": {
                "type": "object",
                "required": ["trigger_at"],
                "properties": {
                    "trigger_at": {"type": "string", "format": "date-time", "example": "2026-03-15T08:00:00"},
                    "channel":    {"type": "string", "enum": ["push", "email", "sms"], "example": "push"}
                }
            },
            "SnoozeRequest": {
                "type": "object",
                "properties": {
                    "minutes": {"type": "integer", "example": 10}
                }
            },
            "ReminderResponse": {
                "type": "object",
                "properties": {
                    "id":         {"type": "integer", "example": 1},
                    "task_id":    {"type": "integer", "example": 1},
                    "trigger_at": {"type": "string",  "format": "date-time", "example": "2026-03-15T08:00:00"},
                    "channel":    {"type": "string",  "example": "push"},
                    "is_sent":    {"type": "boolean", "example": False}
                }
            },

            # ── Notes ─────────────────────────────────────────────────────────
            "NoteRequest": {
                "type": "object",
                "required": ["content"],
                "properties": {
                    "title":     {"type": "string",  "example": "Sprint planning ideas"},
                    "content":   {"type": "string",  "example": "Consider breaking auth into its own service"},
                    "color":     {"type": "string",  "enum": ["yellow", "blue", "green", "pink", "white"], "example": "yellow"},
                    "is_pinned": {"type": "boolean", "example": False},
                    "task_id":   {"type": "integer", "example": 1, "description": "Optionally link to a task"}
                }
            },
            "NoteUpdateRequest": {
                "type": "object",
                "properties": {
                    "title":     {"type": "string",  "example": "Updated title"},
                    "content":   {"type": "string",  "example": "Updated note content"},
                    "color":     {"type": "string",  "enum": ["yellow", "blue", "green", "pink", "white"], "example": "green"},
                    "is_pinned": {"type": "boolean", "example": True},
                    "task_id":   {"type": "integer", "example": 2}
                }
            },
            "NoteResponse": {
                "type": "object",
                "properties": {
                    "id":         {"type": "integer", "example": 1},
                    "user_id":    {"type": "integer", "example": 1},
                    "task_id":    {"type": "integer", "example": None},
                    "title":      {"type": "string",  "example": "Sprint planning ideas"},
                    "content":    {"type": "string",  "example": "Consider breaking auth into its own service"},
                    "color":      {"type": "string",  "example": "yellow"},
                    "is_pinned":  {"type": "boolean", "example": False},
                    "created_at": {"type": "string",  "example": "2026-02-21T10:00:00"},
                    "updated_at": {"type": "string",  "example": "2026-02-21T10:00:00"}
                }
            },

            # ── Generic ───────────────────────────────────────────────────────
            "ErrorResponse": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": False},
                    "error":   {"type": "string",  "example": "Something went wrong"},
                    "detail":  {"type": "array",   "items": {"type": "string"}}
                }
            }
        }
    }