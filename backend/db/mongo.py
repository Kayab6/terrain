from pymongo import MongoClient
from pymongo.errors import PyMongoError


class MongoConnectionError(RuntimeError):
    pass


_client = None


def init_mongo(app):
    global _client

    uri = app.config["MONGO_URI"]
    database_name = app.config["MONGO_DATABASE"]
    if not uri or not database_name:
        raise MongoConnectionError("MONGO_URI and MONGO_DATABASE must be configured")

    try:
        timeout = int(app.config.get("MONGO_SERVER_SELECTION_TIMEOUT_MS", 3000))
        _client = MongoClient(uri, serverSelectionTimeoutMS=timeout)
        _client.admin.command("ping")
        app.extensions["mongo"] = {
            "client": _client,
            "database": _client[database_name],
        }
        _client[database_name]["saved_routes"].create_index("createdAt")
        _client[database_name]["evacuation_scenarios"].create_index("createdAt")
        return app.extensions["mongo"]["database"]
    except PyMongoError as exc:
        raise MongoConnectionError(
            f"Unable to connect to MongoDB database '{database_name}'"
        ) from exc


def get_database(app):
    mongo = app.extensions.get("mongo")
    if mongo is None:
        raise MongoConnectionError("MongoDB has not been initialized")
    return mongo["database"]


def close_mongo(app=None):
    global _client
    if _client is not None:
        _client.close()
        _client = None
    if app is not None:
        app.extensions.pop("mongo", None)


def mongo_status(app):
    enabled = bool(app.config.get("MONGO_PERSISTENCE_ENABLED", False))
    uri_configured = bool(app.config.get("MONGO_URI"))
    database_configured = bool(app.config.get("MONGO_DATABASE"))
    if not enabled:
        return {
            "enabled": False,
            "connected": False,
            "backend": "memory",
            "message": "MongoDB persistence is disabled",
            "uri_configured": uri_configured,
            "database_configured": database_configured,
        }
    if "mongo" not in app.extensions:
        return {
            "enabled": True,
            "connected": False,
            "backend": "memory",
            "message": "MongoDB persistence is unavailable; using memory storage",
            "uri_configured": uri_configured,
            "database_configured": database_configured,
        }
    try:
        app.extensions["mongo"]["client"].admin.command("ping")
        return {
            "enabled": True,
            "connected": True,
            "backend": "mongodb",
            "message": "MongoDB persistence is available",
            "uri_configured": uri_configured,
            "database_configured": database_configured,
        }
    except PyMongoError as exc:
        return {
            "enabled": True,
            "connected": False,
            "backend": "memory",
            "message": "MongoDB persistence is unavailable; using memory storage",
            "error": type(exc).__name__,
        }
