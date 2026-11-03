from django.urls import include, path

urlpatterns = [
    path("api/health", include("api.urls_health")),
    path("api/v1/", include("api.urls")),
]
