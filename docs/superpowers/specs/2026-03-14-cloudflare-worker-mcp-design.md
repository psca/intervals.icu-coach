# Cloudflare Worker MCP Server — Design Spec

**Date:** 2026-03-14
**Repo:** `intervals.icu-server/` (new, blank — sibling of `intervals.icu-coach/`)
**Status:** Approved for implementation

---

## Overview

Replace the Python `intervals-mcp-server` fork with a TypeScript Cloudflare Worker that implements the full MCP server. The Worker exposes all existing tools plus a new server-side `get_activity_weather` tool, removing the need for `weather.py`, `uvx`, or any local runtime.

---

## Architecture

```
Claude (Desktop / Code / mobile)
        │  MCP Streamable HTTP
        ▼
CF Worker  (intervals.icu-server, TypeScript)
  ├── MCP protocol layer  (@modelcontextprotocol/sdk)
  ├── Tools               (activities, events, wellness, weather)
  ├── intervals.icu client (fetch + Basic auth, init once from env secrets)
  └── Open-Meteo client   (weather pipeline)
        │
        ├──► https://api.intervals.icu/api/v1
        └──► https://api.open-meteo.com  (recent)
             https://archive-api.open-meteo.com  (historical)
```

### Secrets (stored via `wrangler secret put`)

| Secret | Value |
|---|---|
| `API_KEY` | intervals.icu API key |
| `ATHLETE_ID` | Athlete ID, e.g. `i388529` |

### `.mcp.json` update (in `intervals.icu-coach`)

```json
{
  "mcpServers": {
    "intervals-mcp": {
      "type": "http",
      "url": "https://intervals-mcp.your-subdomain.workers.dev/mcp"
    }
  }
}
```

No local processes. No uvx. No Python environment.

---

## Project Structure

```
intervals.icu-server/
├── src/
│   ├── index.ts          ← Worker entry point; initialise MCP server + HTTP handler
│   ├── client.ts         ← intervals.icu fetch client (one instance, secrets injected)
│   ├── weather.ts        ← Open-Meteo pipeline: streams → waypoints → formatted summary
│   └── tools/
│       ├── activities.ts ← get_activities, get_activity_details, get_activity_intervals,
│       │                    get_activity_streams, get_activity_stream_sampled,
│       │                    get_activity_weather
│       ├── events.ts     ← get_events, get_event_by_id, add_or_update_event,
│       │                    delete_event, delete_events_by_date_range
│       └── wellness.ts   ← get_wellness_data
├── wrangler.toml
├── package.json
└── tsconfig.json
```

---

## MCP Transport Setup

Uses `@modelcontextprotocol/sdk` with Streamable HTTP transport. Minimal Worker skeleton:

```typescript
// src/index.ts
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";

export interface Env {
  API_KEY: string;
  ATHLETE_ID: string;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const server = new McpServer({ name: "intervals-mcp", version: "1.0.0" });
    const transport = new StreamableHTTPServerTransport({ sessionIdGenerator: undefined });

    // Register all tools (pass env to each)
    registerActivityTools(server, env);
    registerEventTools(server, env);
    registerWellnessTools(server, env);

    await server.connect(transport);
    return transport.handleRequest(request);
  },
};
```

Route handled: `POST /mcp`, `GET /mcp`, `DELETE /mcp` — all routed through `transport.handleRequest`.

---

## intervals.icu Client (`client.ts`)

Initialised per-request with secrets from the CF environment:

```typescript
const client = new IntervalsClient(env.API_KEY, env.ATHLETE_ID);
```

Uses `fetch()` with `Authorization: Basic base64("API_KEY:{api_key}")`.

Handles: GET with query params, POST/PUT with JSON body, DELETE, error responses → throws with status + message.

Base URL: `https://api.intervals.icu/api/v1`

---

## Tool Inventory

All tools ported from the Python fork. **`api_key` and `athlete_id` parameters are removed from all tools** — read from CF Secrets, never passed per-call.

### Activities (`tools/activities.ts`)

Port from: `intervals-mcp-server/src/intervals_mcp_server/tools/activities.py`

| Tool | Params kept | Notes |
|---|---|---|
| `get_activities` | `start_date`, `end_date`, `limit`, `include_unnamed` | — |
| `get_activity_details` | `activity_id` | — |
| `get_activity_intervals` | `activity_id` | — |
| `get_activity_streams` | `activity_id`, `stream_types` | — |
| `get_activity_stream_sampled` | `activity_id`, `stream_types`, `interval_seconds` | Kept for direct use; also called internally by `get_activity_weather` |
| `get_activity_weather` | `activity_id` | **New** — see Weather Pipeline section |

Formatting helpers to port: `format_activity_summary`, `format_intervals` from `intervals-mcp-server/src/intervals_mcp_server/utils/formatting.py`.

### Events (`tools/events.ts`)

Port from: `intervals-mcp-server/src/intervals_mcp_server/tools/events.py`

