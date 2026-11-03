# Architecture Decision Records

---

## ADR-001: OpenRouteService for routing and geocoding

**Context:** The assessment requires a routing API. Paid options (Google Maps, HERE) require billing setup.

**Options considered:**
1. OpenRouteService (ORS) — free tier (2,000 req/day), supports `driving-hgv` profile for heavy trucks, returns encoded polylines
2. Mapbox — free tier but requires credit card
3. GraphHopper — free tier, supports truck routing

**Decision:** OpenRouteService with `driving-hgv` profile.

**Consequences:** API key required (free signup). Free tier is sufficient for demo. Polyline decoding handled by the `polyline` Python package.

---

## ADR-002: Open-Meteo for weather (no API key)

**Context:** Need hourly weather forecasts (wind, rain, snow) at arbitrary lat/lng + time.

**Options considered:**
1. Open-Meteo — free, no API key, hourly forecast up to 16 days, MPH/inch units available
2. OpenWeatherMap — free tier limited to current weather; forecast requires paid plan
3. Tomorrow.io — generous free tier but needs API key

**Decision:** Open-Meteo because it requires no key and provides all needed variables in a single call.

**Consequences:** No auth overhead. Concurrent fetching via `ThreadPoolExecutor` keeps latency low. Snow returned in cm → converted to inches in the service layer.

---

## ADR-003: Stateless Django backend (no persistent DB)

**Context:** The app is a calculator — given a trip, return route options. No user accounts, no history.

**Options considered:**
1. No database at all — `DATABASES = {}` — breaks Django internals
2. SQLite file — adds an unnecessary artifact to the repo
3. In-memory SQLite (`:memory:`) — Django's internals happy, nothing persisted, nothing to commit

**Decision:** In-memory SQLite as the database backend.

**Consequences:** App restarts with zero state (by design). No migrations needed for app data. `pytest-django` works normally.

---

## ADR-004: DRF authentication disabled

**Context:** The API is public — no user accounts. DRF defaults to `SessionAuthentication` + `BasicAuthentication`, which imports `django.contrib.auth` → `contenttypes`, requiring those apps to be in `INSTALLED_APPS`.

**Options considered:**
1. Add `django.contrib.auth` and `django.contrib.contenttypes` to `INSTALLED_APPS`
2. Set `DEFAULT_AUTHENTICATION_CLASSES: []`, `DEFAULT_PERMISSION_CLASSES: []`, `UNAUTHENTICATED_USER: None`

**Decision:** Option 2 — disable auth entirely in `REST_FRAMEWORK` settings.

**Consequences:** Minimal `INSTALLED_APPS`. No unnecessary DB tables. Any future auth would need these apps added back.

---

## ADR-005: React Query `useMutation` instead of `useQuery` for route fetching

**Context:** Route results are triggered by a form submit, not by URL/state changes. React Query's `useQuery` auto-fires on mount and re-fires on focus, which is wrong here.

**Options considered:**
1. `useQuery` with `enabled: false` + manual `refetch()` — awkward, fires on focus
2. `useMutation` — designed for user-triggered side effects with `onSuccess`/`onError` callbacks

**Decision:** `useMutation` via `useRoutesMutation()`.

**Consequences:** Clean submit → result flow. No background refetching. Error handling with `mutation.isError` and `mutation.error`.

---

## ADR-006: Separate vite.config.ts and vitest.config.ts

**Context:** Vitest 2.x bundles its own Vite version. When both `vite` and `vitest/config` exports of `defineConfig` are used in the same file, TypeScript sees incompatible plugin types.

**Options considered:**
1. Use only `vitest/config`'s `defineConfig` in vite.config.ts — plugin type mismatch error
2. Add `// @ts-ignore` — hides the problem
3. Split into two files: `vite.config.ts` (uses `vite`) and `vitest.config.ts` (uses `vitest/config`)

**Decision:** Split config files (Option 3).

**Consequences:** `tsconfig.node.json` includes both files. Each config is clean and type-safe. `package.json` `test` script uses vitest which auto-discovers `vitest.config.ts`.

---

## ADR-007: Checkpoint sampling every 25 miles

**Context:** Need weather at representative points along the route. Too few = miss localized hazards. Too many = too many Open-Meteo API calls.

**Options considered:**
1. Every 10 miles — many API calls, slow
2. Every 25 miles — ~12–50 checkpoints for a typical US cross-country trip
3. Every 50 miles — may miss short storm cells

**Decision:** Every 25 miles (`CHECKPOINT_INTERVAL_MILES = 25` in `risk_thresholds.py`).

**Consequences:** A 1,500-mile route has ~60 checkpoints. With concurrent fetching (ThreadPoolExecutor, 10 workers), this resolves in ~2–3 seconds. The heatmap deduplicates locations within 0.15° to avoid redundant calls.
