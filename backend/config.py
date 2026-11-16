import os


class Config:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DATABASE = os.getenv("MONGO_DATABASE", "depthwizard")
    MONGO_SERVER_SELECTION_TIMEOUT_MS = int(
        os.getenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", "3000")
    )
    MONGO_PERSISTENCE_ENABLED = os.getenv(
        "MONGO_PERSISTENCE_ENABLED", "false"
    ).lower() in {"1", "true", "yes", "on"}
    NOMINATIM_URL = os.getenv(
        "NOMINATIM_URL", "https://nominatim.openstreetmap.org"
    )
    OVERPASS_URL = os.getenv(
        "OVERPASS_URL", "https://overpass-api.de/api/interpreter"
    )
    OVERPASS_FALLBACK_URLS = [
        url.strip()
        for url in os.getenv(
            "OVERPASS_FALLBACK_URLS",
            "https://overpass.kumi.systems/api/interpreter",
        ).split(",")
        if url.strip()
    ]
    ELEVATION_URL = os.getenv(
        "ELEVATION_URL", "https://api.open-elevation.com/api/v1/lookup"
    )
    EXTERNAL_API_TIMEOUT = float(os.getenv("EXTERNAL_API_TIMEOUT", "15"))
    ROUTE_MAX_DISTANCE_METERS = float(
        os.getenv("ROUTE_MAX_DISTANCE_METERS", "5000")
    )
    MULTI_STOP_EXACT_THRESHOLD = int(os.getenv("MULTI_STOP_EXACT_THRESHOLD", "8"))
