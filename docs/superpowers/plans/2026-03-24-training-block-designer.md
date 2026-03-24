# Training Block Designer — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a training block designer to the triathlon coaching skill that generates multi-week periodized plans from evidence-based templates and writes them to intervals.icu.

**Architecture:** Two new reference files (BLOCK_TEMPLATES.md + WORKOUT_LIBRARY.md) provide the building blocks. Three existing files get updated (SKILL.md, COACH.md, WORKOUT_PLANNING.md). The LLM assembles plans from templates and workout archetypes — it does not freestyle generate training content.

**Tech Stack:** Markdown skill files, intervals.icu MCP tools, intervals.icu workout description syntax.

**Spec:** `docs/superpowers/specs/2026-03-24-training-block-designer-design.md`

---

## Chunk 1: Workout Library

### Task 1: Create WORKOUT_LIBRARY.md — Swim Archetypes

**Files:**
- Create: `skills/triathlon-training/WORKOUT_LIBRARY.md`

This is the canonical workout reference. Start with swim because it has the most distinctive syntax (distance-based, pace targets per 100m).

- [ ] **Step 1: Create the file with header and swim section**

Write `skills/triathlon-training/WORKOUT_LIBRARY.md` with:

```markdown
# Workout Library — Triathlon Training

Canonical workout archetypes for swim, bike, run, and strength. Each entry includes metadata for the LLM to select the right workout, and the full intervals.icu structured description syntax to write to the calendar.

**Usage:** Templates in BLOCK_TEMPLATES.md reference these workouts by name. The LLM looks up the archetype here and writes the `description` field content to `add_or_update_event`.

**Scaling by tier:**
- **Short tier:** ~75% of standard volume (fewer sets / shorter duration)
- **Standard tier:** as written below
- **Long tier:** ~125% of standard volume (more sets / longer duration)

---

## Zone Resolution

Before writing workouts, verify zone data is available per discipline:

- **Bike:** FTP from most recent ride with power data, or intervals.icu athlete settings
- **Run:** threshold pace from most recent tempo/interval run, or ask athlete
- **Swim:** CSS from most recent CSS test or interval set, or ask athlete
- **Fallback chain:** power/pace zones → HR zones (`Z2 HR`) → RPE-based text cues. If no zone data exists for any discipline, ask the athlete directly for recent test results. If unavailable, generate RPE-only plans with a note that workouts can be updated once zones are established.

---

## Swim
```

Then add these swim archetypes (each with When, Duration range, Intensity metadata + full intervals.icu syntax):

1. **Aerobic Endurance** — Base phase. 2000-3000m. Steady easy swimming.
2. **Technique Drills** — All phases. 1500-2500m. Drill-focused with short swim sets.
3. **CSS Intervals** — Base 2 / Build. 3000-4000m. Threshold pace intervals (e.g., 8x100m at 95-100% Pace).
4. **VO2max Swim** — Build / Peak. 2500-3500m. Short fast intervals (e.g., 12x50m at 105-110% Pace).
5. **Race Pace Set** — Peak / Taper. 2000-3000m. Race-distance simulation at target pace.
6. **Recovery Swim** — All phases (recovery weeks). 1500-2000m. Easy, drill-focused.
7. **Open Water Simulation** — Build / Peak. 2000-3000m. Continuous effort with sighting practice cues.

Use `Pace` targets with `/100m` unit. Use `mtr` for distances. Include warmup/main/cooldown structure with section headers and repeat syntax.

- [ ] **Step 2: Verify swim archetypes use correct intervals.icu syntax**

Read the file back. For each archetype, verify:
- Steps start with `- ` (dash + space)
- Distance uses `mtr` suffix (e.g., `400mtr`)
- Pace targets use `% Pace` or absolute `X:XX/100m Pace` format
- Repeats use `Nx` header before step block with blank lines around
- Section headers (Warmup, Main Set, Cooldown) do NOT start with `- `

