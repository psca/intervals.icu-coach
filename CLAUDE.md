# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A Claude skill that acts as a triathlon coach, pulling live data from intervals.icu via MCP. The skill enforces per-discipline analysis (swim/bike/run never aggregated).

## MCP Setup

**Claude Code — team/project config (`.mcp.json` already present):**

No local env vars needed. Credentials (`API_KEY`, `ATHLETE_ID`) are stored as Cloudflare Worker secrets on the deployed server.

The `.mcp.json` points to the deployed CF Worker:
```
https://intervals-mcp.anthonypoh1998.workers.dev/mcp
```

No `uvx`, no Python, no local process required.

## MCP Server

TypeScript Cloudflare Worker at `github.com:psca/intervals.icu-server`. Deployed via Wrangler. Tools:
- All standard intervals.icu tools (activities, events, wellness)
- `get_activity_weather` — full GPS + Open-Meteo weather pipeline, server-side (replaces `weather.py`)
- `get_activity_stream_sampled` — GPS + bearing at 30-min intervals (still available for direct use)

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
- Use `get_activity_weather` for weather context — single call returns full GPS + Open-Meteo summary; do not call `get_activity_stream_sampled` manually for weather
- `get_activity_streams` is high token cost — only call it when aerobic decoupling or VI analysis explicitly requires second-by-second data
- MCP tool call order matters: `get_activities` → `get_wellness_data` → `get_activity_details` for fitness status; `get_activity_details` → `get_activity_intervals` → `get_activity_streams` for single activity analysis
