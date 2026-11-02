# Metrics Reference — Triathlon Training Insights

All thresholds and benchmarks used during analysis. Apply these consistently across every insight.

---

## PMC (Performance Management Chart)

**Critical rule for triathletes:** use only clearly labelled server-estimated discipline CTL/ATL/TSB. Never derive discipline values from activity-level Intervals aggregate CTL/ATL; show aggregate load separately when useful.
A triathlete can have materially different discipline load states even when aggregate load looks fine, so assess each sport from the server estimate and its own trend evidence.

### Load and recovery interpretation

- CTL and ATL describe modeled training load. A flat CTL or low ramp rate does not establish detraining; a positive ramp does not establish fitness gain.
- Review changes relative to that discipline’s recent load, training phase, data coverage, symptoms, and comparable performance. Abrupt changes warrant context rather than an automatic injury-risk label.
- ATL above CTL and negative TSB can occur during planned overload. Neither their duration nor a universal numerical cutoff diagnoses overreaching.
- Positive TSB can follow reduced training. Check `training_state` and recent history before describing freshness.
- There is no universal race-day TSB target in this skill. Discuss current modeled load separately from preparation, and use the athlete’s own prior taper/race response when available. Do not forecast race-day freshness from today’s TSB.

---

## Aerobic Decoupling (Pw:HR or Pa:HR)

Measures cardiac drift during aerobic efforts. Higher decoupling = less aerobic efficiency.

| Decoupling % | Assessment |
|---|---|
| <5% | Aerobically sound — good base fitness |
| 5–10% | Yellow flag — monitor trend; may indicate heat, fatigue, or base gap |
| >10% | Red flag — flag for fueling gap, recovery deficit, or aerobic base issue |

**Application rules:**
- Only apply to efforts ≥60 min (run) or ≥90 min (bike) at Z1–Z2 effort
- A single session >10% is not a pattern — look for trend across last 3–4 similar efforts
- Compare to prior 4-week average to assess direction

---

## Cycling Metrics

### Variability Index (VI = NP / Avg Power)
| VI | Assessment |
|---|---|
| 1.00–1.05 | Smooth, controlled pacing |
| 1.05–1.08 | Slightly variable — acceptable for hilly terrain |
| 1.08–1.10 | Pacing concern — evaluate course context |
| >1.10 | Matches burned — flag as pacing issue (especially on flat courses) |

### Intensity Factor (IF = NP / FTP)
| IF | Typical Session Type |
|---|---|
| <0.75 | Recovery / easy endurance |
| 0.75–0.85 | Aerobic endurance (Z2 long ride) |
| 0.85–0.95 | Tempo / sweet spot |
| 0.95–1.05 | Threshold work |
| >1.05 | VO2max / race effort |

Use IF to assess whether session intensity matched the intended training phase.

### Efficiency Factor (EF — Cycling)
- EF = Normalized Power / Average Heart Rate
- Track week-over-week trend: rising EF = aerobic fitness gain
- Declining EF over 3+ weeks at same effort = flag for recovery or fitness regression
- Compare only sessions of similar type, duration, and conditions

### Power Zone Distribution
For base-building phases, flag if >30% of weekly TSS comes from Z3 or higher. "Polarized" training should show majority Z1–Z2 + some Z4–Z5, minimal Z3.

---

## Running Metrics

### Efficiency Factor (EF — Running)
- EF = normalized graded **speed** / average HR. Convert pace to speed first: `speed_m_per_min = 1000 / pace_min_per_km`; then `EF = speed_m_per_min / HR_bpm`. Never divide min/km or sec/km directly by HR.
- Example: at 140 bpm, 6:00/km gives EF 1.190 m/beat and 5:30/km gives 1.299 m/beat. Faster speed at unchanged HR increases EF. Compare only identical units and compatible conditions.
- A rising trend in comparable aerobic sessions supports improved efficiency; preserve tool confidence and caveats.
- A declining trend prompts review of conditions, sensor quality, effort, and recovery; it does not establish the cause.
- Compare only efforts of similar distance, course profile, and weather

### Cadence
- Target: 170–180 spm for most runners
- Cadence drops during a run = fatigue signal
- Compare within-session (early vs. late cadence) — drops >5 spm = flag

### Aerobic Decoupling (Running)
- Apply only to efforts ≥60 min at Z2 effort
- Thresholds same as above (<5% / 5–10% / >10%)
- More sensitive to heat than cycling — note conditions before flagging

---

## Swimming Metrics

### SWOLF (Stroke count + Time per length)
| Pool Length | Typical SWOLF Range |
|---|---|
| 25m pool | 35–45 |
| 50m pool | low 70s |

**Trend interpretation:**
- Improving SWOLF at same pace = technique + fitness gain — celebrate
- Declining SWOLF at same pace = fatigue or form breakdown — flag
- SWOLF improving with slowing pace = fatigue (swimming slower but more efficiently — not a win)