| Tool | Params kept |
|---|---|
| `get_events` | `start_date`, `end_date` |
| `get_event_by_id` | `event_id` |
| `add_or_update_event` | `workout_type`, `name`, `event_id`, `start_date`, `workout_doc`, `moving_time`, `distance` |
| `delete_event` | `event_id` |
| `delete_events_by_date_range` | `start_date`, `end_date` |

**`add_or_update_event` — `workout_doc` serialisation note:**
- `workout_doc` is received as a JSON object from the MCP tool input (nested steps, reps, ramps — see Python `WorkoutDoc` type in `intervals-mcp-server/src/intervals_mcp_server/utils/types.py`)
- When sent to the intervals.icu API, `workout_doc` is serialised as a **JSON string** in the event's `description` field: `description: JSON.stringify(workout_doc)`
- See `_prepare_event_data` in `events.py` line 59: `"description": str(workout_doc)`
- The intervals.icu API then parses the description to extract workout steps

Formatting helpers to port: `format_event_summary`, `format_event_details` from `formatting.py`.

### Wellness (`tools/wellness.ts`)

Port from: `intervals-mcp-server/src/intervals_mcp_server/tools/wellness.py`

| Tool | Params kept |
|---|---|
| `get_wellness_data` | `start_date`, `end_date` |

Formatting helper to port: `format_wellness_entry` from `formatting.py`.

---

## Weather Pipeline (`weather.ts` + `get_activity_weather` tool)

**Replaces `weather.py` entirely.** Implementing this correctly is the main new work. Follow the Python source at `intervals.icu-coach/skills/triathlon-training/scripts/weather.py` closely.

### Tool signature

```typescript
get_activity_weather(activity_id: string): Promise<string>
```

### Step 1 — Fetch activity metadata

Call `GET /activity/{activity_id}` to get `start_date_local` (ISO string, e.g. `"2026-03-10T09:15:00"`).
Extract `date` (first 10 chars) and `start_hour` (hour component, 0–23).

If the activity has no GPS (check: `start_latlng` is null or `type` is not Ride/Run), return:
`"Weather unavailable: no GPS data for this activity."`

### Step 2 — Fetch and sample streams

Call `GET /activity/{activity_id}/streams?types=time,latlng,bearing`.

Sample by time stream: find all indices `i` where `time[i] % 1800 === 0`. Always include index 0.
This matches the sampling logic in `get_activity_stream_sampled` (see `activities.py` lines 394–402).

Extract sampled arrays: `lats` (latlng `data`), `lngs` (latlng `data2`), `bearings` (`data`, may contain nulls).

For each sampled index `i`, compute `hour = (start_hour + Math.floor(time[i] / 3600)) % 24`.

### Step 3 — Fetch Open-Meteo per waypoint (parallel)

Use `Promise.all` to fetch all waypoints concurrently (avoids timeout on long activities).

**API selection by activity age:**
```typescript
const daysAgo = Math.floor((Date.now() - activityDate.getTime()) / 86400000);
const variables = "temperature_2m,apparent_temperature,windspeed_10m,winddirection_10m,precipitation,snowfall,cloudcover,weathercode";

let url: string;
if (daysAgo <= 5) {
  url = `https://api.open-meteo.com/v1/forecast`
      + `?latitude=${lat}&longitude=${lng}&hourly=${variables}`
      + `&past_days=${Math.min(daysAgo + 1, 5)}&forecast_days=1`
      + `&timezone=auto&wind_speed_unit=kmh`;
} else {
  url = `https://archive-api.open-meteo.com/v1/archive`
      + `?latitude=${lat}&longitude=${lng}&start_date=${date}&end_date=${date}`
      + `&hourly=${variables}&timezone=auto&wind_speed_unit=kmh`;
}
```

From the response, find the hourly slot matching `{date}T{hour:02d}:00` and extract all 8 fields.

If Open-Meteo returns non-200 → return `"Weather unavailable: forecast service error."`

### Step 4 — Aggregate across waypoints

- `average_temp` — mean `temperature_2m`
- `average_feels_like` — mean `apparent_temperature`
- `average_wind_speed` — mean `windspeed_10m`
- `prevailing_wind_deg` — mean `winddirection_10m`
- `prevailing_wind_cardinal` — convert degrees to cardinal (16-point: N, NNE, NE … NNW)
  ```typescript
  const dirs = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"];
  dirs[Math.round(deg / 22.5) % 16]
  ```
- `max_rain` — max `precipitation`
- `max_snow` — max `snowfall`
- `average_clouds` — mean `cloudcover`
- `worst_code` — max `weathercode` (used for description)

### Step 5 — Headwind/tailwind classification

Iterate over bearing samples (skip null values). For each bearing, find the nearest waypoint weather by waypoint index distance:

```typescript
// Binary classification — NOT cosine projection
function isHeadwind(travelBearing: number, windFromDeg: number): boolean {
  const delta = Math.abs(((travelBearing - windFromDeg + 180) % 360) - 180);
  return delta < 90;
}
```

Count `headwindCount` and `tailwindCount`. Accumulate `yawSum` with the same angular delta expression used in `isHeadwind`:
```typescript
const delta = Math.abs(((travelBearing - windFromDeg + 180) % 360) - 180);
yawSum += delta;
// delta < 90 → headwind, else tailwind

