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
2. Add credentials to your shell profile (`~/.zshrc` or `~/.bashrc`):
   ```bash
   export INTERVALS_API_KEY=<your-intervals-api-key>
   export INTERVALS_ATHLETE_ID=<your-athlete-id>
   ```
3. Update `cwd` in `.mcp.json` to the path of your cloned repo.

The `.mcp.json` spawns the server automatically via `npm run stdio`. Then load the skill:
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
