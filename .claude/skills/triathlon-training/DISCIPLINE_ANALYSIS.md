# Discipline Analysis — Triathlon Training Insights

Sport-specific guidance for session breakdowns. Use this alongside METRICS_REFERENCE.md thresholds and COACH_PERSONA.md style.

---

## Cycling Session Analysis

### Tools to Call
1. `get_activity_details` — NP, IF, average power, average HR, duration, distance
2. `get_activity_intervals` — if structured workout (intervals present)
3. `get_activity_streams` — only if computing aerobic decoupling manually (high token cost; check if decoupling is already in details response first)

### Analysis Sequence

**1. Assess session quality via NP + IF**
- What was the intended session type? (ask or infer from name/structure)
- Is IF consistent with that type? (see IF table in METRICS_REFERENCE.md)
- A "Z2 long ride" with IF 0.85+ = pacing issue or mislabeled session

**2. Variability Index (NP / Avg Power)**
- VI target: 1.00–1.05 on flat/rolling terrain
- Always contextualize with course profile — mountain stage VI of 1.12 is fine; flat TT VI of 1.12 is a problem
- If >1.08 on a flat course, flag as pacing consistency concern

**3. Aerobic Decoupling (efforts ≥90 min, Z1–Z2)**
- Flag if >10% — see METRICS_REFERENCE.md for thresholds
- Compare to prior 3–4 similar efforts for trend
- Note conditions: heat and humidity inflate decoupling even in fit athletes

**4. Power Zone Distribution**
- What percentage of time was spent in each zone?
- For base phase: flag if >30% of TSS from Z3+
- For build phase: higher Z3–Z4 is expected — assess appropriateness for training block

**5. Efficiency Factor Trend**
- EF = NP / Avg HR
- Compare to 3 most recent similar efforts (same type, similar duration)
- Rising = aerobic fitness gain; flat = stable; declining = flag

### What to Highlight in Output
- Lead with: "This was a [type] effort at IF [X], which [aligns with / doesn't match] [intended session type]"
- VI interpretation tied to course type
- Whether aerobic decoupling suggests the effort was aerobically appropriate
- EF comparison to recent history

---

## Running Session Analysis

### Tools to Call
1. `get_activity_details` — pace, average HR, cadence, elevation, distance, duration
2. `get_activity_intervals` — if structured (track workout, tempo intervals)
3. `get_activity_streams` — for decoupling analysis if not in details response

### Analysis Sequence

**1. Normalized Graded Pace (NGP) + Average HR → EF**
- EF = NGP / Avg HR (higher = more efficient)
- Compare to 3 most recent similar efforts
- NGP accounts for elevation, enabling fair comparison across hilly and flat courses

**2. Aerobic Decoupling (efforts ≥60 min, Z1–Z2)**
- More sensitive to heat than cycling — always note temperature if available
- <5% = aerobically sound; 5–10% = monitor; >10% = flag
- Trend across last 3–4 long runs matters more than a single session value

**3. Cadence Consistency**
- Compare early-session vs. late-session cadence (first 20% vs. last 20%)
- Drop >5 spm = fatigue signal
- Consistent cadence at declining pace = controlled fatigue management (good); erratic cadence = form breakdown

**4. EF vs. Prior Similar Efforts**
- Only compare same distance range + similar conditions (flat road vs. flat road, trail vs. trail)
- Rising EF over 4+ week window = aerobic adaptation
- Declining EF = flag — possible causes: accumulated fatigue, heat, illness, overtraining

**5. Interval Analysis (structured workouts)**
- Use `get_activity_intervals` for track/tempo sessions
- Flag intervals where HR exceeded target zone significantly (pacing errors)
- Rest interval HR recovery rate: faster recovery = better fitness
- Compare interval times to prior similar sessions

### What to Highlight in Output
- Lead with: "This [easy/tempo/long] run covered [distance] at average HR [X] — here's what the data shows..."
- Whether decoupling suggests the pace was aerobically appropriate for the distance
- EF trend direction (rising/flat/declining) with recent context
- Flag fatigue signals (cadence drops, HR drift) without over-alarming on single sessions

---

## Swimming Session Analysis

### Tools to Call
1. `get_activity_details` — distance, duration, average pace, average HR (if available), average cadence (stroke rate)
2. `get_activity_intervals` — for structured sets (critical for swim analysis — intervals are the workout)

### Analysis Sequence

**1. SWOLF Trend**
- SWOLF = stroke count per length + time per length
- Target ranges: 35–45 (25m pool), low 70s (50m pool)
- Improving SWOLF at same pace = technique + fitness gain
- Declining SWOLF = fatigue or form breakdown
- SWOLF improving while pace slows = athlete is swimming slower more efficiently (fatigue signal, not progress)

**2. Pace per 100m vs. Historical**
- Track trend relative to effort level, not absolute
- Faster pace at same perceived effort (or HR if available) = fitness adaptation
- Slower pace with same stroke count = power/fitness decline

**3. Interval Hit/Miss (structured sessions)**
- `get_activity_intervals` is essential for structured swim sets
- Were interval targets met in first half vs. second half of session?
- Drop-off in later intervals = aerobic or muscular fatigue
- Consistent performance across all reps = aerobic capacity sufficient for the set

**4. Stroke Rate Consistency**
- Use cadence field (strokes per minute) from `get_activity_details`
- Inconsistency across intervals or session halves = fatigue indicator
- Compare to athlete's historical stroke rate baseline

**5. Volume Context**
- Swimming requires more frequent sessions to maintain technique than bike or run
- Flag if <2 swims per week for athletes targeting Olympic or longer
- SWOLF degrades quickly with layoffs — note if returning from a swim break

### Swimming-Specific Limitations
- Heart rate data is less reliable for swimming (chest strap issues underwater)
- GPS data unreliable in pool — rely on laps/intervals data, not distance from GPS
- Wearable HR in pool: accept with more uncertainty than bike/run

### What to Highlight in Output
- Lead with: "This [easy/structured] swim covered [distance] in [time] — SWOLF trend and interval data tell the story here..."
- SWOLF direction (improving/stable/declining) with prior context
- For structured sessions: interval consistency across the set
- Flag if swim volume is low relative to race distance targets

---

## Cross-Discipline Patterns

Watch for these cross-sport signals that single-discipline analysis misses:

**Cumulative fatigue signal:**
- Run EF declining + bike VI spiking + SWOLF degrading simultaneously across 2–3 weeks = systemic fatigue (not just one sport)
- This warrants a stronger overtraining flag than any single metric alone

**Discipline imbalance for race distance:**
- Use race-distance priority table from METRICS_REFERENCE.md
- If an athlete is 8 weeks from a 70.3 and bike CTL >> run CTL: flag the imbalance
- Don't just report it — explain why it matters for that specific race distance

**Off-bike run quality:**
- For athletes targeting Olympic+ distances, brick workout data is valuable
- If available, compare run EF in standalone runs vs. run legs following bike sessions
- Declining off-bike EF = specific brick fitness gap

**Recovery asymmetry:**
- Some athletes recover faster from swim than bike, or bike than run
- If HRV/resting HR data available alongside activity types: note which disciplines correlate with worse recovery signals
