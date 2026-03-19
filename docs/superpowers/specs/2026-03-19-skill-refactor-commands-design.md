# Skill Refactor: Command-Driven Templates with Visual Artifacts

**Date:** 2026-03-19
**Status:** Approved for implementation

---

## Problem

The current skill produces inconsistent output structure across sessions. The same query ("how am I doing") can yield a different shape of response depending on which reference files Claude leans on. Only single-activity analysis has a defined output template; all other query types rely on COACH_PERSONA.md's generic 5-step pattern, which is too loose to produce predictable results.

Additionally, there is no command system — the user must phrase questions carefully to trigger the right analysis path.

---

## Goals

1. **Predictable output** — the same command always produces the same structure, only the data differs
2. **Command system** — slash commands for Claude Code; natural language trigger phrases catch the same paths in Claude Desktop
3. **Visual output for data-heavy responses** — HTML artifacts for wellness, fitness status, weekly summary, and race readiness; markdown narrative retained for activity analysis
4. **Maintainability** — fewer files, no cross-referencing between files to understand a command's full behavior

---

## File Structure

**Before (5 files):**
```
SKILL.md
METRICS_REFERENCE.md
COACH_PERSONA.md          ← dissolve into COMMANDS.md
DISCIPLINE_ANALYSIS.md    ← dissolve into COMMANDS.md
WORKOUT_PLANNING.md
```

**After (4 files):**
```
SKILL.md              — router only: command list, MCP tool map, data quality gates
COMMANDS.md           — NEW: every command with trigger phrases, tool sequence, output template
METRICS_REFERENCE.md  — unchanged
WORKOUT_PLANNING.md   — unchanged
```

`COACH_PERSONA.md` and `DISCIPLINE_ANALYSIS.md` are dissolved. Content migration:

| Source | Destination |
|---|---|
| COACH_PERSONA.md — tone rules, do/don't patterns | Tone and Guardrails section of COMMANDS.md |
| COACH_PERSONA.md — liability guardrail | Tone and Guardrails section of COMMANDS.md |
| COACH_PERSONA.md — edge case handling | Inline in relevant command templates |
| DISCIPLINE_ANALYSIS.md — cycling analysis sequence | `/last` cycling sport-specific rules |
| DISCIPLINE_ANALYSIS.md — running analysis sequence | `/last` running sport-specific rules |
| DISCIPLINE_ANALYSIS.md — swimming analysis sequence | `/last` swimming sport-specific rules |
| DISCIPLINE_ANALYSIS.md — cross-discipline patterns | `/status` cross-discipline note section |
| SKILL.md — data quality gates (existing) | Retained in SKILL.md router section |
| SKILL.md — MCP tool map (existing) | Retained in SKILL.md router section |
| SKILL.md — single activity output template (sections 0–6) | Replaced by `/last` command template |

---

## SKILL.md Role (post-refactor)

Becomes a pure router. Contains:
- Prerequisite setup (MCP credentials)
- MCP tool map table
- Data quality gates (carried over from current SKILL.md unchanged)
- Command routing table (slash command → section in COMMANDS.md)
- Ambiguous phrase fallback rules

Does NOT contain: output templates, analysis sequences, persona guidance, or thresholds.

**Ambiguous routing fallback:**
- "how am I doing" → `/status`
- Unclear intent → ask "Are you asking about fitness load (`/status`), recovery (`/wellness`), or this week's activities (`/weekly`)?"

---

## Commands

### `/help`
- **Triggers:** "what can you do", "commands", "help"
- **Tools:** none
- **Output:** markdown — compact table of all commands with one-line descriptions
- **Note:** no liability guardrail on this command

---

### `/wellness`
- **Triggers:** "how's my wellness", "how am I recovering", "HRV", "recovery check", "how's my recovery"
- **Tools:** `get_wellness_data` (14 days)
- **Output:** HTML artifact + 2-sentence markdown summary below
- **Template:**
  - HRV sparkline (7 days) with horizontal baseline marker
  - Resting HR trend line below it
  - Sleep score as dot-per-day row (omit section silently if field absent)
  - Single verdict: `● RECOVERING WELL` / `● MONITOR` / `● REST NEEDED` in green/amber/red
  - 2-sentence plain-language summary below the artifact
  - Liability guardrail
- **Degradation:**
  - HRV absent: use resting HR as primary signal, note HRV gap in summary
  - Both HRV and resting HR absent: tell the user what data is missing, decline to give a verdict, suggest enabling HRV tracking in intervals.icu

> **Implementation gate:** Before building the `/wellness` template, call `get_wellness_data` against a live athlete and confirm exact field names for HRV, resting HR, and sleep score. Do not assume field names. Block template implementation until confirmed.

---

