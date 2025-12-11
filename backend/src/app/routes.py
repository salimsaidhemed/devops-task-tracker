from datetime import datetime


from flask import Blueprint, jsonify, request

from .extensions import db, redis_client
from .models import Task

api_bp = Blueprint("api", __name__)

# Redis cache settings
TASK_LIST_CACHE_KEY = "tasks:all"
TASK_LIST_TTL_SECONDS = 30

def _parse_task_payload(data: dict, partial: bool = False) -> dict:
    """
    Extract and validate task fields from incoming JSON.
    If partial=True, fields are optional (for updates).
    """
    allowed_status = {"todo", "in_progress", "done"}
    allowed_priority = {"low", "medium", "high"}

    title = data.get("title")
    description = data.get("description")
    status = data.get("status")
    priority = data.get("priority")
    due_date_raw = data.get("due_date")

    if not partial:
        if not title or not isinstance(title, str):
            raise ValueError("Field 'title' is required and must be a string.")

    out: dict = {}

    if title is not None:
        out["title"] = title.strip()

    if description is not None:
        out["description"] = description.strip() if isinstance(description, str) else description

    if status is not None:
        if status not in allowed_status:
            raise ValueError(f"Invalid status '{status}'. Allowed: {sorted(allowed_status)}")
        out["status"] = status

    if priority is not None:
        if priority not in allowed_priority:
            raise ValueError(f"Invalid priority '{priority}'. Allowed: {sorted(allowed_priority)}")
        out["priority"] = priority

    if due_date_raw is not None:
        if due_date_raw == "":
            out["due_date"] = None
        else:
            try:
                out["due_date"] = datetime.fromisoformat(due_date_raw)
            except Exception as exc:  # noqa: BLE001
                raise ValueError(
                    "Invalid 'due_date'. Use ISO 8601 format, e.g. '2025-01-01T10:00:00'"
                ) from exc

    return out


def _invalidate_task_list_cache() -> None:
    if redis_client is not None:
        redis_client.delete(TASK_LIST_CACHE_KEY)

@api_bp.get("/tasks")
def list_tasks():
    """
    List all tasks.
    - If no query params: try Redis cache.
    - If query params present: bypass cache (simple for now).
    """
    use_cache = redis_client is not None and not request.args

    if use_cache:
        cached = redis_client.get(TASK_LIST_CACHE_KEY)
        if cached:
            # cached is a JSON string
            from json import loads

            return jsonify({"tasks": loads(cached), "cached": True}), 200
    # Basic filtering (optional)
    query = Task.query
    status = request.args.get("status")
    priority = request.args.get("priority")

    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)

    tasks = query.order_by(Task.created_at.desc()).all()
    tasks_data = [t.to_dict() for t in tasks]

    if use_cache:
        from json import dumps

        redis_client.setex(TASK_LIST_CACHE_KEY, TASK_LIST_TTL_SECONDS, dumps(tasks_data))

    return jsonify({"tasks": tasks_data, "cached": False}), 200

@api_bp.post("/tasks")
def create_task():
    data = request.get_json(silent=True) or {}
    try:
        fields = _parse_task_payload(data, partial=False)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    task = Task(
        title=fields["title"],
        description=fields.get("description"),
        status=fields.get("status", "todo"),
        priority=fields.get("priority", "medium"),
        due_date=fields.get("due_date"),
    )
    db.session.add(task)
    db.session.commit()

    _invalidate_task_list_cache()

    return jsonify(task.to_dict()), 201

@api_bp.get("/tasks/<int:task_id>")
def get_task(task_id: int):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(task.to_dict()), 200

@api_bp.put("/tasks/<int:task_id>")
def update_task(task_id: int):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404

    data = request.get_json(silent=True) or {}
    try:
        fields = _parse_task_payload(data, partial=True)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    for key, value in fields.items():
        setattr(task, key, value)

    db.session.commit()
    _invalidate_task_list_cache()

    return jsonify(task.to_dict()), 200

@api_bp.delete("/tasks/<int:task_id>")
def delete_task(task_id: int):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404

    db.session.delete(task)
    db.session.commit()
    _invalidate_task_list_cache()

    return jsonify({"message": "Task deleted"}), 200