- [ ] **Step 3: Commit**

```bash
git add skills/triathlon-training/WORKOUT_LIBRARY.md
git commit -m "feat: create WORKOUT_LIBRARY.md with swim archetypes"
```

---

### Task 2: Add Bike Archetypes to WORKOUT_LIBRARY.md

**Files:**
- Modify: `skills/triathlon-training/WORKOUT_LIBRARY.md`

- [ ] **Step 1: Add bike section**

Append `## Bike` section with these archetypes:

1. **Easy Endurance** — Base / All. 60-180min. Z2, 55-75% FTP.
2. **Tempo** — Base 2 / Build. 75-120min. Sustained blocks at 76-87% FTP.
3. **Sweet Spot Intervals** — Build. 60-90min. 3x12min at 88-93% FTP.
4. **Threshold Intervals** — Build. 60-90min. 3x10min at 95-105% FTP.
5. **VO2max Intervals** — Build / Peak. 60-75min. 5x4min at 106-120% FTP.
6. **Race Pace Ride** — Peak. 90-180min. Sustained at race IF (distance-dependent).
7. **Recovery Spin** — All (recovery days). 45-60min. <55% FTP.
8. **Openers** — Taper / Race week. 45-60min. Easy with 3x30s at 120%+ to activate.

Use `%` for FTP-relative targets. Include `rpm` cadence where relevant. Use `ramp` syntax for warmups/cooldowns.

- [ ] **Step 2: Verify bike archetypes syntax**

Read back and verify: `%` targets (no `w` unless absolute), `rpm` cadence appended, `ramp` warmups, `Nx` repeat headers.

- [ ] **Step 3: Commit**

```bash
git add skills/triathlon-training/WORKOUT_LIBRARY.md
git commit -m "feat: add bike archetypes to WORKOUT_LIBRARY.md"
```

---

### Task 3: Add Run Archetypes to WORKOUT_LIBRARY.md

**Files:**
- Modify: `skills/triathlon-training/WORKOUT_LIBRARY.md`

- [ ] **Step 1: Add run section**

Append `## Run` section with these archetypes:

1. **Easy Aerobic** — Base / All. 30-90min. Z2 HR or 65-75% Pace.
2. **Easy + Strides** — Base / Build. 45-60min easy + 6x20s strides with full recovery.
3. **Threshold Cruise Intervals** — Build. 50-70min total. 3x10min at 90-95% Pace.
4. **VO2max Intervals** — Build / Peak. 50-65min total. 5x3min at 98-105% Pace.
5. **Long Run** — Base / Build. 75-150min. Z2 HR, steady effort.
6. **Race Pace Run** — Peak. 45-75min. Extended blocks at target race pace.
7. **Recovery Jog** — All (recovery days). 30-40min. Very easy, Z1 HR.
8. **Hill Repeats** — Build. 50-65min. 8x90s uphill at 5K effort.

Use `Pace` targets with `/km` unit. Use `HR` zones for easy/recovery runs.

- [ ] **Step 2: Verify run archetypes syntax**

Read back and verify: `% Pace` or `Z2 HR` targets, `m` for durations (minutes), strides use short durations with `freeride` or text cues.

- [ ] **Step 3: Commit**

```bash
git add skills/triathlon-training/WORKOUT_LIBRARY.md
git commit -m "feat: add run archetypes to WORKOUT_LIBRARY.md"
```

---

### Task 4: Add Strength Archetypes to WORKOUT_LIBRARY.md

**Files:**
- Modify: `skills/triathlon-training/WORKOUT_LIBRARY.md`

- [ ] **Step 1: Add strength section**

