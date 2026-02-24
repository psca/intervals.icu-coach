# intervals.icu Triathlon Coach — Claude Skill

A Claude skill that acts as a triathlon coach, pulling live data from intervals.icu via MCP and delivering per-discipline analysis (swim / bike / run analysed separately — never aggregated).

## Quick Start

### Claude Code (CLI)

1. **Add the MCP server** (one-time):
   ```bash
   claude mcp add --env INTERVALS_API_KEY=<your-key> --env INTERVALS_ATHLETE_ID=<i12345> \
     intervals-mcp uvx \
     --from git+https://github.com/mvilanova/intervals-mcp-server.git \
     python -m intervals_mcp_server.server
   ```

2. **Or use `.mcp.json`** (team/project-level):
   ```bash
   export INTERVALS_API_KEY=<your-key>
   export INTERVALS_ATHLETE_ID=<i12345>
   # .mcp.json is already in this repo — Claude Code picks it up automatically
   ```

3. **Load the skill** — Claude Code reads `.claude/skills/triathlon-training/` automatically.

4. **Start coaching:**
   ```
   Analyse my last 6 weeks of running
   Am I ready for my A-race in 3 weeks?
   How's my swim fitness trending?
   ```

### Claude Desktop (Desktop Extension)

1. Pack the extension:
   ```bash
   npx @anthropic-ai/mcpb pack ./desktop-extension
   ```
2. Double-click the generated `.mcpb` file.
3. Enter your intervals.icu API Key and Athlete ID in the install dialog.

## Skill Files

| File | Purpose |
|------|---------|
| `SKILL.md` | Entry point: 5-step workflow, MCP tool map, command patterns |
| `METRICS_REFERENCE.md` | Thresholds: CTL ramp rates, TSB by race distance, decoupling, VI, EF, SWOLF |
| `COACH_PERSONA.md` | Communication style and liability guardrail |
| `DISCIPLINE_ANALYSIS.md` | Per-sport analysis sequences with exact MCP tool call order |

## Credentials

Find them at **intervals.icu → Settings → API**:
- **API Key** — long alphanumeric string
- **Athlete ID** — format `i12345`

## Project Structure

```
intervals.icu-coach/
├── .claude/
│   └── skills/
│       └── triathlon-training/
│           ├── SKILL.md
│           ├── METRICS_REFERENCE.md
│           ├── COACH_PERSONA.md
│           └── DISCIPLINE_ANALYSIS.md
├── desktop-extension/
│   ├── manifest.json
│   └── icon.png
├── .mcp.json          ← team/project MCP config
├── README.md
└── [original .md files kept for reference]
```
# intervals.icu-coach
