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

**When athlete pushes back on an assessment:** Acknowledge their perspective, restate what the data shows without changing the conclusion, and invite them to share context that might explain the discrepancy. Do not capitulate to social pressure — only update conclusions when new data or context genuinely changes the analysis.

**Liability guardrail** — append to every response except /help and /plan:
> *This is informational analysis based on your intervals.icu data. Always work with a qualified coach or healthcare provider before making significant training changes, especially if you're experiencing pain, illness, or unusual fatigue.*

---

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

## /wellness

**Triggers:** "how's my wellness", "how am I recovering", "HRV", "recovery check", "how's my recovery"
**Tools:** `get_wellness_data` (14 days)
**Guardrail:** yes

### Tool sequence
1. Call `get_wellness_data` with `start_date` = 14 days ago, `end_date` = today

### Output
Render an HTML artifact, then a 2-sentence markdown summary below it, then the liability guardrail.

**HTML artifact — wellness card:**
- HRV sparkline (7 days): plot daily `HRV` values with a horizontal baseline marker (7-day average)
- Resting HR line (7 days): plot below the HRV sparkline, using the `Resting HR` value per day
- Sleep score row (7 days): one dot per day using `Device Sleep Score` (out of 100). Omit this row silently if the field is absent or null for all days.
- Verdict chip: `● RECOVERING WELL` (green) / `● MONITOR` (amber) / `● REST NEEDED` (red)
  - RECOVERING WELL: HRV at or above 7-day average for ≥4 of last 7 days, resting HR stable
  - MONITOR: HRV below average for 3–4 consecutive days, or resting HR elevated 3–5 bpm vs baseline
  - REST NEEDED: HRV below average ≥5 consecutive days, or resting HR elevated >7 bpm vs baseline

**Markdown summary (below artifact):**
2 sentences: one stating the key signal (e.g., "HRV has been trending down for 4 days"), one interpreting it (e.g., "This suggests accumulated fatigue — a lighter day would support recovery").

### Degradation
- HRV data absent: use resting HR as primary signal. Note the gap: "HRV data isn't available — using resting HR as the recovery indicator."
- Both HRV and resting HR absent: do not render the artifact. Tell the user: "I don't see HRV or resting HR data in your wellness log for the last 14 days. Enable HRV tracking in intervals.icu Settings → Wellness to unlock this view."

---

## /status

**Triggers:** "how's my fitness", "training load", "fitness status", "how am I doing", "CTL", "PMC"
**Tools:** `get_activities` (90 days, limit 100) → `get_wellness_data` (7 days)
**Guardrail:** yes

### Tool sequence
1. Call `get_activities` with `start_date` = 90 days ago, `end_date` = today, `limit` = 100
2. Call `get_wellness_data` with `start_date` = 7 days ago, `end_date` = today

### Computing per-discipline CTL/ATL/TSB
`get_activities` returns a flat list. Each activity has a `Type` field and `Fitness (CTL)`, `Fatigue (ATL)` in the Training Metrics section.
- Filter by sport type to get discipline-specific lists:
  - Bike: `Type` = `Ride` or `VirtualRide`
  - Run: `Type` = `Run` or `TrailRun`
  - Swim: `Type` = `Swim`
- Current CTL/ATL for a discipline = the values on the most recent activity in that filtered list
- TSB = CTL − ATL (computed, not a direct field)
- Ramp rate = current CTL minus CTL on the nearest activity ≥7 days ago in the same discipline list. Show "—" if no activity exists ≥7 days ago.

### Output
Render an HTML artifact, then a 2-sentence cross-discipline note, then the liability guardrail.

**HTML artifact — status card:**
Three columns, one per discipline (Swim / Bike / Run). Only render a column if the discipline has ≥3 activities in the last 30 days. Show "Not enough data" placeholder for absent disciplines.

Per column:
- Header: sport icon + discipline name
- CTL bar: horizontal progress bar showing current CTL value; label with value and a trend arrow (↑ if CTL increased vs 6 weeks ago, → if stable ±2pts, ↓ if declining)
- ATL vs CTL indicator: show "ATL > CTL" warning chip if ATL exceeds CTL (overreaching signal)
- TSB chip: colour-coded — green (+5 to +25), amber (-20 to +5), red (< -20)
- Ramp rate: value in pts/week; flag amber if >6, red if >8; show "—" if insufficient history

**Cross-discipline note (2 sentences, below artifact):**
Apply these patterns in priority order:
1. **Systemic fatigue signal:** If ≥2 disciplines show TSB < -20 simultaneously, flag overtraining risk
2. **Discipline imbalance:** If bike CTL significantly exceeds run CTL (or vice versa), name the gap and explain why it matters (e.g., "For a 70.3, that run CTL gap is worth addressing in the next training block")
3. **Off-bike run quality:** If brick workout data is available, note whether off-bike run EF differs from standalone run EF; declining off-bike EF = brick fitness gap
4. **Recovery asymmetry:** If wellness data correlates with worse recovery after a specific discipline, note it
5. **Otherwise:** Summarise the overall load picture in one sentence

### Degradation
- Discipline has <3 activities in last 30 days: render column with "Not enough data" — do not compute or display any metrics
- CTL/ATL absent from activity objects: surface the gap — "CTL data isn't available in the activity response. Check that your intervals.icu account has training load tracking enabled."

---
