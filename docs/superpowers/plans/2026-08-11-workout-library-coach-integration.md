# Workout Library Coach Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update the canonical triathlon-training skill so it reuses suitable private Intervals.icu library workouts and plans while retaining direct calendar writes for bespoke sessions, races, notes, and edits.

**Architecture:** Keep `SKILL.md` as the compact routing and tool map, put operational decision rules in `WORKOUT_PLANNING.md`, and update the two existing coaching workflows in `COACH.md`. Keep `WORKOUT_LIBRARY.md` as the canonical workout-archetype source while treating saved Intervals.icu workouts as persisted instances. Add a deterministic shell validator so the required routing and safety contracts are testable.

**Tech Stack:** Markdown skill files, Bash validation, ripgrep, Git.

## Global Constraints

- Modify only the canonical skill under `skills/triathlon-training/`, its validation script under `scripts/`, and this plan/spec documentation.
- Do not restore or modify deleted `docs/chatgpt-projects/` artifacts.
- Do not update the installed `.agents/skills/triathlon-training` copy, plugin metadata, or desktop extension.
- Preserve profile lookup, history review, zone resolution, health intake, calendar conflict checks, preview, and explicit athlete approval.
- Do not create library containers or workouts during planning or preview; persist them only after the athlete approves the complete workout or block.
- Keep `WORKOUT_LIBRARY.md` as the canonical archetype source and use Intervals.icu library entries as reusable persisted instances.
- Keep separate calendar events for separate disciplines, including bricks.
- Treat ambiguous bulk scheduling failures as unknown outcomes and inspect the calendar before retrying.
- Never use `delete_library_item` to resolve calendar conflicts.

---

### Task 1: Add a failing workout-library guidance contract

**Files:**
- Create: `scripts/validate-workout-library-guidance.sh`
- Test: `skills/triathlon-training/SKILL.md`
- Test: `skills/triathlon-training/references/COACH.md`
- Test: `skills/triathlon-training/references/WORKOUT_PLANNING.md`
- Test: `skills/triathlon-training/references/WORKOUT_LIBRARY.md`

**Interfaces:**
- Consumes: the four canonical Markdown skill files.
- Produces: executable `scripts/validate-workout-library-guidance.sh` returning zero only when the workout-library routing and safety contract is present.

- [ ] **Step 1: Create the contract validator**

Create an executable Bash script with this exact structure:

```bash
#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
skill="$repo_root/skills/triathlon-training/SKILL.md"
coach="$repo_root/skills/triathlon-training/references/COACH.md"
planning="$repo_root/skills/triathlon-training/references/WORKOUT_PLANNING.md"
library="$repo_root/skills/triathlon-training/references/WORKOUT_LIBRARY.md"

failures=0

require_text() {
  local file="$1"
  local pattern="$2"
  local label="$3"
  if ! rg -q -- "$pattern" "$file"; then
    printf 'FAIL: %s\n' "$label" >&2
    failures=$((failures + 1))
  fi
}

for tool in \
  search_workout_library \
  get_library_workout \
  save_library_container \
  save_library_workout \
  delete_library_item \
  schedule_library
do
  require_text "$skill" "\`$tool\`" "SKILL.md tool map includes $tool"
done

require_text "$skill" 'schedule_library.*WORKOUTS' 'SKILL.md routes reusable workouts through WORKOUTS mode'
require_text "$skill" 'schedule_library.*PLAN' 'SKILL.md routes reusable blocks through PLAN mode'
require_text "$coach" 'search_workout_library' 'single-workout workflow searches the private library'
require_text "$coach" 'get_library_workout' 'single-workout workflow supports detail lookup'
require_text "$coach" 'schedule_library.*WORKOUTS' 'single-workout workflow schedules selected templates'
require_text "$coach" 'save_library_container' 'block workflow can create a PLAN after approval'
require_text "$coach" 'save_library_workout' 'block workflow persists approved plan workouts'
require_text "$coach" 'schedule_library.*PLAN' 'block workflow schedules a reusable plan'
require_text "$coach" 'zero-based' 'block workflow documents zero-based plan days'
require_text "$planning" 'flat' 'planning reference documents flat folders'
require_text "$planning" '100' 'planning reference documents the scheduling limit'
require_text "$planning" 'calendar_id.*integer' 'planning reference requires integer calendar_id'
require_text "$planning" 'unknown.*outcome|outcome.*unknown' 'planning reference handles ambiguous bulk outcomes'
require_text "$planning" 'get_events.*retry|retry.*get_events' 'planning reference checks the calendar before retry'
require_text "$planning" 'delet.*folder.*plan.*contained workout|folder.*plan.*delet.*contained workout' 'planning reference warns about cascading container deletion'
require_text "$library" 'persisted instance' 'archetype reference explains saved-library boundary'
require_text "$library" 'bespoke' 'archetype reference retains direct bespoke authoring'

if (( failures > 0 )); then
  printf '%d workout-library guidance check(s) failed.\n' "$failures" >&2
  exit 1
fi

printf 'Workout-library guidance checks passed.\n'
```

