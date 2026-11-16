from flask import current_app

from .external_api import ExternalApiError, _get_json


HEADERS = {"User-Agent": "DepthWizard/Phase2"}


def geocode(query, limit=5):
    if not query or not query.strip():
        raise ExternalApiError("Search query is required")

    data = _get_json(
        f"{current_app.config['NOMINATIM_URL'].rstrip('/')}/search",
        {"q": query, "format": "jsonv2", "limit": limit},
        current_app.config["EXTERNAL_API_TIMEOUT"],
        "Nominatim",
        HEADERS,
    )
    if not isinstance(data, list):
        raise ExternalApiError("Nominatim returned malformed data")
    return data


def reverse_geocode(latitude, longitude):
    data = _get_json(
        f"{current_app.config['NOMINATIM_URL'].rstrip('/')}/reverse",
        {"lat": latitude, "lon": longitude, "format": "jsonv2"},
        current_app.config["EXTERNAL_API_TIMEOUT"],
        "Nominatim",
        HEADERS,
    )
    if not isinstance(data, dict) or "lat" not in data or "lon" not in data:
        raise ExternalApiError("Nominatim returned malformed data")
    return data
