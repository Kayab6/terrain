from flask import current_app

from .external_api import ExternalApiError, _post_json


def _geojson_geometry(element):
    if element["type"] == "way":
        return {
            "type": "LineString",
            "coordinates": [
                [node["lon"], node["lat"]]
                for node in element.get("geometry", [])
            ],
        }
    if element["type"] == "node":
        return {
            "type": "Point",
            "coordinates": [element["lon"], element["lat"]],
        }
    return None


def load_map_features(south, west, north, east):
    if max(north - south, east - west) > 0.75:
        center_latitude = (south + north) / 2
        center_longitude = (west + east) / 2
        south = center_latitude - 0.375
        north = center_latitude + 0.375
        west = center_longitude - 0.375
        east = center_longitude + 0.375

    query = (
        "[out:json][timeout:25];("
        f"way[\"highway\"]({south},{west},{north},{east});"
        f"way[\"railway\"]({south},{west},{north},{east});"
        f"way[\"route\"=\"hiking\"]({south},{west},{north},{east});"
        ");out geom tags;"
    )
    urls = [
        current_app.config["OVERPASS_URL"],
        *current_app.config.get("OVERPASS_FALLBACK_URLS", []),
    ]
    data = None
    last_error = None
    for url in dict.fromkeys(urls):
        try:
            data = _post_json(
                url,
                {"data": query},
                current_app.config["EXTERNAL_API_TIMEOUT"],
                "Overpass",
                headers={
                    "User-Agent": "DepthWizard/1.0 (terrain route optimizer)",
                    "Accept": "application/json",
                },
            )
            break
        except ExternalApiError as exc:
            last_error = exc
    if data is None:
        raise ExternalApiError(
            "Overpass services are unavailable (request timed out or failed)"
        ) from last_error
    if not isinstance(data, dict) or not isinstance(data.get("elements"), list):
        raise ExternalApiError("Overpass returned malformed data")

    features = []
    for element in data["elements"]:
        geometry = _geojson_geometry(element)
        if geometry is not None and (
            geometry["type"] != "LineString" or len(geometry["coordinates"]) >= 2
        ):
            features.append(
                {
                    "type": "Feature",
                    "geometry": geometry,
                    "properties": {
                        key: value
                        for key, value in element.get("tags", {}).items()
                        if isinstance(value, str)
                    },
                }
            )
    return {"type": "FeatureCollection", "features": features}
