# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A Claude skill that acts as a triathlon coach, pulling live data from intervals.icu via MCP. The skill enforces per-discipline analysis (swim/bike/run never aggregated).

## MCP Setup

**Claude Code — one-time setup:**
```bash
claude mcp add intervals \
  --env API_KEY=your_api_key_here \
  --env ATHLETE_ID=your_athlete_id_here \
  -- uvx \
  --from git+https://github.com/mvilanova/intervals-mcp-server.git \
  python -m intervals_mcp_server.server
```

**Claude Code — team/project config (`.mcp.json` already present):**
```bash
export INTERVALS_API_KEY=<your-key>
export INTERVALS_ATHLETE_ID=<i12345>  # format: i followed by number
```

Note: `.mcp.json` references `${INTERVALS_API_KEY}` and `${INTERVALS_ATHLETE_ID}` — the env var names differ from what `.mcp.json` passes as `API_KEY` / `ATHLETE_ID` to the server.

## Desktop Extension

Pack command:
```bash
npx @anthropic-ai/mcpb pack ./desktop-extension
# Output goes to parent dir as desktop-extension.mcpb — rename/move manually
```

The packed `.mcpb` is pre-built at `intervals-mcp-1.0.0.mcpb`. Double-click to install in Claude Desktop; credentials are entered in the install dialog.

## Architecture

**Skill files** (`skills/triathlon-training/` — loaded via marketplace or manually):

| File | Role |
|------|------|
| `SKILL.md` | Entry point: 5-step workflow, MCP tool map, command patterns, data quality gates |
| `METRICS_REFERENCE.md` | All thresholds: CTL ramp rates, TSB by race distance, decoupling %, VI, IF, EF, SWOLF |
| `COACH_PERSONA.md` | Output style and liability guardrail |
| `DISCIPLINE_ANALYSIS.md` | Per-sport analysis sequences with exact MCP tool call order |

**Desktop extension** (`desktop-extension/`):
- `manifest.json` — manifest_version `"0.3"`, requires `author` field, `sensitive` (not `secret`) for API key
- `server/run.py` — thin launcher that calls `uvx` to fetch and run the MCP server at runtime
- `icon.png` — 128×128 (512×512 recommended for quality)

## Key Constraints

- **Never aggregate swim/bike/run** into a single training load figure — this is a hard invariant enforced throughout the skill
- `get_activity_streams` is high token cost — only call it when aerobic decoupling or VI analysis explicitly requires second-by-second data
- MCP tool call order matters: `get_activities` → `get_wellness_data` → `get_activity_details` for fitness status; `get_activity_details` → `get_activity_intervals` → `get_activity_streams` for single activity analysis
