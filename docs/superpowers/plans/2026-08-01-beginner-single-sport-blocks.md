# Beginner Single-Sport Training Blocks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add explicit beginner running and cycling blocks that the coaching skill can select, preview, and write without improvising a plan.

**Architecture:** Keep `intervals.icu-coach/skills/triathlon-training/` as the sole source of truth. Add reusable beginner workout archetypes, compose them into four fixed week-by-week templates, route beginner requests through the existing training-block intake, then mirror the resulting behavior in the required ChatGPT Project source. A POSIX shell validator provides repeatable structural checks for the Markdown-based feature.

**Tech Stack:** Markdown skill files, intervals.icu structured workout syntax, POSIX `sh`, `rg`, Git.

## Global Constraints

- Do not read from, modify, or synchronize the workspace-root `.agents` copy.
- Preserve the existing preview and explicit-approval gates for calendar writes.
- Beginner prescriptions are completion-oriented and use talk-test/RPE cues first.
- Do not claim that a universal weekly progression percentage prevents injury.
- Running plans allow walking breaks and require a non-running day between sessions.
- Beginner cycling has two required sessions plus one optional session; cycling endurance adds controlled tempo only after an easy base.
- Pain, active injury, illness, or medical restriction blocks normal plan assembly and prompts appropriate professional guidance.
- Keep the canonical skill and `docs/chatgpt-projects/TRIATHLON_TRAINING_CHATGPT_PROJECT_SKILL.md` behaviorally equivalent.

---

## File Structure

- Create `scripts/validate-beginner-blocks.sh`: structural validation for routing, intake, templates, archetypes, safety language, and ChatGPT parity.
- Modify `skills/triathlon-training/SKILL.md`: advertise and route beginner single-sport requests.
- Modify `skills/triathlon-training/references/COACH.md`: add beginner intake, selection, preview, repeat-week, and safety rules.
- Modify `skills/triathlon-training/references/BLOCK_TEMPLATES.md`: add the four approved week-by-week blocks.
- Modify `skills/triathlon-training/references/WORKOUT_LIBRARY.md`: add RPE-first beginner run and cycling archetypes.
- Modify `docs/chatgpt-projects/TRIATHLON_TRAINING_CHATGPT_PROJECT_SKILL.md`: mirror the canonical router, coach, template, and library changes.

---

### Task 1: Add a Failing Structural Validator

**Files:**
- Create: `scripts/validate-beginner-blocks.sh`
- Test: `scripts/validate-beginner-blocks.sh`

**Interfaces:**
- Consumes: the canonical skill files and the consolidated ChatGPT Project source.
- Produces: exit code `0` only when all beginner-block contracts are present; a named error and non-zero exit otherwise.

- [ ] **Step 1: Write the validator before changing skill content**

Create this executable POSIX shell script:

