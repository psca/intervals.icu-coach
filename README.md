# intervals.icu Triathlon Coach — Claude Skill

A Claude skill that acts as a triathlon coach, pulling live data from intervals.icu via MCP and delivering per-discipline analysis (swim / bike / run analysed separately — never aggregated).

## Prerequisites

You need a deployed **intervals-mcp Worker** — a Cloudflare Worker that connects to your intervals.icu account.

1. Follow the setup guide at [psca/intervals.icu-server](https://github.com/psca/intervals.icu-server)
2. Deploy your own Worker with your `API_KEY`, `ATHLETE_ID`, and `WORKER_SECRET` set as CF secrets
3. Note your Worker URL: `https://intervals-mcp.<your-account>.workers.dev/mcp`

---

## Setup by Platform

### Claude Desktop (Extension)

1. Build the extension:
   ```bash
   npx @anthropic-ai/mcpb pack ./desktop-extension
   ```
2. Double-click the generated `.mcpb` to install
3. Enter your **Worker URL** and **Worker Secret** in the install dialog
4. Install the **Triathlon Training** skill from the marketplace (or load skill files manually)

### Claude Code

Add to your shell profile (`~/.zshrc` or `~/.bashrc`):
```bash
export INTERVALS_MCP_URL=https://intervals-mcp.<your-account>.workers.dev/mcp
export INTERVALS_MCP_SECRET=<your-worker-secret>
```

The `.mcp.json` in this repo picks them up automatically. Then load the skill:
```
/plugin install triathlon-training@intervals-icu-coach
```

### claude.ai (Web)

Add a custom connector at **Settings → Integrations → Add integration**:
- URL: `https://intervals-mcp.<your-account>.workers.dev/mcp`

Then load the skill from the marketplace.

---

## Local MCP (Alternative — no Worker)

If you prefer to run the MCP server locally instead of deploying a Worker:

```bash
claude mcp add intervals \
  --env API_KEY=<your-intervals-api-key> \
  --env ATHLETE_ID=<i12345> \
  -- uvx \
  --from git+https://github.com/psca/intervals-mcp-server.git \
  python -m intervals_mcp_server.server
```

Or via `.mcp.json` (replace the `type: http` entry with the `uvx` command form). Note: the `get_activity_weather` tool is only available on the CF Worker — local MCP uses the Python fork which does not include it.

---

## Skill Files

All skill files live in `skills/triathlon-training/`:

| File | Purpose |
|------|---------|
| `SKILL.md` | Entry point: 5-step workflow, MCP tool map, command patterns |
| `METRICS_REFERENCE.md` | Thresholds: CTL ramp rates, TSB by race distance, decoupling, VI, EF, SWOLF |
| `COACH_PERSONA.md` | Communication style and liability guardrail |
| `DISCIPLINE_ANALYSIS.md` | Per-sport analysis sequences with exact MCP tool call order |

## Weather Analysis

Weather context is fetched automatically for every outdoor bike and run via the `get_activity_weather` MCP tool (CF Worker only). It samples GPS waypoints every 30 minutes and computes temperature, feels-like, wind speed/direction, headwind %, and precipitation — all via Open-Meteo (free, no API key).

## Project Structure

```
intervals.icu-coach/
├── skills/triathlon-training/
│   ├── SKILL.md
│   ├── METRICS_REFERENCE.md
│   ├── COACH_PERSONA.md
│   └── DISCIPLINE_ANALYSIS.md
├── desktop-extension/         ← source for .mcpb (pack with npx @anthropic-ai/mcpb)
│   ├── manifest.json
│   ├── icon.png
│   └── server/run.py
├── .mcp.json                  ← Claude Code config (reads INTERVALS_MCP_URL/SECRET from env)
└── .claude-plugin/
    └── plugin.json            ← marketplace plugin manifest
```
