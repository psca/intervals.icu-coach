# Workout Planning — Triathlon Training Insights

Guidance for creating planned workouts on the intervals.icu calendar via `add_or_update_event`. Follow this before every MCP write call.

---

## Pre-Flight Checklist

Run before constructing any event payload:

- [ ] `start_date_local` provided in `YYYY-MM-DD` format?
- [ ] Sport type identified — `Ride`, `VirtualRide`, `Run`, `Swim`, `Walk`, etc.?
- [ ] Appropriate `target` metric selected for this discipline? (see table below)
- [ ] Duration (`moving_time`) or distance (`distance`) specified — at least one required for a meaningful planned workout?
- [ ] No server-computed fields included in the payload? (see Excluded Fields)

---

## Minimal Required Payload

Only these four fields are strictly required:

```json
{
  "start_date_local": "YYYY-MM-DD",
  "category": "WORKOUT",
  "type": "Run",
  "name": "Easy aerobic run"
}
```

Add fields from the discipline-specific tables below to make the workout actionable.

---

## Discipline-Specific Field Guidance

### Cycling

| Field | Value | Notes |
|---|---|---|
| `type` | `"Ride"` or `"VirtualRide"` | `VirtualRide` for indoor/trainer |
| `target` | `"POWER"` | Use `"HR"` if athlete has no power meter |
| `indoor` | `true` / `false` | Set explicitly for trainer sessions |
| `moving_time` | seconds | Primary duration field |
| `load_target` | int (TSS) | Optional planned training stress |
| `joules_above_ftp` | — | **Do not set** — computed from completed activity |

### Running

| Field | Value | Notes |
|---|---|---|
| `type` | `"Run"` | `"TrailRun"` for off-road |
| `target` | `"PACE"` | Use `"HR"` for HR-controlled easy runs |
| `moving_time` | seconds | Use for time-based sessions |
| `distance` | meters | Use for distance-based sessions (e.g., 10,000m tempo) |
| `distance_target` | meters | Mirrors `distance` for the planning target |

### Swimming

| Field | Value | Notes |
|---|---|---|
| `type` | `"Swim"` | |
| `target` | `"PACE"` | Pace per 100m is the primary swim metric |
| `distance` | meters | Primary field for swim planning — always set |
| `moving_time` | seconds | Set as secondary; swim volume is distance-first |
| `indoor` | `true` | Set for pool sessions |

---

## Full Writable Field Reference

These are the fields you may include. Do not include fields from the Excluded Fields section.

**Calendar / Identity**
- `start_date_local` — `YYYY-MM-DD` — **required**
- `end_date_local` — `YYYY-MM-DD` — only for multi-day events (rarely needed)
- `uid` — client-assigned string; enables upsert via `upsertOnUid=true` — useful for idempotent writes
- `external_id` — string; used with OAuth upsert — omit unless integrating external system
- `calendar_id` — int; omit to use athlete's default calendar

**Classification**
- `category` — `WORKOUT` for planned sessions; `RACE_A/B/C` for races; `NOTE` for text-only entries — **required**
- `type` — sport string: `Ride`, `VirtualRide`, `Run`, `TrailRun`, `Swim`, `Walk`, `Hike`, `Workout`, etc.
- `sub_type` — `NONE` (default), `WARMUP`, `COOLDOWN`, `RACE`
- `tags` — array of strings; use for training phase labels, focus areas, etc.
- `indoor` — boolean

**Content**
- `name` — workout name — **required**
- `description` — free-text description of the workout; see Workout Description Format below
- `color` — hex string for calendar colour coding

**Duration / Load**
- `moving_time` — planned duration in seconds
- `distance` — planned distance in meters
- `load_target` — planned training stress score (TSS equivalent)
- `time_target` — time goal in seconds (e.g., for a race or time trial)
- `distance_target` — distance goal in meters

**Targets**
- `target` — primary target metric: `AUTO`, `POWER`, `HR`, `PACE`
- `targets` — array of the same enum; use when a workout has multiple target modes (e.g., power + HR)

**Coach Controls**
- `hide_from_athlete` — boolean; use when preparing a surprise plan
- `athlete_cannot_edit` — boolean; lock structure if sharing a coached plan
- `structure_read_only` — boolean; allows text edits but locks workout steps
- `not_on_fitness_chart` — boolean; exclude from PMC (use for test events or notes)
- `show_as_note` — boolean
- `show_on_ctl_line` — boolean
- `for_week` — boolean; applies to the whole training week, not a specific day

**Availability Hints (AI scheduling)**
- `training_availability` — `NORMAL`, `LIMITED`, `UNAVAILABLE`
- `max_training_time` — max available seconds for this session
- `can_train_sports` — array of sport types the athlete can do on this day

**Nutrition**
- `carbs_per_hour` — planned carbohydrate intake (g/hr)

**File Import (alternative to description)**
- `file_contents` — raw workout file content (`.zwo`, `.mrc`, `.erg`, `.fit`)
- `file_contents_base64` — base64-encoded version of the above
- `filename` — filename including extension; required when using file import fields

---

## Excluded Fields (server-computed — never set on create/update)

Sending these is harmless but wasteful; the server ignores or overwrites them:

```
id, icu_training_load, icu_atl, icu_ctl, icu_ftp, w_prime, p_max,
atl_days, ctl_days, updated, joules, joules_above_ftp, ss_p_max,
ss_w_prime, ss_cp, push_errors, created_by_id, plan_applied,
entered, oauth_client_id, shared_event_id
```

---

## Workout Description Format

The `description` field accepts free text. intervals.icu also parses a structured step syntax from this field to populate `workout_doc` — use plain language if unsure of the exact syntax.

**Effective description patterns:**

```
// Time-based with HR zone
Warm-up 10 min easy (Z1)
Main set: 3x10 min at threshold HR (Z4), 3 min recovery jog between
Cool-down 10 min easy (Z1)

// Distance-based swim set
Warm-up: 400m easy (mix of strokes)
Main: 8x100m on 1:50 (target 1:30/100m)
Cool-down: 200m easy backstroke

// Power-based cycling
20 min warm-up, building to Z2
3x8 min at 95-105% FTP (sweet spot), 4 min recovery at 55% FTP
15 min cool-down
```

**Note on `workout_doc`:** This is an opaque JSON object populated by intervals.icu's workout builder. If you have a `workout_doc` from a prior event or plan template (e.g., fetched via `get_event_by_id`), you may pass it through unmodified. Do not construct `workout_doc` JSON by hand — use `description` text instead and let the server parse it.

---

## MCP Call Pattern

**Create a new planned workout:**
```
add_or_update_event(athlete_id, event_payload)
```

**Upsert (create or update by uid):**
Pass `uid` in the payload and use `upsertOnUid=true` if the MCP tool exposes that parameter. This allows idempotent re-scheduling without duplicate entries.

**Fetch an existing event to copy structure:**
```
get_event_by_id(athlete_id, event_id)
```
Use this to clone a prior workout's `workout_doc` into a new planned event.

---

## Cross-Discipline Constraints

Consistent with the no-aggregation rule in SKILL.md:

- **Create one event per discipline** — do not create a single event for a brick workout; create a `Ride` event and a `Run` event on the same day
- **Swim distance in meters, not yards** — intervals.icu defaults to meters; confirm athlete's unit setting if uncertain
- **Never set `load_target` across disciplines** — load scales differently per sport; a bike TSS of 80 ≠ a run TSS of 80
