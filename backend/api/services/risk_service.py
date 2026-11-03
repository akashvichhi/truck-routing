"""Applies weather risk rules and ranks routes."""

from typing import Any

from api.constants.risk_thresholds import (
    LOAD_RULES,
    RAIN_HIGH_MIN,
    RAIN_MODERATE_MIN,
    RAIN_NO_TRAVEL_MIN,
    RAIN_SEVERE_MIN,
    RISK_HIGH,
    RISK_LOW,
    RISK_MODERATE,
    RISK_NO_TRAVEL,
    RISK_SCORES,
    RISK_SEVERE,
    SNOW_HIGH_MIN,
    SNOW_MODERATE_MIN,
    SNOW_NO_TRAVEL_MIN,
    SNOW_SEVERE_MIN,
    WIND_HIGH_MIN,
    WIND_MODERATE_MIN,
    WIND_NO_TRAVEL_MIN,
    WIND_SEVERE_MIN,
)

CheckpointWeather = dict[str, Any]
CheckpointScored = dict[str, Any]
RouteRaw = dict[str, Any]
RouteScored = dict[str, Any]


class RiskService:
    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def score_checkpoints(
        self,
        checkpoints: list[CheckpointWeather],
        load_weight_lbs: float,
    ) -> list[CheckpointScored]:
        scored: list[CheckpointScored] = []
        for cp in checkpoints:
            risk = self.calculate_checkpoint_risk(
                cp["wind_mph"],
                cp["rain_in_hr"],
                cp["snow_in_hr"],
                load_weight_lbs,
            )
            eta_val = cp["eta"]
            scored.append(
                {
                    "lat": cp["lat"],
                    "lng": cp["lng"],
                    "mile": cp["mile"],
                    "eta": eta_val.isoformat() if hasattr(eta_val, "isoformat") else str(eta_val),
                    "wind_mph": round(cp["wind_mph"], 1),
                    "rain_in_hr": round(cp["rain_in_hr"], 3),
                    "snow_in_hr": round(cp["snow_in_hr"], 3),
                    "risk_level": risk,
                }
            )
        return scored

    def summarize_route(
        self,
        route: RouteRaw,
        scored_checkpoints: list[CheckpointScored],
        load_weight_lbs: float,
    ) -> RouteScored:
        """Compute per-route risk metrics and attach a human summary."""
        interval = _checkpoint_interval(scored_checkpoints)

        severe_miles = 0.0
        high_miles = 0.0
        total_score = 0.0

        for cp in scored_checkpoints:
            level = cp["risk_level"]
            score = RISK_SCORES[level]
            total_score += score
            if level == RISK_SEVERE or level == RISK_NO_TRAVEL:
                severe_miles += interval
            elif level == RISK_HIGH:
                high_miles += interval

        avg_score = total_score / len(scored_checkpoints) if scored_checkpoints else 0.0
        summary = _build_summary(severe_miles, high_miles, avg_score)

        return {
            "index": route["index"],
            "summary": summary,
            "distance_miles": round(route["distance_miles"], 1),
            "duration_hours": round(route["duration_hours"], 2),
            "risk_score": round(avg_score, 2),
            "severe_miles": round(severe_miles, 1),
            "high_miles": round(high_miles, 1),
            "geometry": [[lat, lng] for lat, lng in route["geometry"]],
            "checkpoints": scored_checkpoints,
        }

    def rank_routes(self, routes: list[RouteScored]) -> list[RouteScored]:
        """
        Sort by: fewest Severe miles → fewest High miles →
                 lowest avg risk score → shortest duration.
        Re-index so index 0 is always the recommended route.
        """
        sorted_routes = sorted(
            routes,
            key=lambda r: (
                r["severe_miles"],
                r["high_miles"],
                r["risk_score"],
                r["duration_hours"],
            ),
        )
        for new_idx, r in enumerate(sorted_routes):
            r["index"] = new_idx
        return sorted_routes

    def calculate_checkpoint_risk(
        self,
        wind_mph: float,
        rain_in_hr: float,
        snow_in_hr: float,
        load_weight_lbs: float,
    ) -> str:
        """Return the worst risk level for a single checkpoint."""
        wind_risk = _classify_wind(wind_mph)
        rain_risk = _classify_rain(rain_in_hr)
        snow_risk = _classify_snow(snow_in_hr)

        base_risk = _worst(wind_risk, rain_risk, snow_risk)
        return _apply_load_rules(base_risk, wind_mph, load_weight_lbs)


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------


def _classify_wind(mph: float) -> str:
    if mph >= WIND_NO_TRAVEL_MIN:
        return RISK_NO_TRAVEL
    if mph >= WIND_SEVERE_MIN:
        return RISK_SEVERE
    if mph >= WIND_HIGH_MIN:
        return RISK_HIGH
    if mph >= WIND_MODERATE_MIN:
        return RISK_MODERATE
    return RISK_LOW


def _classify_rain(in_hr: float) -> str:
    if in_hr > RAIN_NO_TRAVEL_MIN:
        return RISK_NO_TRAVEL
    if in_hr >= RAIN_SEVERE_MIN:
        return RISK_SEVERE
    if in_hr >= RAIN_HIGH_MIN:
        return RISK_HIGH
    if in_hr >= RAIN_MODERATE_MIN:
        return RISK_MODERATE
    return RISK_LOW


def _classify_snow(in_hr: float) -> str:
    if in_hr > SNOW_NO_TRAVEL_MIN:
        return RISK_NO_TRAVEL
    if in_hr >= SNOW_SEVERE_MIN:
        return RISK_SEVERE
    if in_hr >= SNOW_HIGH_MIN:
        return RISK_HIGH
    if in_hr >= SNOW_MODERATE_MIN:
        return RISK_MODERATE
    return RISK_LOW


def _worst(a: str, b: str, c: str) -> str:
    return max(a, b, c, key=lambda x: RISK_SCORES[x])


def _apply_load_rules(base_risk: str, wind_mph: float, load_lb: float) -> str:
    """Escalate risk based on wind + load combination."""
    for min_wind, max_load, result_level in LOAD_RULES:
        if wind_mph >= min_wind and load_lb > max_load:
            return _worst(base_risk, result_level, result_level)
    return base_risk


def _checkpoint_interval(checkpoints: list[CheckpointScored]) -> float:
    """Estimate the miles each checkpoint 'represents' for aggregation."""
    if len(checkpoints) < 2:
        return 0.0
    miles: list[float] = [float(cp["mile"]) for cp in checkpoints]
    total: float = miles[-1] - miles[0]
    return total / max(len(checkpoints) - 1, 1)


def _build_summary(severe_miles: float, high_miles: float, avg_score: float) -> str:
    if severe_miles > 0:
        return f"Severe weather: {severe_miles:.0f} mi"
    if high_miles > 50:
        return f"High risk: {high_miles:.0f} mi"
    if avg_score < 1.5:
        return "Low risk"
    if avg_score < 2.5:
        return "Moderate risk"
    return "Elevated risk"
