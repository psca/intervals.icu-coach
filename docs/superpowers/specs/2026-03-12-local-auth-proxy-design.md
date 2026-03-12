# Local Auth Proxy — Design Spec
**Date:** 2026-03-12
**Status:** Approved
**Replaces:** `docs/superpowers/specs/2026-03-12-weather-enrichment-design.md` (superseded)

---

## Problem

The triathlon coaching skill currently relies on a third-party MCP server (`mvilanova/intervals-mcp-server`) to access intervals.icu. This is being sunset due to inflexibility. The replacement must:

1. Work on Claude Desktop, Claude Code/CLI, and any harness that supports WebFetch
2. Handle intervals.icu Basic auth without requiring Claude to send custom HTTP headers (WebFetch cannot)
3. Expose the native intervals.icu weather endpoint (`/activity/{id}/weather-summary`), which is richer than any external weather source

**Mobile (Claude.ai app) is deferred:** No MCP, no Bash, and WebFetch can't reach localhost. Future path: Cloudflare Workers serverless proxy that holds credentials and proxies to intervals.icu. Same skill files would work unchanged — only the base URL would differ.

---

## Solution

A local auth proxy: a single Python file (~60 lines), zero external dependencies (stdlib only), that runs on localhost and injects Basic auth on every request before forwarding to `https://api.intervals.icu`.

The Claude skill calls `WebFetch http://localhost:{PORT}/api/v1/...` instead of MCP tools. No protocol overhead, no third-party code, full control over the API surface.

---

## Architecture

```
Claude skill (SKILL.md instructions)
    ↓  WebFetch http://localhost:8080/api/v1/athlete/i388529/activities
Local proxy  (intervals-proxy/server.py)
    ↓  GET https://api.intervals.icu/api/v1/athlete/i388529/activities
    ↓  Authorization: Basic base64("API_KEY:{INTERVALS_API_KEY}")
intervals.icu REST API
    ↓  JSON response
Local proxy  (passes through status + body unchanged)
    ↑  Claude skill parses and interprets
```

The proxy is a **generic passthrough** — it adds auth and forwards. No business logic, no response shaping. The skill stays the intelligence layer.

---

## Proxy Implementation

### File Structure

```
intervals-proxy/
├── __init__.py
└── server.py      # ~60 lines, zero deps
```

### Behaviour

- **GET, POST, PUT, DELETE, PATCH** all supported — passes method, headers (minus auth), query params, and body through unchanged
- **Auth injection:** `Authorization: Basic base64("API_KEY:{INTERVALS_API_KEY}")`
- **Response passthrough:** Status code, Content-Type, and body returned as-is from intervals.icu
- **Logging:** Each request logged to stdout as `METHOD /path → STATUS`

### Configuration

| Env var | Required | Default | Purpose |
|---|---|---|---|
| `INTERVALS_API_KEY` | Yes | — | intervals.icu API key |
| `INTERVALS_ATHLETE_ID` | No (skill uses it) | — | Athlete ID used in skill URLs |
| `INTERVALS_PROXY_PORT` | No | `8080` | Port the proxy listens on |

`INTERVALS_ATHLETE_ID` is not used by the proxy itself — it's injected into WebFetch URLs by the skill instructions.

### Startup

```bash
# Direct
python -m intervals_proxy.server

# Via uvx (zero local install)
uvx --from git+https://github.com/your-repo/intervals-proxy.git python -m intervals_proxy.server
```

Add to shell profile for auto-start, or run manually before using the skill.

---

## Weather Integration

### Native Endpoint (replaces Open-Meteo)

`GET /api/v1/activity/{id}/weather-summary`

Returns `ActivityWeatherSummary` — route-aware weather already computed by intervals.icu:

| Field | Coaching use |
|---|---|
| `average_weather_temp`, `min_weather_temp`, `max_weather_temp` | Heat/cold context for decoupling and EF |
| `average_feels_like` | Perceived temperature (humidity + wind combined) |
| `average_wind_speed`, `prevailing_wind_deg` | Wind intensity + direction |
| `headwind_percent`, `tailwind_percent` | Route-aware wind impact — primary VI/IF context for cycling |
| `max_rain`, `max_showers`, `max_snow` | Precipitation — explains anomalous HR/power |
| `description` | Plain-language summary; use as the weather lead line in output |

### Why This Is Better Than Open-Meteo

- **Route-aware:** `headwind_percent`/`tailwind_percent` are computed against the actual GPS route, not just wind direction at a point
- **No GPS extraction needed:** No lat/lng parsing, no hour-matching, no archive lag
- **Already computed by intervals.icu:** Zero extra complexity — one API call
- **Feels-like temp:** Accounts for humidity + wind together; more relevant to decoupling than raw temp

### Previous Design Superseded

