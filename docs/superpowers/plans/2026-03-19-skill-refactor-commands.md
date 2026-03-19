# Skill Refactor: Command-Driven Templates with Visual Artifacts

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the triathlon coaching skill from 5 loosely-coupled reference files into a command-driven system with rigid output templates and HTML artifact support.

**Architecture:** Replace `COACH_PERSONA.md` and `DISCIPLINE_ANALYSIS.md` with a new `COMMANDS.md` that owns every command end-to-end (trigger phrases, MCP tool sequence, output template). `SKILL.md` becomes a pure router. Three implementation gates (API field verification) must be completed before writing the templates that depend on them.

**Tech Stack:** Markdown skill files only — no code. Validation is done by invoking the skill manually and checking output shape.

**Spec:** `docs/superpowers/specs/2026-03-19-skill-refactor-commands-design.md`

---

## Chunk 1: API Field Verification

Three implementation gates from the spec must be resolved before writing the templates. Do these first — their answers directly affect field names used in `COMMANDS.md`.

### Task 1: Verify `get_wellness_data` field names

**Files:**
- Read: MCP tool output (live call)

- [ ] **Step 1: Call `get_wellness_data` for the last 3 days**

  Using the intervals.icu MCP tool:
  ```
  get_wellness_data(athlete_id, oldest="<3 days ago>", newest="<today>")
  ```

- [ ] **Step 2: Record the actual field names for HRV, resting HR, and sleep**

  Look for fields matching these concepts and note exact names:
  - HRV (could be `hrv`, `hrvScore`, `icu_hrv_score`, etc.)
  - Resting HR (could be `restingHR`, `resting_hr`, `icu_resting_hr`, etc.)
  - Sleep score (could be `sleepScore`, `sleep_score`, `icu_sleep_score`, etc.)
  - Note which fields are absent or null for this athlete

- [ ] **Step 3: Record the date range parameter names**

  Note the exact parameter names for filtering by date range.

- [ ] **Step 4: Write findings to a scratch note**

  Create `docs/superpowers/plans/api-field-notes.md` with confirmed field names. This file is temporary — delete it after Task 3.

---

### Task 2: Verify `get_activities` per-discipline CTL/ATL/TSB fields

**Files:**
- Read: MCP tool output (live call)

- [ ] **Step 1: Call `get_activities` for the last 14 days**

  ```
  get_activities(athlete_id, oldest="<14 days ago>", newest="<today>")
  ```

- [ ] **Step 2: Record CTL/ATL/TSB field names on activity objects**

  Look for: `icu_ctl`, `icu_atl`, `icu_tsb` (or equivalent). Confirm they are present per activity.

- [ ] **Step 3: Record the sport type field name**

  Find the field that distinguishes Ride/Run/Swim — likely `type`, `sport_type`, or `icu_activity_type`. Note the exact string values used (e.g., `"Ride"`, `"Run"`, `"Swim"`).

- [ ] **Step 4: Add findings to `docs/superpowers/plans/api-field-notes.md`**

---

### Task 3: Verify `get_activity_weather` field names

**Files:**
- Read: MCP tool output (live call)

- [ ] **Step 1: Find a recent outdoor Run or Ride activity ID**

  From the activities list in Task 2.

- [ ] **Step 2: Call `get_activity_weather` for that activity**

  ```
  get_activity_weather(athlete_id, activity_id)
  ```

- [ ] **Step 3: Resolve the `prevailing_wind_cardinal` vs `prevailing_wind_deg` inconsistency**

  The existing codebase is inconsistent — `DISCIPLINE_ANALYSIS.md` uses `prevailing_wind_cardinal` (a cardinal string like "NW") while `METRICS_REFERENCE.md` references `prevailing_wind_deg` (a degree integer). Check the actual response and record which field name the MCP tool returns.

- [ ] **Step 4: Record all weather field names**

  Confirm: `average_feels_like`, `average_wind_speed`, `headwind_percent`, `tailwind_percent`, `temp_bar`, `max_rain`, `max_snow`, `description`, and the wind direction field.

- [ ] **Step 5: Add findings to `docs/superpowers/plans/api-field-notes.md`**

- [ ] **Step 6: Commit the api-field-notes file**

  ```bash
  git add docs/superpowers/plans/api-field-notes.md
  git commit -m "docs: record verified MCP API field names for skill refactor"
  ```

