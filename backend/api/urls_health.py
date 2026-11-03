from django.urls import path

from api.views.health_view import HealthView

urlpatterns = [
    path("", HealthView.as_view()),
]
