# Correctness and Calibration Scenario Results

Scope: canonical coaching guidance at baseline `9c0965f` versus the feature working tree. These are synthetic agent applications and static arithmetic checks. No live MCP calls or athlete/calendar writes were performed. One baseline agent and a fresh post-change agent evaluated the core scenarios; this is a focused regression check, not a repeated statistical evaluation.

## Inputs and Observed Outcomes

| Case and supplied evidence | Baseline observation | Post-change observation | Acceptance |
|---|---|---|---|
| A: 70.3 eight weeks away, completion goal, estimated CTL swim/bike/run 25/72/58, ATL 40/90/70; appropriate recent sessions, stable performance, no symptoms. Post-change fixture explicitly supplies known course and advisory readiness MODERATE. | Literal race template yields NOT YET from today's negative TSB despite adequate benchmark CTL. | Supports preparation from supplied race-specific evidence, preserves today's MODERATE status separately, and does not predict race-day freshness. | Pass; post-change context additions exercise the new required fields, so this is not an identical-input comparison. |
| B: Olympic this weekend, no swim or open-water evidence, high bike/run CTL and positive TSB, HRV absent. | Agent withholds READY through data gates, but notes the template lacks an insufficient-evidence outcome. | INSUFFICIENT EVIDENCE; swim/skill evidence and missing recovery data are explicit. | Pass; adds a defined output for behavior the baseline could partly recover. |
| C: flat CTL four weeks, ATL above CTL 17 days, slightly falling HRV five days, one hilly high-VI ride; stable performance, athlete feels fine. | Avoids a diagnosis but flags the prescribed “overreached” and flat-CTL “detraining” labels. | Contextual recovery review; no overtraining diagnosis or detraining conclusion from load alone. | Pass. |
| D: unchanged CSS Intervals default. | Expands to 1800 m but identifies the contradictory 3000–4000 m range. | Default metadata and steps both give 1800 m; timed rests add 200 seconds, not metres. | Pass. |
| E: graded pace 6:00/km then 5:30/km, both HR 140; only two observations. | Literal pace/HR declines 8.33%, conflicting with improved performance. | Converts to speed: EF 1.190 then 1.299 m/beat, approximately 9.09% higher; two points do not establish a trend. | Pass. |
| F: seven wellness records spread across 14 days; server reports below-baseline streak seven and supplies median baseline. Post-change only. | Not run. | Shows dated observations and coverage; retains supplied field as a server estimate while flagging that seven observations do not prove consecutive calendar days. | Pass; new scenario, no baseline comparison. |

## Mechanical Checks

`python3 scripts/validate-workout-volumes.py` expands repetitions and checks eight explicitly declared default volumes: seven swims plus Race Pace Ride. Timed swim rests do not add distance. Parameterized ranges and unstructured strength descriptions are outside this validator's coverage.

The validator must reject a deliberately mismatched default and an unexpandable step; run these negative controls with temporary copies. Existing beginner and workout-library validators continue to check routing and safety text. A passing keyword check alone is not evidence that an agent follows the methodology.

## Remaining Work

- Reproducible race-template progression and feasibility checks.
- Dedicated adaptation workflow and common response semantics.
- Installed-version consistency and broader/repeated scenario evaluation.
- Live runtime verification of tool interpretation and scheduling, when appropriate.
