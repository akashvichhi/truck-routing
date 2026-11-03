"""Django settings for truck-routing backend."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY: str = os.environ.get("DJANGO_SECRET_KEY", "dev-secret-key")
DEBUG: bool = os.environ.get("DJANGO_DEBUG", "True") == "True"

_allowed = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1")
ALLOWED_HOSTS: list[str] = [h.strip() for h in _allowed.split(",") if h.strip()]

INSTALLED_APPS: list[str] = [
    "corsheaders",
    "rest_framework",
    "api",
]

MIDDLEWARE: list[str] = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

# In-memory SQLite — app is stateless, no app data stored, but Django internals need it
DATABASES: dict[str, object] = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

_cors_origins = os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:5173")
CORS_ALLOWED_ORIGINS: list[str] = [o.strip() for o in _cors_origins.split(",") if o.strip()]

REST_FRAMEWORK: dict[str, object] = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    # No auth or permissions — this is a stateless public API
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
    "UNAUTHENTICATED_USER": None,
}

# External API config
NOMINATIM_BASE_URL: str = "https://nominatim.openstreetmap.org"
OSRM_BASE_URL: str = "http://router.project-osrm.org"
OPEN_METEO_BASE_URL: str = "https://api.open-meteo.com/v1/forecast"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
