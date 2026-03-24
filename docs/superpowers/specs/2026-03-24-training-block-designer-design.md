# Training Block Designer — Design Spec

**Date:** 2026-03-24
**Status:** Draft
**Scope:** New feature for the triathlon-training skill

---

## Problem

The skill can analyze training and schedule individual workouts, but cannot generate multi-week periodized training blocks. Athletes who want a structured plan must go to a separate platform (Athletica, TrainerRoad, etc.) or build one manually. No open-source tool exists that generates triathlon-aware, per-discipline training blocks and writes them directly to intervals.icu.

## Goal

Add a training block designer to the existing skill that:

1. Generates evidence-based, multi-week periodized training plans
2. Uses a reference library of vetted workout archetypes — the LLM assembles, it does not invent
3. Writes structured workouts to intervals.icu using their native workout description syntax
4. Supports full customization before any calendar writes
5. Covers triathlon (Sprint through Ironman) and standalone running (Half/Full Marathon)

## Non-Goals

- Ongoing plan management (fire and forget — existing coaching commands handle analysis)
- CTL/ATL-driven scaling of templates (templates are standalone)
- Calendar modification after write (the LLM handles this naturally)
- Integration with external platforms (intervals.icu only)

---

## Supported Race Distances

| Distance | Short Plan | Standard Plan | Long Plan | Taper |
|----------|-----------|---------------|-----------|-------|
| Sprint tri | 8 wk | 10-12 wk | 14-16 wk | 3-5 days |
| Olympic tri | 12 wk | 14-16 wk | 18-20 wk | 1 week |
| 70.3 | 16 wk | 20 wk | 24 wk | 2 weeks |
| Ironman | 20 wk | 24 wk | 28-30 wk | 2-3 weeks |
| Half Marathon | 10-12 wk | 12-14 wk | 18 wk | 10-14 days |
| Marathon | 12 wk | 18 wk | 24 wk | 2-3 weeks |

Each distance has 3 volume tiers (short/standard/long) corresponding roughly to beginner/intermediate/advanced. Templates are fixed-length but the LLM can intelligently stretch or compress the base phase when the athlete's timeline doesn't match exactly. Taper and build phases are sacred — base is the flex zone.

**Sources:** Friel (Training Bible), Fitzgerald (80/20 Triathlon), Pfitzinger (Advanced Marathoning), Higdon, Hansons, TrainerRoad Plan Builder, TrainingPeaks marketplace consensus.

---

## Architecture

### Approach: Template + Rules, LLM Assembles

Templates define phase structures and weekly load patterns. A workout library defines each archetype with intervals.icu structured syntax. The LLM assembles specific weeks by selecting from the library and slotting into the template's structure, using periodization rules to make judgment calls.

This avoids both the rigidity of fully pre-built plans and the risk of LLM freestyle generation.

### File Structure

**New files:**

| File | Role | Est. Size |
|------|------|-----------|
| `BLOCK_TEMPLATES.md` | Phase modules + default assemblies per distance/tier | ~15-20KB |
| `WORKOUT_LIBRARY.md` | Canonical workout archetypes per discipline with intervals.icu syntax | ~12-15KB |

**Modified files:**

| File | Changes |
|------|---------|
| `SKILL.md` | New trigger row for "build a training plan" |
| `COACH.md` | New "Build Training Block" section with intake flow, preview format, approval gate |
| `WORKOUT_PLANNING.md` | Add intervals.icu workout description syntax reference |

**Unchanged:** `METRICS_REFERENCE.md`

**Total skill size after changes:** ~70-75KB across 6 files.

### Composable Phase Modules

Templates are modular at the phase level, not monolithic. This allows mixing methodology variants:

**Base phase variants:**
- Standard aerobic base (volume-focused)
- Polarized base (80/20 distribution)
- Reverse periodization base (intensity-first, experienced athletes)

**Build phase variants:**
- Threshold-focused build (classic Friel)
- VO2max-heavy build (Seiler-influenced)
- Race-specific build (high specificity early)

**Peak & Taper:** Standardized by distance, less variation needed.

Default templates are pre-assembled combinations (e.g., "Ironman Standard = Standard Base + Threshold Build + 2wk Peak + 3wk Taper"). The athlete can request different combinations during the intake ("I prefer polarized training" swaps in the polarized base module).

---

## User Flow

### Step 0: Auto-Pull MCP Data

Before asking any questions, the skill pulls:

| Data | MCP Call | Infers |
|------|----------|--------|
| Last 8 weeks of activities | `get_activities` | Current weekly hours, discipline split, consistency, experience proxy |
| Upcoming events | `get_events` | Existing calendar conflicts, possibly race date already entered |
| Athlete zones | from activity data | FTP, threshold pace, HR zones for workout parameterization |

### Step 1-10: Structured Intake

Each question has a sensible default. The athlete can skip through quickly or fine-tune.