---

### Task 4: Verify `get_events` field names (gate for `/weekly`)

**Files:**
- Read: MCP tool output (live call)

- [ ] **Step 1: Call `get_events` for the current week**

  ```
  get_events(athlete_id, oldest="<Monday of this week>", newest="<today>")
  ```

- [ ] **Step 2: Confirm date range parameter names**

  Note the exact parameter names for `oldest`/`newest` or equivalent date filter.

- [ ] **Step 3: Confirm planned event fields**

  Verify these fields are present on planned event objects:
  - `type` (sport type — should match activity sport type values from Task 2)
  - `name` (workout name)
  - `moving_time` (planned duration in seconds)
  - `load_target` (planned TSS — note if this is absent or null for typical planned workouts)

- [ ] **Step 4: Add findings to `docs/superpowers/plans/api-field-notes.md`**

  Note especially whether `load_target` is reliably populated — this determines whether the TSS overlay in `/weekly` is useful in practice.

---

## Chunk 2: Rewrite SKILL.md as Router

### Task 5: Rewrite `SKILL.md`

The current `SKILL.md` is a 194-line file doing too many jobs. Replace it entirely with a focused router.

**Files:**
- Modify: `skills/triathlon-training/SKILL.md`

**What the new SKILL.md must contain (and only this):**
1. Frontmatter (name, description)
2. One-line identity statement ("You are a triathlon training analyst...")
3. Instruction to read COMMANDS.md for every request
4. MCP tool map table (carried from current SKILL.md lines 89–106, unchanged)
5. Data quality gates (carried from current SKILL.md lines 185–194, unchanged)
6. Command routing table — maps slash commands and trigger phrases to sections in COMMANDS.md
7. Ambiguous routing fallback rules

**What it must NOT contain:**
- Setup/installation instructions (move to README.md)
- Output templates
- Analysis sequences
- Persona guidance

- [ ] **Step 1: Read the current SKILL.md in full**

  Identify which sections to carry forward vs drop vs move to README.

- [ ] **Step 2: Write the new SKILL.md**

  Structure:
  ```markdown
  ---
  name: triathlon-training-insights
  description: [existing description]
  ---

  # Triathlon Training Insights

  You are a triathlon training analyst with access to an athlete's intervals.icu data via MCP.
  For every request: read COMMANDS.md to identify the command, follow its tool sequence and output template exactly.

  ## MCP Tool Map
  [carry from current SKILL.md — unchanged]

  ## Data Quality Gates
  [carry from current SKILL.md — unchanged]

  ## Command Routing

  | Slash command | Natural language triggers | Template section |
  |---|---|---|
  | /help | "what can you do", "commands", "help" | COMMANDS.md § /help |
  | /wellness | "how's my wellness", "how am I recovering", "HRV", "recovery check" | COMMANDS.md § /wellness |
  | /status | "how's my fitness", "training load", "how am I doing", "CTL", "PMC" | COMMANDS.md § /status |
  | /last [sport?] | "how was my last run/ride/swim", "analyze my last [sport]", "last activity" | COMMANDS.md § /last |
  | /weekly | "weekly summary", "how was my week", "this week", "week recap" | COMMANDS.md § /weekly |
  | /readiness [distance] | "am I ready for [race]", "race readiness", "ready for [distance]" | COMMANDS.md § /readiness |
  | /plan [date] [sport] [desc] | "schedule a workout", "add a session", "plan [sport] for [date]" | COMMANDS.md § /plan |

  ## Ambiguous Routing
  - "how am I doing" → /status
  - Unclear intent → ask: "Are you asking about fitness load (/status), recovery (/wellness), or this week's activities (/weekly)?"
  ```

- [ ] **Step 3: Verify the new SKILL.md**

  Check: does it contain any output templates, analysis instructions, or persona guidance? If yes, remove them — that content belongs in COMMANDS.md.

- [ ] **Step 4: Commit**

  ```bash
  git add skills/triathlon-training/SKILL.md
  git commit -m "refactor(skill): rewrite SKILL.md as pure command router"
  ```

---

## Chunk 3: Create COMMANDS.md — Foundation + `/help` + `/wellness` + `/status`

### Task 6: Write COMMANDS.md foundation and `/help`

**Files:**
- Create: `skills/triathlon-training/COMMANDS.md`