### `/status`
- **Triggers:** "how's my fitness", "training load", "fitness status", "how am I doing", "CTL", "PMC"
- **Tools:** `get_activities` (90 days, limit 100) → `get_wellness_data` (7 days)
- **Output:** HTML artifact + 2-sentence markdown summary below
- **Template:** Three discipline columns (swim / bike / run). Only render columns for disciplines with ≥3 activities in last 30 days; show a muted "Not enough data" placeholder for absent disciplines.
  - Per column: sport icon + name, CTL bar with current value + 6-week trend arrow, ATL vs CTL indicator, TSB chip (colour-coded by value range), ramp rate with flag if >6 pts/week (show "—" if no activity for this discipline exists ≥7 days ago)
  - Below columns: 2-sentence cross-discipline note — flag imbalances, cumulative fatigue signals (run EF declining + bike VI spiking + SWOLF degrading = systemic flag)
  - Liability guardrail
- **How CTL/ATL/TSB are computed per discipline:** `get_activities` returns a flat list of activities each with `icu_ctl`, `icu_atl`, `icu_tsb` fields (per-activity computed values from intervals.icu). Filter the list by sport type (Ride/VirtualRide, Run/TrailRun, Swim) and take the most recent activity's values as the current CTL/ATL/TSB for that discipline. Ramp rate = difference between most recent CTL and CTL from 7 days prior (find nearest activity ≥7 days ago for the same discipline).
- **Degradation:** if a discipline has <3 activities in last 30 days, show placeholder; do not compute or display metrics

> **Implementation gate:** Before building the `/status` template, call `get_activities` against a live athlete and confirm `icu_ctl`, `icu_atl`, `icu_tsb` are present on activity objects and the sport type field name used for discipline filtering. Block template implementation until confirmed.

---

### `/last [sport?]`
- **Triggers:** "how was my last run/ride/swim", "analyze my last [sport]", "feedback on yesterday's [sport]", "last activity"
- **Sport arg:** optional — if omitted, use the most recent activity regardless of type; if provided, filter to that sport
- **Tools:**
  1. `get_activities` (limit 10, or filtered by sport type if arg provided)
  2. `get_activity_details` for the most recent activity
  3. `get_activity_weather` — **outdoor Run/Ride only; skip entirely for Swim, VirtualRide, and treadmill Run** (detect via `indoor: true` or activity type); call before constructing any output
  4. `get_activity_intervals` — structured workouts only (intervals present in details response)
  5. `get_activity_streams` — only if decoupling % not in details response; high token cost
- **Output:** two-part
  - **HTML artifact (stat card):**
    - Weather strip across top (outdoor Run/Ride only): conditions, feels-like temp, wind; cycling adds headwind/tailwind %, running omits them
    - Key metrics grid: duration, IF or pace, avg HR, decoupling %, EF, VI (cycling only) — omit any unavailable field
    - Signals row: 🟢/🟡/🔴 badges with one-word label per signal, thresholds from METRICS_REFERENCE.md
    - Comparison bar: this session vs last 3 comparable efforts (same sport, similar duration ±25%, similar session type inferred from IF/pace zone); footnote if FTP changed between compared sessions
  - **Markdown narrative (below artifact):**
    - "What happened" — 2–4 sentences, observation only, no recommendations
    - One question — single clarifying question inviting athlete context
    - Liability guardrail

**Sport-specific analysis rules:**
- **Cycling:** assess IF vs session type, VI with course context (always contextualize before flagging), decoupling (≥90 min Z1–Z2 only), EF trend, power zone distribution; apply weather context before flagging any metric
- **Running:** EF via NGP, decoupling (≥60 min Z1–Z2 only), cadence early vs late session (first 20% vs last 20%, drop >5 spm = flag), heat adjustment via `average_feels_like` before flagging decoupling
- **Swimming:** SWOLF trend, pace per 100m, interval consistency via `get_activity_intervals`, stroke rate consistency; no weather fetch; HR data less reliable (note uncertainty if used)

> **Implementation gate:** Weather field names must be verified against a live `get_activity_weather` response before building the template. DISCIPLINE_ANALYSIS.md references `prevailing_wind_cardinal` (cardinal string) while METRICS_REFERENCE.md references `prevailing_wind_deg` (degree integer) — these are inconsistent in the current codebase. Confirm which the MCP tool actually returns and use that name consistently in COMMANDS.md.

---

### `/weekly`
- **Triggers:** "weekly summary", "how was my week", "this week", "week recap"
- **Tools:** `get_activities` (14 days) → `get_wellness_data` (7 days) → `get_events` (current week)
- **Week boundaries:** Mon–Sun; current week = Mon of this week through today
- **Output:** HTML artifact + 2–3 sentence markdown summary below
- **Template:**
  - Wellness strip across top (Mon–Sun): HRV dot + resting HR dot per day; empty dot (grey outline) for days with no wellness data
  - 7-day calendar row: completed activities as cards (sport icon, duration, key metric); planned sessions in dashed-border style; empty day cells shown as blank
  - Bottom: TSS bar chart by discipline — completed bars only if `load_target` absent on planned events; add planned-target outline bars only when `load_target` is present on the planned event
  - Below artifact: 2–3 sentence summary — what got done, what's left this week, any load flag
  - Liability guardrail