```sh
#!/bin/sh

set -eu

SKILL="skills/triathlon-training/SKILL.md"
COACH="skills/triathlon-training/references/COACH.md"
BLOCKS="skills/triathlon-training/references/BLOCK_TEMPLATES.md"
LIBRARY="skills/triathlon-training/references/WORKOUT_LIBRARY.md"
CHATGPT="docs/chatgpt-projects/TRIATHLON_TRAINING_CHATGPT_PROJECT_SKILL.md"

require_text() {
  pattern=$1
  file=$2
  label=$3
  if ! rg -q --fixed-strings "$pattern" "$file"; then
    echo "FAIL: $label"
    exit 1
  fi
}

for file in "$SKILL" "$COACH" "$BLOCKS" "$LIBRARY" "$CHATGPT"; do
  if [ ! -f "$file" ]; then
    echo "FAIL: missing $file"
    exit 1
  fi
done

require_text '### Run/Walk Intervals' "$LIBRARY" 'missing run/walk archetype'
require_text '### Beginner Easy Ride' "$LIBRARY" 'missing beginner easy ride archetype'
require_text '### Optional Easy Spin' "$LIBRARY" 'missing optional ride archetype'
require_text '### Controlled Tempo Ride' "$LIBRARY" 'missing controlled tempo archetype'
require_text '## Couch to 5K — 9 weeks' "$BLOCKS" 'missing Couch to 5K block'
require_text '## 5K to 10K — 8 weeks' "$BLOCKS" 'missing 5K-to-10K block'
require_text '## Beginner Cycling Consistency — 8 weeks' "$BLOCKS" 'missing cycling consistency block'
require_text '## Cycling Endurance Base — 12 weeks' "$BLOCKS" 'missing cycling endurance block'
require_text 'couch to 5K' "$SKILL" 'router lacks couch-to-5K language'
require_text 'beginner cycling' "$SKILL" 'router lacks beginner-cycling language'
require_text '**Current baseline:**' "$COACH" 'intake lacks baseline confirmation'
require_text '**Training days:**' "$COACH" 'intake lacks training-day cap'
require_text '**Goal:**' "$COACH" 'intake lacks beginner goal'
require_text 'Repeating a week is normal' "$COACH" 'missing repeat-week rule'
require_text 'does not guarantee covering 5 km' "$COACH" 'missing 30-minute distance caveat'
require_text '## Couch to 5K — 9 weeks' "$CHATGPT" 'ChatGPT source lacks Couch to 5K block'
require_text '### Controlled Tempo Ride' "$CHATGPT" 'ChatGPT source lacks controlled tempo archetype'

five_to_ten=$(sed -n '/^## 5K to 10K — 8 weeks$/,/^---$/p' "$BLOCKS")
beginner_bike=$(sed -n '/^## Beginner Cycling Consistency — 8 weeks$/,/^---$/p' "$BLOCKS")
endurance_bike=$(sed -n '/^## Cycling Endurance Base — 12 weeks$/,/^---$/p' "$BLOCKS")

if printf '%s\n' "$five_to_ten" | rg -q 'Threshold|VO2max'; then
  echo 'FAIL: 5K-to-10K contains threshold or VO2max work'
  exit 1
fi

if printf '%s\n' "$beginner_bike" | rg -q 'Tempo|Threshold|VO2max|Maximal'; then
  echo 'FAIL: beginner cycling contains intensity'
  exit 1
fi

if printf '%s\n' "$endurance_bike" | rg -q 'VO2max|Maximal'; then
  echo 'FAIL: cycling endurance contains maximal work'
  exit 1
fi

echo "Beginner block validation passed"
```

- [ ] **Step 2: Make the validator executable**

Run:

```bash
chmod +x scripts/validate-beginner-blocks.sh
```

- [ ] **Step 3: Run it and verify RED**

Run:

```bash
./scripts/validate-beginner-blocks.sh
```

Expected: exit non-zero with `FAIL: missing run/walk archetype`. The failure must occur because the feature content is absent, not because the script has a syntax error.

- [ ] **Step 4: Validate script syntax**

Run:

```bash
sh -n scripts/validate-beginner-blocks.sh
```

Expected: exit `0` with no output.

- [ ] **Step 5: Commit the failing validator**

```bash
git add scripts/validate-beginner-blocks.sh
git commit -m "test: define beginner block contracts"
```

---

### Task 2: Add Beginner Workout Archetypes

**Files:**
- Modify: `skills/triathlon-training/references/WORKOUT_LIBRARY.md`
- Test: `scripts/validate-beginner-blocks.sh`

**Interfaces:**
- Consumes: intervals.icu plain-text workout syntax and the existing zone-resolution fallback order.
- Produces: `Run/Walk Intervals`, `Easy Run with Optional Walks`, `Relaxed Strides`, `Beginner Easy Ride`, `Optional Easy Spin`, and `Controlled Tempo Ride` names referenced verbatim by templates.

- [ ] **Step 1: Confirm the library-specific checks fail**

Run:

```bash
rg -n '### (Run/Walk Intervals|Beginner Easy Ride|Optional Easy Spin|Controlled Tempo Ride)' skills/triathlon-training/references/WORKOUT_LIBRARY.md
```

Expected: no matches and exit non-zero.

- [ ] **Step 2: Add three running archetypes under `## Run`**

Add:

```markdown
### Run/Walk Intervals
- **When:** Couch to 5K
- **Duration range:** 25-40min total
- **Intensity:** Conversational running at RPE 3-4/10; easy walking recovery
- **Beginner rule:** Parameterize run/walk repetitions from BLOCK_TEMPLATES.md. Do not replace RPE with a pace target.

Warmup
- 5m walk

Main Set Nx
- Xm run RPE 3-4
- Ym walk

Cooldown
- 5m walk

### Easy Run with Optional Walks
- **When:** Couch to 5K / 5K to 10K
- **Duration range:** 20-75min
- **Intensity:** Conversational RPE 3-4/10
- **Beginner rule:** Walking breaks are always allowed. Parameterize duration from BLOCK_TEMPLATES.md.

Warmup
- 5m walk

Main
- Xm run RPE 3-4 — take short walking breaks whenever needed

Cooldown
- 5m walk

### Relaxed Strides
- **When:** 5K to 10K after an easy running base
- **Duration range:** 30-45min total
- **Intensity:** Easy running plus relaxed, controlled accelerations; never sprinting

Warmup
- 10m run RPE 3

Main
- Xm run RPE 3-4

Strides 4x
- 20s relaxed acceleration RPE 6
- 100s walk or easy jog

Cooldown
- 5m run or walk RPE 2
```

- [ ] **Step 3: Add three cycling archetypes under `## Bike`**

Add:

```markdown
### Beginner Easy Ride
- **When:** Beginner Cycling Consistency / Cycling Endurance Base
- **Duration range:** 30-120min
- **Intensity:** Conversational RPE 2-4/10
- **Beginner rule:** RPE and the talk test are primary. Power or HR may clarify effort only when current zones are reliable.

Warmup
- 5m very easy RPE 2

Main
- Xm conversational riding RPE 2-4

Cooldown
- 5m very easy RPE 2

### Optional Easy Spin
- **When:** Beginner Cycling Consistency
- **Duration range:** 20-45min
- **Intensity:** Very easy RPE 2-3/10
- **Beginner rule:** This session is optional and is never required for progression.

Warmup
- 5m very easy RPE 2

Main
- Xm easy spinning RPE 2-3

Cooldown
- 5m very easy RPE 2

### Controlled Tempo Ride
- **When:** Cycling Endurance Base after at least four easy consistency weeks
- **Duration range:** 50-90min
- **Intensity:** Mostly easy with controlled tempo at RPE 5-6/10; never all-out

Warmup
- 10m easy RPE 2-3

Main Set Nx
- Xm controlled tempo RPE 5-6
- Ym easy RPE 2-3

Endurance
- Zm conversational riding RPE 3-4

Cooldown
- 5m very easy RPE 2
```

- [ ] **Step 4: Run focused library checks**

Run:

```bash
rg -n '### (Run/Walk Intervals|Easy Run with Optional Walks|Relaxed Strides|Beginner Easy Ride|Optional Easy Spin|Controlled Tempo Ride)' skills/triathlon-training/references/WORKOUT_LIBRARY.md
```

Expected: exactly six headings.

- [ ] **Step 5: Run the validator and confirm it advances to a template failure**

Run:

```bash
./scripts/validate-beginner-blocks.sh
```

Expected: still fails, but with `FAIL: missing Couch to 5K block` rather than a missing-library or shell-syntax error.

- [ ] **Step 6: Commit**

```bash
git add skills/triathlon-training/references/WORKOUT_LIBRARY.md
git commit -m "feat: add beginner workout archetypes"
```

---

### Task 3: Add Four Week-by-Week Templates

**Files:**
- Modify: `skills/triathlon-training/references/BLOCK_TEMPLATES.md`
- Test: `scripts/validate-beginner-blocks.sh`

**Interfaces:**
- Consumes: the six exact workout names from Task 2.
- Produces: four fixed templates selected by the coach and mirrored into the ChatGPT source.

- [ ] **Step 1: Add shared beginner rules before the new templates**

State that completion outranks pace or power, repeat weeks are normal, walking breaks are allowed, pain/illness/unusual fatigue stops progression, and duration progresses before intensity. State that running days need at least one non-running day between them.

- [ ] **Step 2: Add `## Couch to 5K — 9 weeks`**

Use three sessions weekly. Encode the following progression in a table with columns `Wk | Session 1 | Session 2 | Session 3 | Notes`:

| Wk | Sessions |
|---|---|
| 1 | Run/Walk Intervals: 8 x 1min run / 90s walk |
| 2 | Run/Walk Intervals: 6 x 90s run / 2min walk |
| 3 | Run/Walk Intervals: 2 rounds of 90s run, 90s walk, 3min run, 3min walk |
| 4 | Run/Walk Intervals: 3min run, 90s walk, 5min run, 2.5min walk, 3min run, 90s walk, 5min run |
| 5 | S1: 3 x 5min run / 3min walk; S2: 8min run / 5min walk / 8min run; S3: 20min Easy Run with Optional Walks |
| 6 | S1: 5min run / 3min walk / 8min run / 3min walk / 5min run; S2: 10min run / 3min walk / 10min run; S3: 25min Easy Run with Optional Walks |
| 7 | 25min Easy Run with Optional Walks for all three sessions |
| 8 | 28min Easy Run with Optional Walks for all three sessions |
| 9 | 30min Easy Run with Optional Walks for all three sessions |

Every session includes the archetype's five-minute walking warmup and cooldown. State explicitly that 30 continuous minutes does not guarantee covering 5 km and walking breaks remain valid.

- [ ] **Step 3: Add `## 5K to 10K — 8 weeks`**

Use three sessions weekly: easy, easy or relaxed strides, and a longer easy session. Parameterize durations:

| Wk | Easy | Easy / strides | Long easy |
|---|---:|---:|---:|
| 1 | 25min | 30min easy | 40min |
| 2 | 30min | 30min Relaxed Strides | 45min |
| 3 | 30min | 35min easy | 50min |
| 4 | 25min | 30min easy | 40min recovery |
| 5 | 35min | 35min Relaxed Strides | 55min |
| 6 | 35min | 40min easy | 60min |
| 7 | 30min | 35min Relaxed Strides | 70min |
| 8 | 25min | 20min easy | Complete 10 km easily with optional walking breaks |

Exclude threshold and VO2max work. The goal session is completion-oriented and may take longer than prior timed runs.

- [ ] **Step 4: Add `## Beginner Cycling Consistency — 8 weeks`**

Use two required `Beginner Easy Ride` sessions and one `Optional Easy Spin`:

| Wk | Required 1 | Required 2 | Optional |
|---|---:|---:|---:|
| 1 | 30min | 40min | 20min |
| 2 | 35min | 45min | 25min |
| 3 | 40min | 50min | 30min |
| 4 | 30min | 40min | 20min recovery |
| 5 | 45min | 60min | 30min |
| 6 | 45min | 70min | 35min |
| 7 | 50min | 80min | 40min |
| 8 | 40min | 60min | 30min consolidation |

State that omitting the optional session never blocks progression. Include no tempo, threshold, VO2max, or maximal work.

- [ ] **Step 5: Add `## Cycling Endurance Base — 12 weeks`**

Use three rides weekly. Weeks 1–4 are easy only; weeks 5–11 use at most one `Controlled Tempo Ride`; weeks 4, 8, and 12 reduce volume:

| Wk | Easy 1 | Quality / easy | Long easy | Tempo prescription |
|---|---:|---:|---:|---|
| 1 | 45min | 60min easy | 75min | none |
| 2 | 50min | 60min easy | 90min | none |
| 3 | 50min | 65min easy | 105min | none |
| 4 | 40min | 45min easy | 75min | recovery |
| 5 | 50min | 60min controlled | 105min | 2 x 6min RPE 5 |
| 6 | 55min | 65min controlled | 120min | 2 x 8min RPE 5 |
| 7 | 60min | 70min controlled | 135min | 3 x 8min RPE 5-6 |
| 8 | 45min | 50min easy | 90min | recovery |
| 9 | 60min | 75min controlled | 135min | 2 x 12min RPE 5-6 |
| 10 | 60min | 80min controlled | 150min | 3 x 10min RPE 5-6 |
| 11 | 60min | 85min controlled | 165min | 2 x 15min RPE 5-6 |
| 12 | 45min | 60min easy | 105min | consolidation |

State entry criteria: comfortable 60-minute ride. Allow duration scaling down to available time while preserving the relative easy/long pattern. Include no maximal or VO2max work.

