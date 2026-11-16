from flask import jsonify, request
from werkzeug.exceptions import BadRequest

from services.coordinates import CoordinateError, validate_latitude, validate_longitude
from services.elevation import load_elevation
from services.external_api import ExternalApiError
from services.geocoding import geocode, reverse_geocode
from services.osm_features import load_map_features

from . import api
from .errors import error_response


def _external_error(exc):
    return error_response(str(exc), 502, "external_service_error")


def _required_query(name):
    value = request.args.get(name)
    if value is None or value == "":
        raise BadRequest(f"{name} is required")
    return value


@api.get("/api/map/features")
def map_features():
    try:
        south = validate_latitude(_required_query("south"))
        west = validate_longitude(_required_query("west"))
        north = validate_latitude(_required_query("north"))
        east = validate_longitude(_required_query("east"))
    except CoordinateError as exc:
        return error_response(str(exc), 400)
    if south >= north or west >= east:
        return error_response("Bounds are invalid or reversed", 400)

    try:
        data = load_map_features(south, west, north, east)
    except ExternalApiError as exc:
        return _external_error(exc)
    return jsonify({"success": True, "data": data})


@api.get("/api/elevation")
def elevation():
    try:
        latitude = validate_latitude(_required_query("lat"))
        longitude = validate_longitude(_required_query("lng"))
        value = load_elevation(latitude, longitude)
    except CoordinateError as exc:
        return error_response(str(exc), 400)
    except ExternalApiError as exc:
        return _external_error(exc)
    return jsonify(
        {"success": True, "data": {"latitude": latitude, "longitude": longitude, "elevation": value}}
    )


@api.get("/api/geocode")
def geocode_route():
    query = _required_query("q")
    try:
        limit = min(max(int(request.args.get("limit", "5")), 1), 10)
        results = geocode(query, limit)
    except (ValueError, TypeError):
        return error_response("limit must be an integer", 400)
    except ExternalApiError as exc:
        return _external_error(exc)
    return jsonify({"success": True, "data": results})


@api.get("/api/reverse-geocode")
def reverse_geocode_route():
    try:
        latitude = validate_latitude(_required_query("lat"))
        longitude = validate_longitude(_required_query("lng"))
        result = reverse_geocode(latitude, longitude)
    except CoordinateError as exc:
        return error_response(str(exc), 400)
    except ExternalApiError as exc:
        return _external_error(exc)
    return jsonify({"success": True, "data": result})
