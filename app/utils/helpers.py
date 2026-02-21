from flask import jsonify, request
from datetime import datetime


# ── Response helpers ──────────────────────────────────────────────────────────

def success(data=None, message="OK", status=200):
    return jsonify({"success": True, "message": message, "data": data}), status


def error(message="Error", status=400, detail=None):
    body = {"success": False, "error": message}
    if detail:
        body["detail"] = detail
    return jsonify(body), status


# ── Pagination helper ─────────────────────────────────────────────────────────

def paginate(query):
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 100)  # cap at 100
    result = query.paginate(page=page, per_page=per_page, error_out=False)
    return result.items, {
        "page": result.page,
        "per_page": result.per_page,
        "total": result.total,
        "pages": result.pages,
    }


# ── Date parsing ──────────────────────────────────────────────────────────────

def parse_datetime(value: str):
    """Parse ISO 8601 datetime string, return None on failure."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


# ── Validation ────────────────────────────────────────────────────────────────

VALID_PRIORITIES = {"low", "medium", "high"}
VALID_STATUSES = {"pending", "completed", "archived"}
VALID_CHANNELS = {"push", "email", "sms"}
VALID_RECURRENCE = {"daily", "weekly", "monthly"}


def validate_task_payload(data: dict) -> list:
    """Returns a list of validation error strings."""
    errors = []
    if not data.get("title", "").strip():
        errors.append("title is required")
    if "priority" in data and data["priority"] not in VALID_PRIORITIES:
        errors.append(f"priority must be one of {VALID_PRIORITIES}")
    if "status" in data and data["status"] not in VALID_STATUSES:
        errors.append(f"status must be one of {VALID_STATUSES}")
    if data.get("is_recurring") and data.get("recurrence_rule") not in VALID_RECURRENCE:
        errors.append(f"recurrence_rule must be one of {VALID_RECURRENCE}")
    return errors