"""Unit tests for WeatherService helpers."""

from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import requests

from api.exceptions import WeatherAPIError
from api.services.weather_service import WeatherService, _close, _pick_weather_at


def _make_forecast(
    hours: int = 3,
    base_wind: float = 10.0,
    base_rain: float = 0.0,
    base_snow: float = 0.0,
    start_hour: int = 8,
) -> dict[str, Any]:
    base = datetime(2026, 11, 2, start_hour, 0)
    times = [(base + timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M") for i in range(hours)]
    return {
        "time": times,
        "windspeed_10m": [base_wind + i * 5 for i in range(hours)],
        "rain": [base_rain] * hours,
        "snowfall": [base_snow] * hours,
    }


class TestPickWeatherAt:
    def _forecast(self) -> dict[str, Any]:
        return {
            "time": [
                "2026-11-02T08:00",
                "2026-11-02T09:00",
                "2026-11-02T10:00",
            ],
            "windspeed_10m": [10.0, 20.0, 30.0],
            "rain": [0.0, 0.1, 0.0],
            "snowfall": [0.0, 0.0, 2.54],  # cm → 1 in
        }

    def test_picks_exact_match(self) -> None:
        eta = datetime(2026, 11, 2, 9, 0)
        result = _pick_weather_at(self._forecast(), eta)
        assert result["wind_mph"] == 20.0
        assert result["rain_in_hr"] == 0.1

    def test_picks_nearest_slot(self) -> None:
        # 09:29 → closer to 09:00 than 10:00
        eta = datetime(2026, 11, 2, 9, 29)
        result = _pick_weather_at(self._forecast(), eta)
        assert result["wind_mph"] == 20.0

    def test_picks_later_slot_when_closer(self) -> None:
        # 09:31 → closer to 10:00 than 09:00
        eta = datetime(2026, 11, 2, 9, 31)
        result = _pick_weather_at(self._forecast(), eta)
        assert result["wind_mph"] == 30.0

    def test_converts_snow_cm_to_inches(self) -> None:
        eta = datetime(2026, 11, 2, 10, 0)
        result = _pick_weather_at(self._forecast(), eta)
        assert abs(result["snow_in_hr"] - 1.0) < 0.01

    def test_empty_forecast_returns_zeros(self) -> None:
        eta = datetime(2026, 11, 2, 9, 0)
        result = _pick_weather_at({}, eta)
        assert result == {"wind_mph": 0.0, "rain_in_hr": 0.0, "snow_in_hr": 0.0}

    def test_timezone_aware_eta_is_handled(self) -> None:
        eta = datetime(2026, 11, 2, 9, 0, tzinfo=UTC)
        result = _pick_weather_at(self._forecast(), eta)
        assert result["wind_mph"] == 20.0


class TestCloseHelper:
    def test_same_point_is_close(self) -> None:
        assert _close((40.0, -74.0), (40.0, -74.0))

    def test_points_within_threshold_are_close(self) -> None:
        assert _close((40.0, -74.0), (40.1, -74.1))

    def test_points_outside_threshold_are_not_close(self) -> None:
        assert not _close((40.0, -74.0), (40.2, -74.2))

    def test_lat_outside_threshold_is_not_close(self) -> None:
        assert not _close((40.0, -74.0), (40.2, -74.0))

    def test_lng_outside_threshold_is_not_close(self) -> None:
        assert not _close((40.0, -74.0), (40.0, -74.2))


class TestWeatherServiceFetchForecast:
    def _service(self) -> WeatherService:
        return WeatherService(base_url="http://meteo.test/v1/forecast")

    def test_fetch_forecast_returns_hourly_dict(self) -> None:
        forecast = _make_forecast()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"hourly": forecast}
        with patch("api.services.weather_service.requests.get", return_value=mock_resp):
            result = self._service()._fetch_forecast(40.0, -74.0)
        assert result["time"] == forecast["time"]
        assert result["windspeed_10m"] == forecast["windspeed_10m"]

    def test_fetch_forecast_raises_weather_api_error_on_request_exception(self) -> None:
        with patch(
            "api.services.weather_service.requests.get",
            side_effect=requests.RequestException("timeout"),
        ):
            with pytest.raises(WeatherAPIError, match="Weather fetch failed"):
                self._service()._fetch_forecast(40.0, -74.0)

    def test_fetch_forecast_raises_on_http_error(self) -> None:
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = requests.HTTPError("500")
        with patch("api.services.weather_service.requests.get", return_value=mock_resp):
            with pytest.raises(WeatherAPIError):
                self._service()._fetch_forecast(40.0, -74.0)

    def test_fetch_forecast_empty_hourly_returns_empty_dict(self) -> None:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {}
        with patch("api.services.weather_service.requests.get", return_value=mock_resp):
            result = self._service()._fetch_forecast(40.0, -74.0)
        assert result == {}


class TestWeatherServiceFetchForCheckpoints:
    def _service(self) -> WeatherService:
        return WeatherService(base_url="http://meteo.test")

    def _checkpoints(self) -> list[dict[str, Any]]:
        base = datetime(2026, 11, 2, 10, 0, tzinfo=UTC)
        return [
            {"lat": 40.0, "lng": -74.0, "mile": 0, "eta": base},
            {"lat": 41.0, "lng": -75.0, "mile": 50, "eta": base + timedelta(hours=1)},
        ]

    def test_enriches_checkpoints_with_weather(self) -> None:
        forecast = _make_forecast(hours=48, start_hour=0)
        service = self._service()
        with patch.object(service, "_fetch_forecast", return_value=forecast):
            result = service.fetch_weather_for_checkpoints(self._checkpoints())
        assert len(result) == 2
        assert "wind_mph" in result[0]
        assert "rain_in_hr" in result[0]
        assert "snow_in_hr" in result[0]
        # original checkpoint fields are preserved
        assert result[0]["lat"] == 40.0
        assert result[0]["mile"] == 0

    def test_returns_empty_list_for_no_checkpoints(self) -> None:
        service = self._service()
        result = service.fetch_weather_for_checkpoints([])
        assert result == []


class TestWeatherServiceBuildHeatmapData:
    def _service(self) -> WeatherService:
        return WeatherService(base_url="http://meteo.test")

    def _checkpoints(self) -> list[dict[str, Any]]:
        return [
            {"lat": 40.0, "lng": -74.0, "mile": 0},
            {"lat": 41.0, "lng": -75.0, "mile": 50},
            # duplicate of first (within 0.15°)
            {"lat": 40.05, "lng": -74.05, "mile": 25},
        ]

    def test_returns_48_points_per_unique_location(self) -> None:
        forecast = _make_forecast(hours=48, start_hour=0)
        service = self._service()
        with patch.object(service, "_fetch_forecast", return_value=forecast):
            result = service.build_heatmap_data(
                self._checkpoints(), datetime(2026, 11, 2, 8, 0, tzinfo=UTC)
            )
        # 2 unique locations × 48 hours = 96 points
        assert len(result) == 96

    def test_deduplicates_nearby_locations(self) -> None:
        """Third checkpoint is close to first — only 2 unique locations."""
        forecast = _make_forecast(hours=48, start_hour=0)
        service = self._service()
        call_count = 0

        def counting_fetch(lat: float, lng: float) -> dict[str, Any]:
            nonlocal call_count
            call_count += 1
            return forecast

        with patch.object(service, "_fetch_forecast", side_effect=counting_fetch):
            service.build_heatmap_data(
                self._checkpoints(), datetime(2026, 11, 2, 8, 0, tzinfo=UTC)
            )
        assert call_count == 2

    def test_heatmap_points_have_required_fields(self) -> None:
        forecast = _make_forecast(hours=4, start_hour=0)
        service = self._service()
        single_cp = [{"lat": 40.0, "lng": -74.0, "mile": 0}]
        with patch.object(service, "_fetch_forecast", return_value=forecast):
            result = service.build_heatmap_data(
                single_cp, datetime(2026, 11, 2, 8, 0, tzinfo=UTC)
            )
        assert len(result) == 4  # stops at hours available, not MAX_FORECAST_HOURS
        for pt in result:
            assert "lat" in pt
            assert "lng" in pt
            assert "risk_value" in pt
            assert "forecast_hour" in pt

    def test_heatmap_risk_value_is_positive_integer(self) -> None:
        forecast = _make_forecast(hours=1, base_wind=60.0, start_hour=0)
        service = self._service()
        single_cp = [{"lat": 40.0, "lng": -74.0, "mile": 0}]
        with patch.object(service, "_fetch_forecast", return_value=forecast):
            result = service.build_heatmap_data(
                single_cp, datetime(2026, 11, 2, 8, 0, tzinfo=UTC)
            )
        assert result[0]["risk_value"] >= 1
