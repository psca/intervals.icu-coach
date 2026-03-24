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
