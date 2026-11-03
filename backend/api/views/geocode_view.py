"""Address autocomplete endpoint."""

from django.conf import settings
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from api.exceptions import GeocodingError
from api.services.routing_service import RoutingService


class GeocodeView(APIView):
    def get(self, request: Request) -> Response:
        query: str = str(request.query_params.get("q", "")).strip()
        if len(query) < 2:
            return Response([])

        routing = RoutingService(settings.NOMINATIM_BASE_URL, settings.OSRM_BASE_URL)
        try:
            suggestions = routing.suggest_addresses(query)
        except GeocodingError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response(suggestions)
