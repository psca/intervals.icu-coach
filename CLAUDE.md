# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A Claude skill that acts as a triathlon coach, pulling live data from intervals.icu via MCP. The skill enforces per-discipline analysis (swim/bike/run never aggregated).

## MCP Setup

1. Clone and install the server:
   ```bash
   git clone https://github.com/psca/intervals.icu-server
   cd intervals.icu-server
   npm install
   ```
2. Add credentials to `.mcp.json` — Claude Code spawns the server automatically:
   ```json
   {
     "mcpServers": {
       "intervals-mcp": {
         "type": "stdio",
         "command": "npm",
         "args": ["run", "stdio"],
         "env": {
           "API_KEY": "your_intervals_icu_api_key",
           "ATHLETE_ID": "i12345"
         }
       }
     }
   }
   ```

## MCP Server

TypeScript server at `github.com:psca/intervals.icu-server`. Two modes: local stdio (Claude Code / Desktop) and remote Cloudflare Worker (Claude Web — see server repo for deploy instructions). Tools:
- All standard intervals.icu tools (activities, events, wellness)
- `get_activity_weather` — GPS + Open-Meteo weather pipeline with headwind/tailwind analysis
- `get_activity_route` — GPS route data sampled at regular intervals for route and elevation analysis

## Architecture

**Skill files** (`skills/triathlon-training/` — loaded via marketplace or manually):

| File | Role |
|------|------|
| `SKILL.md` | Router: natural language trigger table, MCP tool map, data quality gates |
| `COACH.md` | Coach knowledge: how to respond to each type of request, tool sequences, response templates |
| `METRICS_REFERENCE.md` | Thresholds: CTL ramp rates, TSB, decoupling, VI, IF, EF, SWOLF |
| `WORKOUT_PLANNING.md` | Write-operation guidance for `add_or_update_event` |

## Key Constraints

- **Never aggregate swim/bike/run** into a single training load figure — this is a hard invariant enforced throughout the skill
- Use `get_activity_weather` for weather context — single call returns full GPS + Open-Meteo summary; do not call `get_activity_route` manually for weather
- `get_activity_streams` is high token cost — only call it when aerobic decoupling or VI analysis explicitly requires second-by-second data
- MCP tool call order matters: `get_activities` → `get_wellness_data` → `get_activity_details` for fitness status; `get_activity_details` → `get_activity_intervals` → `get_activity_streams` for single activity analysis

## Testing Changes

No automated tests — validation is manual. Load the skill in Claude Code and invoke each scenario conversationally. See the Validation checklist in `docs/superpowers/plans/` for scenarios to cover.
