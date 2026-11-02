# Coaching Methodology Exploration

Status: exploration brief; proposed behavior requires design before implementation.
Baseline: `a183b92`, pushed to `origin/main` before creating `feat/coaching-methodology`.

## Purpose

Improve the skill's correctness, calibration, and usefulness throughout a training block. Make prescriptions and conclusions as verifiable as calendar writes. Preserve discipline separation, evidence provenance, missing-data handling, and preview/approval gates.

## Findings and Proposed Work

### 1. Workout and metric correctness

Observed in the canonical references:

- CSS Intervals advertises 3000–4000 m; the written steps total 1800 m.
- Aerobic Endurance advertises 2000–3000 m; the written steps total 1600 m.
- Race Pace Ride advertises 90–180 minutes; the written steps total 85 minutes.
- Easy + Strides mixes HR and pace targets despite the planning guide's single-target rule. Mixed targets are supported by Intervals; the conflict is between our instructions.
- Running efficiency-factor guidance uses “pace / HR” without requiring conversion to speed. Dividing time-per-distance by HR would reverse the intended direction.

Explore explicit archetype parameters and totals derived from the fully expanded steps. Decide whether advertised ranges describe a parameterized family or the written default, and identify each default. Preserve intentional mixed-target exceptions only when documented.

Acceptance examples:

- Preview, authored steps, and reported distance/duration agree for the standard workout and scaled variants.
- Increasing running speed at unchanged HR improves EF; pace units cannot invert the verdict.
- Every archetype follows the chosen target policy or names its exception.

### 2. Calibration of recovery and race verdicts

The metrics reference uses categorical statements about ramp rate, ATL/CTL, and an “overtraining” signal count. Those statements conflict with the newer separation of load from fitness and can overstate what the available evidence establishes.

Wellness uses a seven-day average as both the displayed baseline and the reference for consecutive low days. Define baseline period, minimum coverage, measurement consistency, and missing-day behavior explicitly; reconcile wellness with the compact readiness assessment.

Race readiness currently asks for distance but does not require a race date or goal. Approximate CTL benchmarks determine READY/CLOSE/NOT YET, while sparse evidence has no explicit overall verdict. TSB chip bands also differ from the distance-specific target ranges in the metrics reference.

Explore advisory fatigue language, individualized context, and distinct race-preparation versus current-freshness assessments. Define how conflicting or insufficient evidence affects a verdict. Do not invent replacement physiological cutoffs during implementation.

Acceptance examples:

- An athlete racing in eight weeks is not assessed as if racing today.
- Missing swim evidence produces an explicit limitation instead of a confident overall READY verdict.
- A load increase alone cannot establish improved fitness, and flat CTL cannot establish detraining.
- Conflicting wellness and readiness evidence remains visible and has a consistent resolution rule.

### 3. Reproducible progression and feasibility

Race templates largely list workout names and volume-change notes. They do not consistently identify the session parameters that change or reconcile expanded workouts against the athlete's available hours. Methodology “modules” are prose descriptions; 80/20 lacks an explicit zone model and denominator.

Explore weekly discipline targets, session-level progression parameters, recovery constraints, and a final feasibility check. Distinguish plan length from athlete capacity when selecting volume. Treat methodology variants as preferences until their substitutions and accounting rules are defined.

Acceptance examples:

- Two assemblies from the same confirmed intake produce explainable, comparable progression.
- Expanded sessions fit the confirmed weekly hours and available days.
- A methodology variant identifies what changes, what stays fixed, and how distribution is measured.

### 4. Adaptation during a block

Weekly reporting identifies missed sessions, but the skill has no dedicated workflow for revising an existing block. Beginner repeat-week guidance is a useful starting point.

Explore a review flow: compare planned/completed work by discipline, collect relevant athlete context, propose retain/progress/reduce changes, preview affected events, obtain approval, and verify the result. Include the next review date or trigger. Avoid automatically compensating for missed volume.

Acceptance examples:

- Two missed sessions lead to a reasoned proposal rather than automatic catch-up scheduling.
- Reduced availability produces a feasible revision with protected priorities explained.
- Changed thresholds prompt a review of future workout targets, with edits previewed before writes.
- Partial writes do not produce an unconditional success message.

### 5. Response structure and scenario evaluation

Current templates specify cards and sentence counts, but there is no common decision structure. Explore a shared semantic core: assessment, supporting evidence, uncertainty, next action, and reassessment trigger. Allow compact answers for simple requests and expandable detail for deeper reviews. Keep machine-readable output optional until a consumer needs it.

Evaluate behavior with fixed scenarios rather than additional keyword checks alone. Use generic or synthetic athlete data. Record the input, relevant tool results, expected conclusions, prohibited claims/actions, and observed outcome. Separate static validation, simulated tool runs, and live MCP evidence.

Initial scenarios:

1. Sparse discipline history and absent HRV.
2. Positive estimated TSB with low recent training.
3. Increased volume with stable or declining performance evidence.
4. Conflicting recovery signals and athlete-reported fatigue.
5. Race date far away versus race week with identical current load.
6. Missed workouts and reduced next-week availability.
7. Workout totals and target consistency across tiers.
8. Ambiguous or partial calendar writes.
9. Existing plans over 100 workouts and capped library discovery.

### 6. Installed skill consistency

The local `.agents/skills/triathlon-training` copy contains older routing and references. Decide how consumers refresh the installed copy, and document how to identify the active version. Check whether a canonical-folder link or repeatable installation procedure fits the supported harnesses before introducing a synchronization mechanism.

## Suggested Sequence

1. Correctness and verdict calibration, including the scenarios that expose current failures.
2. Explicit progression and feasibility checks.
3. Ongoing adaptation and a common response structure.
4. Installation/version verification and broader scenario coverage.

## Decisions to Resolve in Design

- Which existing thresholds have sufficient source support, and which should become contextual heuristics?
- What evidence is required for each overall race-readiness verdict?
- Which progression parameters are prescribed versus left to coaching judgment?
- How much plan history can existing MCP events/library metadata supply without new persistence?
- Which response fields are mandatory for each request type?

## Source Starting Points

- Canonical files: `skills/triathlon-training/SKILL.md` and `references/`.
- ECSS/ACSM consensus on overtraining assessment: https://pubmed.ncbi.nlm.nih.gov/23247672/
- TrainingPeaks running EF definition and speed conversion: https://www.trainingpeaks.com/blog/the-efficiency-factor-in-running/

The review established internal inconsistencies and workflow gaps. It did not establish new clinical thresholds or prove live coaching outcomes.