- **Degradation:**
  - No planned sessions from `get_events`: omit planned-session overlays entirely, show completed activities only; note "No planned sessions found for this week" in summary
  - Wellness data absent for some days: show empty dots (grey outline) — do not interpolate
  - Wellness data entirely absent: omit wellness strip row, note the gap in summary
  - `load_target` absent on planned events: show planned sessions in calendar row but omit the target outline from the TSS bar chart; show completed bars only

> **Implementation gate:** Verify `get_events` supports a date-range filter and returns `type`, `name`, `moving_time`, `load_target`. Confirm whether `load_target` is reliably populated for the athlete's planned sessions before building the TSS overlay.

---

### `/readiness [sprint|olympic|703|ironman]`
- **Triggers:** "am I ready for [race]", "race readiness", "ready for [distance]"
- **Distance arg:** required — if missing, ask before any tool calls
- **Tools:** `get_activities` (90 days) → `get_wellness_data` (14 days)
- **Output:** HTML artifact + 1-sentence markdown verdict below
- **Template:**
  - Race distance banner at top
  - Per-discipline row: CTL gauge (actual vs target — see table below), TSB chip colour-coded per METRICS_REFERENCE.md TSB table, decoupling health indicator (average of last 3 long aerobic sessions)
  - Verdict chip: `READY` / `CLOSE` / `NOT YET` — with the single biggest gap called out in one sentence
  - Liability guardrail
- **CTL benchmark targets by race distance and discipline** (approximate minimums for completing the distance without significant suffering; not podium targets):

| Distance | Swim CTL | Bike CTL | Run CTL |
|---|---|---|---|
| Sprint | 12–20 | 40–55 | 30–45 |
| Olympic | 18–28 | 55–70 | 45–60 |
| 70.3 | 22–32 | 65–80 | 50–65 |
| 140.6 | 28–40 | 75–95 | 55–75 |

  These are benchmarks, not hard thresholds — an athlete with strong run fitness may need lower run CTL. The gauge shows actual vs midpoint of the range; note when an athlete is near the boundary.

- **Verdict logic:**
  - `READY` — all disciplines at or above lower bound of range, TSB within race-day window
  - `CLOSE` — one discipline below lower bound, or TSB outside window but trending correctly
  - `NOT YET` — two or more disciplines below lower bound, or TSB significantly outside window

> **Implementation note:** `/readiness` assesses current state, not taper trajectory. Future extension: accept optional `[date]` arg to project TSB on race day.

---

### `/plan [date] [sport] [description]`
- **Triggers:** "schedule a workout", "add a session", "plan [sport] for [date]"
- **Tools:** `add_or_update_event` (pre-flight per WORKOUT_PLANNING.md)
- **Output:** markdown — display proposed event summary, ask "Schedule this?" (yes/no), then call `add_or_update_event` on confirmation; echo the created event fields after success
- **Arg handling:** if date or sport missing, ask before constructing any payload; description is optional (generate a sensible default name from sport + session type)
- **Note:** no liability guardrail on this command

---

## Output Mode Summary

| Command | Output | Visual | Guardrail |
|---|---|---|---|
| `/help` | Markdown | — | No |
| `/wellness` | HTML artifact + markdown | Sparklines, verdict chip | Yes |
| `/status` | HTML artifact + markdown | Discipline columns, bars | Yes |
| `/last` | HTML artifact + markdown narrative | Stat card, comparison bar | Yes |
| `/weekly` | HTML artifact + markdown | Calendar, TSS bars | Yes |
| `/readiness` | HTML artifact + markdown | Gauges, verdict chip | Yes |
| `/plan` | Markdown confirmation | — | No |

---

## Tone and Guardrails

Tone rules embedded in COMMANDS.md (not a separate file). Key rules:

- Observe before concluding — lead with what the data shows, not the interpretation
- Translate every number into plain language
- Distinguish trend from noise — single session ≠ pattern; need ≥3 sessions to call a trend
- Never prescribe specific workouts or training plans
- Celebrate real improvements with specific metric evidence
- Handle missing disciplines explicitly — name the gap, don't infer from aggregate

**Liability guardrail** (required on all commands except `/help` and `/plan`):
> *This is informational analysis based on your intervals.icu data. Always work with a qualified coach or healthcare provider before making significant training changes, especially if you're experiencing pain, illness, or unusual fatigue.*

---

## Iteration Notes

- HTML artifact visual design (colours, layout density, chart types) is intentionally deferred to post-build iteration
- `/readiness` future extension: `[date]` arg for TSB taper projection
- Future commands to consider: `/compare [period]` for period-over-period comparison, `/overtraining` as an explicit overtraining cascade check
