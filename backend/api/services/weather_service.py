"""Fetches weather forecasts from Open-Meteo (no API key required)."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any

import requests

from api.constants.risk_thresholds import MAX_FORECAST_HOURS
from api.exceptions import WeatherAPIError

CheckpointBase = dict[str, Any]
CheckpointWeather = dict[str, Any]
HeatmapPoint = dict[str, Any]

_OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
_MAX_WORKERS = 10


class WeatherService:
    def __init__(self, base_url: str = _OPEN_METEO_URL) -> None:
        self._base_url = base_url

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch_weather_for_checkpoints(
        self, checkpoints: list[CheckpointBase]
    ) -> list[CheckpointWeather]:
        """
        Fetch hourly weather for every checkpoint in parallel and attach
        wind_mph, rain_in_hr, snow_in_hr at the checkpoint's ETA.
        """
        forecasts: dict[int, dict[str, Any]] = {}

        with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as executor:
            future_to_idx = {
                executor.submit(self._fetch_forecast, cp["lat"], cp["lng"]): idx
                for idx, cp in enumerate(checkpoints)
            }
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                forecasts[idx] = future.result()

        enriched: list[CheckpointWeather] = []
        for idx, cp in enumerate(checkpoints):
            weather = _pick_weather_at(forecasts[idx], cp["eta"])
            enriched.append({**cp, **weather})

        return enriched

    def build_heatmap_data(
        self,
        all_checkpoints: list[CheckpointBase],
        departure_dt: datetime,
    ) -> list[HeatmapPoint]:
        """
        For unique checkpoint locations, fetch 48-hour forecasts and
        return flat list of {lat, lng, risk_value, forecast_hour}.
        risk_value uses raw wind_mph only for heatmap weight (0–55 mph → 0–1).
        """
        from api.services.risk_service import RiskService

        risk_service = RiskService()

        # Deduplicate locations (within 0.15 degree)
        unique: list[tuple[float, float]] = []
        for cp in all_checkpoints:
            pt = (cp["lat"], cp["lng"])
            if not any(_close(pt, u) for u in unique):
                unique.append(pt)

        forecasts: dict[int, dict[str, Any]] = {}
        with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as executor:
            future_to_idx = {
                executor.submit(self._fetch_forecast, lat, lng): i
                for i, (lat, lng) in enumerate(unique)
            }
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                forecasts[idx] = future.result()

        heatmap: list[HeatmapPoint] = []
        for i, (lat, lng) in enumerate(unique):
            forecast = forecasts.get(i, {})
            times: list[str] = forecast.get("time", [])
            winds: list[float] = forecast.get("windspeed_10m", [])
            rains: list[float] = forecast.get("rain", [])
            snows: list[float] = forecast.get("snowfall", [])

            for hour in range(MAX_FORECAST_HOURS):
                if hour >= len(times):
                    break
                wind = winds[hour] if hour < len(winds) else 0.0
                rain = rains[hour] if hour < len(rains) else 0.0
                snow_cm = snows[hour] if hour < len(snows) else 0.0
                snow_in = snow_cm / 2.54

                risk_level = risk_service.calculate_checkpoint_risk(wind, rain, snow_in, 0)
                from api.constants.risk_thresholds import RISK_SCORES

                risk_value = RISK_SCORES[risk_level]

                heatmap.append(
                    {
                        "lat": lat,
                        "lng": lng,
                        "risk_value": risk_value,
                        "forecast_hour": hour,
                    }
                )

        return heatmap

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _fetch_forecast(self, lat: float, lng: float) -> dict[str, Any]:
        """Return the raw hourly forecast dict from Open-Meteo."""
        params: dict[str, Any] = {
            "latitude": round(lat, 4),
            "longitude": round(lng, 4),
            "hourly": "windspeed_10m,rain,snowfall",
            "forecast_days": 3,
            "windspeed_unit": "mph",
            "precipitation_unit": "inch",
            "timezone": "UTC",
        }
        try:
            resp = requests.get(self._base_url, params=params, timeout=10)
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise WeatherAPIError(f"Weather fetch failed for ({lat}, {lng}): {exc}") from exc

        return dict(resp.json().get("hourly", {}))


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------


def _pick_weather_at(forecast: dict[str, Any], eta: datetime) -> dict[str, float]:
    """Find the forecast slot closest to eta and return weather values."""
    times: list[str] = forecast.get("time", [])
    winds: list[float] = forecast.get("windspeed_10m", [])
    rains: list[float] = forecast.get("rain", [])
    snows: list[float] = forecast.get("snowfall", [])

    if not times:
        return {"wind_mph": 0.0, "rain_in_hr": 0.0, "snow_in_hr": 0.0}

    # Ensure eta is naive UTC for comparison
    eta_naive = eta.replace(tzinfo=None) if eta.tzinfo else eta

    best_idx = 0
    best_diff = float("inf")
    for idx, t_str in enumerate(times):
        # Open-Meteo format: "2026-11-02T14:00"
        t = datetime.fromisoformat(t_str)
        diff = abs((t - eta_naive).total_seconds())
        if diff < best_diff:
            best_diff = diff
            best_idx = idx

    wind = winds[best_idx] if best_idx < len(winds) else 0.0
    rain = rains[best_idx] if best_idx < len(rains) else 0.0
    snow_cm = snows[best_idx] if best_idx < len(snows) else 0.0

    return {
        "wind_mph": float(wind),
        "rain_in_hr": float(rain),
        "snow_in_hr": float(snow_cm) / 2.54,  # cm → inches
    }


def _close(a: tuple[float, float], b: tuple[float, float]) -> bool:
    return abs(a[0] - b[0]) < 0.15 and abs(a[1] - b[1]) < 0.15