1. **Race date + distance** — required, triggers everything
2. **Confirm weeks available** — "That's 16 weeks. I'll build a 16-week block." (minimum-weeks guardrail per distance)
3. **Confirm inferred fitness** — "You're averaging ~9 hrs/week. Sound right?" (falls back to asking if MCP data is sparse)
4. **Available hours/week** — contextualized: "You're doing 9 now. Want to keep that, build, or scale back?"
5. **Discipline focus** — "Your run is lagging. Focus there, or stay balanced?" (skip for marathon-only)
6. **Key sessions to protect** — "Any existing sessions to keep? (group ride, masters swim)"
7. **Scheduling constraints** — "Days you can't train or sport-specific day limits?"
8. **Include strength?** — Yes / No (default: no). If yes: 2x/week base → 1x/week build → drop in peak
9. **Injury/health notes** — "Anything I should know?"
10. **Methodology preference** — only for intermediate+, otherwise standard by default

### Step 11: Template Selection + Assembly

Based on intake answers:
1. Select the closest matching template (distance + tier)
2. Adjust plan length if athlete's timeline doesn't match (stretch/compress base phase)
3. Swap in phase variants if athlete requested (polarized, discipline focus, etc.)
4. Walk through template week-by-week, pull workout archetypes from library
5. Parameterize workouts with athlete's zones
6. Apply scheduling constraints (slot sessions into available days)
7. Respect protected sessions (build around group ride, masters swim, etc.)

### Step 12: Preview

Present a scannable overview:

```
## Olympic Triathlon — 14 Week Block
Race: June 28, 2026 | Level: Intermediate | ~9 hrs/week

### Phase Overview
Base (wk 1-5) → Build (wk 6-10) → Peak (wk 11-12) → Taper (wk 13-14)

### Week-by-Week Summary
| Wk | Phase | Mon | Tue | Wed | Thu | Fri | Sat | Sun | Hrs |
|----|-------|-----|-----|-----|-----|-----|-----|-----|-----|
| 1  | Base  | Rest | Swim: Technique | Run: Easy | Strength | Swim: Aerobic | Bike: Endurance | Run: Easy | 7.5 |
| 2  | Base  | Rest | Swim: Technique | Run: Easy + Strides | Strength | Swim: Aerobic | Bike: Endurance | Run: Easy | 8.0 |
| 3  | Recovery | Rest | Swim: Easy | Run: Easy | — | Swim: Easy | Bike: Easy | Rest | 5.0 |
| ... |

### Key Sessions
- Build wk 6: First threshold bike (3x10min at 95-105% FTP)
- Build wk 8: First VO2max run intervals (5x3min at vVO2max)
- Peak wk 11: Race-pace brick (40min bike + 20min run at race effort)
- Taper wk 14: Openers only — race week

Total planned hours: ~124 | Swim: 22 | Bike: 52 | Run: 42 | Strength: 8
```

### Step 13: Free Customization

The athlete can modify anything in conversation:
- Swap days ("move long ride to Sunday")
- Change workouts ("replace VO2max run with tempo")
- Adjust volume ("more swim in the build")
- Remove sessions
- No restrictions — full creative control

### Step 14: Approval + Batch Write

**Hard gate: no writes without explicit athlete approval.**

On approval, batch-write all events to intervals.icu via `add_or_update_event`:
- One event per session per day (never aggregate disciplines into a single event)
- Use intervals.icu structured workout description syntax in the `description` field
- Follow all WORKOUT_PLANNING.md pre-flight checks per event

### Step 15: Fire and Forget

The block lives on the intervals.icu calendar. The existing coaching commands (fitness status, weekly summary, race readiness) naturally pick up planned vs completed workouts. No special block awareness needed.

---

## Guardrails

| Guardrail | Rule |
|-----------|------|
| Minimum weeks | Sprint 6wk, Olympic 10wk, 70.3 14wk, Ironman 18wk, HM 8wk, Marathon 12wk — warn below these |
| Volume ramp | If requested hours > current hours × 1.3, add explicit ramp-up weeks and warn |
| Beginner + polarized | Silently default to standard periodization — beginners lack pacing discipline |
| Calendar conflicts | If existing events in target date range, surface: "You have X events. Clear, work around, or merge?" |
| Empty MCP data | Fall back to asking all questions explicitly — no broken inferences |
| Marathon-only path | Skip discipline split/focus questions for single-sport plans |
| Taper integrity | Taper phase is never compressed below evidence-based minimums per distance |
| Per-discipline events | One `add_or_update_event` call per discipline per day — never aggregate |

---

## BLOCK_TEMPLATES.md Structure

Each template entry defines a phase-by-phase weekly pattern referencing workout names from the library:

