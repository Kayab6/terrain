from unittest.mock import patch

import pytest
from pymongo.errors import ServerSelectionTimeoutError

from app import create_app
from db.mongo import MongoConnectionError, init_mongo, mongo_status


def test_mongo_connection_failure_is_reported():
    app = create_app(
        {
            "MONGO_URI": "mongodb://127.0.0.1:1",
            "MONGO_DATABASE": "depthwizard-test",
        }
    )

    with patch("db.mongo.MongoClient") as mongo_client:
        mongo_client.return_value.admin.command.side_effect = (
            ServerSelectionTimeoutError("Connection refused")
        )
        with pytest.raises(MongoConnectionError, match="Unable to connect to MongoDB"):
            init_mongo(app)


def test_disabled_mongo_uses_memory_status():
    app = create_app({"TESTING": True, "MONGO_PERSISTENCE_ENABLED": False})
    status = mongo_status(app)
    assert status["enabled"] is False
    assert status["connected"] is False
    assert status["backend"] == "memory"
    assert status["message"] == "MongoDB persistence is disabled"


def test_mongo_status_does_not_expose_uri():
    app = create_app(
        {
            "TESTING": True,
            "MONGO_PERSISTENCE_ENABLED": True,
            "MONGO_URI": "mongodb://user:secret@127.0.0.1:27017",
            "MONGO_DATABASE": "depthwizard-test",
        }
    )
    status = mongo_status(app)
    serialized = repr(status)
    assert "secret" not in serialized
    assert status["uri_configured"] is True


def test_backend_env_enables_persistence():
    app = create_app({"TESTING": True})
    assert app.config["MONGO_PERSISTENCE_ENABLED"] is True


def test_mocked_mongo_connection_is_reachable():
    app = create_app(
        {
            "TESTING": True,
            "MONGO_PERSISTENCE_ENABLED": True,
            "MONGO_URI": "mongodb://127.0.0.1:27017",
            "MONGO_DATABASE": "depthwizard-test",
        }
    )
    with patch("db.mongo.MongoClient") as mongo_client:
        mongo_client.return_value.admin.command.return_value = {"ok": 1}
        init_mongo(app)
        assert mongo_status(app)["connected"] is True
