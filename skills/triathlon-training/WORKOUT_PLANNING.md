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

## Workout Description Syntax

The `description` field supports structured text that intervals.icu parses into workout steps. This is the recommended approach — use `description` text, not raw `workout_doc` JSON.

### Step Format

Each step starts with `- ` (dash + space):
```
- [optional text cue] [duration OR distance] [target] [optional cadence]
```

### Duration
`30s`, `10m`, `1h`, `1h30m`, `5'30"` (short form)

### Distance
`500mtr`, `2km`, `1mi`, `100y` — space between number and unit is allowed

⚠️ **`m` = minutes, `mtr` = metres.** `10m` is 10 minutes. `10mtr` is 10 metres. Never use `m` for distance.

### Power Targets
- FTP-relative: `75%`, `88-93%` (range)
- Absolute: `220w`, `200-240w`
- Zones: `Z2`, `Z3-Z4`
- MMP-relative: `60% MMP 5m`

### Heart Rate Targets
- Max HR: `70% HR`, `75-80% HR`
- LTHR: `95% LTHR`, `90-95% LTHR`
- Zones: `Z2 HR`, `Z2-Z3 HR`

### Pace Targets
- Threshold-relative: `60% Pace`, `78-82% Pace`
- Zones: `Z2 Pace`, `Z2-Z3 Pace`
- Absolute: `5:00/km Pace`, `3:00/100m Pace`
- Units: `/100m`, `/100y`, `/km`, `/mi`, `/500m`, `/400m`

### Cadence
Append after target: `- 10m 75% 90rpm` or `- 12m 85% 90-100rpm`

### Ramps
`- 10m ramp 50%-75%` — gradual change over step duration

### Freeride
`- 20m freeride` — no target (ERG mode off)

### Repeats
Header before step block — blank lines required before and after:
```
Main Set 5x
- 2m 95%
- 2m 55%
```
Nested repeats are NOT supported.

### Section Headers
Lines without `- ` prefix become section headers:
```
Warmup
- 10m ramp 40-65%

Main Set 4x
- 8m 88-93%
- 4m 55%

Cooldown
- 10m ramp 65-40%
```

### Single Target Type Per Workout

**Use one target metric throughout a workout — all LTHR, all pace, or all power.** Mixing target types (e.g. some steps pace, some LTHR) is supported by intervals.icu but requires the athlete to manually toggle the zone chart display between metrics. Sticking to one type produces accurate zone times, correct training load, and a clean chart without any manual intervention.

- Running workouts: prefer `% LTHR` for load accuracy; use absolute pace when the athlete explicitly needs pacing targets
- If pacing context is needed alongside HR targets, add it as a text cue on the step: `- Race effort 3m 92% LTHR`

**Source:** [R2Tom's Quick Guide](https://forum.intervals.icu/t/workout-builder-syntax-quick-guide/123701), [Workout Builder thread](https://forum.intervals.icu/t/workout-builder/1163)

**CRITICAL — `description` must be plain text, never JSON.** The `description` field is rendered directly on the calendar. If you put JSON in it, the athlete sees raw `{"steps":[...]}` garbage. Always use the text-based workout syntax above. Do not construct `workout_doc` JSON by hand — use `description` text and let the server parse it into structured steps. If cloning from an existing event, pass `workout_doc` through unmodified.

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

## Batch Write Guidance (Training Blocks)

When writing a multi-week training block to the calendar:

**Idempotent writes:**
- All events must include a deterministic `uid` (e.g., `block-{race-date}-w{week}-{day}-{discipline}`)
- Use `upsertOnUid=true` on all calls — retries do not create duplicates

**Batch strategy:**
- Write in phase-sized batches (base → build → peak/taper)
- Provide progress feedback after each phase: "Base phase written (weeks 1-5). Writing build phase..."
- On partial failure: surface which events succeeded and which failed, offer retry

**Calendar conflicts:**
- Before writing, call `get_events` for the target date range
- If conflicts found, offer: **work around** (slot around existing), **merge** (write alongside), or **clear and replace** (`delete_events_by_date_range` — requires second confirmation)

**Race day event:**
- If the race date does not already have a `RACE_A` event, create one with `category: "RACE_A"`, the race name, and distance

---

## Cross-Discipline Constraints

Consistent with the no-aggregation rule in SKILL.md:

- **Create one event per discipline** — do not create a single event for a brick workout; create a `Ride` event and a `Run` event on the same day
- **Swim distance in meters, not yards** — intervals.icu defaults to meters; confirm athlete's unit setting if uncertain
- **Never set `load_target` across disciplines** — load scales differently per sport; a bike TSS of 80 ≠ a run TSS of 80
