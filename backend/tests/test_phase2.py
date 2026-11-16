from unittest.mock import patch

import pytest
import requests

from app import create_app
from services.coordinates import (
    CoordinateError,
    validate_start_destination,
)
from services.external_api import ExternalApiError, _get_json


@pytest.fixture
def client():
    return create_app({"TESTING": True}).test_client()


def test_coordinate_validation():
    with pytest.raises(CoordinateError):
        validate_start_destination(91, 0, 1, 1)


def test_duplicate_coordinates_rejected():
    with pytest.raises(CoordinateError, match="cannot be identical"):
        validate_start_destination(27.1, 86.1, 27.1, 86.1)


@patch("services.osm_features._post_json")
def test_map_features_mock(mock_post_json, client):
    mock_post_json.return_value = {
        "elements": [
            {
                "type": "way",
                "geometry": [
                    {"lat": 27.1, "lon": 86.1},
                    {"lat": 27.2, "lon": 86.2},
                ],
                "tags": {"highway": "trail"},
            }
        ]
    }
    response = client.get(
        "/api/map/features?south=27&west=86&north=28&east=87"
    )
    assert response.status_code == 200
    feature = response.get_json()["data"]["features"][0]
    assert feature["geometry"]["type"] == "LineString"
    assert feature["geometry"]["coordinates"][0] == [86.1, 27.1]


def test_external_timeout():
    with patch("services.external_api.requests.get", side_effect=requests.Timeout()):
        with pytest.raises(ExternalApiError, match="timed out"):
            _get_json("https://example.invalid", {}, 1, "Test service")


def test_malformed_external_json():
    response = type("Response", (), {"raise_for_status": lambda self: None})()
    response.json = lambda: (_ for _ in ()).throw(ValueError())
    with patch("services.external_api.requests.get", return_value=response):
        with pytest.raises(ExternalApiError, match="malformed JSON"):
            _get_json("https://example.invalid", {}, 1, "Test service")


@patch("services.geocoding._get_json")
def test_geocoding(mock_get_json, client):
    mock_get_json.return_value = [
        {"lat": "27.9881", "lon": "86.9250", "display_name": "Everest"}
    ]
    response = client.get("/api/geocode?q=Everest")
    assert response.status_code == 200
    assert response.get_json()["data"][0]["display_name"] == "Everest"


@patch("services.geocoding._get_json", side_effect=ExternalApiError("Nominatim unavailable"))
def test_reverse_geocoding_error(mock_get_json, client):
    response = client.get("/api/reverse-geocode?lat=27.9881&lng=86.925")
    assert response.status_code == 502
    assert response.get_json()["success"] is False


@patch("services.elevation._get_json")
def test_elevation_mapping(mock_get_json, client):
    mock_get_json.return_value = {"results": [{"elevation": 8848.0}]}
    response = client.get("/api/elevation?lat=27.9881&lng=86.925")
    assert response.status_code == 200
    assert response.get_json()["data"]["elevation"] == 8848.0
