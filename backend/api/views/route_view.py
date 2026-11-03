"""Main endpoint: POST /api/v1/routes"""

from django.conf import settings
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from api.exceptions import GeocodingError, RoutingAPIError, WeatherAPIError
from api.serializers.route_request_serializer import RouteRequestSerializer
from api.services.risk_service import RiskService
from api.services.routing_service import RoutingService
from api.services.weather_service import WeatherService


class RouteView(APIView):
    def post(self, request: Request) -> Response:
        req_serializer = RouteRequestSerializer(data=request.data)
        if not req_serializer.is_valid():
            return Response(
                {"error": "Validation failed", "details": req_serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = req_serializer.validated_data
        origin: str = data["origin"]
        destination: str = data["destination"]
        departure_dt = data["departure_datetime"]
        load_weight_lbs: float = float(data["load_weight_lbs"])

        routing = RoutingService(settings.NOMINATIM_BASE_URL, settings.OSRM_BASE_URL)
        weather = WeatherService(settings.OPEN_METEO_BASE_URL)
        risk = RiskService()

        try:
            origin_coord = routing.geocode(origin)
            dest_coord = routing.geocode(destination)
        except GeocodingError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            raw_routes = routing.get_routes(origin_coord, dest_coord)
        except RoutingAPIError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        # Collect ALL checkpoints across routes for heatmap
        all_checkpoints = []
        routes_with_checkpoints = []

        for route in raw_routes:
            checkpoints_base = routing.sample_checkpoints(
                route["geometry"],
                departure_dt,
                route["distance_miles"],
                route["duration_hours"],
            )
            routes_with_checkpoints.append((route, checkpoints_base))
            all_checkpoints.extend(checkpoints_base)

        try:
            # Fetch weather for all checkpoints in one batched parallel call
            all_weather = weather.fetch_weather_for_checkpoints(all_checkpoints)
        except WeatherAPIError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        # Distribute weather-enriched checkpoints back to their routes
        scored_routes = []
        offset = 0
        for route, checkpoints_base in routes_with_checkpoints:
            n = len(checkpoints_base)
            enriched = all_weather[offset : offset + n]
            offset += n
            scored_cp = risk.score_checkpoints(enriched, load_weight_lbs)
            scored_routes.append(risk.summarize_route(route, scored_cp, load_weight_lbs))

        ranked = risk.rank_routes(scored_routes)

        try:
            heatmap_points = weather.build_heatmap_data(all_checkpoints, departure_dt)
        except WeatherAPIError:
            heatmap_points = []  # heatmap is non-critical; degrade gracefully

        return Response(
            {
                "data": {
                    "recommended_route_index": 0,  # index 0 is always best after ranking
                    "routes": ranked,
                    "heatmap_points": heatmap_points,
                }
            },
            status=status.HTTP_200_OK,
        )
