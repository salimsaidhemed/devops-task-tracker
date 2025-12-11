from flask import Blueprint, jsonify

api_bp = Blueprint("api", __name__)

@api_bp.get("/tasks")
def list_tasks():
    # TODO: implement DB call + optional Redis caching
    return jsonify({"tasks": [], "message": "Not implemented yet"}), 200