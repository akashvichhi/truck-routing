# AI Workflow Log

---

## 2026-11-02 — Full project scaffold and implementation

**Prompt / instruction given to the AI:**
> "Please complete entire project. Do not commit the code. I will commit by myself."
> Tech stack: Django 5 + DRF, React 18 + TypeScript + Vite + Tailwind CSS 3, React-Leaflet + leaflet.heat, Open-Meteo (weather), OpenRouteService (routing/geocoding).

**What the AI produced:**
- `backend/`: Django project with `config/`, `api/views/`, `api/services/` (routing, weather, risk), `api/serializers/`, `api/constants/risk_thresholds.py`, full test suite (43 unit + integration tests at 80%+ coverage)
- `frontend/`: React app with TripForm, RouteMap (Leaflet + heatmap), RoutePanel, ForecastSlider, axios interceptors for snake_case↔camelCase conversion, React Query mutation hook
- `docs/`, `README.md`, `.gitignore`, `.env.example` files

**What was changed, rejected, or corrected:**
- Python 3.14 was installed; Django 5.1.3 doesn't support 3.14 → pinned `django==5.2.18`
- `uv` not available on system → switched to `python -m venv .venv` + pip
- `os.setdefault(...)` typo in manage.py → corrected to `os.environ.setdefault(...)`
- `DATABASES = {}` caused Django errors → used in-memory SQLite `NAME: ":memory:"`
- DRF's default auth classes import `AnonymousUser` which requires `contenttypes` in INSTALLED_APPS → disabled auth by setting `DEFAULT_AUTHENTICATION_CLASSES: []`, `DEFAULT_PERMISSION_CLASSES: []`, `UNAUTHENTICATED_USER: None`
- `@pytest.mark.django_db` removed from integration tests (stateless app)
- vite.config.ts: using `defineConfig` from `vitest/config` caused plugin type conflicts with vite 6 → split into separate `vite.config.ts` (vite) and `vitest.config.ts` (vitest)
- ESLint flat config missing browser globals (`HTMLInputElement`, `FormData`, `Blob`) → added to globals
- `@types/chai` missing (vitest internal dep) → installed as devDependency
- mypy strict: `polyline` missing stubs → added `# type: ignore[import-untyped]`; `dict[str, object]` incompatible with requests params → typed as `dict[str, str | int]`; route_request_serializer type-ignore codes were stale post-django-stubs → updated
- Haversine `R` variable uppercase in function → renamed to `earth_radius_miles`
- Weather service tests only covered `_pick_weather_at` (43% coverage) → added 17 new tests for `_fetch_forecast`, `fetch_weather_for_checkpoints`, `build_heatmap_data`, `_close` → coverage reached 93%
- `_make_forecast` helper generated invalid hours (>23) for 48h range → fixed with proper datetime arithmetic

**How it was verified:**
- `make check` equivalent: `ruff check --fix` → clean; `mypy api config --strict` → 0 errors; `pytest` → 60 passed, 93% coverage
- `npm run check` → ESLint clean + `tsc -b --noEmit` passes + 6 vitest tests pass
- Both dev servers confirmed running: `GET /api/health` → `{"status": "ok"}`; `POST /api/v1/routes` with same origin/destination → correct 400 validation error; with valid payload + no ORS key → correct 401 upstream error message

---

## 2026-11-02 — ORS API key setup (pending user action)

**Prompt / instruction given to the AI:**
> (Implicit) The app requires an ORS API key for geocoding and routing.

**What the AI produced:**
> Nothing — this is a user action item.

**What I changed:**
> User must sign up at https://openrouteservice.org/dev/#/signup, copy the API key, and paste it into `backend/.env` as `ORS_API_KEY=<key>`.
> After that, `POST /api/v1/routes` with a real origin/destination/departure/load will return routes.

**How it will be verified:**
> Submit the trip form in the browser at http://localhost:5173 with a valid US origin and destination. The map should show 3 polylines with checkpoint risk markers and a heatmap.