Make it executable:

```bash
chmod +x scripts/validate-workout-library-guidance.sh
```

- [ ] **Step 2: Run the validator and verify RED**

Run:

```bash
./scripts/validate-workout-library-guidance.sh
```

Expected: non-zero exit with failures for the six missing library tools and their routing/safety guidance. Confirm the failure is about absent guidance, not a shell syntax error.

- [ ] **Step 3: Commit the failing contract**

```bash
git add scripts/validate-workout-library-guidance.sh
git commit -m "test: define workout library skill contract"
```

---

### Task 2: Add library tools and primary routing to SKILL.md

**Files:**
- Modify: `skills/triathlon-training/SKILL.md`
- Test: `scripts/validate-workout-library-guidance.sh`

**Interfaces:**
- Consumes: the deployed MCP tool names and the hybrid routing model from the design spec.
- Produces: compact, discoverable tool-map entries and primary sequences used by the detailed coaching workflows.

- [ ] **Step 1: Extend the MCP tool map**

Add these six rows near the existing calendar write tools:

```markdown
| Search private workout library | `search_workout_library` | Compact folders, plans, and workouts; workout results omit descriptions and raw parsed structures |
| Inspect one saved workout | `get_library_workout` | Fetch full saved description only when content must be verified or modified |
| Create / update library folder or plan | `save_library_container` | ⚠️ Write operation; folders are flat, plans hold progressive workouts |
| Create / update library workout | `save_library_workout` | ⚠️ Write operation; author with text `description`, never construct `workout_doc` |
| Schedule saved workout(s) or plan | `schedule_library` | ⚠️ Bulk calendar write; preflight conflicts and require explicit approval |
| Delete library item | `delete_library_item` | ⚠️ Destructive maintenance only; deleting a folder or plan cascades to all contained workouts |
```

Retain `add_or_update_event` and clarify that it remains the route for bespoke one-offs, races, notes, and direct calendar-event edits.

- [ ] **Step 2: Add the two primary library call sequences**

Append these concise routes under **Primary call sequences**:

```markdown
- Reusable workout: `search_workout_library` → optional `get_library_workout` → `get_events` → preview and explicit approval → `schedule_library` in `WORKOUTS` mode
- Reusable block: existing profile/history/intake/assembly flow → `search_workout_library` for a matching `PLAN` → preview and explicit approval → reuse, or create with `save_library_container` + `save_library_workout` → `schedule_library` in `PLAN` mode
```

- [ ] **Step 3: Run the focused validator**

Run:

```bash
./scripts/validate-workout-library-guidance.sh
```

Expected: still FAIL, but all six `SKILL.md` tool-name checks and both scheduling-mode checks pass; remaining failures point to the reference files.

- [ ] **Step 4: Commit the routing map**

