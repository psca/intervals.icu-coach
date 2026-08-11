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
