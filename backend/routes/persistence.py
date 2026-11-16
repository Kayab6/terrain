from flask import current_app, jsonify, request
from pymongo.errors import PyMongoError

from db.mongo import mongo_status
from db.repositories import MemoryRepository, MongoRepository

from . import api
from .errors import error_response


COLLECTIONS = {
    "routes": "saved_routes",
    "scenarios": "evacuation_scenarios",
}


def _repository(kind):
    repositories = current_app.extensions.setdefault("repositories", {})
    if kind not in repositories:
        mongo = current_app.extensions.get("mongo")
        if mongo_status(current_app)["connected"]:
            repositories[kind] = MongoRepository(mongo["database"], COLLECTIONS[kind])
        else:
            repositories[kind] = MemoryRepository()
    return repositories[kind]


def _payload():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None
    return payload


@api.get("/api/persistence/status")
def persistence_status():
    return jsonify({"success": True, **mongo_status(current_app)})


@api.get("/api/persistence/health")
def persistence_health():
    status = mongo_status(current_app)
    database_configured = bool(
        current_app.config.get("MONGO_URI")
        and current_app.config.get("MONGO_DATABASE")
    )
    return jsonify(
        {
            "success": True,
            "persistence_enabled": status["enabled"],
            "mongodb_reachable": status["connected"],
            "database_configured": database_configured,
            "message": status["message"],
        }
    )


@api.get("/api/persistence/<kind>")
def list_persisted(kind):
    if kind == "health":
        return persistence_health()
    if kind == "status":
        return persistence_status()
    if kind not in COLLECTIONS:
        return error_response("Unknown persistence collection", 404, "not_found")
    try:
        return jsonify({"success": True, "items": _repository(kind).list()})
    except PyMongoError as exc:
        return error_response(
            "Persistence storage is unavailable", 503, "persistence_error",
            {"operation": "list", "reason": type(exc).__name__},
        )


@api.post("/api/persistence/<kind>")
def create_persisted(kind):
    if kind not in COLLECTIONS:
        return error_response("Unknown persistence collection", 404, "not_found")
    payload = _payload()
    if payload is None:
        return error_response("Request body must be a JSON object")
    try:
        item = _repository(kind).create(payload)
        return jsonify({"success": True, "item": item}), 201
    except PyMongoError as exc:
        return error_response(
            "Persistence storage is unavailable", 503, "persistence_error",
            {"operation": "create", "reason": type(exc).__name__},
        )


@api.get("/api/persistence/<kind>/<item_id>")
def get_persisted(kind, item_id):
    if kind not in COLLECTIONS:
        return error_response("Unknown persistence collection", 404, "not_found")
    item = _repository(kind).get(item_id)
    if item is None:
        return error_response("Persisted item not found", 404, "not_found")
    return jsonify({"success": True, "item": item})


@api.put("/api/persistence/<kind>/<item_id>")
def update_persisted(kind, item_id):
    if kind not in COLLECTIONS:
        return error_response("Unknown persistence collection", 404, "not_found")
    payload = _payload()
    if payload is None:
        return error_response("Request body must be a JSON object")
    item = _repository(kind).update(item_id, payload)
    if item is None:
        return error_response("Persisted item not found", 404, "not_found")
    return jsonify({"success": True, "item": item})


@api.delete("/api/persistence/<kind>/<item_id>")
def delete_persisted(kind, item_id):
    if kind not in COLLECTIONS:
        return error_response("Unknown persistence collection", 404, "not_found")
    if not _repository(kind).delete(item_id):
        return error_response("Persisted item not found", 404, "not_found")
    return jsonify({"success": True, "message": "Persisted item deleted"})