```bash
git add skills/triathlon-training/SKILL.md
git commit -m "docs: route coaching through workout library tools"
```

---

### Task 3: Update the single-workout coaching workflow

**Files:**
- Modify: `skills/triathlon-training/references/COACH.md` (`## Schedule a Workout`)
- Test: `scripts/validate-workout-library-guidance.sh`

**Interfaces:**
- Consumes: `search_workout_library`, `get_library_workout`, `get_events`, `schedule_library`, `save_library_workout`, and `add_or_update_event`.
- Produces: an approval-gated routing workflow for reusable versus bespoke sessions.

- [ ] **Step 1: Replace the workflow tool declaration and routing steps**

State that the workflow uses:

```markdown
**Tools:** `search_workout_library` → optional `get_library_workout` → `get_events` → `schedule_library` (`WORKOUTS`), or `add_or_update_event` for bespoke writes; optional `save_library_workout` after approval
```

Then make the sequence implement this decision contract:

1. Require date and sport as today.
2. Decide whether the requested session is a reusable archetype or bespoke/materially adjusted session.
3. For reusable sessions, search by sport plus useful name/tag terms. Do not retrieve every workout description.
4. If one candidate is plausible, call `get_library_workout` only when its steps/content must be checked.
5. If no suitable template exists, offer either a one-off calendar event or, when reuse is useful or requested, a new flat-folder template.
6. Call `get_events` for the target date/range before any calendar write.
7. Preview saved name, sport, duration, load, intensity, destination date/time, and human-readable steps when available.
8. Wait for explicit approval.
9. On approval, use `schedule_library` in `WORKOUTS` mode for a saved workout; for a new reusable workout, save it first and then schedule it; use `add_or_update_event` for bespoke sessions.
10. Report returned results without claiming success beyond the tool response.

Keep the existing plain-text description example, but place it under the bespoke/new-template branch rather than making it the universal path.

- [ ] **Step 2: Add single-workout failure handling**

Add these rules:

```markdown
- Do not force reuse when the saved workout differs materially from the approved session.
- Do not create a library workout during search or preview.
- If bulk scheduling has an unknown outcome, call `get_events` for the affected date before retrying and do not claim that zero events were created.
- Report template-save failure separately from calendar-scheduling failure.
```

- [ ] **Step 3: Run the focused validator**

Run `./scripts/validate-workout-library-guidance.sh`.

Expected: the COACH single-workout checks pass; failures remain for block and planning/archetype guidance.

- [ ] **Step 4: Commit the workflow**

```bash
git add skills/triathlon-training/references/COACH.md
git commit -m "docs: reuse library workouts in coaching flow"
```

---

### Task 4: Update the training-block coaching workflow

**Files:**
- Modify: `skills/triathlon-training/references/COACH.md` (`## Build Training Block`)
- Test: `scripts/validate-workout-library-guidance.sh`

**Interfaces:**
- Consumes: the unchanged profile/history/zone/intake/template/preview pipeline plus all plan-library tools.
- Produces: approval-gated plan reuse or plan creation followed by one bulk PLAN scheduling call.

- [ ] **Step 1: Replace the block tool declaration**

Use this tool route:

```markdown
**Tools:** `get_athlete_profile` → `get_activities` (56 days) → `get_events` (target date range) → optional `search_activities` / curve tools → `search_workout_library` → after approval, `schedule_library` (`PLAN`) or `save_library_container` + `save_library_workout` + `schedule_library`; `add_or_update_event` for race day and bespoke exceptions
```

- [ ] **Step 2: Add plan discovery during assembly without writing**

After assembling from `BLOCK_TEMPLATES.md` and `WORKOUT_LIBRARY.md`, require a private-library search for a matching `PLAN`. State explicitly:

- a name match alone is insufficient;
- duration, discipline mix, workout sequence, progression, and recovery pattern must match the approved preview;
- no plan/container/workout writes occur during intake, assembly, discovery, or preview;
- separate disciplines remain separate workouts, including same-day bricks.

