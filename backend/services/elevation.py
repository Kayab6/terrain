from flask import current_app

from .external_api import ExternalApiError, _get_json


def load_elevation(latitude, longitude):
    data = _get_json(
        current_app.config["ELEVATION_URL"],
        {"locations": f"{latitude},{longitude}"},
        current_app.config["EXTERNAL_API_TIMEOUT"],
        "Elevation provider",
    )
    if not isinstance(data, dict) or not isinstance(data.get("results"), list):
        raise ExternalApiError("Elevation provider returned malformed data")
    if not data["results"]:
        raise ExternalApiError("Elevation provider returned no result")

    elevation = data["results"][0].get("elevation")
    if isinstance(elevation, bool) or not isinstance(elevation, (int, float)):
        raise ExternalApiError("Elevation provider returned an invalid elevation")
    return float(elevation)


def load_elevations(points):
    if len(points) > 200:
        points = points[:200]
    locations = "|".join(f"{latitude},{longitude}" for latitude, longitude in points)
    data = _get_json(
        current_app.config["ELEVATION_URL"],
        {"locations": locations},
        current_app.config["EXTERNAL_API_TIMEOUT"],
        "Elevation provider",
    )
    if not isinstance(data, dict) or not isinstance(data.get("results"), list):
        raise ExternalApiError("Elevation provider returned malformed data")
    if len(data["results"]) != len(points):
        raise ExternalApiError("Elevation provider returned incomplete elevation data")
    elevations = []
    for result in data["results"]:
        value = result.get("elevation")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ExternalApiError("Elevation provider returned an invalid elevation")
        elevations.append(float(value))
    return elevations