- [ ] **Step 1: Create `COMMANDS.md` with the file header and Tone & Guardrails section**

  ```markdown
  # Commands — Triathlon Training Insights

  Each command section defines: trigger phrases, MCP tool sequence, output template, and degradation rules.
  Follow the template exactly — same command = same output shape, every time.

  ---

  ## Tone and Guardrails

  These rules apply to every command:

  - **Observe before concluding** — lead with what the data shows, not the interpretation
  - **Translate every number** — never output a raw metric without a plain-language meaning
  - **Trend vs noise** — need ≥3 sessions to call a trend; single session is noise
  - **Never prescribe** — do not suggest specific workouts or training plans
  - **Celebrate real gains** — acknowledge improvements with specific metric evidence
  - **Name discipline gaps** — never infer aggregate fitness; state what each sport shows

  **Liability guardrail** — append to every response except /help and /plan:
  > *This is informational analysis based on your intervals.icu data. Always work with a qualified coach or healthcare provider before making significant training changes, especially if you're experiencing pain, illness, or unusual fatigue.*

  ---
  ```

- [ ] **Step 2: Add the `/help` command section**

  ```markdown
  ## /help

  **Triggers:** "what can you do", "commands", "help"
  **Tools:** none
  **Guardrail:** none

  Output a markdown table:

  | Command | What it does |
  |---|---|
  | /help | List available commands |
  | /wellness | HRV, resting HR, and sleep trend — recovery verdict |
  | /status | Per-discipline CTL/ATL/TSB fitness snapshot |
  | /last [sport?] | Stat card + analysis for your most recent activity |
  | /weekly | This week's training + planned sessions + wellness |
  | /readiness [sprint\|olympic\|703\|ironman] | Race readiness check against CTL and TSB targets |
  | /plan [date] [sport] [description] | Schedule a planned workout on your calendar |

  ---
  ```

- [ ] **Step 3: Commit**

  ```bash
  git add skills/triathlon-training/COMMANDS.md
  git commit -m "feat(skill): add COMMANDS.md with tone rules and /help"
  ```

---

### Task 7: Write `/wellness` command

**Files:**
- Modify: `skills/triathlon-training/COMMANDS.md`

Use the verified field names from Task 1 (`api-field-notes.md`).

- [ ] **Step 1: Append `/wellness` to COMMANDS.md**

  ```markdown
  ## /wellness

  **Triggers:** "how's my wellness", "how am I recovering", "HRV", "recovery check", "how's my recovery"
  **Tools:** `get_wellness_data` (14 days)
  **Guardrail:** yes

  ### Tool sequence
  1. Call `get_wellness_data` for the last 14 days

  ### Output
  Render an HTML artifact, then a 2-sentence markdown summary below it, then the liability guardrail.

  **HTML artifact — wellness card:**
  - HRV sparkline (7 days): plot daily HRV values with a horizontal baseline marker (7-day average). Field: `[CONFIRMED FIELD NAME FROM TASK 1]`
  - Resting HR line (7 days): plot below the HRV sparkline. Field: `[CONFIRMED FIELD NAME FROM TASK 1]`
  - Sleep score row (7 days): one dot per day. Field: `[CONFIRMED FIELD NAME FROM TASK 1]`. Omit this row silently if the field is absent or null for all days.
  - Verdict chip: `● RECOVERING WELL` (green) / `● MONITOR` (amber) / `● REST NEEDED` (red)
    - RECOVERING WELL: HRV at or above 7-day average for ≥4 of last 7 days, resting HR stable
    - MONITOR: HRV below average for 3–4 consecutive days, or resting HR elevated 3–5 bpm
    - REST NEEDED: HRV below average ≥5 consecutive days, or resting HR elevated >7 bpm vs baseline

  **Markdown summary (below artifact):**
  2 sentences: one stating the key signal (e.g., "HRV has been trending down for 4 days"), one interpreting it (e.g., "This suggests accumulated fatigue — a lighter day would support recovery").

  ### Degradation
  - HRV data absent: use resting HR as primary signal. Note the gap: "HRV data isn't available — using resting HR as the recovery indicator."
  - Both HRV and resting HR absent: do not render the artifact. Tell the user: "I don't see HRV or resting HR data in your wellness log for the last 14 days. Enable HRV tracking in intervals.icu Settings → Wellness to unlock this view."

  ---
  ```

