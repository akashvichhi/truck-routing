# Weather-Aware Truck Routing

A full-stack web app that helps truck drivers choose the safest route based on weather, load weight, and travel time.

## Tech Stack

- **Backend:** Python 3.11 + Django 5 + Django REST Framework
- **Frontend:** React 18 + TypeScript + Vite + Tailwind CSS
- **Map:** React-Leaflet + Leaflet.heat
- **APIs:** OpenRouteService (routing + geocoding), Open-Meteo (weather)

## Prerequisites

- Python 3.11+
- Node.js 18+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- OpenRouteService API key (free at https://openrouteservice.org)

## Local Development

### Backend

```bash
cd backend
cp .env.example .env
# Fill in your ORS_API_KEY in .env

uv sync
uv run python manage.py runserver
```

Backend runs at http://localhost:8000

### Frontend

```bash
cd frontend
cp .env.example .env
# VITE_API_URL is already set to http://localhost:8000 for local dev

npm install
npm run dev
```

Frontend runs at http://localhost:5173

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description |
|---|---|
| `ORS_API_KEY` | OpenRouteService API key |
| `DJANGO_SECRET_KEY` | Django secret key (any long random string) |
| `DJANGO_DEBUG` | `True` for local dev, `False` in production |
| `ALLOWED_HOSTS` | Comma-separated hosts (e.g. `localhost,127.0.0.1`) |
| `CORS_ALLOWED_ORIGINS` | Frontend origin (e.g. `http://localhost:5173`) |

### Frontend (`frontend/.env`)

| Variable | Description |
|---|---|
| `VITE_API_URL` | Backend URL (leave empty in production if same origin) |

## Running Tests

```bash
cd backend
uv run make check
```

## Deployment

- **Backend:** Render (set env vars in dashboard, health check path: `/api/health`)
- **Frontend:** Vercel (set `VITE_API_URL` to deployed backend URL)
