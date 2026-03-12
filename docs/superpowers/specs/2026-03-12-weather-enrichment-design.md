# Weather Enrichment — Design Spec
**Date:** 2026-03-12
**Status:** Approved
**Scope:** Add historical weather context to single-activity analysis in the triathlon coaching skill

---

## Problem

Metrics like aerobic decoupling and Efficiency Factor (EF) are highly sensitive to ambient conditions. A 14% decoupling reading means something very different at 31°C / 78% humidity vs. 15°C with cloud cover. Without weather context, the coach must either ignore conditions or ask the athlete to recall them — both degrade analysis quality.

---

## Solution

After `get_activity_details` (already part of every single-activity analysis), check for GPS coordinates and fetch historical weather from Open-Meteo's free archive API. Weave conditions into existing decoupling, EF, and VI commentary as 1–2 sentence contextualizers. No separate "weather report" section.

---

## Scope Constraints

- **Single-activity analysis only.** Not triggered during fitness overviews, race readiness checks, or batch activity lists. Adding weather to 30+ activities would hit Open-Meteo rate limits and bloat context.
- **Cycling and running only.** Pool swimming has no GPS and controlled conditions — weather is irrelevant. Open-water swimming TBD (out of scope for this iteration).
- **No new files.** Changes land in three existing skill files: `DISCIPLINE_ANALYSIS.md`, `METRICS_REFERENCE.md`, and `SKILL.md`.

---

## Architecture

### Files Modified

| File | Change |
|---|---|
| `DISCIPLINE_ANALYSIS.md` | Add `## Weather Context` decision block to cycling and running tool-call sequences, after `get_activity_details` |
| `METRICS_REFERENCE.md` | Add `## Weather Context Thresholds` section |
| `SKILL.md` | Add `WebFetch` row to MCP Tool Map; add weather-aware phrase to Command Patterns |

---

## Data Flow

```
get_activity_details
  └─ start_lat_lng present?
       ├─ NO (indoor / pool / no GPS lock)
       │    └─ Skip weather. Note in output: "indoor or no GPS — weather unavailable"
       └─ YES
            ├─ Extract: lat, lon, start_date_local (YYYY-MM-DD), activity start hour, moving_time, sport_type
            │
            ├─ WebFetch → Open-Meteo archive API (start location, activity date)
            │    URL: https://archive-api.open-meteo.com/v1/archive
            │    Params: latitude, longitude, start_date, end_date (same day),
            │            hourly=temperature_2m,relative_humidity_2m,windspeed_10m,
            │                   winddirection_10m,precipitation,weathercode,
            │            timezone=auto
            │    → Extract the array index matching the activity's start hour
            │    → Store: temp_c, humidity_pct, wind_kph, wind_dir_deg, precip_mm, condition_code
            │
            ├─ moving_time > threshold? (cycling: 7200s / running: 5400s)
            │    ├─ NO → use start-point weather only
            │    └─ YES → check get_activity_intervals for a mid-session interval with lat/lon
            │              ├─ Found → WebFetch Open-Meteo for midpoint (same date, mid-session hour)
            │              │           → store midpoint weather alongside start-point
            │              └─ Not found → silently fall back to start-point only
            │
            └─ Weather context now available for analysis sections:
                 ├─ Aerobic decoupling commentary
                 ├─ EF comparison commentary
                 └─ VI commentary (cycling)
```

---

## Open-Meteo API Reference

**Endpoint:** `https://archive-api.open-meteo.com/v1/archive`

**Query parameters:**
```
latitude={lat}
longitude={lon}
start_date={YYYY-MM-DD}
end_date={YYYY-MM-DD}
hourly=temperature_2m,relative_humidity_2m,windspeed_10m,winddirection_10m,precipitation,weathercode
timezone=auto
```