- [ ] **Step 6: Run template checks**

Run:

```bash
./scripts/validate-beginner-blocks.sh
```

Expected: advances past all template/archetype checks and fails with `FAIL: router lacks couch-to-5K language`.

- [ ] **Step 7: Commit**

```bash
git add skills/triathlon-training/references/BLOCK_TEMPLATES.md
git commit -m "feat: add beginner running and cycling blocks"
```

---

### Task 4: Extend Coach Intake, Selection, and Routing

**Files:**
- Modify: `skills/triathlon-training/SKILL.md`
- Modify: `skills/triathlon-training/references/COACH.md`
- Test: `scripts/validate-beginner-blocks.sh`

**Interfaces:**
- Consumes: athlete profile/history, explicit athlete answers, and the four template headings from Task 3.
- Produces: deterministic routing and selection without beginner-plan improvisation.

- [ ] **Step 1: Extend `SKILL.md` routing**

Add `couch to 5K`, `5K to 10K`, `beginner running`, `beginner cycling`, `cycling base`, and `cycling-only plan` to the **Build Training Block** trigger row. Update **What I Can Help With** so training blocks explicitly include beginner running and cycling alongside race plans.

- [ ] **Step 2: Extend the required structured intake in `COACH.md`**

Before existing race-specific questions, add a beginner/single-sport branch that explicitly confirms:

```markdown
1. **Current baseline:** Ask what the athlete can comfortably do today: walking duration, continuous running duration, or comfortable cycling duration. Present MCP history as context, but require confirmation.
2. **Training days:** Ask for the maximum number of days per week they can consistently commit, separate from available hours.
3. **Goal:** Confirm complete 5K, progress from 5K to 10K, ride consistently, build cycling endurance, or prepare for a stated event.
```

Retain schedule constraints and health context as required questions. Do not require a race date for general cycling consistency or cycling endurance; do ask for one when preparing for a stated event.

- [ ] **Step 3: Add deterministic template selection**

Add this mapping to **Template selection + assembly**:

- Cannot yet run continuously for 20 minutes + begin running/complete 5K → Couch to 5K
- Can run about 30 continuous minutes or recently completed 5K + complete 10K → 5K to 10K
- New/returning cyclist + consistency/basic comfort → Beginner Cycling Consistency
- Comfortable 60-minute ride + greater endurance/long recreational ride → Cycling Endurance Base

If the athlete does not meet an entry criterion, explain the mismatch and select the safer earlier block. Never silently compress a beginner block.

- [ ] **Step 4: Add beginner progression and preview rules**

Require the preview to show baseline, goal, required versus optional sessions, RPE/talk-test explanation, repeat-week rule, and pain warning. Use these exact phrases so validation remains stable:

```markdown
Repeating a week is normal when the athlete cannot complete the sessions comfortably, recovery is inadequate, or persistent soreness develops.

Completing 30 continuous minutes does not guarantee covering 5 km; completion and comfort matter more than pace or distance.
```

The second sentence must contain the substring `does not guarantee covering 5 km` used by the validator.

- [ ] **Step 5: Add safety degradation**

If the athlete reports current pain, active injury, illness, or a relevant medical restriction, do not assemble a normal beginner block through the issue. State that the skill is not a rehabilitation plan and recommend qualified medical or coaching guidance as appropriate.

- [ ] **Step 6: Run canonical validation**

Run:

```bash
./scripts/validate-beginner-blocks.sh
```

Expected: all canonical checks pass; the first failure is ChatGPT parity because the consolidated source is not updated yet.

- [ ] **Step 7: Commit**

```bash
git add skills/triathlon-training/SKILL.md skills/triathlon-training/references/COACH.md
git commit -m "feat: route beginner single-sport plans"
```

---

### Task 5: Mirror the Canonical Skill into the ChatGPT Project Source

**Files:**
- Modify: `docs/chatgpt-projects/TRIATHLON_TRAINING_CHATGPT_PROJECT_SKILL.md`
- Test: `scripts/validate-beginner-blocks.sh`

**Interfaces:**
- Consumes: final canonical content from Tasks 2–4.
- Produces: behaviorally equivalent single-file instructions for ChatGPT Projects.