The `2026-03-12-weather-enrichment-design.md` spec (Open-Meteo via WebFetch) is obsolete. The `feature/weather-enrichment` git branch has been discarded. Weather enrichment is redesigned here using the native endpoint.

---

## Skill File Changes

### SKILL.md

Replace the MCP Tool Map with a WebFetch endpoint table:

| Use Case | Endpoint | Notes |
|---|---|---|
| Load history, CTL/ATL/TSB | `GET /api/v1/athlete/{id}/activities` | Add `?oldest=&newest=` date range params |
| Wellness / HRV / resting HR | `GET /api/v1/athlete/{id}/wellness` | Add `?oldest=&newest=` |
| Single activity detail | `GET /api/v1/activity/{id}` | — |
| Activity intervals | `GET /api/v1/activity/{id}/intervals` | — |
| Activity weather | `GET /api/v1/activity/{id}/weather-summary` | Single-activity only; skip if no response |
| Power/HR streams | `GET /api/v1/activity/{id}/streams` | ⚠️ High token cost — only for decoupling/VI |
| Create planned event | `POST /api/v1/athlete/{id}/events` | ⚠️ Write operation |
| Update planned event | `PUT /api/v1/athlete/{id}/events/{eventId}` | ⚠️ Write operation |
| Delete planned event | `DELETE /api/v1/athlete/{id}/events/{eventId}` | ⚠️ Permanent |

Update tool call order notes to reference WebFetch URLs instead of MCP tool names.

### DISCIPLINE_ANALYSIS.md

**Cycling and running step 0 (weather context):**

Replace the Open-Meteo block with:

```
**0. Fetch weather context**

Call `WebFetch http://localhost:8080/api/v1/activity/{id}/weather-summary`
- If response empty or non-200 → skip weather, note "weather unavailable" and proceed
- If OK → extract: description, average_weather_temp, average_feels_like,
  average_wind_speed, prevailing_wind_deg (convert to cardinal), headwind_percent,
  tailwind_percent, max_rain, max_showers, max_snow
- Lead output with: "{description} — {feels_like}°C feels-like,
  {wind} km/h {dir} ({headwind}% headwind / {tailwind}% tailwind)"
```

No GPS extraction. No lat/lng. No hour-matching. One call.

**All other MCP tool references** (get_activities, get_wellness_data, get_activity_details, get_activity_intervals, get_activity_streams) replaced with their WebFetch equivalents.

### METRICS_REFERENCE.md

Update `## Weather Context Thresholds` to reflect native response fields:

- Use `average_feels_like` (not raw temp) as the primary heat signal — it accounts for humidity automatically
- `headwind_percent > 40%` → flag as significant aerodynamic load on cycling VI/IF
- `tailwind_percent > 60%` → note in output; power may be understated vs. typical efforts
- `max_rain > 0` or `max_showers > 0` → explain conservative pacing and VI anomalies

---

## Error Handling

| Scenario | Proxy behaviour | Skill behaviour |
|---|---|---|
| intervals.icu returns 401 | Pass through 401 | Note "API key invalid or expired" |
| intervals.icu returns 404 | Pass through 404 | Note "activity/athlete not found" |
| intervals.icu unavailable | Connection error → 503 | Note "intervals.icu unreachable" |
| Proxy not running | WebFetch fails (connection refused) | Note "proxy not running — start with `python -m intervals_proxy.server`" |
| Weather endpoint returns empty | Pass through | Skip weather, proceed with analysis |

---

## What Is Not Changing

- `COACH_PERSONA.md` — output style unchanged
- `WORKOUT_PLANNING.md` — write operation logic unchanged (endpoints update, logic stays)
- Analysis thresholds in `METRICS_REFERENCE.md` (decoupling %, EF, VI, TSB) — unchanged
- Per-discipline analysis sequences in `DISCIPLINE_ANALYSIS.md` — steps 1–5 unchanged; only step 0 (weather) and tool references update

---

## Future: Mobile Support

When mobile support is needed, deploy a Cloudflare Worker (~15 lines) that:
- Accepts a user-scoped token in the URL or a query param
- Holds credentials server-side
- Proxies to intervals.icu with Basic auth

The skill files would change only the base URL (`http://localhost:8080` → `https://your-worker.workers.dev`). No other skill changes needed.

---

## Implementation Sequence

1. Build `intervals-proxy/server.py` (proxy server)
2. Update `SKILL.md` (tool map → endpoint table)
3. Update `DISCIPLINE_ANALYSIS.md` (MCP calls → WebFetch, native weather block)
4. Update `METRICS_REFERENCE.md` (weather thresholds for native fields)
5. Test end-to-end with a real activity
6. Update desktop extension packaging (separate task — MCP → proxy distribution TBD)
