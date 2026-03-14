# Cloudflare Worker MCP Server — Design Spec

**Date:** 2026-03-14
**Repo:** `intervals.icu-server/` (new, blank — sibling of `intervals.icu-coach/`)
**Status:** Approved for implementation

---

## Overview

Replace the Python `intervals-mcp-server` fork with a TypeScript Cloudflare Worker that implements the full MCP server. The Worker exposes all existing tools plus a new server-side weather tool, removing the need for `weather.py`, `uvx`, or any local runtime.

---

## Architecture

```
Claude (Desktop / Code / mobile)
        │  MCP Streamable HTTP
        ▼
CF Worker  (intervals.icu-server, TypeScript)
  ├── MCP protocol layer  (@modelcontextprotocol/sdk)
  ├── Tools               (activities, events, wellness, weather)
  ├── intervals.icu client (fetch + Basic auth, init once from secrets)
  └── Open-Meteo client   (weather pipeline)
        │
        ├──► https://api.intervals.icu/api/v1
        └──► https://archive-api.open-meteo.com/v1/archive
```

### Secrets (stored via `wrangler secret put`)

| Secret | Value |
|---|---|
| `API_KEY` | intervals.icu API key |
| `ATHLETE_ID` | Athlete ID, e.g. `i388529` |

### `.mcp.json` (in `intervals.icu-coach`)

```json
{
  "mcpServers": {
    "intervals-mcp": {
      "type": "http",
      "url": "https://your-worker.workers.dev/mcp"
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
│       │                    get_activity_streams, get_activity_stream_sampled
│       ├── events.ts     ← get_events, get_event_by_id, add_or_update_event,
│       │                    delete_event, delete_events_by_date_range
│       └── wellness.ts   ← get_wellness_data
├── wrangler.toml
├── package.json
└── tsconfig.json
```

---

## intervals.icu Client (`client.ts`)

Initialised once at Worker startup with secrets from the CF environment:

```typescript
const client = new IntervalsClient(env.API_KEY, env.ATHLETE_ID);
```

All methods use `fetch()` with `Authorization: Basic base64("API_KEY:{api_key}")`.

Handles:
- GET with query params
- POST / PUT with JSON body
- DELETE
- Error responses → throw with status + message

Base URL: `https://api.intervals.icu/api/v1`

---

## Tool Inventory

All tools ported from the Python fork. `api_key` and `athlete_id` parameters are **removed from all tools** — they are read from CF Secrets at startup, never passed per-call.

### Activities (`tools/activities.ts`)

| Tool | Signature change from Python | Notes |
|---|---|---|
| `get_activities` | Remove `api_key`, `athlete_id` | Keep `start_date`, `end_date`, `limit`, `include_unnamed` |
| `get_activity_details` | Remove `api_key` | Keep `activity_id` |
| `get_activity_intervals` | Remove `api_key` | Keep `activity_id` |
| `get_activity_streams` | Remove `api_key` | Keep `activity_id`, `stream_types` |
| `get_activity_stream_sampled` | Remove `api_key` | Keep `activity_id`, `stream_types`, `interval_seconds` |

### Events (`tools/events.ts`)

| Tool | Signature change |
|---|---|
| `get_events` | Remove `api_key`, `athlete_id` |
| `get_event_by_id` | Remove `api_key`, `athlete_id` |
| `add_or_update_event` | Remove `api_key`, `athlete_id` |
| `delete_event` | Remove `api_key`, `athlete_id` |
| `delete_events_by_date_range` | Remove `api_key`, `athlete_id` |

`add_or_update_event` retains the full `workout_doc` structure (nested steps, reps, ramps, etc.) exactly as defined in the Python fork.

### Wellness (`tools/wellness.ts`)

| Tool | Signature change |
|---|---|
| `get_wellness_data` | Remove `api_key`, `athlete_id` |

### Weather (`weather.ts` + registered as a tool)

**New tool: `get_activity_weather(activity_id: string)`**

Replaces `weather.py` entirely. Works on any client (Desktop, Code, mobile) with no client-side script.

Pipeline:
1. Call `GET /activity/{id}/streams?types=time,latlng,bearing` via intervals client
2. Apply `get_activity_stream_sampled` logic: sample one point every 1800s from time stream
3. For each waypoint (lat, lng, bearing, datetime): call Open-Meteo archive API
   - Fields: `windspeed_10m`, `winddirection_10m`, `apparent_temperature`, `precipitation`, `weathercode`
4. Per waypoint: compute headwind % — `cos(bearing_rad - wind_dir_rad) * 100`, clamp 0–100
5. Aggregate across waypoints: average feels-like, prevailing wind direction, % headwind, % tailwind, max precipitation
6. Return formatted summary string (same format as current `weather.py` output):
   ```
   {description} — {feels_like}°C feels-like, {wind} km/h {dir} ({headwind}% headwind / {tailwind}% tailwind)
   ```

If activity has no GPS data → return `"Weather unavailable: no GPS data for this activity."`
If Open-Meteo returns non-200 → return `"Weather unavailable: forecast service error."`

---

## MCP Transport

Uses MCP Streamable HTTP transport (`@modelcontextprotocol/sdk`). The Worker's `fetch` handler routes:

- `POST /mcp` — MCP JSON-RPC (tool calls, init)
- `GET /mcp` — SSE stream (server-initiated messages, if needed)
- `DELETE /mcp` — session cleanup

CF Workers Streamable HTTP is well-supported by the MCP SDK. Reference: Cloudflare's `workers-mcp` examples.

---

## Wrangler Config (`wrangler.toml`)

```toml
name = "intervals-mcp"
main = "src/index.ts"
compatibility_date = "2025-01-01"

[vars]
# Non-secret config here if needed

# Secrets set via: wrangler secret put API_KEY
#                  wrangler secret put ATHLETE_ID
```

---

## Setup & Deployment

```bash
# One-time setup
cd intervals.icu-server
npm create cloudflare@latest .   # select "Hello World" Worker, TypeScript
npm install @modelcontextprotocol/sdk

# Set secrets
wrangler secret put API_KEY
wrangler secret put ATHLETE_ID

# Deploy
wrangler deploy

# Connect Claude Code
# Update .mcp.json url to the deployed worker URL
# Or: claude mcp add intervals-mcp --transport http https://intervals-mcp.your-subdomain.workers.dev/mcp
```

---

## Skill File Impact

`SKILL.md` and `DISCIPLINE_ANALYSIS.md` need minor updates:
- Remove references to `weather.py` / running the weather script
- Replace "call `get_activity_stream_sampled` → run weather.py" with "call `get_activity_weather(activity_id)`"
- MCP tool names (`get_activities`, `get_wellness_data`, etc.) are **unchanged** — no other skill file changes needed

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
- Response streaming (all tools return complete strings, no SSE needed for tool results)
