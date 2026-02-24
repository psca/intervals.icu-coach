# Metrics Reference — Triathlon Training Insights

All thresholds and benchmarks used during analysis. Apply these consistently across every insight.

---

## PMC (Performance Management Chart)

**Critical rule for triathletes: always compute per-discipline, never aggregate.**
A triathlete with CTL 80 on the bike and CTL 20 on the run is undertrained for running, even if aggregate looks fine.

### CTL Ramp Rate (per discipline)
| Rate (pts/week) | Assessment |
|---|---|
| 4–6 | Healthy base building |
| 6–8 | Acceptable — monitor recovery signals |
| >8 | Elevated injury/overtraining risk — flag immediately |
| <2 | Detraining signal if sustained >3 weeks |

### TSB (Training Stress Balance) by Race Distance
| Race Distance | Target TSB at Race Day |
|---|---|
| Sprint | +10 to +25 |
| Olympic | +5 to +20 |
| 70.3 (Half Ironman) | +5 to +15 |
| 140.6 (Full Ironman) | +5 to +10 |

**Note:** Higher TSB = more freshness. Lower TSB = more fatigue. Negative TSB is normal during training blocks but should trend toward target in the 10–14 days before race.

### ATL/CTL Relationship
- ATL > CTL sustained for >2 weeks = overreached — flag
- ATL spike (single week) = normal hard training week — monitor
- TSB < -20 = significant fatigue burden — note in analysis

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
- EF = Normalized Graded Pace / Average Heart Rate
- Rising trend = aerobic adaptation — celebrate
- Declining trend = fatigue signal or fitness plateau
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

## Overtraining Cascade

Check in this order — each level confirmed makes the case stronger:

1. **HRV downtrend ≥5 consecutive days** — most reliable single indicator
2. **Resting HR elevated +7–10 bpm above baseline ≥5 days** — strong signal, especially combined with HRV
3. **TSB < -20 with stalled CTL** — fatigue without adaptation
4. **Aerobic decoupling deteriorating vs. prior 4-week average** — efficiency regression under same load
5. **VI spike on normally smooth rides (>1.10 habitually)** — neuromuscular fatigue indicator

**Diagnosis threshold:**
- 1 signal = "watch closely"
- 2 signals = "flag for recovery week consideration"
- 3+ signals = "strong overtraining signal — recommend recovery action"

Always surface which signals are present and which are absent. Don't diagnose from a single data point.

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
