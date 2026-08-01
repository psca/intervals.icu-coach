# Beginner Single-Sport Training Blocks — Design Spec

**Date:** 2026-08-01
**Status:** Ready for implementation
**Scope:** Add explicit beginner running and cycling paths to the triathlon-training skill

## Problem

The skill can build run-only half-marathon and marathon plans, but its shortest half-marathon template begins at four to five runs per week. It has no couch-to-5K, 5K-to-10K, or cycling-only block. Because coaching principles require prescriptions to come from templates, the coach cannot safely improvise these missing plans.

## Goal

Add four conservative, completion-oriented templates:

1. **Couch to 5K:** 9 weeks, three run/walk sessions per week
2. **5K to 10K:** 8 weeks, three runs per week
3. **Beginner Cycling Consistency:** 8 weeks, two or three rides per week
4. **Cycling Endurance Base:** 12 weeks, three rides per week

These blocks should help a healthy adult establish consistent single-sport training. They are not rehabilitation plans and do not promise a particular finish time.

## Evidence Basis and Interpretation

- The Couch to 5K structure follows the NHS pattern: nine weeks, three sessions per week, alternating walking and running, with a rest day between runs.
- Running progressions remain conservative, but the skill must not claim that a universal weekly percentage prevents injury. Reviews find conflicting evidence linking specific volume, frequency, duration, or intensity changes to running injury.
- Beginner cycling begins with easy aerobic consistency. The endurance block uses a pyramidal distribution: most time easy, some controlled moderate work after an initial base, and little or no hard work. Current evidence does not establish polarized training as universally superior, and recreational athletes may respond well to pyramidal training.
- The templates express intensity using talk-test/RPE cues first. Reliable athlete-specific HR, pace, or power zones may refine those cues but must not replace them for an absolute beginner.

Primary references:

- [NHS Couch to 5K](https://www.nhs.uk/better-health/get-active/get-running-with-couch-to-5k/couch-to-5k-running-plan/)
- [Fredette et al., 2022: running injuries and training parameters](https://pubmed.ncbi.nlm.nih.gov/34478518/)
- [Rosenblat et al., 2025: training-intensity distribution meta-analysis](https://pubmed.ncbi.nlm.nih.gov/39888556/)

## Routing and Intake

The existing **Build Training Block** flow remains the entry point. Add natural-language coverage for beginner running, couch-to-5K, 5K-to-10K, beginner cycling, cycling base, and cycling-only plans.

Before selecting a beginner template, the coach must explicitly confirm:

1. **Current baseline:** comfortable walking duration; continuous running duration; or comfortable cycling duration
2. **Training days:** maximum days per week the athlete can consistently commit
3. **Goal:** complete 5K, progress from 5K to 10K, ride consistently, build cycling endurance, or prepare for a stated event
4. **Schedule constraints:** unavailable days and protected activities
5. **Health context:** current pain, injury, illness, or relevant medical restriction

MCP history may inform the baseline but does not replace athlete confirmation. If the athlete reports pain, active injury, illness, or a medical restriction, the coach must avoid prescribing through it and recommend appropriate professional guidance.

## Template Selection

| Athlete baseline and goal | Template |
|---|---|
| Cannot yet run continuously for 20 minutes; wants to begin running or complete 5K | Couch to 5K |
| Can run continuously for about 30 minutes or has recently completed 5K; wants to complete 10K | 5K to 10K |
| New or returning cyclist; wants consistency or basic comfort on the bike | Beginner Cycling Consistency |
| Can comfortably ride 60 minutes; wants greater endurance or preparation for a longer recreational ride | Cycling Endurance Base |

If the baseline does not fit, the coach must explain the mismatch and select a safer entry point or an existing advanced template. It must not silently compress a beginner block.

## Progression Rules

### Shared rules

- Completion and comfort matter more than speed, distance, power, or pace.
- A session is successful when completed at the prescribed conversational effort.
- Repeating a week is normal when a session cannot be completed comfortably, recovery is inadequate, or persistent soreness develops.
- Do not progress through pain, illness, or unusual fatigue.
- Progress only one primary demand at a time: duration before intensity for these beginner blocks.
- Recovery weeks reduce duration while preserving routine.

### Running

- Schedule three sessions per week with at least one non-running day between them.
- Couch to 5K uses timed walk/run intervals and progresses toward 30 continuous minutes; it does not promise that every athlete will cover exactly 5 km in that time.
- 5K to 10K retains three weekly runs: two easy sessions and one gradually extended easy run. Strides may be introduced as short, relaxed accelerations; threshold and VO2max intervals are excluded.
- Walking breaks remain permitted in both blocks.

### Cycling

- Beginner Cycling Consistency uses two required easy rides plus one optional easy ride. The optional ride must never be required to progress.
- Cycling Endurance Base uses three rides: two easy aerobic rides and, after the initial consistency phase, one session containing controlled tempo segments. It contains no maximal efforts or VO2max work.
- Easy effort means conversational RPE 2–4 out of 10. Controlled tempo means RPE 5–6 out of 10, sustainable and never all-out.
- Duration scales to the athlete's available time; the template provides conservative default ranges and preserves a recovery week pattern.

## Files and Responsibilities

- `intervals.icu-coach/` is the sole source of truth for this feature. Do not read from, modify, or synchronize the workspace-root `.agents` copy during implementation.
- `skills/triathlon-training/SKILL.md`: add routing phrases and clearly advertise beginner single-sport block support.
- `skills/triathlon-training/references/COACH.md`: extend intake, template-selection, degradation, and safety rules.
- `skills/triathlon-training/references/BLOCK_TEMPLATES.md`: add the four week-by-week templates and progression rules.
- `skills/triathlon-training/references/WORKOUT_LIBRARY.md`: add run/walk and beginner cycling archetypes needed by the templates, using intervals.icu workout syntax.
- `docs/chatgpt-projects/TRIATHLON_TRAINING_CHATGPT_PROJECT_SKILL.md`: mirror all behavior-changing instructions required by repository policy.

## Preview and Calendar Writes

The existing preview and explicit approval gates remain unchanged. Beginner previews additionally show:

- baseline and goal used for selection
- required versus optional sessions
- RPE/talk-test explanation
- repeat-week rule
- a plain statement that pain is not a progression target

Calendar workouts use structured plain-text descriptions. Run/walk repetitions must be represented as explicit timed steps. Optional cycling sessions must be named clearly as optional. No event is written until the athlete approves the preview.

## Validation

Because the repository has no automated test suite, validation is structural and scenario-based:

1. Confirm all four triggers route to **Build Training Block**.
2. Confirm the coach asks baseline, training days, goal, constraints, and health context before assembly.
3. Confirm every workout name in the four templates exists in the workout library.
4. Confirm Couch to 5K has three weekly sessions with rest-day scheduling guidance and reaches 30 continuous minutes without a guaranteed 5 km claim.
5. Confirm 5K-to-10K excludes threshold and VO2max sessions.
6. Confirm beginner cycling contains only easy riding and marks the third ride optional.
7. Confirm cycling endurance adds controlled tempo only after the initial base and contains no maximal or VO2max work.
8. Confirm canonical skill files and the ChatGPT Project source contain equivalent behavioral rules.
9. Run `git diff --check` and inspect the complete diff before committing.

## Non-Goals

- Rehabilitation or return-to-sport programming
- Weight-loss prescriptions
- Beginner swimming blocks
- Race-time guarantees
- Automated adaptation of a live plan after every completed workout
- Replacing existing half-marathon, marathon, or triathlon templates