headwind_percent = Math.round(headwindCount / total * 1000) / 10;  // one decimal
tailwind_percent = Math.round(tailwindCount / total * 1000) / 10;
avg_yaw = Math.round(yawSum / total * 10) / 10;  // mean absolute delta
```

### Step 6 — Return value

Return a **JSON string** (same fields as `weather.py` `compute_weather` output):

```typescript
return JSON.stringify({
  description,              // from weathercode_to_description(worst_code)
  average_temp,
  average_feels_like,
  average_wind_speed,
  prevailing_wind_deg,
  prevailing_wind_cardinal,
  headwind_percent,
  tailwind_percent,
  avg_yaw,
  max_rain,
  max_snow,
  average_clouds,
  temp_bar,                 // ASCII bar string — see below
  source: "open-meteo",
}, null, 2);
```

**`temp_bar`** (port directly from `weather.py` `temp_bar()` function):
```
  Temp        26.8°C  ████████████░░░░░░░░
  Feels like  31.0°C  ████████████████░░░░
```
Scale: 15–45°C, 20-char width, filled = `█`, empty = `░`.

**`weathercode_to_description`** mapping (port from `weather.py`):
- 0 → "Clear sky", 1/2 → "Partly cloudy", 3 → "Overcast", 45/48 → "Foggy"
- 51/53/55 → "Drizzle", 61/63/65 → "Rain", 71/73/75 → "Snow"
- 80/81/82 → "Rain showers", 95/96/99 → "Thunderstorm", else → "Mixed conditions"

---

## Wrangler Config (`wrangler.toml`)

```toml
name = "intervals-mcp"
main = "src/index.ts"
compatibility_date = "2026-01-01"

# Secrets set via:
#   wrangler secret put API_KEY
#   wrangler secret put ATHLETE_ID
```

---

## Setup & Deployment

```bash
cd intervals.icu-server
npm create cloudflare@latest .   # select "Hello World" Worker, TypeScript
npm install @modelcontextprotocol/sdk

wrangler secret put API_KEY
wrangler secret put ATHLETE_ID

wrangler deploy
# → deploys to https://intervals-mcp.<subdomain>.workers.dev
```

Then update `.mcp.json` in `intervals.icu-coach` with the deployed URL.

---

## Skill File Updates (in `intervals.icu-coach`)

Two files need targeted edits. An agent working on skill files should read both files in full first to locate all references.

### `skills/triathlon-training/SKILL.md`

1. **MCP Tool Map table** — add a row for `get_activity_weather`; remove `get_activity_stream_sampled` from the "weather" use-case description (it's now internal)
2. **Tool call order notes** (lines ~36–70) — remove references to `uvx` and the Python MCP server command; replace with CF Worker URL note
3. **Cycling analysis tool call order** — replace "`get_activity_stream_sampled` → run weather.py" with "`get_activity_weather(activity_id)`"
4. **Running analysis tool call order** — same replacement

### `skills/triathlon-training/DISCIPLINE_ANALYSIS.md`

1. **Cycling `### Tools to Call`** (approx. lines 29–38) — replace step referencing `get_activity_stream_sampled` + weather script with `get_activity_weather`
2. **Cycling step 0 weather block** — replace the "run weather.py" instructions with "call `get_activity_weather(activity_id)`; parse returned JSON for `description`, `average_feels_like`, `average_wind_speed`, `prevailing_wind_cardinal`, `headwind_percent`, `tailwind_percent`"
3. **Running `### Tools to Call`** (approx. lines 110–119) — same replacement
4. **Running step 0 weather block** — same replacement

MCP tool names (`get_activities`, `get_wellness_data`, etc.) are **unchanged** — no other edits needed.

---

## What This Replaces

| Before | After |
|---|---|
| `uvx` + Python MCP server running locally | CF Worker (always-on, no local process) |
| `weather.py` script (Desktop: WebFetch workaround, Code: Bash) | `get_activity_weather` MCP tool |
| `get_activity_stream_sampled` as skill-orchestrated weather step | Used internally by `get_activity_weather`; still callable directly |
| `.mcp.json` with `command: uvx` | `.mcp.json` with `type: http, url: https://...` |
| API key in shell env (`INTERVALS_API_KEY`) | API key in CF Secrets |

---

## Out of Scope

- Custom items tools (from plugin — not in the Python fork, not ported here)
- Authentication / multi-user (personal use only — single API key in secrets)
- Response streaming (all tools return complete strings)
