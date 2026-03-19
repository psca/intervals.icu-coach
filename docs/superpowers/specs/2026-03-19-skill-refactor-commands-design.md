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

`COACH_PERSONA.md` and `DISCIPLINE_ANALYSIS.md` are dissolved. Their content moves directly into the per-command templates in `COMMANDS.md`, eliminating the need for Claude to cross-reference multiple files during analysis.

---

## SKILL.md Role (post-refactor)

Becomes a pure router. Contains:
- Prerequisite setup (MCP credentials)
- MCP tool map table
- Data quality gates
- Command routing table (slash command → section in COMMANDS.md)
- Ambiguous phrase fallback rules

Does NOT contain: output templates, analysis sequences, persona guidance, or thresholds (those live in COMMANDS.md and METRICS_REFERENCE.md respectively).

**Ambiguous routing fallback:**
- "how am I doing" → `/status`
- Unclear intent → ask "Are you asking about fitness load (`/status`), recovery (`/wellness`), or this week's activities (`/weekly`)?"

---

## Commands

### `/help`
- **Triggers:** "what can you do", "commands", "help"
- **Tools:** none
- **Output:** markdown — compact table of all commands with one-line descriptions

---

### `/wellness`
- **Triggers:** "how's my wellness", "how am I recovering", "HRV", "recovery check", "how's my recovery"
- **Tools:** `get_wellness_data` (14 days)
- **Output:** HTML artifact
- **Template:**
  - HRV sparkline (7 days) with horizontal baseline marker
  - Resting HR trend line below it
  - Sleep score as dot-per-day row (omit section if unavailable)
  - Single verdict: `● RECOVERING WELL` / `● MONITOR` / `● REST NEEDED` in green/amber/red
  - 2-sentence plain-language summary below the artifact
- **Degradation:** if HRV absent, use resting HR + note the gap; if both absent, tell the user what's missing and decline to give a verdict

> **Implementation note:** Verify field names in `get_wellness_data` response — expected: `hrv`, `restingHR`, `sleepScore` (or equivalent). Confirm date range parameter format.

---

### `/status`
- **Triggers:** "how's my fitness", "training load", "fitness status", "how am I doing", "CTL", "PMC"
- **Tools:** `get_activities` (90 days, limit 100) → `get_wellness_data` (7 days)
- **Output:** HTML artifact
- **Template:** Three discipline columns (swim / bike / run). Only render columns for disciplines with ≥3 activities in last 30 days.
  - Per column: sport icon + name, CTL bar with current value + 6-week trend arrow, ATL vs CTL indicator, TSB chip (colour-coded by value range), ramp rate with flag if >6 pts/week
  - Below columns: 2-sentence cross-discipline note (e.g. imbalance relative to race distance if known)
- **Degradation:** if a discipline has <3 activities, show a muted "Insufficient data" placeholder instead of hiding silently

> **Implementation note:** Verify CTL/ATL/TSB are returned per-discipline in `get_activities` response, or whether they must be derived from activity-level data. Confirm field names.

---

### `/last [sport?]`
- **Triggers:** "how was my last run/ride/swim", "analyze my last [sport]", "feedback on yesterday's [sport]", "last activity"
- **Sport arg:** optional — if omitted, use the most recent activity regardless of type; if provided, filter to that sport
- **Tools:** `get_activities` (limit 10) → `get_activity_details` → `get_activity_weather` (outdoor only, mandatory before output) → `get_activity_intervals` (structured workouts only) → `get_activity_streams` (only if decoupling not in details response)
- **Output:** two-part
  - **HTML artifact (stat card):**
    - Weather strip across top (outdoor only): conditions, feels-like temp, wind; cycling adds headwind/tailwind %, running omits them
    - Key metrics grid: duration, IF or pace, avg HR, decoupling %, EF, VI (cycling only) — omit any unavailable field
    - Signals row: 🟢/🟡/🔴 badges with one-word label per signal
    - Comparison bar: this session vs last 3 comparable efforts on the same metrics; footnote if FTP changed between compared sessions
  - **Markdown narrative (below artifact):**
    - "What happened" — 2–4 sentences, observation only, no recommendations
    - One question — single clarifying question inviting athlete context
    - Liability guardrail

