from math import isfinite


class CoordinateError(ValueError):
    pass


def coordinate(value, name):
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise CoordinateError(f"{name} must be a number") from exc
    if not isfinite(number):
        raise CoordinateError(f"{name} must be a finite number")
    return number


def validate_latitude(value):
    latitude = coordinate(value, "Latitude")
    if latitude < -90 or latitude > 90:
        raise CoordinateError("Latitude must be between -90 and 90")
    return latitude


def validate_longitude(value):
    longitude = coordinate(value, "Longitude")
    if longitude < -180 or longitude > 180:
        raise CoordinateError("Longitude must be between -180 and 180")
    return longitude


def validate_start_destination(start_lat, start_lng, destination_lat, destination_lng):
    start = (
        validate_latitude(start_lat),
        validate_longitude(start_lng),
    )
    destination = (
        validate_latitude(destination_lat),
        validate_longitude(destination_lng),
    )
    if start == destination:
        raise CoordinateError("Start and destination cannot be identical")
    return {"start": start, "destination": destination}
