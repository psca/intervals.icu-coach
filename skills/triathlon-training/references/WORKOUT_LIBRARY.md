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

- **Start with `get_athlete_profile`:** use current sport settings first for FTP, HR zones, pace zones, threshold pace, weight, and default discipline context.
- **Bike:** if profile FTP or zones are missing/stale, use `get_power_curves`; optionally use `search_activities` to find recent FTP or benchmark rides.
- **Run:** use profile threshold pace and pace zones first; if they are missing/stale, use `get_pace_curves` and optionally `search_activities` to find recent tempo/interval/race runs.
- **Swim:** use profile swim pace settings first; if they are missing/stale, use `get_pace_curves` and optionally `search_activities` to find recent CSS tests or interval sets.
- **HR fallback:** use profile HR zones first, then `get_hr_curves` only as a secondary fallback when pace/power data is absent.
- **Last fallback:** power/pace zones → HR zones (`Z2 HR`) → RPE-based text cues. If no zone data exists for any discipline, ask the athlete directly for recent test results. If unavailable, generate RPE-only plans with a note that workouts can be updated once zones are established.

---

## Swim

### Aerobic Endurance
- **When:** Base phase
- **Duration range:** 2000-3000m
- **Intensity:** Easy, Z2 effort

Warmup
- 200mtr 60% Pace
- 200mtr drill

Main Set 5x
- 200mtr 70-75% Pace
- 15s rest

Cooldown
- 200mtr 60% Pace

---

### Technique Drills
- **When:** All phases
- **Duration range:** 1500-2500m
- **Intensity:** Easy, technique focus

Warmup
- 200mtr 60% Pace

Drill Set 4x
- 50mtr drill
- 50mtr 70% Pace

Main Set 4x
- 100mtr 75% Pace
- 10s rest

Cooldown
- 200mtr 60% Pace

---

### CSS Intervals
- **When:** Base 2 / Build phase
- **Duration range:** 3000-4000m
- **Intensity:** Threshold pace

Warmup
- 400mtr 60% Pace

Main Set 8x
- 100mtr 95-100% Pace
- 20s rest

Pull Set 4x
- 100mtr 80% Pace paddles
- 10s rest

Cooldown
- 200mtr 60% Pace

---

### VO2max Swim
- **When:** Build / Peak phase
- **Duration range:** 2500-3500m
- **Intensity:** Above threshold

Warmup
- 400mtr 60% Pace

Main Set 12x
- 50mtr 105-110% Pace
- 20s rest

Recovery
- 200mtr 60% Pace

Kick Set 4x
- 50mtr kick hard
- 10s rest

Cooldown
- 200mtr 60% Pace

---

### Race Pace Set
- **When:** Peak / Taper phase
- **Duration range:** 2000-3000m
- **Intensity:** Race pace

Warmup
- 400mtr 60% Pace

Race Simulation 3x
- 300mtr 95-100% Pace
- 30s rest

Cooldown
- 200mtr 60% Pace

---

### Recovery Swim
- **When:** All phases (recovery weeks)
- **Duration range:** 1500-2000m
- **Intensity:** Very easy

Warmup
- 200mtr 55% Pace

Drill Set 4x
- 50mtr drill
- 50mtr 60% Pace

Easy Swim
- 400mtr 60% Pace

Cooldown
- 200mtr 55% Pace

---

### Open Water Simulation
- **When:** Build / Peak phase
- **Duration range:** 2000-3000m
- **Intensity:** Race effort, continuous

Warmup
- 400mtr 60% Pace

Main Set
- 1500mtr 80-85% Pace continuous — sight every 8 strokes, practice bilateral breathing

Cooldown
- 200mtr 55% Pace

---

## Bike

### Easy Endurance
- **When:** Base / All phases
- **Duration range:** 60-180min
- **Intensity:** Z2, 55-75% FTP

Warmup
- 10m ramp 40-60% 85rpm

Main Set
- 50m 60-70% 85-90rpm

Cooldown
- 10m ramp 65-40%

---

### Tempo
- **When:** Base 2 / Build phase
- **Duration range:** 75-120min
- **Intensity:** 76-87% FTP

Warmup
- 15m ramp 40-65% 85rpm

Main Set 3x
- 12m 76-87% 85-90rpm
- 5m 55% 85rpm

Cooldown
- 10m ramp 65-40%

---

### Sweet Spot Intervals
- **When:** Build phase
- **Duration range:** 60-90min
- **Intensity:** 88-93% FTP

Warmup
- 15m ramp 40-65% 85rpm

Main Set 3x
- 12m 88-93% 90rpm
- 5m 55% 85rpm

Cooldown
- 10m ramp 65-40%

---

### Threshold Intervals
- **When:** Build phase
- **Duration range:** 60-90min
- **Intensity:** 95-105% FTP

Warmup
- 15m ramp 40-65% 85rpm

Main Set 3x
- 10m 95-105% 90rpm
- 5m 55% 85rpm

Cooldown
- 10m ramp 65-40%

---

### VO2max Intervals
- **When:** Build / Peak phase
- **Duration range:** 60-75min
- **Intensity:** 106-120% FTP

