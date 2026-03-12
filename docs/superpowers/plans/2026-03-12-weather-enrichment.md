# Weather Enrichment Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add historical weather context (temperature, humidity, wind, precipitation) to single-activity cycling and running analysis so the coach can contextualize aerobic decoupling, Efficiency Factor, and Variability Index against ambient conditions.

**Architecture:** After `get_activity_details` (already in every single-activity flow), check for GPS coordinates and fetch weather from the free Open-Meteo historical archive API via `WebFetch`. For long efforts (cycling >2h, running >1.5h), attempt a midpoint weather fetch using `get_activity_intervals` lat/lon. Weather is woven inline into existing decoupling, EF, and VI commentary — no new section or file.

**Tech Stack:** Markdown skill files only (no code). Open-Meteo archive API (free, no key). `WebFetch` built-in tool.

**Spec:** `docs/superpowers/specs/2026-03-12-weather-enrichment-design.md`

---

## Chunk 1: SKILL.md updates (tool map + command patterns)

### Task 1: Add WebFetch to the MCP Tool Map in SKILL.md

**Files:**
- Modify: `skills/triathlon-training/SKILL.md:108` (insert after the `get_activity_streams` row)

- [ ] **Step 1: Add WebFetch row to MCP Tool Map**

  In `skills/triathlon-training/SKILL.md`, find the MCP Tool Map table and insert this row after the `get_activity_streams` row (currently line 108):

  ```
  | Historical weather context | `WebFetch` (Open-Meteo archive API) | Single-activity analysis only — cycling and running; skip if no GPS or archive not yet available |
  ```

  The table should now look like:
  ```markdown
  | Use Case | Tool | Notes |
  |---|---|---|
  | HRV trend, resting HR, sleep | `get_wellness_data` | Fetch last 14–30 days |
  | Load history, CTL/ATL/TSB signals | `get_activities` | Fetch last 30–90 days, limit=50+ |
  | Single session breakdown | `get_activity_details` | Use activity ID from `get_activities` |
  | Interval hit/miss analysis | `get_activity_intervals` | For structured workouts only |
  | Power/HR time-series | `get_activity_streams` | ⚠️ High token cost — use only when aerobic decoupling or VI analysis requires second-by-second data |
  | Historical weather context | `WebFetch` (Open-Meteo archive API) | Single-activity analysis only — cycling and running; skip if no GPS or archive not yet available |
  | Create / update planned workout | `add_or_update_event` | ⚠️ Write operation — run WORKOUT_PLANNING.md pre-flight checks first |
  | Delete planned workout | `delete_event` | Permanent — confirm with athlete before calling |
  | Fetch a specific event | `get_event_by_id` | Use to clone an existing workout's structure |
  ```

- [ ] **Step 2: Update tool call order note for activity analysis**

  In `skills/triathlon-training/SKILL.md`, find this line (currently line 115):
  ```
  **Tool call order for activity analysis:** `get_activity_details` → `get_activity_intervals` (if structured) → `get_activity_streams` (only if decoupling analysis needed)
  ```

  Replace it with:
  ```
  **Tool call order for activity analysis:** `get_activity_details` → `WebFetch` (Open-Meteo weather, if GPS present) → `get_activity_intervals` (if structured or if activity >2h/1.5h for midpoint weather) → `get_activity_streams` (only if decoupling analysis needed)
  ```

- [ ] **Step 3: Add weather command pattern**

  In `skills/triathlon-training/SKILL.md`, find the Command Patterns table and append this row before the closing `---`:
  ```
  | "how did the heat affect my run", "did the wind affect my power", "analyze in context of conditions" | Weather-enriched activity breakdown | `get_activity_details` → `WebFetch` (Open-Meteo) |
  ```

- [ ] **Step 4: Verify SKILL.md changes**

  Re-read lines 100–135 of `skills/triathlon-training/SKILL.md`. Confirm:
  - WebFetch row appears in the tool map table
  - Tool call order line includes WebFetch
  - Weather command pattern row appears in the Command Patterns table

- [ ] **Step 5: Commit**

  ```bash
  git add skills/triathlon-training/SKILL.md
  git commit -m "feat(skill): add WebFetch weather enrichment to tool map and command patterns"
  ```

---

## Chunk 2: METRICS_REFERENCE.md weather thresholds

### Task 2: Add Weather Context Thresholds section to METRICS_REFERENCE.md