- [ ] **Step 2: Replace `[CONFIRMED FIELD NAME FROM TASK 1]` placeholders with actual field names from `api-field-notes.md`**

- [ ] **Step 3: Commit**

  ```bash
  git add skills/triathlon-training/COMMANDS.md
  git commit -m "feat(skill): add /wellness command with HTML artifact template"
  ```

---

### Task 8: Write `/status` command

**Files:**
- Modify: `skills/triathlon-training/COMMANDS.md`

Use verified field names from Task 2.

- [ ] **Step 1: Append `/status` to COMMANDS.md**

  ```markdown
  ## /status

  **Triggers:** "how's my fitness", "training load", "fitness status", "how am I doing", "CTL", "PMC"
  **Tools:** `get_activities` (90 days, limit 100) → `get_wellness_data` (7 days)
  **Guardrail:** yes

  ### Tool sequence
  1. Call `get_activities` for the last 90 days, limit 100
  2. Call `get_wellness_data` for the last 7 days

  ### Computing per-discipline CTL/ATL/TSB
  `get_activities` returns a flat list. Each activity has `[SPORT TYPE FIELD]` and `[CTL FIELD]`, `[ATL FIELD]`, `[TSB FIELD]` fields.
  - Filter by sport type to get discipline-specific lists:
    - Bike: type = `Ride` or `VirtualRide`
    - Run: type = `Run` or `TrailRun`
    - Swim: type = `Swim`
  - Current CTL/ATL/TSB for a discipline = the values on the most recent activity in that filtered list
  - Ramp rate = current CTL minus CTL on the nearest activity ≥7 days ago in the same discipline list. Show "—" if no activity exists ≥7 days ago.

  ### Output
  Render an HTML artifact, then a 2-sentence markdown cross-discipline note, then the liability guardrail.

  **HTML artifact — status card:**
  Three columns, one per discipline. Only render a column if the discipline has ≥3 activities in the last 30 days. Show "Not enough data" placeholder for absent disciplines.

  Per column:
  - Header: sport icon + discipline name
  - CTL bar: horizontal progress bar showing current CTL value; label with value and a trend arrow (↑ if CTL increased vs 6 weeks ago, → if stable ±2pts, ↓ if declining)
  - ATL vs CTL indicator: show "ATL > CTL" warning chip if ATL exceeds CTL (overreaching signal)
  - TSB chip: colour-coded by value — green (+5 to +25), amber (-20 to +5), red (< -20)
  - Ramp rate: value in pts/week; flag in amber if >6, red if >8; show "—" if insufficient history

  **Cross-discipline note (below artifact):**
  2 sentences. Examples:
  - Flag imbalance: "Bike CTL is strong at 72, but run CTL is 38 — for a 70.3 that's a gap worth watching."
  - Flag systemic fatigue if ≥2 disciplines show TSB < -20 simultaneously
  - Otherwise: summarise the overall load picture

  ### Degradation
  - Discipline has <3 activities in last 30 days: render column with "Not enough data" — do not compute or display any metrics for that column
  - CTL/ATL/TSB fields absent from activity objects: surface the gap — "CTL data isn't available in the activity response. Check that your intervals.icu account has training load tracking enabled."

  ---
  ```

- [ ] **Step 2: Replace field name placeholders with actuals from `api-field-notes.md`**

- [ ] **Step 3: Migrate cross-discipline patterns from `DISCIPLINE_ANALYSIS.md`**

  Read the `## Cross-Discipline Patterns` section of `DISCIPLINE_ANALYSIS.md` (covers: cumulative fatigue signal across disciplines, discipline imbalance for race distance, off-bike run quality, recovery asymmetry). Incorporate this logic explicitly into the cross-discipline note instructions in the `/status` template — the 2-sentence note should be driven by these patterns.

- [ ] **Step 4: Commit**

  ```bash
  git add skills/triathlon-training/COMMANDS.md
  git commit -m "feat(skill): add /status command with per-discipline PMC artifact"
  ```

---

## Chunk 4: Create COMMANDS.md — `/last`

### Task 9: Write `/last` command

This is the most complex command — it absorbs all content from `DISCIPLINE_ANALYSIS.md` and the old single-activity output format from `SKILL.md`.

**Files:**
- Modify: `skills/triathlon-training/COMMANDS.md`
- Read: `skills/triathlon-training/DISCIPLINE_ANALYSIS.md` (source material)

