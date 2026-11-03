"""Integration tests for POST /api/v1/routes."""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from rest_framework.test import APIClient


def _future_dt() -> str:
    dt = datetime.now(tz=UTC) + timedelta(hours=2)
    return dt.isoformat()


def _mock_geocode(address: str):  # type: ignore[no-untyped-def]
    if "York" in address:
        return (40.7128, -74.006)
    return (34.0522, -118.2437)


def _mock_get_routes(origin, dest):  # type: ignore[no-untyped-def]
    return [
        {
            "index": 0,
            "distance_miles": 2800.0,
            "duration_hours": 42.0,
            "geometry": [(40.7128, -74.006), (37.0, -96.0), (34.0522, -118.2437)],
        }
    ]


def _mock_weather(checkpoints):  # type: ignore[no-untyped-def]
    return [{**cp, "wind_mph": 15.0, "rain_in_hr": 0.0, "snow_in_hr": 0.0} for cp in checkpoints]


def _mock_heatmap(checkpoints, departure_dt):  # type: ignore[no-untyped-def]
    return []


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


class TestRouteView:
    def _post(self, client: APIClient, payload: dict) -> object:
        return client.post("/api/v1/routes", payload, format="json")

    def test_returns_200_with_valid_payload(self, api_client: APIClient) -> None:
        with (
            patch("api.views.route_view.RoutingService.geocode", side_effect=_mock_geocode),
            patch("api.views.route_view.RoutingService.get_routes", side_effect=_mock_get_routes),
            patch(
                "api.views.route_view.WeatherService.fetch_weather_for_checkpoints",
                side_effect=_mock_weather,
            ),
            patch(
                "api.views.route_view.WeatherService.build_heatmap_data",
                side_effect=_mock_heatmap,
            ),
        ):
            resp = self._post(
                api_client,
                {
                    "origin": "New York, NY",
                    "destination": "Los Angeles, CA",
                    "departure_datetime": _future_dt(),
                    "load_weight_lbs": 30000,
                },
            )

        assert resp.status_code == 200
        body = resp.data["data"]
        assert "routes" in body
        assert "recommended_route_index" in body
        assert body["recommended_route_index"] == 0

    def test_returns_400_for_past_departure(self, api_client: APIClient) -> None:
        past = (datetime.now(tz=UTC) - timedelta(hours=5)).isoformat()
        resp = self._post(
            api_client,
            {
                "origin": "New York, NY",
                "destination": "Los Angeles, CA",
                "departure_datetime": past,
                "load_weight_lbs": 30000,
            },
        )
        assert resp.status_code == 400

    def test_returns_400_when_origin_equals_destination(self, api_client: APIClient) -> None:
        resp = self._post(
            api_client,
            {
                "origin": "New York, NY",
                "destination": "New York, NY",
                "departure_datetime": _future_dt(),
                "load_weight_lbs": 30000,
            },
        )
        assert resp.status_code == 400

    def test_returns_400_for_negative_load(self, api_client: APIClient) -> None:
        resp = self._post(
            api_client,
            {
                "origin": "New York, NY",
                "destination": "Los Angeles, CA",
                "departure_datetime": _future_dt(),
                "load_weight_lbs": -1,
            },
        )
        assert resp.status_code == 400

    def test_health_endpoint(self, api_client: APIClient) -> None:
        resp = api_client.get("/api/health")
        assert resp.status_code == 200
        assert resp.data["status"] == "ok"