**Response shape (relevant fields):**
```json
{
  "hourly": {
    "time": ["2026-03-10T06:00", "2026-03-10T07:00", ...],
    "temperature_2m": [14.2, 15.1, ...],
    "relative_humidity_2m": [72, 68, ...],
    "windspeed_10m": [18.3, 21.0, ...],
    "winddirection_10m": [225, 230, ...],
    "precipitation": [0.0, 0.0, ...],
    "weathercode": [1, 1, ...]
  }
}
```

Match the activity start hour to the `time` array to extract the relevant index.

**Weather codes (WMO standard):** 0=clear, 1–3=partly cloudy, 45–48=fog, 51–67=rain/drizzle, 71–77=snow, 80–82=showers, 95–99=thunderstorm.

---

## Error Handling

| Scenario | Behavior |
|---|---|
| `start_lat_lng` absent | Skip weather. Note "indoor or no GPS lock — weather unavailable" |
| Open-Meteo returns 404 or empty `hourly` | Skip weather. Note "weather data not yet available (archive can lag up to 7 days for recent activities)" |
| Open-Meteo returns data but activity hour not in range | Use nearest available hour, note limitation |
| `get_activity_intervals` has no lat/lon for midpoint | Fall back to start-point only — no error surfaced to athlete |
| Rain detected (precip > 0 or weathercode 51–82) | Actively surface in output as context for anomalous HR/power readings |

---

## Weather Thresholds (additions to METRICS_REFERENCE.md)

### Temperature
| Threshold | Effect | Coaching Action |
|---|---|---|
| >28°C | Cardiac drift elevated; decoupling inflated | Adjust decoupling flag threshold by +2–3%; note heat before flagging |
| 20–28°C | Moderate; normal thresholds apply | Standard interpretation |
| <5°C | HR suppression common; EF artificially high | Flag EF comparisons as less reliable; note cold |

### Humidity
| Threshold | Effect | Coaching Action |
|---|---|---|
| >70% + temp >22°C | Compounds heat stress significantly | Add to decoupling context even if temp alone is moderate |

### Wind
| Threshold | Effect | Coaching Action |
|---|---|---|
| Speed >25 km/h | Explains elevated power/IF on exposed routes | Note in VI and IF commentary |
| Direction: headwind on return leg | Typical for out-and-back rides — explains power asymmetry | Use to contextualize VI spike if mid-session weather available |

### Precipitation
| Scenario | Effect | Coaching Action |
|---|---|---|
| Any rain | Explains conservative pacing, lower HR, potential VI anomalies | Actively mention; don't flag these anomalies as fitness issues |

---

## Coaching Output Style

Weather is not a separate section. It's woven in as a 1–2 sentence contextualizer inside existing sections.

**Decoupling example (hot and humid):**
> "Conditions: 31°C, 78% humidity. Your 14% aerobic decoupling is above the 10% red-flag threshold, but heat and humidity alone typically add 3–5% — this is consistent with the conditions rather than a base fitness gap."

**EF example (cold):**
> "Note: 4°C at start — cold suppresses HR response, which can inflate EF readings. Compare this session to other cold-weather efforts rather than your full history."

**VI / power example (wind):**
> "Conditions: 34 km/h SW headwind. The IF of 0.92 and VI of 1.09 on what was planned as a Z2 ride are largely explained by wind resistance on the exposed return leg — not a pacing failure."

---

## What This Does NOT Do

- No real-time weather (forecast) — historical archive only
- No weather for batch analysis or fitness overviews
- No wind direction → route heading calculation (would require full GPS stream + vector math — out of scope)
- No weather for swimming (pool or open-water) in this iteration

---

## Implementation Touchpoints

1. **`DISCIPLINE_ANALYSIS.md`** — Insert weather context decision block into cycling and running tool-call sequences (after `get_activity_details`, before decoupling/EF steps)
2. **`METRICS_REFERENCE.md`** — Append `## Weather Context Thresholds` section
3. **`SKILL.md`** — Add `WebFetch` to MCP Tool Map; add weather-aware command pattern ("analyze my run in the heat", "how did the wind affect my ride")
