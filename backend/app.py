import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(BACKEND_DIR / ".env", override=False)

from flask import Flask
from flask_cors import CORS

try:
    from .config import Config
    from .routes import api
    from .db.mongo import MongoConnectionError, init_mongo
except ImportError:
    from config import Config
    from routes import api
    from db.mongo import MongoConnectionError, init_mongo


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    CORS(app, resources={r"/api/*": {"origins": "*"}})
    app.register_blueprint(api)
    app.extensions["repositories"] = {}

    if app.config["MONGO_PERSISTENCE_ENABLED"]:
        try:
            init_mongo(app)
        except MongoConnectionError as exc:
            app.extensions["mongo_startup_error"] = str(exc)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
