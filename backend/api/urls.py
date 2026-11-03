from django.urls import path

from api.views.geocode_view import GeocodeView
from api.views.route_view import RouteView

urlpatterns = [
    path("routes", RouteView.as_view()),
    path("geocode", GeocodeView.as_view()),
]
