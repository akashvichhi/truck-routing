class GeocodingError(Exception):
    """Raised when an address cannot be geocoded."""


class RoutingAPIError(Exception):
    """Raised when the routing API call fails."""


class WeatherAPIError(Exception):
    """Raised when the weather API call fails."""