Use verified weather field names from Task 3.

- [ ] **Step 1: Read `DISCIPLINE_ANALYSIS.md` in full**

  Note: cycling analysis (lines 9–66), running analysis (lines 69–129), swimming analysis (lines 132–178), cross-discipline patterns (lines 182–202). All of this moves into the `/last` sport-specific rules below.

- [ ] **Step 2: Append `/last` to COMMANDS.md**

  ```markdown
  ## /last [sport?]

  **Triggers:** "how was my last run/ride/swim", "analyze my last [sport]", "feedback on yesterday's [sport]", "last activity"
  **Sport arg:** optional. If omitted, use the most recent activity of any type. If provided (run/ride/swim), filter to that sport.
  **Guardrail:** yes

  ### Tool sequence
  1. `get_activities` — limit 10, filtered by sport type if arg provided
  2. `get_activity_details` — for the most recent activity from step 1
  3. `get_activity_weather` — **ONLY for outdoor Run or Ride**. Skip for: Swim, VirtualRide, indoor Run (detect via `indoor: true` field or activity type). Call this BEFORE constructing any output.
  4. `get_activity_intervals` — only if the activity is structured (intervals are present in the details response)
  5. `get_activity_streams` — only if aerobic decoupling % is not already in the details response; high token cost, use as last resort

  ### Output — Part 1: HTML artifact (stat card)

  **Weather strip (outdoor Run/Ride only):**
  Lead with: "{description} — {average_feels_like}°C feels-like, {average_wind_speed} km/h {[CONFIRMED WIND DIRECTION FIELD]}"
  - Cycling only: append "({headwind_percent}% headwind / {tailwind_percent}% tailwind)"
  - Running: omit headwind/tailwind — wind drag at running pace is negligible
  - Include `temp_bar` if feels-like > 25°C or < 5°C
  - If tool returns "Weather unavailable": skip strip silently

  **Key metrics grid:**
  Show available fields only — omit rows where data is null/absent:
  | Metric | Notes |
  |---|---|
  | Date | |
  | Type | Sport + session type (e.g. "Z2 long ride") |
  | Duration | |
  | Avg Power / Avg Pace | Power for cycling, NGP for running, pace/100m for swimming |
  | IF | Cycling only |
  | Avg HR | |
  | Decoupling % | Long aerobic efforts only (≥90 min bike, ≥60 min run) |
  | EF | NP/Avg HR (cycling) or NGP/Avg HR (running) |
  | VI | Cycling only (NP / Avg Power) |
  | SWOLF | Swimming only |

  **Signals row:**
  One badge per signal. Tag each: 🟢 Good / 🟡 Watch / 🔴 Flag. Use thresholds from METRICS_REFERENCE.md.
  Always apply weather context before flagging — heat explains decoupling; headwind explains elevated power and IF.

  **Comparison bar:**
  Show this session vs last 3 comparable efforts. Comparable = same sport, duration within ±25%, session type inferred from IF or pace zone.
  - If FTP changed between sessions: add footnote "† FTP changed from [X] to [Y] on [date] — IF values before and after are not directly comparable"
  - If <3 comparable sessions exist: write "Not enough comparable sessions to compare — this is the baseline"

  ### Output — Part 2: Markdown narrative

  **What happened (2–4 sentences):**
  Observation only — describe what the data shows. No recommendations. Examples:
  - "This was a Z2 long ride at IF 0.79, which aligns with the intended aerobic session."
  - "Decoupling of 8.2% is above the 5% threshold for a 2-hour effort — worth watching across the next few long rides."

  **One question:**
  A single clarifying question inviting athlete context. Examples: sleep quality, life stress, race schedule, perceived effort, recent illness. Never ask more than one question.

  ### Sport-specific analysis rules

  **Cycling:**
  - Assess IF vs intended session type — a "Z2 long ride" with IF > 0.85 is a pacing issue or mislabelled session
  - VI (NP / Avg Power): target 1.00–1.05 on flat/rolling; always contextualize with course profile before flagging; mountain stage VI 1.12 is fine, flat TT VI 1.12 is a problem
  - Aerobic decoupling: only flag for efforts ≥90 min at Z1–Z2; adjust threshold +2–3% if average_feels_like > 28°C
  - EF trend: compare to 3 most recent similar efforts (same type, similar duration); rising = aerobic gain; declining ≥3 sessions = flag
  - Power zone distribution: in base phase, flag if >30% of TSS from Z3+

  **Running:**
  - EF = NGP / Avg HR (NGP accounts for elevation — use it for fair cross-course comparison)
  - Aerobic decoupling: only flag for efforts ≥60 min at Z2; running is more heat-sensitive than cycling — apply heat adjustment at average_feels_like > 25°C (lower threshold than cycling)
  - Cadence: compare first 20% of session vs last 20% — drop >5 spm = fatigue signal
  - EF trend: compare to 3 most recent efforts of similar distance and course type (flat road vs flat road, trail vs trail)
  - Do NOT report headwind/tailwind for running

  **Swimming:**
  - No weather fetch — skip get_activity_weather entirely
  - SWOLF (stroke count + time per length): target 35–45 (25m pool), low 70s (50m pool); improving SWOLF at same pace = technique + fitness gain; SWOLF improving while pace slows = fatigue signal, not progress
  - Pace per 100m: track relative to effort level, not absolute
  - Interval consistency: use get_activity_intervals — flag drop-off in later intervals vs earlier
  - Stroke rate: compare early vs late session; inconsistency = fatigue indicator
  - HR data less reliable (chest strap issues underwater) — note uncertainty if HR is the basis for any flag
  - GPS unreliable in pool — rely on laps/intervals data, not GPS distance

  ---
  ```

