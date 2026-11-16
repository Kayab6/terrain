from flask import jsonify, request
from werkzeug.exceptions import BadRequest

from . import api


@api.get("/api/health")
def health():
    return jsonify({"success": True, "message": "Backend is running"})


@api.post("/api/validate-request")
def validate_request():
    payload = request.get_json(silent=False)
    if not isinstance(payload, dict):
        raise BadRequest("Request body must be a JSON object")
    return jsonify(
        {"success": True, "message": "Request format is valid", "data": payload}
    )