```markdown
## Olympic Triathlon — Standard (14 weeks)

Phases: Base (5wk) → Build (5wk) → Peak (2wk) → Taper (2wk)
Mesocycle: 3:1 (2 load weeks + 1 recovery)
Weekly hours: 8-10hr (tier: intermediate)

| Week | Phase | Swim | Bike | Run | Strength | Notes |
|------|-------|------|------|-----|----------|-------|
| 1 | Base 1 | Aerobic Endurance, Technique Drills | Easy Endurance | Easy Aerobic | General Strength A x2 | Build consistency |
| 2 | Base 1 | Aerobic Endurance, Technique Drills | Easy Endurance, Tempo | Easy Aerobic, Strides | General Strength A x2 | +10% volume |
| 3 | Base 1 (recovery) | Technique Drills | Easy Endurance | Easy Aerobic | General Strength A x1 | -40% volume |
| ... |
```

Phase modules are composable — the LLM can swap base/build variants based on athlete methodology preference.

---

## WORKOUT_LIBRARY.md Structure

Each archetype includes metadata for selection and the full intervals.icu syntax for writing:

```markdown
## Bike

### Sweet Spot Intervals
- **When:** Build phase
- **Duration range:** 60-90min total
- **Intensity:** 88-93% FTP

Warmup
- 15m ramp 40-65% 85rpm

Main Set 3x
- 12m 88-93% 90rpm
- 5m 55% 85rpm

Cooldown
- 10m ramp 65-40%

---

### VO2max Intervals
- **When:** Build/Peak phase
- **Duration range:** 60-75min total
- **Intensity:** 106-120% FTP
...
```

Swim and run use pace targets:

```markdown
### CSS Intervals
- **When:** Base 2 / Build phase
- **Duration range:** 3000-4000m total

Warmup
- 400mtr 60% Pace

Main Set 8x
- 100mtr 95-100% Pace
- 20s rest

Cooldown
- 200mtr 60% Pace
```

The LLM scales sets (e.g., 6x100 for short tier, 10x100 for long tier) based on the template's load target for that week.

---

## WORKOUT_PLANNING.md Updates

Add the full intervals.icu workout description syntax reference:

- Step format: `- [cue] [duration/distance] [target] [cadence]`
- Duration: `30s`, `10m`, `1h`, `5'30"`
- Distance: `500mtr`, `2km`, `1mi`, `100y`
- Power: `75%`, `88-93%`, `Z2`, `220w`
- HR: `70% HR`, `Z2 HR`, `90-95% LTHR`
- Pace: `5:00/km Pace`, `3:00/100m Pace`, `Z2 Pace`
- Cadence: `90rpm`, `85-95rpm`
- Ramps: `ramp 50%-75%`
- Repeats: `4x` header before step block (no nesting)
- Section headers: lines without `- ` prefix

**Source:** [R2Tom's Quick Guide](https://forum.intervals.icu/t/workout-builder-syntax-quick-guide/123701), [Main Workout Builder thread](https://forum.intervals.icu/t/workout-builder/1163)

---

## Sports Science Foundation

All templates and rules grounded in freely available research:

| Principle | Source | Access |
|-----------|--------|--------|
| Polarized intensity distribution (80/20) | Stoggl & Sperlich 2014, Seiler 2010 | Free (PMC3912323) |
| Taper: reduce volume, maintain intensity | Bosquet et al. 2007, Mujika & Padilla 2003 | Free PDF available |
| Taper performance gain ~2-3% | Bosquet et al. 2007 | Free summary |
| Triathlon-specific taper | Mujika 2011, J Human Sport & Exercise | Free |
| Tri load distribution (~15-20% swim, 40-50% bike, 30-35% run) | Etxebarria, Mujika & Pyne 2019 | Free (PMC6571715) |
| ACWR guardrails (avoid >10% weekly spikes) | Gabbett 2016 | Free PDF |
| Periodization phases (base/build/peak/taper) | Friel, Bompa — general coaching knowledge | Not copyrightable |
| Workout archetypes (sweet spot, threshold, VO2max, etc.) | Generic coaching terminology | Not copyrightable |
| CTL/ATL/TSB math (Banister's model) | Banister 1975; implemented in GoldenCheetah GPL v2 | Free |

**Licensing note:** We do not reproduce specific plans from copyrighted books. Templates encode general periodization principles and intensity distributions from published sports science. The term "80/20" as a brand is avoided (use "polarized" instead).

---

## Competitive Landscape

No existing tool does LLM + MCP + intervals.icu + triathlon per-discipline periodization:

- **Athletica.ai** — has intervals.icu integration but is a standalone platform, not conversational
- **LeCoach.app** — LLM + intervals.icu but cycling-only, beta
- **DunMove** — algorithmic, cycling-only
- **TrainerRoad/TriDot** — proprietary platforms, no intervals.icu integration

This skill meets athletes where they already train and plan, requires no additional subscription (bring your own Claude), and is open-source.