Warmup
- 15m ramp 40-65% 85rpm

Main Set 5x
- 4m 106-120% 95-100rpm
- 4m 55% 85rpm

Cooldown
- 10m ramp 65-40%

---

### Race Pace Ride
- **When:** Peak phase
- **Duration range:** 90-180min
- **Intensity:** Race IF (distance-dependent)

Warmup
- 15m ramp 40-65% 85rpm

Main Set
- 60m 75-85% 85-90rpm

Cooldown
- 10m ramp 65-40%

---

### Recovery Spin
- **When:** All phases (recovery days)
- **Duration range:** 45-60min
- **Intensity:** <55% FTP

Easy Spin
- 45m 40-55% 85-90rpm

---

### Openers
- **When:** Taper / Race week
- **Duration range:** 45-60min
- **Intensity:** Easy with short bursts

Warmup
- 15m ramp 40-60% 85rpm

Easy Riding
- 15m 55% 85rpm

Activation 3x
- 30s 120% 100rpm
- 3m 50% 85rpm

Cooldown
- 10m 50% 85rpm

---

## Run

### Easy Aerobic
- **When:** Base / All phases
- **Duration range:** 30-90min
- **Intensity:** Z2 HR or 65-75% Pace

Easy Run
- 45m Z2 HR

---

### Easy + Strides
- **When:** Base / Build phase
- **Duration range:** 45-60min easy + strides
- **Intensity:** Z2 + short fast bursts

Easy Run
- 40m Z2 HR

Strides 6x
- 20s 100% Pace
- 60s freeride

---

### Threshold Cruise Intervals
- **When:** Build phase
- **Duration range:** 50-70min total
- **Intensity:** 90-95% Pace

Warmup
- 15m ramp 60-75% Pace

Main Set 3x
- 10m 90-95% Pace
- 3m 60% Pace

Cooldown
- 10m 65% Pace

---

### VO2max Intervals
- **When:** Build / Peak phase
- **Duration range:** 50-65min total
- **Intensity:** 98-105% Pace

Warmup
- 15m ramp 60-75% Pace

Main Set 5x
- 3m 98-105% Pace
- 3m 55% Pace

Cooldown
- 10m 60% Pace

---

### Long Run
- **When:** Base / Build phase
- **Duration range:** 75-150min
- **Intensity:** Z2 HR, steady effort

Long Run
- 90m Z2 HR

---

### Race Pace Run
- **When:** Peak phase
- **Duration range:** 45-75min
- **Intensity:** Target race pace

Warmup
- 15m ramp 60-75% Pace

Main Set 3x
- 10m 90-95% Pace
- 2m 60% Pace

Cooldown
- 10m 60% Pace

---

### Recovery Jog
- **When:** All phases (recovery days)
- **Duration range:** 30-40min
- **Intensity:** Very easy, Z1 HR

Recovery
- 30m Z1 HR

---

### Hill Repeats
- **When:** Build phase
- **Duration range:** 50-65min total
- **Intensity:** 5K effort uphill

Warmup
- 15m ramp 60-75% Pace

Hill Repeats 8x
- 90s 98-105% Pace uphill
- 2m freeride jog down

Cooldown
- 10m 60% Pace

---

## Strength

Strength workouts use plain-text descriptions (not intervals.icu structured syntax — intervals.icu doesn't parse strength sets). Set `type: "WeightTraining"` in the event payload.

### General Strength A
- **When:** Base phase
- **Duration range:** 45-60min
- **Intensity:** Moderate load, compound movements

Full-body compound session. 3 sets x 10-12 reps each:
- Back squat or goblet squat
- Romanian deadlift
- Walking lunge
- Overhead press
- Bent-over row
- Plank hold (3 x 45s)

Rest 60-90s between sets.

---

### General Strength B
- **When:** Base / Build phase
- **Duration range:** 45-60min
- **Intensity:** Moderate load, single-leg focus

Single-leg and core emphasis. 3 sets x 8-10 reps each:
- Bulgarian split squat
- Single-leg deadlift
- Step-ups (box height: knee)
- Single-arm dumbbell press
- Pallof press (3 x 10 each side)
- Side plank (3 x 30s each side)

Rest 60-90s between sets.

---

### Maintenance Strength
- **When:** Build phase
- **Duration range:** 30-40min
- **Intensity:** Reduced volume — maintain, don't build

Abbreviated session. 2 sets only of key movements:
- Back squat (2 x 8)
- Romanian deadlift (2 x 8)
- Bulgarian split squat (2 x 8 each)
- Plank hold (2 x 45s)

Rest 60s between sets. Goal is to preserve neuromuscular adaptations without adding fatigue.

---

## Brick Workouts

Brick sessions are NOT a single workout archetype. Per the no-aggregation rule, a brick is two separate events on the same day:
- A **Bike** event (e.g., Race Pace Ride, 60-90min)
- A **Run** event (e.g., Easy Aerobic or Race Pace Run, 15-30min) scheduled immediately after

When templates in BLOCK_TEMPLATES.md reference "Brick: Bike→Run", the implementer should create two events on that day using the named bike and run archetypes. Add a text cue in the run event description: "Off-the-bike run — start easy, settle into pace."
