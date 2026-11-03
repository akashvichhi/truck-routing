"""Validates incoming route request data."""

from datetime import UTC, datetime, timedelta
from typing import Any

from rest_framework import serializers


class RouteRequestSerializer(serializers.Serializer):  # type: ignore[type-arg]
    origin = serializers.CharField(max_length=300)
    destination = serializers.CharField(max_length=300)
    departure_datetime = serializers.DateTimeField()
    load_weight_lbs = serializers.FloatField(min_value=0, max_value=200_000)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        origin: str = attrs["origin"].strip()
        destination: str = attrs["destination"].strip()

        if not origin:
            raise serializers.ValidationError({"origin": "Origin cannot be blank."})
        if not destination:
            raise serializers.ValidationError({"destination": "Destination cannot be blank."})
        if origin.lower() == destination.lower():
            raise serializers.ValidationError(
                {"destination": "Destination must differ from origin."}
            )

        departure: datetime = attrs["departure_datetime"]
        # Ensure timezone-aware
        if departure.tzinfo is None:
            departure = departure.replace(tzinfo=UTC)
            attrs["departure_datetime"] = departure

        now = datetime.now(tz=UTC)
        if departure < now - timedelta(hours=1):
            raise serializers.ValidationError(
                {"departure_datetime": "Departure time cannot be in the past."}
            )
        if departure > now + timedelta(days=10):
            raise serializers.ValidationError(
                {"departure_datetime": "Departure time must be within the next 10 days."}
            )

        attrs["origin"] = origin
        attrs["destination"] = destination
        return attrs
