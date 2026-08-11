# Workout Library Coach Integration Design

## Goal

Update the canonical triathlon coaching skill to reuse the athlete's private Intervals.icu workout library for repeatable workouts and progressive plans while preserving direct calendar writes for bespoke sessions, races, notes, and edits.

## Scope

This change updates only the canonical skill under `skills/triathlon-training/` and its repository guidance where necessary. It will not restore or modify the deleted `docs/chatgpt-projects/` artifacts, update the installed `.agents` skill copy, change plugin metadata, rebuild the desktop extension, or deploy another server version.

The coaching skill will recognize all six deployed private-library tools:

- `search_workout_library`;
- `get_library_workout`;
- `save_library_container`;
- `save_library_workout`;
- `delete_library_item`;
- `schedule_library`.

## Routing Model

The skill will use a hybrid routing model.

An existing repeatable workout is discovered through `search_workout_library`, inspected through `get_library_workout` only when its full content is needed, and scheduled through `schedule_library` in `WORKOUTS` mode after conflict checking and athlete approval.

A bespoke one-off workout continues to use `add_or_update_event`. This route also remains appropriate for races, notes, and direct edits to existing calendar events.

A workout that should become reusable is saved through `save_library_workout` in a flat discipline or purpose folder. Examples include standard Zone 2 durations and progressive sweet-spot variants. The text archetypes in `WORKOUT_LIBRARY.md` remain the canonical coaching source; saved Intervals.icu workouts are persisted instances that avoid reconstructing the same description in future conversations.

A progressive block is represented as an Intervals.icu `PLAN`. The coach searches for a matching existing plan first. It reuses that plan only when its progression matches the approved block. Otherwise, after approval, it creates a new plan and saves each workout with a zero-based `day` offset before scheduling the plan through `schedule_library` in `PLAN` mode.

## Tool Map and Primary Sequences

`SKILL.md` will add the six library tools with concise responsibilities and safety notes.

The reusable-workout sequence is:

1. `search_workout_library`;
2. optional `get_library_workout` when compact metadata is insufficient;
3. `get_events` for the target date or range;
4. preview and explicit athlete approval;
5. `schedule_library` in `WORKOUTS` mode.

The training-block sequence retains the existing profile, history, zone-resolution, intake, assembly, and preview steps, then uses:

1. `search_workout_library` for a matching `PLAN`;
2. athlete approval of the complete block;
3. either reuse the plan or call `save_library_container` and `save_library_workout` to persist a new one;
4. `schedule_library` in `PLAN` mode;
5. `add_or_update_event` separately for race-day events or bespoke exceptions.

`delete_library_item` is a maintenance operation, not part of ordinary scheduling. The coach must state that deleting a folder or plan permanently deletes every contained workout and must obtain explicit confirmation for that cascade.

## Schedule a Workout Workflow

The existing schedule workflow will first distinguish reusable archetypes from bespoke sessions.

For a reusable request, the coach searches by sport and useful name or tag terms. When one clear match exists, it previews the saved name, sport, duration, load, intensity, and destination time. It calls `get_library_workout` only when workout steps or content must be verified. It checks the calendar with `get_events`, presents the placement, and schedules only after explicit approval.

When no suitable template exists, the coach will not force reuse. It will either:

- create a one-off event through `add_or_update_event`; or
- save a new template through `save_library_workout` when the athlete wants the session reusable, then schedule it.

The coach will not create library content merely because a one-off resembles a common workout. Reusability must be useful to the athlete or explicit in the request.

## Build Training Block Workflow

The existing intake and safety gates remain unchanged. Library discovery does not replace profile lookup, training-history review, calendar conflict checks, health questions, plan preview, or athlete approval.

During assembly, `BLOCK_TEMPLATES.md` and `WORKOUT_LIBRARY.md` remain the sources for periodization and workout structure. Before writing anything, the coach searches for a matching saved plan. A plan name alone is not sufficient for reuse; its duration and progression must match the approved preview.

No plan container or workout is created during intake, assembly, or preview. After explicit approval:

- for a matching existing plan, call `schedule_library` in `PLAN` mode;
- for a new block, create a `PLAN`, save the approved workouts with zero-based `day` offsets, then schedule that plan;
- use `add_or_update_event` for race-day events and exceptional sessions outside the reusable plan.

The coach will continue to create separate events for separate disciplines, including brick sessions. A plan may place multiple discipline-specific workouts on the same day, but it must not aggregate them into one event.

## Library Planning Rules

`WORKOUT_PLANNING.md` will add a concise decision table:

| Situation | Preferred write |
|---|---|
| Existing reusable workout | `schedule_library` in `WORKOUTS` mode |
| New bespoke one-off | `add_or_update_event` |
| New reusable template | `save_library_workout` |
| Existing reusable block | `schedule_library` in `PLAN` mode |
| New progressive block | Create `PLAN`, save workouts with `day`, then schedule |
| Race, note, or direct event edit | `add_or_update_event` |

The reference will state these exact constraints:

- library folders are flat and do not support nested organization;
- plan day offsets are zero-based non-negative integers;
- compact search results omit workout descriptions and raw parsed structures;
- fetch one full workout only when its content is needed;
- use text `description` syntax for workout authoring and never construct `workout_doc`;
- `calendar_id` must be an integer;
- each scheduling call is limited to 100 workouts;
- calendar conflict checks and explicit approval remain mandatory;
- upstream bulk writes are not documented as transactional;
- after an ambiguous bulk failure, inspect the calendar before retrying;
- deleting a folder or plan permanently deletes its contained workouts.

## Canonical Archetype Boundary

`WORKOUT_LIBRARY.md` will retain all existing workout archetypes and zone-resolution rules. Its usage introduction will change from always writing the archetype directly through `add_or_update_event` to this model:

- the Markdown archetype defines the coach-approved workout structure;
- a matching saved library workout may be reused without retransmitting its description;
- a missing reusable variant may be saved as a persisted instance;
- a bespoke or materially adjusted session remains a direct calendar event unless the athlete wants it saved.

No workout catalogue entries or phase templates will be rewritten as part of this change.

## Error and Safety Behavior

The coach will treat failed `schedule_library` bulk writes as an unknown calendar outcome. It must call `get_events` for the affected range before any retry and must not claim that zero events were created.

Library creation failure will be reported separately from calendar scheduling failure. If a new plan is saved successfully but scheduling fails ambiguously, the saved plan remains reusable; the coach inspects the calendar before deciding whether another schedule call is safe.

The coach will not use `delete_library_item` to resolve calendar conflicts. Calendar events use the existing event deletion tools and confirmation rules; library deletion is reserved for explicit library maintenance.

## Validation

Validation will inspect the canonical skill for these representative scenarios:

1. An existing two-hour Zone 2 ride is found and scheduled without reconstructing its description.
2. A missing `SS-3x10` variant is saved in an appropriate flat folder and then scheduled.
3. A bespoke race-preparation session remains a direct `add_or_update_event` write.
4. An existing matching base plan is reused only after its progression is checked against the approved preview.
5. A new progressive block is saved with correct zero-based day offsets and scheduled only after approval.
6. An ambiguous bulk failure triggers calendar inspection before retry.
7. A folder or plan deletion request states the permanent contained-workout cascade and requires explicit confirmation.

Static checks will confirm that all six tools appear in the tool map, both scheduling modes are documented, the legacy one-event-per-session block loop is no longer the primary batch-write path, and existing `docs/chatgpt-projects/` deletions remain untouched.

## Success Criteria

The update succeeds when the canonical coaching skill:

- reuses suitable saved workouts and plans without forcing every request through the library;
- preserves existing athlete intake, safety, conflict, preview, and approval gates;
- persists new reusable workouts and plans only after approval;
- keeps custom sessions, races, notes, and edits on the direct event path;
- accurately describes library limits, deletion consequences, and ambiguous bulk failures;
- leaves derived ChatGPT artifacts and installed skill copies unchanged.