- [ ] **Step 3: Migrate COACH_PERSONA.md edge cases into command templates**

  Read the `## Handling Edge Cases` section of `COACH_PERSONA.md`. Inline each case into the most relevant command:
  - "Athlete asks for a training plan" → add to `/last` narrative section (scope guardrail)
  - "Athlete pushes back on an assessment" → add to Tone and Guardrails in COMMANDS.md
  - "Athlete has no HRV data" → already in `/wellness` degradation; verify it matches
  - "Athlete is clearly overtrained but data is ambiguous" → add to `/status` cross-discipline note guidance

- [ ] **Step 4: Replace wind direction field placeholder with confirmed name from `api-field-notes.md`**

- [ ] **Step 5: Commit**

  ```bash
  git add skills/triathlon-training/COMMANDS.md
  git commit -m "feat(skill): add /last command with sport-specific analysis rules"
  ```

---

## Chunk 5: Create COMMANDS.md — `/weekly`, `/readiness`, `/plan`

### Task 10: Write `/weekly` command

**Files:**
- Modify: `skills/triathlon-training/COMMANDS.md`

- [ ] **Step 1: Append `/weekly` to COMMANDS.md**

  ```markdown
  ## /weekly

  **Triggers:** "weekly summary", "how was my week", "this week", "week recap"
  **Tools:** `get_activities` (14 days) → `get_wellness_data` (7 days) → `get_events` (current week)
  **Week boundaries:** Mon–Sun; current week = Monday of the current week through today
  **Guardrail:** yes

  ### Tool sequence
  1. `get_activities` for the last 14 days (provides this week + last week for context)
  2. `get_wellness_data` for the last 7 days
  3. `get_events` for the current week (Mon–today) to get planned sessions

  ### Output
  Render an HTML artifact, then a 2–3 sentence markdown summary, then the liability guardrail.

  **HTML artifact — weekly view:**

  *Wellness strip (Mon–Sun across top):*
  One column per day. Each cell: HRV dot + resting HR dot. Empty dot (grey outline) for days with no wellness data — do not interpolate missing days. If wellness data is entirely absent for all 7 days: omit this row and note the gap in the markdown summary.

  *7-day calendar row (Mon–Sun):*
  Each day cell shows:
  - Completed activities: card with sport icon, duration, and key metric (avg power for cycling, avg pace for running, distance for swimming)
  - Planned sessions (from get_events): same card style but dashed border and lighter colour
  - Empty days: blank cell

  *TSS bar chart by discipline (bottom):*
  One bar cluster per discipline (swim / bike / run):
  - Solid bar: completed TSS (sum of icu_training_load from get_activities for this discipline this week)
  - Outline bar: planned target TSS — only show if load_target is present on the planned event. If load_target is absent on all planned events: show completed bars only (no outline bars)

  **Markdown summary (2–3 sentences, below artifact):**
  - What got done this week (total sessions, disciplines covered)
  - What's planned but not yet done
  - Any load flag (e.g., TSB < -20 across disciplines, or ramp rate >6 pts/week)

  ### Degradation
  - No planned sessions from get_events: omit planned overlays in the calendar row. Note in summary: "No planned sessions found for this week."
  - Wellness data absent for some days: show empty dots for those days — do not interpolate
  - Wellness data entirely absent: omit the wellness strip row. Note gap in summary.
  - load_target absent on planned events: show planned sessions in calendar row but omit target outline from TSS bars — show completed bars only

  ---
  ```