- [ ] **Step 1: Update the Core Skill Router section**

Mirror the revised **What I Can Help With** language and trigger row from `SKILL.md` into the router portion of the consolidated file.

- [ ] **Step 2: Update the Coach Knowledge section**

Mirror the full beginner intake, template-selection, progression, preview, and safety rules from `COACH.md`. Preserve the consolidated document's existing `_Source:` boundaries.

- [ ] **Step 3: Update the Block Templates section**

Copy the complete shared beginner rules and all four new templates from `BLOCK_TEMPLATES.md` into the corresponding consolidated section. Preserve headings exactly.

- [ ] **Step 4: Update the Workout Library section**

Copy all six new archetypes from `WORKOUT_LIBRARY.md` into the corresponding bike and run sections. Preserve headings and workout syntax exactly.

- [ ] **Step 5: Run full validation and verify GREEN**

Run:

```bash
./scripts/validate-beginner-blocks.sh
```

Expected: `Beginner block validation passed` and exit `0`.

- [ ] **Step 6: Check behavioral parity with targeted excerpts**

Run:

```bash
rg -n -A 18 '## Couch to 5K — 9 weeks|## Beginner Cycling Consistency — 8 weeks|### Run/Walk Intervals|### Controlled Tempo Ride' skills/triathlon-training/references/BLOCK_TEMPLATES.md skills/triathlon-training/references/WORKOUT_LIBRARY.md docs/chatgpt-projects/TRIATHLON_TRAINING_CHATGPT_PROJECT_SKILL.md
```

Expected: each canonical heading has a corresponding consolidated heading with equivalent nearby rules and workout syntax.

- [ ] **Step 7: Commit**

```bash
git add docs/chatgpt-projects/TRIATHLON_TRAINING_CHATGPT_PROJECT_SKILL.md
git commit -m "docs: sync beginner blocks to ChatGPT source"
```

---

### Task 6: Final Verification and Documentation Check

**Files:**
- Verify: all files changed in Tasks 1–5
- Do not modify: workspace-root `.agents/`

**Interfaces:**
- Consumes: completed feature and commit history.
- Produces: evidence that the canonical skill, validator, and ChatGPT source satisfy the approved design.

- [ ] **Step 1: Run the full validator**

```bash
./scripts/validate-beginner-blocks.sh
```

Expected: `Beginner block validation passed`.

- [ ] **Step 2: Validate shell syntax and whitespace**

```bash
sh -n scripts/validate-beginner-blocks.sh
git diff --check HEAD~5..HEAD
```

Expected: both commands exit `0` with no errors.

- [ ] **Step 3: Verify workout-name integrity**

For each new template name, confirm an exact library heading exists:

```bash
rg -n '^### (Run/Walk Intervals|Easy Run with Optional Walks|Relaxed Strides|Beginner Easy Ride|Optional Easy Spin|Controlled Tempo Ride)$' skills/triathlon-training/references/WORKOUT_LIBRARY.md
```

Expected: exactly six matches.

- [ ] **Step 4: Verify `.agents` stayed untouched**

Run from the repository:

```bash
git status --short
```

Expected: clean repository. Since `.agents` is outside this Git repository and explicitly out of scope, do not run sync or copy commands against it.

- [ ] **Step 5: Review requirements against the design**

Read `docs/superpowers/specs/2026-08-01-beginner-single-sport-blocks-design.md` and verify:

- all four blocks exist with approved lengths and frequencies
- intake confirms baseline, days, goal, constraints, and health
- RPE/talk test is primary
- repeat-week and walking-break rules are visible
- Couch to 5K does not promise 5 km in 30 minutes
- 5K-to-10K has no threshold or VO2max work
- cycling consistency has no intensity and clearly labels the optional ride
- cycling endurance starts tempo only after four easy weeks
- calendar preview and explicit approval gates remain intact
- canonical and ChatGPT instructions are behaviorally equivalent

- [ ] **Step 6: Inspect the final commit range**

```bash
git log --oneline -6
git show --stat --oneline HEAD~5..HEAD
```

Expected: one focused validator commit plus four focused feature/documentation commits, with no unrelated files.
