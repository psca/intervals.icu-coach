# intervals.icu Triathlon Coach — Claude Skill

A Claude skill that acts as a triathlon coach, pulling live data from intervals.icu via MCP and delivering per-discipline analysis (swim / bike / run analysed separately — never aggregated).

---

## Setup by Platform

### Claude Code (Local stdio — recommended)

1. Clone and install the MCP server:
   ```bash
   git clone https://github.com/psca/intervals.icu-server
   cd intervals.icu-server
   npm install
   ```
2. Add to your `.mcp.json`:
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

Claude Code will spawn the server automatically. Then load the skill:
```
/plugin install triathlon-training@intervals-icu-coach
```

### Claude Desktop (Extension)

1. Build the extension:
   ```bash
   npx @anthropic-ai/mcpb pack ./desktop-extension
   ```
2. Double-click the generated `.mcpb` to install
3. Enter your **intervals.icu API key** and **Athlete ID** in the install dialog
4. Install the **Triathlon Training** skill from the marketplace (or load skill files manually)

### claude.ai (Web — requires CF Worker)

Deploy the CF Worker from [psca/intervals.icu-server](https://github.com/psca/intervals.icu-server) via Wrangler, then add the Worker URL at **Settings → Integrations → Add integration**. Authentication is handled by GitHub OAuth — no bearer secret required.

Then load the skill from the marketplace.

---

## Skill Files

All skill files live in `skills/triathlon-training/`:

| File | Purpose |
|------|---------|
| `SKILL.md` | Router: natural language trigger table, MCP tool map, data quality gates |
| `COACH.md` | Coach knowledge: how to respond to each type of request, tool sequences, response templates |
| `METRICS_REFERENCE.md` | Thresholds: CTL ramp rates, TSB by race distance, decoupling, VI, EF, SWOLF |
| `WORKOUT_PLANNING.md` | Write-operation guidance for add_or_update_event |

## MCP Server

This skill requires the [psca/intervals.icu-server](https://github.com/psca/intervals.icu-server) MCP server — a TypeScript server that wraps the intervals.icu API and exposes it as MCP tools.

Notable tools beyond the standard intervals.icu API:
- **`get_activity_weather`** — fetches GPS waypoints from the activity and queries Open-Meteo to return feels-like temperature, wind speed/direction, headwind/tailwind %, and precipitation. No API key required.
- **`get_activity_route`** — GPS route data sampled at regular intervals, useful for route and elevation analysis.

Two modes: local stdio (Claude Code / Claude Desktop) and remote Cloudflare Worker with GitHub OAuth (claude.ai Web). See the server repo for full setup and deployment instructions.

---

## Weather Analysis

Weather context is fetched automatically for every outdoor bike and run via the `get_activity_weather` MCP tool. It samples GPS waypoints every 30 minutes and computes temperature, feels-like, wind speed/direction, headwind %, and precipitation — all via Open-Meteo (free, no API key).

## Project Structure

```
intervals.icu-coach/
├── skills/triathlon-training/
│   ├── SKILL.md
│   ├── COACH.md
│   ├── METRICS_REFERENCE.md
│   └── WORKOUT_PLANNING.md
├── desktop-extension/         ← pre-built .mcpb (drag-and-drop install)
├── .mcp.json                  ← Claude Code config (stdio, spawns npm run stdio)
└── .claude-plugin/
    └── plugin.json            ← marketplace plugin manifest
```