- [ ] **Step 2: Commit**

  ```bash
  git add skills/triathlon-training/COMMANDS.md
  git commit -m "feat(skill): add /weekly command with calendar + wellness artifact"
  ```

---

### Task 11: Write `/readiness` and `/plan` commands

**Files:**
- Modify: `skills/triathlon-training/COMMANDS.md`

- [ ] **Step 1: Append `/readiness` to COMMANDS.md**

  ```markdown
  ## /readiness [sprint|olympic|703|ironman]

  **Triggers:** "am I ready for [race]", "race readiness", "ready for [distance]"
  **Distance arg:** required. If missing, ask before calling any tool: "Which distance are you preparing for — sprint, olympic, 703, or ironman?"
  **Tools:** `get_activities` (90 days) → `get_wellness_data` (14 days)
  **Guardrail:** yes

  ### Tool sequence
  1. `get_activities` for the last 90 days (for per-discipline CTL/ATL/TSB — see /status for computation method)
  2. `get_wellness_data` for the last 14 days (for TSB context and recovery signals)

  ### CTL benchmark targets (approximate minimums for completing the distance without significant suffering)

  | Distance | Swim CTL | Bike CTL | Run CTL |
  |---|---|---|---|
  | Sprint | 12–20 | 40–55 | 30–45 |
  | Olympic | 18–28 | 55–70 | 45–60 |
  | 70.3 | 22–32 | 65–80 | 50–65 |
  | 140.6 | 28–40 | 75–95 | 55–75 |

  These are benchmarks, not hard thresholds. Note when an athlete is near the boundary of a range.

  ### Output
  Render an HTML artifact, then a 1-sentence verdict, then the liability guardrail.

  **HTML artifact — readiness card:**

  *Race distance banner* at top (e.g. "70.3 Half Ironman Readiness")

  *Per-discipline row* (swim / bike / run):
  - CTL gauge: actual value vs midpoint of target range for this distance. Colour: green if at/above lower bound, amber if within 10% below, red if >10% below
  - TSB chip: colour-coded per METRICS_REFERENCE.md TSB by race distance table for this distance
  - Decoupling indicator: green/amber/red based on average decoupling across last 3 long aerobic sessions for this discipline

  *Verdict chip* at bottom:
  - `READY` — all disciplines at or above lower bound of range, TSB within race-day target window for this distance
  - `CLOSE` — one discipline below lower bound, or TSB outside window but trending in the right direction
  - `NOT YET` — two or more disciplines below lower bound, or TSB significantly outside target window

  With the single biggest gap called out in one sentence below the chip.

  ---
  ```

- [ ] **Step 2: Append `/plan` to COMMANDS.md**

  ```markdown
  ## /plan [date] [sport] [description]

  **Triggers:** "schedule a workout", "add a session", "plan [sport] for [date]"
  **Tools:** `add_or_update_event`
  **Guardrail:** none

  ### Arg handling
  - If date is missing: ask "What date should I schedule this for?"
  - If sport is missing: ask "What sport — ride, run, or swim?"
  - Description is optional — generate a sensible default name if not provided (e.g. "Easy aerobic run", "Z2 long ride")

  ### Tool sequence
  1. Build the event payload following WORKOUT_PLANNING.md pre-flight checklist
  2. Display the proposed event as a markdown summary (do NOT call the tool yet):
     ```
     Proposed workout:
     - Date: [date]
     - Sport: [sport]
     - Name: [name]
     - Duration: [if specified]
     - Target: [if specified]
     ```
  3. Ask: "Schedule this?" — wait for explicit yes before calling `add_or_update_event`
  4. On confirmation: call `add_or_update_event` with the payload
  5. Echo the created event fields to confirm success

  ---
  ```

