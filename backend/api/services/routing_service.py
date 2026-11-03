"""Handles geocoding via Nominatim (OSM) and routing via OSRM."""

import math
from datetime import datetime, timedelta
from typing import Any

import requests

from api.constants.risk_thresholds import AVG_TRUCK_SPEED_MPH, CHECKPOINT_INTERVAL_MILES
from api.exceptions import GeocodingError, RoutingAPIError

# Internal type aliases
Coord = tuple[float, float]  # (lat, lng)
CheckpointBase = dict[str, Any]
RouteRaw = dict[str, Any]

_METERS_PER_MILE = 1609.344
_USER_AGENT = "TruckRoutingApp/1.0"


class RoutingService:
    def __init__(self, nominatim_url: str, osrm_url: str) -> None:
        self._nominatim_url = nominatim_url.rstrip("/")
        self._osrm_url = osrm_url.rstrip("/")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def geocode(self, address: str) -> Coord:
        """Return (lat, lng) for the given address string."""
        url = f"{self._nominatim_url}/search"
        params: dict[str, str | int] = {
            "q": address,
            "format": "json",
            "limit": 1,
        }
        try:
            resp = requests.get(
                url, params=params, headers={"User-Agent": _USER_AGENT}, timeout=10
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise GeocodingError(f"Geocoding request failed: {exc}") from exc

        results: list[Any] = resp.json()
        if not results:
            raise GeocodingError(f"Address not found: '{address}'")

        return (float(results[0]["lat"]), float(results[0]["lon"]))

    def get_routes(self, origin: Coord, destination: Coord) -> list[RouteRaw]:
        """
        Request up to 3 alternative routes from OSRM and return them as
        dicts with geometry (list of (lat, lng)), distance_miles, duration_hours.
        """
        # OSRM URL path uses lng,lat order
        coords = f"{origin[1]},{origin[0]};{destination[1]},{destination[0]}"
        url = f"{self._osrm_url}/route/v1/driving/{coords}"
        params: dict[str, str | int] = {
            "alternatives": 3,
            "geometries": "geojson",
            "overview": "full",
        }
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise RoutingAPIError(f"Routing request failed: {exc}") from exc

        data: dict[str, Any] = resp.json()
        if data.get("code") != "Ok":
            raise RoutingAPIError(f"OSRM error: {data.get('message', 'unknown')}")

        raw_routes: list[Any] = data.get("routes", [])
        if not raw_routes:
            raise RoutingAPIError("No routes returned by routing API")

        routes: list[RouteRaw] = []
        for i, r in enumerate(raw_routes):
            # OSRM returns distance in meters, duration in seconds
            distance_miles = float(r["distance"]) / _METERS_PER_MILE
            duration_hours = float(r["duration"]) / 3600.0

            # GeoJSON coordinates are [lng, lat] — convert to (lat, lng) tuples
            raw_coords: list[list[float]] = r["geometry"]["coordinates"]
            geometry = [(c[1], c[0]) for c in raw_coords]

            routes.append(
                {
                    "index": i,
                    "distance_miles": distance_miles,
                    "duration_hours": duration_hours,
                    "geometry": geometry,
                }
            )

        return routes

    def suggest_addresses(self, query: str, limit: int = 5) -> list[dict[str, object]]:
        """Return address suggestions from Nominatim for autocomplete."""
        if len(query.strip()) < 2:
            return []

        url = f"{self._nominatim_url}/search"
        params: dict[str, str | int] = {
            "q": query.strip(),
            "format": "json",
            "limit": limit,
            "addressdetails": 1,
        }
        try:
            resp = requests.get(
                url, params=params, headers={"User-Agent": _USER_AGENT}, timeout=10
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise GeocodingError(f"Geocoding request failed: {exc}") from exc

        results: list[Any] = resp.json()
        suggestions: list[dict[str, object]] = []
        for r in results:
            addr: dict[str, Any] = r.get("address", {})
            city: str = (
                addr.get("city")
                or addr.get("town")
                or addr.get("village")
                or addr.get("county")
                or ""
            )
            state: str = addr.get("state", "")
            country_code: str = str(addr.get("country_code", "")).upper()
            parts = [p for p in [city, state, country_code] if p]
            label = ", ".join(parts) if parts else str(r.get("display_name", ""))
            suggestions.append({"label": label, "lat": float(r["lat"]), "lng": float(r["lon"])})

        return suggestions

    def sample_checkpoints(
        self,
        geometry: list[tuple[float, float]],
        departure_dt: datetime,
        distance_miles: float,
        duration_hours: float,
    ) -> list[CheckpointBase]:
        """
        Walk the route geometry and place a checkpoint every
        CHECKPOINT_INTERVAL_MILES miles. ETA is interpolated from
        departure_dt using the route's average speed.
        """
        avg_speed = distance_miles / duration_hours if duration_hours > 0 else AVG_TRUCK_SPEED_MPH

        checkpoints: list[CheckpointBase] = []
        cumulative: float = 0.0
        next_sample: float = 0.0  # start with mile 0

        def make_checkpoint(lat: float, lng: float, mile: float) -> CheckpointBase:
            eta = departure_dt + timedelta(hours=mile / avg_speed)
            return {"lat": lat, "lng": lng, "mile": round(mile, 1), "eta": eta}

        checkpoints.append(make_checkpoint(geometry[0][0], geometry[0][1], 0.0))
        next_sample = CHECKPOINT_INTERVAL_MILES

        for i in range(1, len(geometry)):
            prev = geometry[i - 1]
            curr = geometry[i]
            seg = _haversine(prev, curr)
            if seg == 0.0:
                continue

            while next_sample <= cumulative + seg:
                frac = (next_sample - cumulative) / seg
                lat = prev[0] + frac * (curr[0] - prev[0])
                lng = prev[1] + frac * (curr[1] - prev[1])
                if next_sample <= distance_miles:
                    checkpoints.append(make_checkpoint(lat, lng, next_sample))
                next_sample += CHECKPOINT_INTERVAL_MILES

            cumulative += seg

        # Always include the destination
        last = geometry[-1]
        checkpoints.append(make_checkpoint(last[0], last[1], distance_miles))

        return checkpoints


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _haversine(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    """Great-circle distance in miles between two (lat, lng) points."""
    earth_radius_miles = 3958.8
    lat1, lon1 = math.radians(p1[0]), math.radians(p1[1])
    lat2, lon2 = math.radians(p2[0]), math.radians(p2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return earth_radius_miles * 2 * math.asin(math.sqrt(a))