**Sport-specific analysis rules embedded in template:**
- **Cycling:** assess IF vs session type, VI with course context, decoupling (≥90 min Z1–Z2 only), EF trend, power zone distribution
- **Running:** EF via NGP, decoupling (≥60 min Z1–Z2 only), cadence early vs late, heat adjustment before flagging
- **Swimming:** SWOLF trend, pace per 100m, interval consistency (use `get_activity_intervals`), stroke rate; no weather fetch

> **Implementation note:** Weather tool call order is mandatory for outdoor activities before constructing the artifact. Verify `get_activity_weather` returns `headwind_percent`, `tailwind_percent`, `average_feels_like`, `prevailing_wind_cardinal`, `temp_bar`.

---

### `/weekly`
- **Triggers:** "weekly summary", "how was my week", "this week", "week recap"
- **Tools:** `get_activities` (14 days) → `get_wellness_data` (7 days) → `get_events` (current week, planned sessions)
- **Output:** HTML artifact
- **Template:**
  - Wellness strip across top (Mon–Sun): HRV dot + resting HR dot per day
  - 7-day calendar row: completed activities as cards (sport icon, duration, key metric); planned sessions in distinct style (dashed border / lighter colour)
  - Bottom: TSS bar chart by discipline — completed (solid) vs planned target (outline)
  - Below artifact: 2–3 sentence summary — what got done, what's left, any load flags

> **Implementation note:** Verify `get_events` supports a date-range filter for current week and returns planned workout fields (`type`, `name`, `moving_time`, `load_target`). Confirm current week boundaries (Mon–Sun vs Sun–Sat).

---

### `/readiness [sprint|olympic|703|ironman]`
- **Triggers:** "am I ready for [race]", "race readiness", "ready for [distance]"
- **Distance arg:** required — if missing, ask before any tool calls
- **Tools:** `get_activities` (90 days) → `get_wellness_data` (14 days)
- **Output:** HTML artifact
- **Template:**
  - Race distance banner at top
  - Per-discipline row: CTL gauge (actual vs target from METRICS_REFERENCE.md race-distance table), TSB chip, decoupling health indicator
  - Verdict chip at bottom: `READY` / `CLOSE` / `NOT YET` — with the single biggest gap called out in one sentence
- **Race-distance CTL targets:** sourced from METRICS_REFERENCE.md race-distance discipline priorities table
- **TSB target windows:** sourced from METRICS_REFERENCE.md TSB by race distance table

> **Implementation note:** `/readiness` does not have a fixed race date — it assesses current state, not taper trajectory. Future iteration could accept a date arg to project TSB on race day.

---

### `/plan [date] [sport] [description]`
- **Triggers:** "schedule a workout", "add a session", "plan [sport] for [date]"
- **Tools:** `add_or_update_event` (pre-flight per WORKOUT_PLANNING.md)
- **Output:** markdown confirmation — echoes date, sport, name, key targets before confirming write; explicit confirmation step before calling the tool
- **Arg handling:** if date or sport missing, ask; description is optional (will generate a sensible default name)

---

## Output Mode Summary

| Command | Output | Visual |
|---|---|---|
| `/help` | Markdown | — |
| `/wellness` | HTML artifact + brief markdown | Sparklines, verdict chip |
| `/status` | HTML artifact + brief markdown | Discipline columns, bars |
| `/last` | HTML artifact + markdown narrative | Stat card, comparison bar |
| `/weekly` | HTML artifact + brief markdown | Calendar, TSS bars |
| `/readiness` | HTML artifact + brief markdown | Gauges, verdict chip |
| `/plan` | Markdown confirmation | — |

---

## Tone and Guardrails

Tone rules (previously in COACH_PERSONA.md) are embedded inline in each command template rather than as a separate file. Key rules carried forward:

- Observe before concluding — lead with what the data shows, not the interpretation
- Translate every number into plain language
- Distinguish trend from noise (single session ≠ pattern)
- Never prescribe specific workouts
- Celebrate real improvements
- Liability guardrail: *"This is informational analysis based on your intervals.icu data. Always work with a qualified coach or healthcare provider before making significant training changes, especially if you're experiencing pain, illness, or unusual fatigue."* — required at the end of every response, every time

---

## Iteration Notes

- HTML artifact visual design (colours, layout density, specific chart types) is intentionally left for post-build iteration — templates define what data appears, not pixel-perfect layout
- `/readiness` future extension: accept an optional `[date]` arg to project TSB trajectory toward race day
- Additional commands to consider in future: `/compare [date range]` for period-over-period training comparison, `/overtraining` as an explicit overtraining cascade check