- [ ] **Step 3: Replace the legacy per-event batch-write loop**

Under **Approval + batch write**, retain the hard approval gate and define:

```markdown
- Matching existing plan: call `schedule_library` in `PLAN` mode with the approved start date and optional integer `calendar_id`.
- New progressive block: create a `PLAN`, save every approved workout with a zero-based non-negative integer `day` offset, then call `schedule_library` in `PLAN` mode.
- Race day and bespoke exceptions: write separately with `add_or_update_event` after approval.
- One scheduling call supports at most 100 workouts; split a larger approved plan deliberately and re-check calendar state between calls.
```

Remove the statement that one `add_or_update_event` call per discipline/day is the primary block-write mechanism. Keep the semantic rule that each discipline is a separate event.

- [ ] **Step 4: Add post-write and ambiguous-outcome behavior**

Specify that if plan creation succeeds but calendar scheduling fails ambiguously, the saved plan remains reusable. Call `get_events` for the affected range before deciding whether retry is safe, and never state that the bulk endpoint is transactional or that zero events were created.

- [ ] **Step 5: Run the focused validator**

Run `./scripts/validate-workout-library-guidance.sh`.

Expected: all COACH checks pass; remaining failures are limited to `WORKOUT_PLANNING.md` and `WORKOUT_LIBRARY.md`.

- [ ] **Step 6: Commit the block workflow**

```bash
git add skills/triathlon-training/references/COACH.md
git commit -m "docs: persist and schedule reusable training plans"
```

---

### Task 5: Add the library decision and safety reference

**Files:**
- Modify: `skills/triathlon-training/references/WORKOUT_PLANNING.md`
- Test: `scripts/validate-workout-library-guidance.sh`

**Interfaces:**
- Consumes: the six MCP library contracts and the existing direct-event authoring rules.
- Produces: one canonical decision table plus precise authoring, scheduling, deletion, and retry constraints.

- [ ] **Step 1: Generalize the introduction and preflight**

Change the introduction so it covers both direct calendar writes and private-library writes. Extend preflight to require:

- a chosen route from the decision table;
- integer `calendar_id` when supplied;
- calendar conflict inspection before scheduling;
- explicit athlete approval before every write;
- no `workout_doc` construction.

- [ ] **Step 2: Add the library routing table**

Add this exact table near the top:

```markdown
| Situation | Preferred write |
|---|---|
| Existing reusable workout | `schedule_library` in `WORKOUTS` mode |
| New bespoke one-off | `add_or_update_event` |
| New reusable template | `save_library_workout` in a flat folder, then schedule after approval |
| Existing reusable block | `schedule_library` in `PLAN` mode |
| New progressive block | Create a `PLAN`, save workouts with zero-based `day`, then schedule |
| Race, note, or direct event edit | `add_or_update_event` |
```

- [ ] **Step 3: Add compact lookup and authoring rules**

Document that folders are flat; search workout results omit descriptions, `workout_doc`, and attachments; container metadata may contain a description; `get_library_workout` returns the selected description but not raw parsed structures; and all new authoring uses plain-text `description`, never a hand-built `workout_doc`.

- [ ] **Step 4: Replace legacy block batching guidance**

State that `schedule_library` supports `WORKOUTS` and `PLAN` modes, accepts at most 100 workouts per call, requires integer `calendar_id`, performs a bulk write whose transactionality is not guaranteed, and must be preceded by conflict checks and approval. Retain `add_or_update_event` guidance for races and bespoke exceptions.

- [ ] **Step 5: Add deletion and retry safety**

State explicitly:

```markdown
- `delete_library_item` is only for explicit library maintenance, never calendar conflict resolution.
- Deleting a folder or plan permanently deletes every contained workout; state the cascade and obtain explicit confirmation.
- If a bulk scheduling error reports an unknown outcome, call `get_events` over the affected range before retrying. Do not claim that no events were created.
```