- [ ] **Step 3: Commit**

  ```bash
  git add skills/triathlon-training/COMMANDS.md
  git commit -m "feat(skill): add /readiness and /plan commands"
  ```

---

## Chunk 6: Delete Dissolved Files + Update Docs

### Task 12: Delete `COACH_PERSONA.md` and `DISCIPLINE_ANALYSIS.md`

**Files:**
- Delete: `skills/triathlon-training/COACH_PERSONA.md`
- Delete: `skills/triathlon-training/DISCIPLINE_ANALYSIS.md`

Before deleting, verify that all content has been migrated:

- [ ] **Step 1: Audit COACH_PERSONA.md against COMMANDS.md**

  Check that each section of `COACH_PERSONA.md` is represented in `COMMANDS.md`:
  - Tone rules → Tone and Guardrails section ✓
  - Liability guardrail → Tone and Guardrails section ✓
  - Do/don't patterns → Tone and Guardrails section ✓
  - Edge case handling → inline in relevant commands ✓

- [ ] **Step 2: Audit DISCIPLINE_ANALYSIS.md against COMMANDS.md**

  Check that each section is represented:
  - Cycling analysis sequence → /last cycling rules ✓
  - Running analysis sequence → /last running rules ✓
  - Swimming analysis sequence → /last swimming rules ✓
  - Cross-discipline patterns → /status cross-discipline note ✓

- [ ] **Step 3: Delete both files**

  ```bash
  git rm skills/triathlon-training/COACH_PERSONA.md
  git rm skills/triathlon-training/DISCIPLINE_ANALYSIS.md
  ```

- [ ] **Step 4: Commit**

  ```bash
  git commit -m "refactor(skill): dissolve COACH_PERSONA.md and DISCIPLINE_ANALYSIS.md into COMMANDS.md"
  ```

---

### Task 13: Update CLAUDE.md and README.md

**Files:**
- Modify: `CLAUDE.md`
- Modify: `README.md`

The desktop extension, tools/, and .mcp.json have been removed. The skill file structure has changed. Both docs need updating.

- [ ] **Step 1: Update CLAUDE.md**

  Remove references to:
  - Desktop extension pack command and `.mcpb` files
  - `tools/` directory
  - CF Worker / remote mode (now documented in the server repo, not here)

  Update the Architecture table to reflect the new 4-file skill structure:
  | File | Role |
  |---|---|
  | `SKILL.md` | Router: command routing table, MCP tool map, data quality gates |
  | `COMMANDS.md` | All commands: trigger phrases, tool sequences, output templates |
  | `METRICS_REFERENCE.md` | Thresholds: CTL ramp rates, TSB, decoupling, VI, IF, EF, SWOLF |
  | `WORKOUT_PLANNING.md` | Write-operation guidance for `add_or_update_event` |

  Update MCP Setup section to reflect local stdio mode only (CF Worker details live in the server repo README).

- [ ] **Step 2: Update `README.md` (repo root — `/README.md`)**

  Move setup instructions that were in SKILL.md (MCP server setup, credentials, local stdio config) to README.md under a "Setup" section. README is the entry point for new users cloning this repo.

- [ ] **Step 3: Delete the temporary api-field-notes.md**

  ```bash
  git rm docs/superpowers/plans/api-field-notes.md
  ```

- [ ] **Step 4: Commit everything**

  ```bash
  git add CLAUDE.md README.md
  git commit -m "docs: update CLAUDE.md and README.md for new skill structure"
  ```

---

## Validation

After all tasks are complete, manually test each command:

- [ ] `/help` — outputs a command table with 7 rows, no guardrail
- [ ] `/wellness` — renders an HTML artifact with HRV/resting HR data; 2-sentence summary; guardrail present
- [ ] `/status` — renders per-discipline columns; cross-discipline note; guardrail present
- [ ] `/last run` — renders stat card artifact + narrative + one question; guardrail present
- [ ] `/last ride` — stat card includes weather strip and VI
- [ ] `/weekly` — renders 7-day calendar artifact; summary; guardrail present
- [ ] `/readiness 703` — asks for no clarification (arg provided); renders readiness artifact; guardrail present
- [ ] `/readiness` (no arg) — asks which distance before fetching data
- [ ] `/plan 2026-03-21 run easy 45 min` — shows proposed event, asks for confirmation, does NOT call the tool until confirmed; no liability guardrail appended
