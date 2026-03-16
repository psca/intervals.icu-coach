# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A Claude skill that acts as a triathlon coach, pulling live data from intervals.icu via MCP. The skill enforces per-discipline analysis (swim/bike/run never aggregated).

## MCP Setup

**Local mode (Claude Code + Claude Desktop):**

1. Clone and install the server:
   ```bash
   git clone https://github.com/psca/intervals.icu-server
   cd intervals.icu-server
   npm install
   ```
2. Set credentials in your shell profile (`~/.zshrc` or `~/.bashrc`):
   ```bash
   export INTERVALS_API_KEY=<your-intervals-api-key>
   export INTERVALS_ATHLETE_ID=<your-athlete-id>
   ```
3. Update `cwd` in `.mcp.json` to the cloned repo path — Claude Code will spawn the server automatically via `npm run stdio`.

**Remote mode (Claude Web only):**

Deploy the CF Worker from [intervals.icu-server](https://github.com/psca/intervals.icu-server) via Wrangler, then add the Worker URL to Claude Web MCP settings. Authentication is handled by GitHub OAuth — no Bearer secret required.

## MCP Server

TypeScript server at `github.com:psca/intervals.icu-server`. Runs locally via `npm run stdio` or remotely as a Cloudflare Worker. Tools:
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
