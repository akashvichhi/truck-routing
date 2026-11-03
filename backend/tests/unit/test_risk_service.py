"""Unit tests for RiskService — covers every threshold boundary and load rule."""

import pytest

from api.services.risk_service import RiskService


@pytest.fixture
def svc() -> RiskService:
    return RiskService()


class TestWindClassification:
    def test_below_25_is_low(self, svc: RiskService) -> None:
        assert svc.calculate_checkpoint_risk(24.9, 0, 0, 0) == "low"

    def test_exactly_25_is_moderate(self, svc: RiskService) -> None:
        assert svc.calculate_checkpoint_risk(25.0, 0, 0, 0) == "moderate"

    def test_exactly_35_is_high(self, svc: RiskService) -> None:
        assert svc.calculate_checkpoint_risk(35.0, 0, 0, 0) == "high"

    def test_exactly_45_is_severe(self, svc: RiskService) -> None:
        assert svc.calculate_checkpoint_risk(45.0, 0, 0, 0) == "severe"

    def test_exactly_55_is_no_travel(self, svc: RiskService) -> None:
        assert svc.calculate_checkpoint_risk(55.0, 0, 0, 0) == "no_travel"

    def test_above_55_is_no_travel(self, svc: RiskService) -> None:
        assert svc.calculate_checkpoint_risk(80.0, 0, 0, 0) == "no_travel"


class TestRainClassification:
    def test_below_0_10_is_low(self, svc: RiskService) -> None:
        assert svc.calculate_checkpoint_risk(0, 0.09, 0, 0) == "low"

    def test_exactly_0_10_is_moderate(self, svc: RiskService) -> None:
        assert svc.calculate_checkpoint_risk(0, 0.10, 0, 0) == "moderate"

    def test_exactly_0_25_is_high(self, svc: RiskService) -> None:
        assert svc.calculate_checkpoint_risk(0, 0.25, 0, 0) == "high"

    def test_exactly_0_50_is_severe(self, svc: RiskService) -> None:
        assert svc.calculate_checkpoint_risk(0, 0.50, 0, 0) == "severe"

    def test_above_1_00_is_no_travel(self, svc: RiskService) -> None:
        assert svc.calculate_checkpoint_risk(0, 1.01, 0, 0) == "no_travel"


class TestSnowClassification:
    def test_below_0_5_is_low(self, svc: RiskService) -> None:
        assert svc.calculate_checkpoint_risk(0, 0, 0.4, 0) == "low"

    def test_exactly_0_5_is_moderate(self, svc: RiskService) -> None:
        assert svc.calculate_checkpoint_risk(0, 0, 0.5, 0) == "moderate"

    def test_exactly_1_0_is_high(self, svc: RiskService) -> None:
        assert svc.calculate_checkpoint_risk(0, 0, 1.0, 0) == "high"

    def test_exactly_2_0_is_severe(self, svc: RiskService) -> None:
        assert svc.calculate_checkpoint_risk(0, 0, 2.0, 0) == "severe"

    def test_above_3_0_is_no_travel(self, svc: RiskService) -> None:
        assert svc.calculate_checkpoint_risk(0, 0, 3.1, 0) == "no_travel"


class TestLoadRules:
    def test_wind_55_any_load_is_no_travel(self, svc: RiskService) -> None:
        assert svc.calculate_checkpoint_risk(55.0, 0, 0, 1000) == "no_travel"

    def test_wind_45_load_over_30000_is_no_travel(self, svc: RiskService) -> None:
        assert svc.calculate_checkpoint_risk(50.0, 0, 0, 30_001) == "no_travel"

    def test_wind_45_load_under_30000_is_severe(self, svc: RiskService) -> None:
        # Base wind risk at 50 mph is severe; load does not escalate further
        assert svc.calculate_checkpoint_risk(50.0, 0, 0, 29_999) == "severe"

    def test_wind_35_load_over_40000_is_severe(self, svc: RiskService) -> None:
        assert svc.calculate_checkpoint_risk(40.0, 0, 0, 40_001) == "severe"

    def test_wind_35_load_under_40000_is_high(self, svc: RiskService) -> None:
        assert svc.calculate_checkpoint_risk(40.0, 0, 0, 39_999) == "high"


class TestWorstRiskWins:
    def test_rain_dominates_when_worse(self, svc: RiskService) -> None:
        # wind=low, rain=severe, snow=low
        assert svc.calculate_checkpoint_risk(10.0, 0.6, 0.1, 0) == "severe"

    def test_snow_dominates_when_worse(self, svc: RiskService) -> None:
        assert svc.calculate_checkpoint_risk(10.0, 0.0, 3.1, 0) == "no_travel"


class TestRankRoutes:
    def _make_route(
        self,
        idx: int,
        severe: float,
        high: float,
        score: float,
        duration: float,
    ) -> dict:
        return {
            "index": idx,
            "severe_miles": severe,
            "high_miles": high,
            "risk_score": score,
            "duration_hours": duration,
            "summary": "",
            "distance_miles": 100.0,
            "geometry": [],
            "checkpoints": [],
        }

    def test_fewest_severe_miles_wins(self, svc: RiskService) -> None:
        routes = [
            self._make_route(0, 50.0, 0, 1.0, 5.0),
            self._make_route(1, 10.0, 0, 2.0, 6.0),
        ]
        ranked = svc.rank_routes(routes)
        assert ranked[0]["severe_miles"] == 10.0

    def test_fewest_high_miles_wins_on_tie(self, svc: RiskService) -> None:
        routes = [
            self._make_route(0, 0, 100.0, 1.0, 5.0),
            self._make_route(1, 0, 20.0, 2.0, 6.0),
        ]
        ranked = svc.rank_routes(routes)
        assert ranked[0]["high_miles"] == 20.0

    def test_shortest_duration_wins_on_full_tie(self, svc: RiskService) -> None:
        routes = [
            self._make_route(0, 0, 0, 1.0, 6.0),
            self._make_route(1, 0, 0, 1.0, 5.0),
        ]
        ranked = svc.rank_routes(routes)
        assert ranked[0]["duration_hours"] == 5.0
