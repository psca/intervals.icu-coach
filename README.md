# intervals.icu Triathlon Coach — Claude Skill

A Claude skill that acts as a triathlon coach, pulling live data from intervals.icu via MCP and delivering per-discipline analysis (swim / bike / run analysed separately — never aggregated).

## Quick Start

### Claude Desktop (Marketplace)

1. Install the **Triathlon Training** skill from the Claude skills marketplace.
2. The skill includes the intervals.icu MCP connector — enter your API Key and Athlete ID when prompted.

### Claude Desktop (Desktop Extension)

1. Double-click `intervals-mcp-1.0.0.mcpb` to install.
2. Enter your intervals.icu API Key and Athlete ID in the install dialog.
3. Install the **Triathlon Training** skill separately from the marketplace.

To repack the extension after changes:
```bash
npx @anthropic-ai/mcpb pack ./desktop-extension
# Output goes to parent dir — rename/move manually
```

### Claude Code (CLI)

1. **Add the MCP server** (one-time):
   ```bash
   claude mcp add intervals \
     --env API_KEY=<your-key> \
     --env ATHLETE_ID=<i12345> \
     -- uvx \
     --from git+https://github.com/psca/intervals-mcp-server.git \
     python -m intervals_mcp_server.server
   ```

2. **Or use `.mcp.json`** (team/project-level):
   ```bash
   export INTERVALS_API_KEY=<your-key>
   export INTERVALS_ATHLETE_ID=<i12345>
   # .mcp.json is already in this repo — Claude Code picks it up automatically
   ```

3. **Start coaching:**
   ```
   Analyse my last 6 weeks of running
   Am I ready for my A-race in 3 weeks?
   How did I do on activity i131201794?
   ```

## Credentials

Find them at **intervals.icu → Settings → API**:
- **API Key** — long alphanumeric string
- **Athlete ID** — format `i12345`

## Skill Files

All skill files live in `skills/triathlon-training/`:

| File | Purpose |
|------|---------|
| `SKILL.md` | Entry point: 5-step workflow, MCP tool map, command patterns |
| `METRICS_REFERENCE.md` | Thresholds: CTL ramp rates, TSB by race distance, decoupling, VI, EF, SWOLF |
| `COACH_PERSONA.md` | Communication style and liability guardrail |
| `DISCIPLINE_ANALYSIS.md` | Per-sport analysis sequences with exact MCP tool call order |
| `scripts/weather.py` | Weather context script — called by agent for bike/run analysis |

## Weather Analysis

The skill fetches weather context for every outdoor bike and run using Open-Meteo (free, no API key). It samples GPS waypoints every 30 minutes along the route and computes:

- Temperature and feels-like (accounts for humidity + wind chill)
- Prevailing wind speed and direction
- Headwind % and tailwind % (per-second bearing matched to nearest waypoint)
- Max rain and snow

**Platform support:**
- **Claude Code** — full weather via `weather.py` script (requires Bash)
- **Claude Desktop** — full weather via WebFetch to Open-Meteo directly
- **claude.ai** — weather unavailable (network egress blocked)

## MCP Server

Uses a custom fork at [psca/intervals-mcp-server](https://github.com/psca/intervals-mcp-server) which adds:
- `get_activity_stream_sampled` — returns GPS + bearing at 30-min intervals (no truncation, correct lat/lng separation)
- Fixed `get_activity_streams` longitude handling (`data2` field previously dropped)

## Project Structure

```
intervals.icu-coach/
├── .claude-plugin/
│   └── plugin.json            ← marketplace plugin manifest
├── skills/triathlon-training/
│   ├── SKILL.md
│   ├── METRICS_REFERENCE.md
│   ├── COACH_PERSONA.md
│   ├── DISCIPLINE_ANALYSIS.md
│   └── scripts/
│       └── weather.py         ← weather context script (bundled with skill)
├── desktop-extension/
│   ├── manifest.json          ← points to psca/intervals-mcp-server
│   ├── icon.png
│   └── server/run.py
├── tools/
│   └── weather.py             ← development copy (keep in sync with scripts/)
├── .mcp.json                  ← team/project MCP config
└── intervals-mcp-1.0.0.mcpb  ← pre-built desktop extension
```