### Pace per 100m
- Track as trend relative to effort level (not absolute)
- Faster pace at same heart rate = fitness adaptation

### Stroke Rate
- Inconsistent stroke rate within a session = fatigue signal
- Compare to athlete's historical baseline

---

## Recovery Concerns

Review wellness changes, subjective fatigue/soreness, illness/injury context, training load, and sustained comparable performance changes together. Use `get_training_readiness` structured status, confidence, and caveats for its advisory assessment; preserve the result rather than replacing it with a signal count.

- HRV changes depend on individual baseline, measurement conditions, and coverage. Do not call HRV the single most reliable diagnostic indicator.
- Elevated resting HR or worsening comparable aerobic efficiency can justify a recovery conversation; neither establishes the cause.
- High VI may reflect terrain or workout structure. It does not establish neuromuscular fatigue.
- Stable CTL does not demonstrate a failure to adapt. Look for performance and athlete-reported evidence.
- Describe persistent concerning patterns as recovery concerns requiring context. Do not diagnose overtraining syndrome, or define it by counting flags. Persistent unexplained underperformance or symptoms warrant qualified assessment.
- State present, absent, and missing signals. Ask about subjective context when signals conflict; a reassuring metric does not erase reported symptoms.

**Evidence:** The [ECSS/ACSM consensus](https://pubmed.ncbi.nlm.nih.gov/23247672/) distinguishes functional overload, nonfunctional overreaching, and overtraining syndrome through clinical course and exclusion of other explanations. The [TrainingPeaks running EF definition](https://www.trainingpeaks.com/blog/the-efficiency-factor-in-running/) converts graded pace to speed before dividing by HR. These sources do not validate universal CTL race-completion cutoffs.

---

## Vanity Metrics — Handle with Care

These are visible in intervals.icu and athletes fixate on them. Don't over-emphasize:

- **Total weekly TSS without CTL context** — 800 TSS means nothing without knowing CTL trend
- **Max power / max pace** — outliers, not fitness indicators
- **Workout streaks** — consistency is good; streaks mask recovery needs
- **Strava segments / KOMs** — irrelevant to training quality

If an athlete cites these, acknowledge them briefly then redirect to meaningful metrics.

---

## Race-Distance Discipline Priorities

Best predictors of race performance (where to focus analysis):

| Distance | Primary limiter | Secondary |
|---|---|---|
| Sprint | Cycling power | Run off-bike speed |
| Olympic | Swimming efficiency | Cycling threshold |
| 70.3 (Half) | Cycling aerobic base | Running durability |
| 140.6 (Full) | Running aerobic base | Cycling efficiency |

Use this to weight which discipline's metrics to emphasize in race readiness analysis.

---

## Weather Context Thresholds

Apply these when weather data is available from `GET /api/v1/activity/{id}/weather-summary`. Conditions explain anomalies — don't flag readings as problems if conditions account for them.

**Primary heat signal: `average_feels_like`** — use this instead of raw temperature. It already accounts for humidity and wind, making it a single number for "how hard is the body working to thermoregulate."

### Feels-Like Temperature

| Range | Effect | Coaching action |
|---|---|---|
| >28°C | Cardiac drift elevated; decoupling inflated | Adjust decoupling flag threshold by +2–3%; note heat *before* flagging |
| 20–28°C | Moderate; normal thresholds apply | Standard interpretation |
| <5°C | HR suppression common; EF may be artificially high | Flag EF comparisons as less reliable; compare only to other cold-weather efforts |

Running-specific: flag decoupling at `average_feels_like > 25°C` (lower threshold than cycling due to higher heat sensitivity).

### Wind (Route-Aware)

| Condition | Effect | Coaching action |
|---|---|---|
| `headwind_percent > 40%` | Significant aerodynamic load on exposed route | Contextualize elevated power, IF, and VI — not a pacing problem |
| `tailwind_percent > 60%` | Power/pace may be understated vs. typical efforts | Note when comparing EF or IF to prior sessions |
| `average_wind_speed > 25 km/h` | Even with mixed direction, total wind load is high | Note in output regardless of headwind/tailwind split |

`prevailing_wind_deg` → convert to cardinal for athlete-facing output (0°=N, 90°=E, 180°=S, 270°=W).

### Precipitation

| Condition | Effect | Coaching action |
|---|---|---|
| `max_rain > 0` or `max_showers > 0` | Conservative pacing, lower HR, potential VI anomalies | Actively mention; do not flag these anomalies as fitness issues |
| `max_snow > 0` | Dramatically affects pace and HR reliability | Flag explicitly; most metrics non-comparable to non-winter efforts |

### Application Rule

Weather thresholds are contextualizers, not overrides. If feels-like explains 3% of a 14% decoupling reading, the remaining 11% still warrants investigation. Always apply standard thresholds first, then adjust with weather context.