- [ ] **Step 6: Run the focused validator**

Run `./scripts/validate-workout-library-guidance.sh`.

Expected: all planning checks pass; only the archetype-boundary checks remain.

- [ ] **Step 7: Commit the planning reference**

```bash
git add skills/triathlon-training/references/WORKOUT_PLANNING.md
git commit -m "docs: define workout library planning rules"
```

---

### Task 6: Clarify the canonical archetype boundary

**Files:**
- Modify: `skills/triathlon-training/references/WORKOUT_LIBRARY.md` (introductory usage text only)
- Test: `scripts/validate-workout-library-guidance.sh`

**Interfaces:**
- Consumes: existing archetype catalog and zone-resolution rules unchanged.
- Produces: a clear relationship between Markdown archetypes, saved library instances, and bespoke calendar events.

- [ ] **Step 1: Replace only the introductory usage text**

Use concise wording with these four points:

```markdown
**Usage:** Templates in BLOCK_TEMPLATES.md reference these archetypes by name. This file remains the canonical coach-approved workout structure.

- Reuse a matching saved library workout as a persisted instance without retransmitting its description.
- When a useful reusable variant is missing, build it from the archetype and save it only after athlete approval.
- Write a bespoke or materially adjusted session directly with `add_or_update_event` unless the athlete wants it saved.
- Continue to resolve athlete-specific zones before either saving or directly scheduling a newly authored workout.
```

Do not edit any workout catalog entry, tier percentage, phase mapping, or zone-resolution fallback.

- [ ] **Step 2: Run the focused validator and verify GREEN**

Run:

```bash
./scripts/validate-workout-library-guidance.sh
```

Expected:

```text
Workout-library guidance checks passed.
```

- [ ] **Step 3: Commit the archetype clarification**

```bash
git add skills/triathlon-training/references/WORKOUT_LIBRARY.md
git commit -m "docs: distinguish archetypes from saved workouts"
```

---

### Task 7: Validate the complete canonical skill update

**Files:**
- Verify: `skills/triathlon-training/SKILL.md`
- Verify: `skills/triathlon-training/references/COACH.md`
- Verify: `skills/triathlon-training/references/WORKOUT_PLANNING.md`
- Verify: `skills/triathlon-training/references/WORKOUT_LIBRARY.md`
- Verify: `scripts/validate-workout-library-guidance.sh`

**Interfaces:**
- Consumes: all prior task outputs.
- Produces: evidence that the skill is structurally valid, its existing beginner-block contracts still pass, the new library contract passes, and unrelated deletions remain untouched.

- [ ] **Step 1: Run all deterministic validators**

```bash
./scripts/validate-workout-library-guidance.sh
./scripts/validate-beginner-blocks.sh
python3 /Users/anthony/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/triathlon-training
git diff --check
```

Expected: both shell validators pass, `quick_validate.py` reports the skill is valid, and `git diff --check` prints no output.

- [ ] **Step 2: Inspect the behavioral diff**

Run:

```bash
git diff -- skills/triathlon-training scripts/validate-workout-library-guidance.sh
```

Confirm all seven design validation scenarios are represented:

1. existing two-hour Zone 2 ride reuse;
2. missing `SS-3x10` persisted and scheduled;
3. bespoke race-preparation session written directly;
4. matching base plan progression verified before reuse;
5. new progressive plan saved with zero-based days after approval;
6. unknown bulk outcome followed by calendar inspection;
7. folder/plan cascade deletion warning and explicit confirmation.

- [ ] **Step 3: Confirm scope preservation**

Run:

```bash
git status --short
```

Expected: the pre-existing `docs/chatgpt-projects/` deletions remain present and unstaged; no `.agents`, plugin, extension, or server files are modified.

- [ ] **Step 4: Commit any validation-only refinement**

If validation required a minimal correction, stage only its exact canonical skill or validator path and commit it. If no correction was required, do not create an empty commit.
