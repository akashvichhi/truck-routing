"""Single source of truth for all weather risk thresholds and load rules."""

# Risk level labels (ordered by severity)
RISK_LOW = "low"
RISK_MODERATE = "moderate"
RISK_HIGH = "high"
RISK_SEVERE = "severe"
RISK_NO_TRAVEL = "no_travel"

# Numeric score for each level (used for ranking and heatmap weight)
RISK_SCORES: dict[str, int] = {
    RISK_LOW: 1,
    RISK_MODERATE: 2,
    RISK_HIGH: 3,
    RISK_SEVERE: 4,
    RISK_NO_TRAVEL: 5,
}

# Wind thresholds in mph
WIND_MODERATE_MIN: float = 25.0
WIND_HIGH_MIN: float = 35.0
WIND_SEVERE_MIN: float = 45.0
WIND_NO_TRAVEL_MIN: float = 55.0

# Rain thresholds in inches/hour
RAIN_MODERATE_MIN: float = 0.10
RAIN_HIGH_MIN: float = 0.25
RAIN_SEVERE_MIN: float = 0.50
RAIN_NO_TRAVEL_MIN: float = 1.00

# Snow thresholds in inches/hour
SNOW_MODERATE_MIN: float = 0.5
SNOW_HIGH_MIN: float = 1.0
SNOW_SEVERE_MIN: float = 2.0
SNOW_NO_TRAVEL_MIN: float = 3.0

# Load rules: (min_wind_mph, max_load_lb, resulting_level)
# Evaluated in order; first match wins (after base risk is computed)
LOAD_RULES: list[tuple[float, float, str]] = [
    # Wind ≥55 → No Travel for any load
    (55.0, float("inf"), RISK_NO_TRAVEL),
    # Wind 45–54 + load > 30,000 lb → No Travel
    (45.0, 30_000.0, RISK_NO_TRAVEL),
    # Wind 35–44 + load > 40,000 lb → Severe
    (35.0, 40_000.0, RISK_SEVERE),
]

# Checkpoint sampling interval in miles
CHECKPOINT_INTERVAL_MILES: float = 25.0

# Average truck speed used for ETA calculation
AVG_TRUCK_SPEED_MPH: float = 55.0

# Maximum weather forecast horizon (hours)
MAX_FORECAST_HOURS: int = 48
