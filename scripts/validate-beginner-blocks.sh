#!/bin/sh

set -eu
PATH="${PATH}:/opt/homebrew/bin:/usr/local/bin"


SKILL="skills/triathlon-training/SKILL.md"
COACH="skills/triathlon-training/references/COACH.md"
BLOCKS="skills/triathlon-training/references/BLOCK_TEMPLATES.md"
LIBRARY="skills/triathlon-training/references/WORKOUT_LIBRARY.md"
CHATGPT="docs/chatgpt-projects/TRIATHLON_TRAINING_CHATGPT_PROJECT_SKILL.md"

has_text() {
  pattern=$1
  file=$2
  if command -v rg >/dev/null 2>&1; then
    rg -q --fixed-strings "$pattern" "$file"
  else
    grep -F -q "$pattern" "$file"
  fi
}

match_regex() {
  pattern=$1
  if command -v rg >/dev/null 2>&1; then
    rg -q "$pattern"
  else
    grep -E -q "$pattern"
  fi
}

require_text() {
  pattern=$1
  file=$2
  label=$3
  if ! has_text "$pattern" "$file"; then
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

if printf '%s\n' "$five_to_ten" | match_regex 'Threshold|VO2max'; then
  echo 'FAIL: 5K-to-10K contains threshold or VO2max work'
  exit 1
fi

if printf '%s\n' "$beginner_bike" | match_regex 'Tempo|Threshold|VO2max|Maximal'; then
  echo 'FAIL: beginner cycling contains intensity'
  exit 1
fi

if printf '%s\n' "$endurance_bike" | match_regex 'VO2max|Maximal'; then
  echo 'FAIL: cycling endurance contains maximal work'
  exit 1
fi


echo "Beginner block validation passed"
