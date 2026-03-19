# API Field Verification Notes

Verified 2026-03-19 for skill refactor. Temporary file — delete after Task 13.

---

## Date range parameters (all tools)

All four MCP tools use `start_date` / `end_date` (not `oldest`/`newest` as the plan assumed).
Correct everywhere in COMMANDS.md.

---

## Task 1: get_wellness_data fields

Called for 2026-03-16 → 2026-03-19. Response is formatted text.

| Concept | Field label in response | Example value |
|---|---|---|
| HRV | `HRV` | `HRV: 84` |
| Resting HR | `Resting HR` | `Resting HR: 47 bpm` |
| Sleep score (device) | `Device Sleep Score` | `Device Sleep Score: 68/100` |
| Sleep hours | `Sleep` | `Sleep: 5.48 hours` |
| Sleep quality | `Sleep Quality` | `Sleep Quality: 3 (Average)` |
| CTL | `Fitness (CTL)` | `Fitness (CTL): 53.06` |
| ATL | `Fatigue (ATL)` | `Fatigue (ATL): 69.20` |

All fields present and populated for this athlete.

---

## Task 2: get_activities fields

Called for last 14 days, limit 20. Response is formatted text.

| Concept | Field label in response | Notes |
|---|---|---|
| Sport type | `Type` | Values: `Run`, `Ride` (expect `Swim`, `VirtualRide`) |
| Activity CTL | `Fitness (CTL)` | CTL at time of activity (Training Metrics section) |
| Activity ATL | `Fatigue (ATL)` | ATL at time of activity |
| TSB | **Not a direct field** | Compute as CTL − ATL |
| Training load (TSS equiv) | `Training Load` | TSS for this session |
| Activity ID | `ID` field | Format: `i132978250` (prefixed with 'i') |
| Wind speed | `Avg Wind Speed` | Shows N/A in get_activities — only from get_activity_weather |
| Headwind/tailwind | `Headwind %` / `Tailwind %` | Shows N/A in get_activities — only from get_activity_weather |

**Per-discipline CTL/ATL:** Use the values on the most recent activity filtered by Type.

---

## Task 3: get_activity_weather fields

Called for `i132978250` (Run) and `i132078993` (Ride). Response is **raw JSON**.

Both `prevailing_wind_cardinal` and `prevailing_wind_deg` are returned. Use `prevailing_wind_cardinal` in templates (human-readable string, e.g., "NE").

Full field list:
```json
{
  "description": "Partly cloudy",
  "average_temp": 29.4,
  "average_feels_like": 32.3,
  "average_wind_speed": 14.1,
  "prevailing_wind_deg": 39.7,
  "prevailing_wind_cardinal": "NE",
  "headwind_percent": 49.9,
  "tailwind_percent": 50.1,
  "avg_yaw": 90.1,
  "max_rain": 0,
  "max_snow": 0,
  "average_clouds": 61,
  "temp_bar": "  Temp        29.4°C  ██████████░░░░░░░░░░\n  Feels like  32.3°C  ████████████░░░░░░░░",
  "source": "open-meteo"
}
```

The wind direction inconsistency from the spec is resolved: both fields exist. Use `prevailing_wind_cardinal` for display.

---

## Task 4: get_events fields

Called for 2026-03-16 → 2026-03-22. Response is formatted text.

| Field | Notes |
|---|---|
| `Type` | **Always `Other`** — not sport-specific (Run/Ride/Swim). Cannot filter planned events by sport. |
| `Name` | Present ✓ (e.g., "16km Long Run", "Long Ride") |
| `moving_time` | **Absent** — not in response |
| `load_target` | **Absent** — not in response |

**Implications for /weekly command:**
- Planned sessions can be shown in the calendar by name only — no duration or sport type available
- TSS target overlay (outline bar) will never render — `load_target` is absent on all events
- The degradation path ("show completed bars only") is the only path in practice
- Sport icons for planned sessions cannot be inferred from event type

Simplify the /weekly template accordingly.