**Files:**
- Modify: `skills/triathlon-training/METRICS_REFERENCE.md` (append new section at end of file, before EOF)

- [ ] **Step 1: Append weather thresholds section**

  In `skills/triathlon-training/METRICS_REFERENCE.md`, append the following at the very end of the file (after the existing "Vanity Metrics" and "Race-Distance Discipline Priorities" sections):

  ````markdown

  ---

  ## Weather Context Thresholds

  Apply these when weather data is available from Open-Meteo. Conditions explain anomalies — don't flag readings as problems if conditions account for them.

  ### Temperature

  | Range | Effect | Coaching action |
  |---|---|---|
  | >28°C | Cardiac drift elevated; decoupling inflated | Adjust decoupling flag threshold by +2–3%; note heat *before* flagging |
  | 20–28°C | Moderate; normal thresholds apply | Standard interpretation |
  | <5°C | HR suppression common (cold vasoconstriction reduces HR response); EF may be artificially high | Flag EF comparisons as less reliable; prefer comparing to other cold-weather efforts |

  ### Humidity

  | Condition | Effect | Coaching action |
  |---|---|---|
  | >70% + temp >22°C | Wet-bulb effect compounds heat stress significantly | Add to decoupling context even when temperature alone is moderate |

  ### Wind

  | Condition | Effect | Coaching action |
  |---|---|---|
  | Speed >25 km/h | Meaningful aerodynamic resistance on exposed routes | Contextualize elevated power, IF, and VI — not a pacing problem |
  | Direction: headwind on return leg (out-and-back routes) | Explains power asymmetry between legs | Note when mid-activity weather available; helps athlete understand VI spike |

  Wind direction is reported in degrees (0° = N, 90° = E, 180° = S, 270° = W). Convert to cardinal (N/NE/E/SE/S/SW/W/NW) for athlete-facing output.

  ### Precipitation

  | Condition | Effect | Coaching action |
  |---|---|---|
  | Any rain (precip > 0 mm or weathercode 51–82) | Conservative pacing, lower HR, potential VI anomalies from road spray and braking | Actively mention in output; do not flag these anomalies as fitness issues |
  | Snow / ice (weathercode 71–77) | Dramatically affects pace and HR reliability | Flag explicitly; most metrics are non-comparable to non-winter efforts |

  ### WMO Weather Codes (reference)

  | Code range | Condition |
  |---|---|
  | 0 | Clear sky |
  | 1–3 | Mainly clear / partly cloudy / overcast |
  | 45–48 | Fog |
  | 51–67 | Drizzle / rain |
  | 71–77 | Snow |
  | 80–82 | Rain showers |
  | 95–99 | Thunderstorm |

  **Application rule:** Weather thresholds are contextualizers, not overrides. If heat explains 3% of a 14% decoupling reading, the remaining 11% still warrants investigation. Always apply standard thresholds first, then adjust with weather context.
  ````

- [ ] **Step 2: Verify METRICS_REFERENCE.md changes**

  Read the last 60 lines of `skills/triathlon-training/METRICS_REFERENCE.md`. Confirm:
  - `## Weather Context Thresholds` section is present
  - Temperature, humidity, wind, precipitation, and WMO code tables all appear
  - The application rule paragraph is at the end

- [ ] **Step 3: Commit**

  ```bash
  git add skills/triathlon-training/METRICS_REFERENCE.md
  git commit -m "feat(metrics): add weather context thresholds for decoupling, EF, VI interpretation"
  ```

---

## Chunk 3: DISCIPLINE_ANALYSIS.md — Cycling weather block

### Task 3: Insert weather context decision block into the Cycling Analysis sequence

**Files:**
- Modify: `skills/triathlon-training/DISCIPLINE_ANALYSIS.md:9-11` (insert after Tools to Call list, before Analysis Sequence heading)

Context: The cycling section currently opens with:
```markdown
### Tools to Call
1. `get_activity_details` — NP, IF, average power, average HR, duration, distance
2. `get_activity_intervals` — if structured workout (intervals present)
3. `get_activity_streams` — only if computing aerobic decoupling manually (high token cost; check if decoupling is already in details response first)
```

