"""Unit tests for RoutingService (network calls mocked)."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
import requests

from api.exceptions import GeocodingError, RoutingAPIError
from api.services.routing_service import RoutingService, _haversine

NOMINATIM_URL = "https://nominatim.openstreetmap.org"
OSRM_URL = "http://router.project-osrm.org"


@pytest.fixture
def svc() -> RoutingService:
    return RoutingService(NOMINATIM_URL, OSRM_URL)


def _osrm_response(routes: list[dict]) -> dict:  # type: ignore[type-arg]
    return {"code": "Ok", "routes": routes}


def _osrm_route(
    distance_m: float = 80467.2,  # 50 miles
    duration_s: float = 3600.0,
    coords: list[list[float]] | None = None,
) -> dict:  # type: ignore[type-arg]
    if coords is None:
        # [lng, lat] order as OSRM returns
        coords = [[-74.0, 40.7], [-73.9, 40.8], [-74.1, 41.0]]
    return {
        "distance": distance_m,
        "duration": duration_s,
        "geometry": {"type": "LineString", "coordinates": coords},
    }


class TestHaversine:
    def test_same_point_is_zero(self) -> None:
        assert _haversine((40.0, -74.0), (40.0, -74.0)) == 0.0

    def test_known_distance(self) -> None:
        # NYC to roughly 1 degree north (~69 miles)
        dist = _haversine((40.0, -74.0), (41.0, -74.0))
        assert 68 < dist < 70


class TestGeocode:
    def test_returns_lat_lng_tuple(self, svc: RoutingService) -> None:
        mock_resp = MagicMock()
        mock_resp.json.return_value = [{"lat": "40.7128", "lon": "-74.0060"}]

        with patch("api.services.routing_service.requests.get", return_value=mock_resp):
            result = svc.geocode("New York")

        assert result == pytest.approx((40.7128, -74.0060))

    def test_raises_geocoding_error_on_empty_results(self, svc: RoutingService) -> None:
        mock_resp = MagicMock()
        mock_resp.json.return_value = []

        with patch("api.services.routing_service.requests.get", return_value=mock_resp):
            with pytest.raises(GeocodingError, match="not found"):
                svc.geocode("Nonexistent Place XYZ")

    def test_raises_geocoding_error_on_request_exception(self, svc: RoutingService) -> None:
        with patch(
            "api.services.routing_service.requests.get",
            side_effect=requests.RequestException("timeout"),
        ):
            with pytest.raises(GeocodingError, match="Geocoding request failed"):
                svc.geocode("New York")


class TestGetRoutes:
    def test_parses_single_route_correctly(self, svc: RoutingService) -> None:
        mock_resp = MagicMock()
        mock_resp.json.return_value = _osrm_response([_osrm_route()])

        with patch("api.services.routing_service.requests.get", return_value=mock_resp):
            routes = svc.get_routes((40.7, -74.0), (41.0, -74.1))

        assert len(routes) == 1
        assert routes[0]["distance_miles"] == pytest.approx(50.0, abs=0.1)
        assert routes[0]["duration_hours"] == pytest.approx(1.0)
        # Geometry is (lat, lng) tuples — lng/lat swapped from OSRM's [lng, lat]
        assert routes[0]["geometry"][0] == pytest.approx((40.7, -74.0))

    def test_parses_multiple_routes(self, svc: RoutingService) -> None:
        mock_resp = MagicMock()
        mock_resp.json.return_value = _osrm_response(
            [_osrm_route(), _osrm_route(distance_m=96560.6)]
        )

        with patch("api.services.routing_service.requests.get", return_value=mock_resp):
            routes = svc.get_routes((40.7, -74.0), (41.0, -74.1))

        assert len(routes) == 2
        assert routes[1]["distance_miles"] == pytest.approx(60.0, abs=0.1)

    def test_raises_routing_error_on_empty_routes(self, svc: RoutingService) -> None:
        mock_resp = MagicMock()
        mock_resp.json.return_value = _osrm_response([])

        with patch("api.services.routing_service.requests.get", return_value=mock_resp):
            with pytest.raises(RoutingAPIError):
                svc.get_routes((40.7, -74.0), (41.0, -74.1))

    def test_raises_routing_error_on_osrm_error_code(self, svc: RoutingService) -> None:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"code": "NoRoute", "message": "Cannot find route"}

        with patch("api.services.routing_service.requests.get", return_value=mock_resp):
            with pytest.raises(RoutingAPIError, match="OSRM error"):
                svc.get_routes((40.7, -74.0), (41.0, -74.1))

    def test_raises_routing_error_on_request_exception(self, svc: RoutingService) -> None:
        with patch(
            "api.services.routing_service.requests.get",
            side_effect=requests.RequestException("timeout"),
        ):
            with pytest.raises(RoutingAPIError, match="Routing request failed"):
                svc.get_routes((40.7, -74.0), (41.0, -74.1))


class TestSampleCheckpoints:
    def test_includes_origin_and_destination(self, svc: RoutingService) -> None:
        geometry = [(40.0, -74.0), (40.5, -74.0), (41.0, -74.0)]
        departure = datetime(2026, 11, 2, 8, 0, tzinfo=UTC)
        cps = svc.sample_checkpoints(geometry, departure, 140.0, 2.55)

        assert cps[0]["mile"] == 0.0
        assert cps[-1]["mile"] == 140.0

    def test_eta_increases_along_route(self, svc: RoutingService) -> None:
        geometry = [(40.0, -74.0), (40.5, -74.0), (41.0, -74.0)]
        departure = datetime(2026, 11, 2, 8, 0, tzinfo=UTC)
        cps = svc.sample_checkpoints(geometry, departure, 140.0, 2.55)

        etas = [cp["eta"] for cp in cps]
        assert all(etas[i] <= etas[i + 1] for i in range(len(etas) - 1))
