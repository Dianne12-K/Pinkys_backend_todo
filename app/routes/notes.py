from flask import Blueprint, request, g
from app.extensions import db
from app.models import Note
from app.middleware.auth import auth_required
from app.utils.helpers import success, error, paginate

notes_bp = Blueprint("notes", __name__, url_prefix="/api/notes")

VALID_COLORS = {"yellow", "blue", "green", "pink", "white"}


@notes_bp.get("/")
@auth_required
def list_notes():
    """
    Get all notes for the current user.
    ---
    tags:
      - Notes
    security:
      - Bearer: []
    parameters:
      - in: query
        name: task_id
        schema:
          type: integer
          example: 1
        description: Filter notes linked to a specific task
      - in: query
        name: is_pinned
        schema:
          type: boolean
          example: true
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
        description: List of notes
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
                    notes:
                      type: array
                      items:
                        $ref: '#/definitions/NoteResponse'
                    meta:
                      type: object
    """
    query = Note.query.filter_by(user_id=g.current_user.id)
    if task_id := request.args.get("task_id", type=int):
        query = query.filter_by(task_id=task_id)
    if request.args.get("is_pinned") == "true":
        query = query.filter_by(is_pinned=True)
    query = query.order_by(Note.is_pinned.desc(), Note.updated_at.desc())
    items, meta = paginate(query)
    return success({"notes": [n.to_dict() for n in items], "meta": meta})


@notes_bp.post("/")
@auth_required
def create_note():
    """
    Create a new note.
    ---
    tags:
      - Notes
    security:
      - Bearer: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/definitions/NoteRequest'
    responses:
      201:
        description: Note created
        content:
          application/json:
            schema:
              $ref: '#/definitions/NoteResponse'
      400:
        description: Validation error
        content:
          application/json:
            schema:
              $ref: '#/definitions/ErrorResponse'
    """
    data = request.get_json() or {}
    if not data.get("content", "").strip():
        return error("content is required")
    color = data.get("color", "yellow")
    if color not in VALID_COLORS:
        return error(f"color must be one of {VALID_COLORS}")
    note = Note(
        user_id=g.current_user.id,
        task_id=data.get("task_id"),
        title=data.get("title", ""),
        content=data["content"].strip(),
        color=color,
        is_pinned=data.get("is_pinned", False),
    )
    db.session.add(note)
    db.session.commit()
    return success(note.to_dict(), "Note created", 201)


@notes_bp.get("/<int:note_id>")
@auth_required
def get_note(note_id):
    """
    Get a single note by ID.
    ---
    tags:
      - Notes
    security:
      - Bearer: []
    parameters:
      - in: path
        name: note_id
        required: true
        schema:
          type: integer
          example: 1
    responses:
      200:
        description: Note found
        content:
          application/json:
            schema:
              $ref: '#/definitions/NoteResponse'
      404:
        description: Note not found
        content:
          application/json:
            schema:
              $ref: '#/definitions/ErrorResponse'
    """
    note = Note.query.filter_by(id=note_id, user_id=g.current_user.id).first()
    if not note:
        return error("Note not found", 404)
    return success(note.to_dict())


@notes_bp.put("/<int:note_id>")
@auth_required
def update_note(note_id):
    """
    Update a note.
    ---
    tags:
      - Notes
    security:
      - Bearer: []
    parameters:
      - in: path
        name: note_id
        required: true
        schema:
          type: integer
          example: 1
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/definitions/NoteUpdateRequest'
    responses:
      200:
        description: Note updated
        content:
          application/json:
            schema:
              $ref: '#/definitions/NoteResponse'
      404:
        description: Note not found
        content:
          application/json:
            schema:
              $ref: '#/definitions/ErrorResponse'
    """
    note = Note.query.filter_by(id=note_id, user_id=g.current_user.id).first()
    if not note:
        return error("Note not found", 404)
    data = request.get_json() or {}
    if "color" in data and data["color"] not in VALID_COLORS:
        return error(f"color must be one of {VALID_COLORS}")
    note.title = data.get("title", note.title)
    note.content = data.get("content", note.content).strip()
    note.color = data.get("color", note.color)
    note.is_pinned = data.get("is_pinned", note.is_pinned)
    note.task_id = data.get("task_id", note.task_id)
    db.session.commit()
    return success(note.to_dict(), "Note updated")


@notes_bp.patch("/<int:note_id>/pin")
@auth_required
def toggle_pin(note_id):
    """
    Toggle pin status of a note.
    ---
    tags:
      - Notes
    security:
      - Bearer: []
    parameters:
      - in: path
        name: note_id
        required: true
        schema:
          type: integer
          example: 1
    responses:
      200:
        description: Pin toggled
        content:
          application/json:
            schema:
              $ref: '#/definitions/NoteResponse'
      404:
        description: Note not found
        content:
          application/json:
            schema:
              $ref: '#/definitions/ErrorResponse'
    """
    note = Note.query.filter_by(id=note_id, user_id=g.current_user.id).first()
    if not note:
        return error("Note not found", 404)
    note.is_pinned = not note.is_pinned
    db.session.commit()
    msg = "Note pinned" if note.is_pinned else "Note unpinned"
    return success(note.to_dict(), msg)


@notes_bp.delete("/<int:note_id>")
@auth_required
def delete_note(note_id):
    """
    Delete a note.
    ---
    tags:
      - Notes
    security:
      - Bearer: []
    parameters:
      - in: path
        name: note_id
        required: true
        schema:
          type: integer
          example: 1
    responses:
      200:
        description: Note deleted
      404:
        description: Note not found
        content:
          application/json:
            schema:
              $ref: '#/definitions/ErrorResponse'
    """
    note = Note.query.filter_by(id=note_id, user_id=g.current_user.id).first()
    if not note:
        return error("Note not found", 404)
    db.session.delete(note)
    db.session.commit()
    return success(None, "Note deleted")