- [ ] **Step 1: Update cycling Tools to Call list**

  Replace the existing cycling "Tools to Call" list in `skills/triathlon-training/DISCIPLINE_ANALYSIS.md` with:

  ```markdown
  ### Tools to Call
  1. `get_activity_details` — NP, IF, average power, average HR, duration, distance, `start_lat_lng`, `start_date_local`, `moving_time`
  2. `WebFetch` (Open-Meteo archive API) — weather context; see Weather Context block below
  3. `get_activity_intervals` — if structured workout (intervals present) OR if `moving_time > 7200` for midpoint weather coords
  4. `get_activity_streams` — only if computing aerobic decoupling manually (high token cost; check if decoupling is already in details response first)
  ```

- [ ] **Step 2: Insert weather context decision block into cycling Analysis Sequence**

  In `skills/triathlon-training/DISCIPLINE_ANALYSIS.md`, find the cycling `### Analysis Sequence` heading and its first step (`**1. Assess session quality via NP + IF**`). Insert the following as a new `**0. Fetch weather context**` step immediately before step 1:

  ```markdown
  **0. Fetch weather context (cycling)**

  After `get_activity_details`:

  - Does `start_lat_lng` exist? (absent for indoor trainer rides)
    - **No** → Skip weather. Note "indoor session — weather unavailable" and proceed to step 1.
    - **Yes** → extract `lat`, `lon`, `start_date_local` (YYYY-MM-DD), start hour (from timestamp), `moving_time`

  Fetch: `WebFetch https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={date}&end_date={date}&hourly=temperature_2m,relative_humidity_2m,windspeed_10m,winddirection_10m,precipitation,weathercode&timezone=auto`

  - If response is empty or 404 → note "weather archive not yet available (can lag up to 7 days)" and proceed without weather.
  - If response OK → extract the array index matching the activity's start hour from `hourly.time`. Store: `temp_c`, `humidity_pct`, `wind_kph`, `wind_dir_deg`, `precip_mm`, `weathercode`.

  Long ride escalation (`moving_time > 7200`):
  - Check `get_activity_intervals` for a mid-session interval with lat/lon coordinates.
  - If found → fetch Open-Meteo for midpoint (same date, mid-session hour). Store as `midpoint_weather`.
  - If not found → proceed with start-point weather only (no error to athlete).

  Convert `wind_dir_deg` to cardinal direction (0°=N, 90°=E, 180°=S, 270°=W).

  **Use this weather context in steps 1–5 below**: note conditions before flagging decoupling or EF anomalies. See METRICS_REFERENCE.md `## Weather Context Thresholds` for adjustment rules.
  ```

- [ ] **Step 3: Add weather to "What to Highlight" for cycling**

  In the cycling `### What to Highlight in Output` section, append:
  ```markdown
  - If weather available: open with "Conditions: {temp}°C, {humidity}%, {wind} km/h {dir}{rain note}" before analysis — one line, not a section
  ```

- [ ] **Step 4: Verify cycling section**

  Read lines 1–50 of `skills/triathlon-training/DISCIPLINE_ANALYSIS.md`. Confirm:
  - Step 0 weather block appears before "1. Assess session quality via NP + IF"
  - Tools to Call list references WebFetch and updated notes for `get_activity_intervals`
  - What to Highlight includes weather opening line guidance

- [ ] **Step 5: Commit**

  ```bash
  git add skills/triathlon-training/DISCIPLINE_ANALYSIS.md
  git commit -m "feat(cycling): add weather context decision block to cycling analysis sequence"
  ```

---

## Chunk 4: DISCIPLINE_ANALYSIS.md — Running weather block

### Task 4: Insert weather context decision block into the Running Analysis sequence

**Files:**
- Modify: `skills/triathlon-training/DISCIPLINE_ANALYSIS.md:49-57` (running section Tools to Call + Analysis Sequence)

Context: The running section currently opens with:
```markdown
### Tools to Call
1. `get_activity_details` — pace, average HR, cadence, elevation, distance, duration
2. `get_activity_intervals` — if structured (track workout, tempo intervals)
3. `get_activity_streams` — for decoupling analysis if not in details response
```

- [ ] **Step 1: Update running Tools to Call list**

  Replace the existing running "Tools to Call" list in `skills/triathlon-training/DISCIPLINE_ANALYSIS.md` with:

  ```markdown
  ### Tools to Call
  1. `get_activity_details` — pace, average HR, cadence, elevation, distance, duration, `start_lat_lng`, `start_date_local`, `moving_time`
  2. `WebFetch` (Open-Meteo archive API) — weather context; see Weather Context block below
  3. `get_activity_intervals` — if structured (track workout, tempo intervals) OR if `moving_time > 5400` for midpoint weather coords
  4. `get_activity_streams` — for decoupling analysis if not in details response
  ```