Append `## Strength` section with these archetypes. Strength workouts use plain-text descriptions (not intervals.icu structured syntax — intervals.icu doesn't parse strength sets). Set `type: "WeightTraining"` in the event payload.

1. **General Strength A** — Base. 45-60min. Full-body compound movements (squat, deadlift, lunge, press, row, plank). 3 sets x 10-12 reps.
2. **General Strength B** — Base / Build. 45-60min. Single-leg focus (Bulgarian split squat, single-leg deadlift, step-ups) + core. 3 sets x 8-10 reps.
3. **Maintenance Strength** — Build. 30-40min. Reduced volume (2 sets) of key movements. Maintain, don't build.

Also add a **Brick Workouts** note at the end of the file:

```markdown
---

## Brick Workouts

Brick sessions are NOT a single workout archetype. Per the no-aggregation rule, a brick is two separate events on the same day:
- A **Bike** event (e.g., Race Pace Ride, 60-90min)
- A **Run** event (e.g., Easy Aerobic or Race Pace Run, 15-30min) scheduled immediately after

When templates in BLOCK_TEMPLATES.md reference "Brick: Bike→Run", the implementer should create two events on that day using the named bike and run archetypes. Add a text cue in the run event description: "Off-the-bike run — start easy, settle into pace."
```

- [ ] **Step 2: Commit**

```bash
git add skills/triathlon-training/WORKOUT_LIBRARY.md
git commit -m "feat: add strength archetypes to WORKOUT_LIBRARY.md"
```

---

## Chunk 2: Block Templates

### Task 5: Create BLOCK_TEMPLATES.md — Structure and Sprint/Olympic Tri

**Files:**
- Create: `skills/triathlon-training/BLOCK_TEMPLATES.md`

- [ ] **Step 1: Create the file with header, rules, and composable phase variant descriptions**

Write `skills/triathlon-training/BLOCK_TEMPLATES.md` with:

```markdown
# Block Templates — Triathlon Training

Week-by-week phase structures for each race distance and tier. Each week references workout names from WORKOUT_LIBRARY.md.

## How to Use This File

1. Select the template matching the athlete's race distance and tier (short/standard/long)
2. If athlete's timeline doesn't match exactly: stretch or compress the **base phase** only. Build, peak, and taper phases are sacred.
3. If athlete requested a methodology variant: swap the matching phase module (see Composable Phase Variants below)
4. Walk through each week, look up the named workouts in WORKOUT_LIBRARY.md, parameterize with athlete's zones, and schedule on their available days

## Mesocycle Patterns

- **2:1** (2 load + 1 recovery): default for beginners, masters (45+), and high-intensity blocks
- **3:1** (3 load + 1 recovery): for experienced athletes in base/build phases
- Recovery weeks: reduce volume by ~40%, maintain 1-2 intensity sessions at reduced sets

## Composable Phase Variants

Templates below use the **Standard** variant by default. Swap when athlete requests:

**Base variants:**
- **Standard base:** Volume-focused. Gradually increasing duration, mostly Z1-Z2. Intensity introduced late in Base 2.
- **Polarized base:** 80/20 distribution from day one. Easy sessions very easy (Z1), with 1-2 short high-intensity sessions per week even in base.
- **Reverse periodization base:** Intensity-first. Short, hard sessions early (when indoor training limits volume), transitioning to volume as base progresses.

**Build variants:**
- **Threshold-focused build:** Classic Friel. Sustained threshold work is the primary quality session (sweet spot, cruise intervals).
- **VO2max-heavy build:** Seiler-influenced. VO2max intervals are the primary quality session, with threshold work secondary.
- **Race-specific build:** High specificity. Sessions mimic race demands early (race-pace bricks, race-distance simulation).

**Peak & Taper:** Standardized per distance. Not swappable — evidence-based taper protocols (Mujika, Bosquet).

## Discipline Load Distribution

Default time split across disciplines (adjust if athlete has a discipline focus):
- **Triathlon:** ~15-20% swim, ~40-50% bike, ~30-35% run (by time)
- **Run-only:** 100% run (obviously)

---
```

- [ ] **Step 2: Add Sprint Triathlon templates (Short 8wk, Standard 12wk, Long 16wk)**

For each tier, write a week-by-week table with columns: Week | Phase | Swim | Bike | Run | Strength | Notes.

Reference workout names exactly as defined in WORKOUT_LIBRARY.md. Each cell contains 1-3 workout names for that discipline on that week (not specific days — day slotting happens at assembly time based on athlete schedule).

Sprint key parameters:
- Taper: 3-5 days (final week only)
- Peak: 1 week
- Build: race-specific intensity, shorter intervals, higher cadence/turnover
- Key sessions: short fast swims, threshold bike intervals, 5K-pace run intervals

- [ ] **Step 3: Add Olympic Triathlon templates (Short 12wk, Standard 14wk, Long 18wk)**

Olympic key parameters:
- Taper: 1 week
- Peak: 1-2 weeks
- Build: threshold + VO2max emphasis, longer race-pace sessions
- Key sessions: CSS swim sets, sweet spot / threshold bike, threshold cruise run intervals

- [ ] **Step 4: Verify template workout names match WORKOUT_LIBRARY.md exactly**

Cross-reference every workout name in the template tables against the headings in WORKOUT_LIBRARY.md. Names must match exactly — the LLM uses these as lookup keys.

- [ ] **Step 5: Commit**

```bash
git add skills/triathlon-training/BLOCK_TEMPLATES.md
git commit -m "feat: create BLOCK_TEMPLATES.md with sprint and olympic tri templates"
```

---

### Task 6: Add 70.3 and Ironman Templates

**Files:**
- Modify: `skills/triathlon-training/BLOCK_TEMPLATES.md`

- [ ] **Step 1: Add 70.3 templates (Short 16wk, Standard 20wk, Long 24wk)**

70.3 key parameters:
- Taper: 2 weeks
- Peak: 2 weeks
- Build: sustained power/pace emphasis, longer race-simulation sessions
- Key sessions: longer CSS swim sets, extended sweet spot bike, marathon-pace run blocks
- Bricks: bike-to-run transition sessions in build/peak

- [ ] **Step 2: Add Ironman templates (Short 20wk, Standard 24wk, Long 28wk)**

Ironman key parameters:
- Taper: 2-3 weeks
- Peak: 2-3 weeks
- Build: endurance capacity dominant, race-pace work at lower IF than shorter distances
- Key sessions: long steady swims (3000m+), 4-5hr Z2 rides, 2-2.5hr long runs
- Bricks: weekly bike-to-run in build phase
- Nutrition practice cues in race-pace sessions (`carbs_per_hour` field)

- [ ] **Step 3: Cross-reference workout names against WORKOUT_LIBRARY.md**

- [ ] **Step 4: Commit**

```bash
git add skills/triathlon-training/BLOCK_TEMPLATES.md
git commit -m "feat: add 70.3 and ironman templates to BLOCK_TEMPLATES.md"
```

---

### Task 7: Add Half Marathon and Marathon Templates

**Files:**
- Modify: `skills/triathlon-training/BLOCK_TEMPLATES.md`

- [ ] **Step 1: Add Half Marathon templates (Short 10wk, Standard 12wk, Long 18wk)**

Half marathon key parameters:
- Run-only (no swim/bike columns)
- Taper: 10-14 days
- Peak: 1-2 weeks
- Key sessions: threshold cruise intervals, tempo runs, progressive long runs
- Long run caps at ~90-100 min
- Weekly structure: 4-6 runs/week depending on tier

- [ ] **Step 2: Add Marathon templates (Short 12wk, Standard 18wk, Long 24wk)**

Marathon key parameters:
- Run-only
- Taper: 2-3 weeks
- Peak: 2 weeks
- Key sessions: marathon-pace long runs, threshold intervals, VO2max intervals in build
- Long run progression: up to 2.5-3hr (cap at ~32km/20mi)
- Hansons-influenced: no single run > ~2.5hr, cumulative fatigue approach
- Step-back weeks: ~40% volume reduction

- [ ] **Step 3: Cross-reference workout names against WORKOUT_LIBRARY.md**

- [ ] **Step 4: Commit**

```bash
git add skills/triathlon-training/BLOCK_TEMPLATES.md
git commit -m "feat: add half marathon and marathon templates to BLOCK_TEMPLATES.md"
```

---

## Chunk 3: Existing File Updates

### Task 8: Update WORKOUT_PLANNING.md with intervals.icu Syntax + Batch Write Guidance

**Files:**
- Modify: `skills/triathlon-training/WORKOUT_PLANNING.md`

- [ ] **Step 1: Replace the "Workout Description Format" section**

Replace the existing "Workout Description Format" section (lines 142-165 of current file) with the full intervals.icu structured syntax reference:

```markdown
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

### Power Targets
- FTP-relative: `75%`, `88-93%` (range)
- Absolute: `220w`, `200-240w`
- Zones: `Z2`, `Z3-Z4`

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

**Source:** [R2Tom's Quick Guide](https://forum.intervals.icu/t/workout-builder-syntax-quick-guide/123701), [Workout Builder thread](https://forum.intervals.icu/t/workout-builder/1163)

**Note on `workout_doc`:** Do not construct `workout_doc` JSON by hand. Use `description` text and let the server parse it. If cloning from an existing event, pass `workout_doc` through unmodified.
```

- [ ] **Step 2: Add Batch Write Guidance section**

Append a new section after "MCP Call Pattern":

```markdown
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
```

- [ ] **Step 3: Verify the file reads cleanly end-to-end**

Read the full updated file. Check for duplicate sections, broken markdown, or inconsistencies with existing content.

- [ ] **Step 4: Commit**

```bash
git add skills/triathlon-training/WORKOUT_PLANNING.md
git commit -m "feat: add intervals.icu workout syntax reference and batch write guidance"
```

---

### Task 9: Update SKILL.md with Block Designer Trigger

**Files:**
- Modify: `skills/triathlon-training/SKILL.md`

- [ ] **Step 1: Add trigger row to "What I Can Help With" table**

Append this row as the last entry in the trigger table in SKILL.md:

```markdown
| "build a training plan", "create a block", "plan my season", "build me a plan for [race]", "training block" | Build Training Block |
```

- [ ] **Step 2: Add `get_events` and `delete_events_by_date_range` to MCP Tool Map**

The MCP Tool Map table in SKILL.md needs these tools listed (they're used by the block designer for calendar conflict detection and the "clear and replace" option):

```markdown
| Calendar conflict check | `get_events` | Fetch events in target date range before batch write |
| Clear calendar range | `delete_events_by_date_range` | ⚠️ Destructive — only for "clear and replace" conflict resolution, requires double confirmation |
```

- [ ] **Step 3: Commit**

```bash
git add skills/triathlon-training/SKILL.md
git commit -m "feat: add training block trigger to SKILL.md"
```

---

### Task 10: Update COACH.md — Remove "Never Prescribe" + Add Build Training Block Section

**Files:**
- Modify: `skills/triathlon-training/COACH.md`

This is the largest change. It modifies the coaching principles and adds a complete new command section.

- [ ] **Step 1: Update Coaching Principles**

In the "Coaching Principles" section (line 14), replace:
```
- **Never prescribe** — do not suggest specific workouts or training plans
```
with:
```
- **Prescribe only from templates** — for ad-hoc analysis, do not freestyle training recommendations. For block design requests, use the template assembly flow in BLOCK_TEMPLATES.md + WORKOUT_LIBRARY.md
```

- [ ] **Step 2: Update Last Activity scope guardrail**

In the "Last Activity" section (line 131), replace the scope guardrail:
```
**Scope guardrail:** If the athlete asks for a training plan during this conversation, respond: "Building a full training plan is outside what I can do responsibly..."
```
with:
```
**Scope guardrail:** If the athlete asks for a training plan during activity analysis, redirect: "I can build you a full training block — just say 'build me a training plan' and we'll go through the intake process together."
```

- [ ] **Step 3: Update "What I Can Help With" response template**

Add to the help text list (after the "Schedule a workout" bullet):
```
- **Training block** — build a multi-week periodized plan for any distance from sprint to Ironman, plus half and full marathon. I'll walk you through the setup and preview the plan before adding anything to your calendar
```

- [ ] **Step 4: Add "Build Training Block" section**

Append a new section at the end of COACH.md (after the "Schedule a Workout" section, at the very end of the file), structured like the existing command sections:

```markdown
## Build Training Block

**Triggers:** "build a training plan", "create a block", "plan my season", "build me a plan for [race]", "training block"
**Tools:** `get_activities` (56 days) → `get_events` (target date range) → `add_or_update_event` (batch write on approval)
**Guardrail:** none (liability guardrail not needed — athlete approves every event before write)

### Pre-assembly: Auto-pull MCP data

Before asking any questions:
1. Call `get_activities` with `start_date` = 56 days ago, `end_date` = today, `limit` = 100
2. Compute: weekly hours per discipline, discipline split, training consistency
3. Call `get_events` with `start_date` = today, `end_date` = 30 weeks from today (wide window to catch conflicts and existing race events)

### Structured intake (target 4-6 conversational turns)

Each question has a sensible default. Consolidate related questions. Accept multi-part answers.

1. **Race date + distance + weeks confirmation** — required. Calculate weeks to race. Confirm: "That's 16 weeks — I'll build a 16-week block."
   - **Minimum weeks guardrail:** Hard floor (refuse): Sprint 6wk, Olympic 8wk, 70.3 12wk, Ironman 16wk, HM 6wk, Marathon 10wk. Warn zone (plan will be compressed): Sprint 6-8wk, Olympic 8-12wk, 70.3 12-16wk, Ironman 16-20wk, HM 6-10wk, Marathon 10-12wk.
2. **Confirm inferred fitness + available hours** — present MCP-inferred data: "You're averaging ~9 hrs/week across swim/bike/run. Want to keep that, build to more, or scale back?" Falls back to asking if MCP data is sparse.
   - **Volume ramp guardrail:** If requested hours > current hours × 1.3, add explicit ramp-up weeks and warn.
3. **Discipline focus + methodology** — "Your run CTL is lagging. Focus there, or stay balanced? Any preference on training approach or should I choose?" Skip discipline focus for marathon-only. Skip methodology for beginners (silently default to standard).
4. **Schedule: protected sessions + constraints** — "Any sessions to keep (group ride, masters swim)? Days you can't train?"
5. **Strength + health** — "Want strength sessions included? Anything injury/health-wise I should know?"
6. **Confirmation** — summarize all inputs, confirm before assembly.

### Template selection + assembly

1. Select closest matching template from BLOCK_TEMPLATES.md (distance + tier)
2. Adjust plan length if needed (stretch/compress base phase — taper and build are sacred)
3. Swap in phase variants if requested (see Composable Phase Variants in BLOCK_TEMPLATES.md)
4. Walk through template week-by-week:
   - Look up each workout name in WORKOUT_LIBRARY.md
   - Parameterize with athlete's zones (see Zone Resolution in WORKOUT_LIBRARY.md)
   - Scale volume per tier (short 75%, standard 100%, long 125%)
   - Slot sessions into available days, respecting constraints and protected sessions
5. For plans > 12 weeks: assemble and present one phase at a time

### Preview format

Present a scannable overview:
- Phase overview bar (Base → Build → Peak → Taper with week ranges)
- Week-by-week table: Wk | Phase | Mon-Sun sessions | Weekly hours
- Key sessions callout (3-5 landmark workouts with week numbers)
- Total hours breakdown by discipline

### Free customization

The athlete can modify anything before approval:
- Swap days, change workouts, adjust volume, remove sessions
- No restrictions — full creative control
- Re-display the preview after significant changes

### Approval + batch write

**Hard gate: no writes without explicit athlete approval.**

On approval, follow WORKOUT_PLANNING.md batch write guidance:
- Deterministic `uid` per event for idempotent writes
- Phase-sized batches with progress feedback
- Calendar conflict resolution (work around / merge / clear and replace)
- Create RACE_A event for race day if not already present
- One `add_or_update_event` call per discipline per day — never aggregate

### After writing

Tell the athlete: "Your training block is on your intervals.icu calendar. You can ask me about your fitness, weekly progress, or race readiness at any time — I'll automatically see your planned and completed sessions."

### Degradation

- **Empty MCP data (new athlete):** Fall back to asking all intake questions explicitly. Use RPE-based workout descriptions if no zone data available.
- **Sparse discipline data:** If <3 activities for a discipline, note: "I don't have much [swim/bike/run] data to work with. I'll use standard defaults — you can adjust after seeing the preview."
- **Single-sport request (marathon/half marathon):** Skip discipline split/focus questions. Use run-only templates. No swim/bike columns in preview.
```

- [ ] **Step 5: Verify the full COACH.md reads cleanly**

Read the entire file. Check:
- No contradictions with updated coaching principles
- New section follows same structure as existing sections (Triggers, Tools, Guardrail, Tool sequence, Output, Degradation)
- All template/library references match actual file names

- [ ] **Step 6: Commit**

```bash
git add skills/triathlon-training/COACH.md
git commit -m "feat: add Build Training Block command to COACH.md, update coaching principles"
```

---

## Chunk 4: Validation

### Task 11: End-to-End File Consistency Check

**Files:**
- Read: all 6 skill files

- [ ] **Step 1: Cross-reference all workout names**

Read BLOCK_TEMPLATES.md and collect every workout name referenced. Read WORKOUT_LIBRARY.md and collect every archetype heading. Every name in the templates must have a matching heading in the library. Flag any mismatches.

- [ ] **Step 2: Verify SKILL.md trigger table matches COACH.md sections**

Read SKILL.md "What I Can Help With" table. Every row must point to a section that exists in COACH.md. Verify the new "Build Training Block" row maps correctly.

- [ ] **Step 3: Check total file sizes**

Run `wc -c` on all 6 skill files. Total should be ~70-75KB per spec. If significantly larger, identify what can be trimmed.

```bash
wc -c skills/triathlon-training/*.md
```

- [ ] **Step 4: Fix any issues found in steps 1-3**

- [ ] **Step 5: Final commit**

```bash
git add skills/triathlon-training/
git commit -m "fix: resolve cross-file consistency issues in training block designer"
```

Only commit if changes were needed. Skip if steps 1-3 found no issues.

---

### Task 12: Manual Validation Scenarios

**No automated tests** — validation is conversational. These scenarios should be tested by loading the skill in Claude Code and invoking each one.

- [ ] **Step 1: Document validation checklist**

Create or update a validation note (not committed — personal testing reference):

1. **Help command** — say "what can you do" → verify training block is listed
2. **Basic block request** — "build me an Olympic tri plan for June 28" → verify intake flow starts, asks questions, doesn't skip to generation
3. **Marathon-only** — "build a marathon training plan" → verify swim/bike questions are skipped
4. **Short timeline guardrail** — "I need an Ironman plan, race is in 4 weeks" → verify refusal
5. **Preview + approval** — complete intake, verify preview table is shown, verify "no writes without approval" gate works
6. **Existing coaching commands** — after a block is written, verify "how's my fitness" and "weekly summary" still work normally and pick up planned events
7. **Last Activity redirect** — during activity analysis, ask for a training plan → verify redirect message

- [ ] **Step 2: Mark plan as complete**

The implementation is done when all 6 files are committed, cross-referenced, and consistent. Manual validation is the athlete's (user's) responsibility.