- [ ] **Step 2: Insert weather context decision block into running Analysis Sequence**

  In the running `### Analysis Sequence`, insert the following as `**0. Fetch weather context (running)**` immediately before step 1 (`**1. Normalized Graded Pace (NGP) + Average HR → EF**`):

  ```markdown
  **0. Fetch weather context (running)**

  After `get_activity_details`:

  - Does `start_lat_lng` exist? (absent for treadmill runs)
    - **No** → Skip weather. Note "treadmill session — weather unavailable" and proceed to step 1.
    - **Yes** → extract `lat`, `lon`, `start_date_local` (YYYY-MM-DD), start hour (from timestamp), `moving_time`

  Fetch: `WebFetch https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={date}&end_date={date}&hourly=temperature_2m,relative_humidity_2m,windspeed_10m,winddirection_10m,precipitation,weathercode&timezone=auto`

  - If response is empty or 404 → note "weather archive not yet available (can lag up to 7 days)" and proceed without weather.
  - If response OK → extract the array index matching the activity's start hour from `hourly.time`. Store: `temp_c`, `humidity_pct`, `wind_kph`, `wind_dir_deg`, `precip_mm`, `weathercode`.

  Long run escalation (`moving_time > 5400`):
  - Check `get_activity_intervals` for a mid-session interval with lat/lon coordinates.
  - If found → fetch Open-Meteo for midpoint (same date, mid-session hour). Store as `midpoint_weather`.
  - If not found → proceed with start-point weather only (no error to athlete).

  Convert `wind_dir_deg` to cardinal direction (0°=N, 90°=E, 180°=S, 270°=W).

  **Running is more heat-sensitive than cycling.** Apply weather thresholds conservatively: >25°C warrants decoupling adjustment even without humidity. See METRICS_REFERENCE.md `## Weather Context Thresholds`.

  **Use this weather context in steps 1–5 below**: note conditions before flagging decoupling or EF anomalies.
  ```

- [ ] **Step 3: Add weather to "What to Highlight" for running**

  In the running `### What to Highlight in Output` section, append:
  ```markdown
  - If weather available: open with "Conditions: {temp}°C, {humidity}%, {wind} km/h {dir}{rain note}" — one line, before analysis begins
  ```

- [ ] **Step 4: Verify running section**

  Read lines 49–95 of `skills/triathlon-training/DISCIPLINE_ANALYSIS.md`. Confirm:
  - Step 0 weather block appears before "1. Normalized Graded Pace (NGP) + Average HR → EF"
  - Tools to Call list references WebFetch and the 5400s threshold for running
  - What to Highlight includes weather opening line guidance
  - Running-specific note about heat sensitivity is present

- [ ] **Step 5: Commit**

  ```bash
  git add skills/triathlon-training/DISCIPLINE_ANALYSIS.md
  git commit -m "feat(running): add weather context decision block to running analysis sequence"
  ```

---

## Final Verification

- [ ] **Read all three modified files in full** and confirm no formatting was broken (tables still render, headers still parse, no dangling markdown)

- [ ] **Check cross-references:** DISCIPLINE_ANALYSIS.md references `METRICS_REFERENCE.md ## Weather Context Thresholds` — confirm that section exists in METRICS_REFERENCE.md

- [ ] **Commit summary (optional):** If all four commits are clean, no additional commit needed. Otherwise:
  ```bash
  git log --oneline -5
  ```

---

## Implementation Notes

**No code, no tests.** These are instructional markdown files. "Tests" are read-file verifications after each edit.

**Edit tool guidance:** Use the `Edit` tool (not `Write`) for all file modifications to avoid overwriting unrelated content. Provide enough surrounding context in `old_string` to make each replacement unique within the file.

**Ordering matters for DISCIPLINE_ANALYSIS.md:** The cycling and running sections are in order in one file. Make cycling edits first (Task 3), then running (Task 4), to avoid offset confusion from the cycling edits changing line numbers.

**Do not modify swimming.** Pool sessions have no GPS and controlled conditions. If a future open-water swimming task comes up, it would follow the same pattern but requires its own spec.
