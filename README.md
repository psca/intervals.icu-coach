# intervals.icu Triathlon Coach

A triathlon coaching setup for Claude and ChatGPT that uses live intervals.icu data through MCP.

## Table of Contents

- [Quick start](#quick-start)
- [Claude](#claude)
- [ChatGPT](#chatgpt)
- [What happens during sign-in](#what-happens-during-sign-in)
- [Artifacts in this repo](#artifacts-in-this-repo)
- [Developer setup](#developer-setup)
- [Skill files](#skill-files)
- [MCP server](#mcp-server)
- [Weather analysis](#weather-analysis)
- [Project structure](#project-structure)

## Quick start

Start from your chat application, not from this repository.

1. In `Claude` or `ChatGPT`, add the intervals.icu connector using:
   ```
   https://intervals-mcp.anthonypoh1998.workers.dev/mcp
   ```
2. Add the coaching layer for your app:
   - `Claude`: upload the coach skill ZIP
   - `ChatGPT`: add the Project source file
3. Let the chat application begin the OAuth flow when it needs the connection.
4. Sign in with GitHub or Google when prompted.
5. On first setup, enter your intervals.icu `Athlete ID` and `API Key`.
6. Return to the chat application and continue normally.

## Claude

1. Open Claude and go to `https://claude.ai/customize`.
2. Under `Connectors`, add a custom connector with:
   ```
   https://intervals-mcp.anthonypoh1998.workers.dev/mcp
   ```
3. Package the skill from the `skills/triathlon-training/` folder.
4. Under `Skills`, create or upload the coach skill.
5. Use the ZIP you packaged from:
   ```
   skills/triathlon-training/
   ```
6. Claude will begin the OAuth flow when it needs the connection.

Claude currently installs the connector and the skill separately for this setup.

## ChatGPT

1. Open ChatGPT and enable developer mode if your plan requires it for custom apps.
2. In ChatGPT settings, open `Apps & Connectors`.
3. Add this custom app URL:
   ```
   https://intervals-mcp.anthonypoh1998.workers.dev/mcp
   ```
4. ChatGPT will begin the OAuth flow when it needs the connection.

The connector provides tool access. The former single-file ChatGPT Project source has been retired; this repo no longer maintains a ChatGPT coaching package. The canonical coaching instructions live in [skills/triathlon-training/](skills/triathlon-training/).

## What happens during sign-in

The sign-in flow always begins from the chat application.

1. ChatGPT or Claude asks to connect the intervals.icu app / connector.
2. The app opens the hosted OAuth flow in the browser.
3. You sign in with GitHub or Google.
4. On first connection, the worker asks for your intervals.icu `Athlete ID` and `API Key`.
5. After saving those credentials, the chat application returns to the conversation with live tool access.

To find your intervals.icu credentials:

1. Open `https://intervals.icu/settings`
2. Scroll to `Developer Settings`
3. Copy your `Athlete ID` and `API Key`

## Artifacts in this repo

- `skills/triathlon-training.zip`
  - a convenience artifact in the repo, but users should expect to package `skills/triathlon-training/` themselves for the normal Claude skill flow
- `desktop-extension.mcpb`
  - still works, but it is no longer the primary end-user install path in this repo
  - keep it in mind mainly for Claude Code / developer-oriented workflows

## Developer setup

This section is for local development, maintenance, and packaging work.

### Claude Code (local stdio)

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
3. Load the skill:
   ```
   /plugin install triathlon-training@intervals-icu-coach
   ```

### Desktop extension and packaging

The desktop extension path still works, but it is not the recommended user-facing flow for this repo anymore.

1. Pack the extension if you need to maintain it:
   ```bash
   npx @anthropic-ai/mcpb pack ./desktop-extension
   ```
2. Use `desktop-extension.mcpb` only when that workflow is specifically what you need.
3. For normal end-user docs, prefer:
   - Claude connector + a user-packaged ZIP from `skills/triathlon-training/`
   - ChatGPT connector + Project source file

## Skill files

All skill files live in `skills/triathlon-training/`:

| File | Purpose |
|------|---------|
| `SKILL.md` | Router: natural language trigger table, MCP tool map, data quality gates |
| `COACH.md` | Coach knowledge: how to respond to each type of request, tool sequences, response templates |
| `METRICS_REFERENCE.md` | Thresholds: CTL ramp rates, TSB by race distance, decoupling, VI, EF, SWOLF |
| `WORKOUT_PLANNING.md` | Write-operation guidance for add_or_update_event |

## MCP server

This setup uses the [psca/intervals.icu-server](https://github.com/psca/intervals.icu-server) MCP server, a TypeScript server that wraps the intervals.icu API and exposes it as MCP tools.

Notable tools beyond the standard intervals.icu API:

- `get_activity_weather` — fetches GPS waypoints from the activity and queries Open-Meteo to return feels-like temperature, wind speed/direction, headwind/tailwind %, and precipitation
- `get_activity_route` — GPS route data sampled at regular intervals, useful for route and elevation analysis

## Weather analysis

Weather context is fetched automatically for outdoor bike and run activities via `get_activity_weather`. It samples GPS waypoints every 30 minutes and computes temperature, feels-like temperature, wind speed/direction, headwind %, and precipitation through Open-Meteo.

## Project structure

```text
intervals.icu-coach/
├── skills/
│   ├── triathlon-training/
│   │   ├── SKILL.md
│   │   ├── COACH.md
│   │   ├── METRICS_REFERENCE.md
│   │   └── WORKOUT_PLANNING.md
│   └── triathlon-training.zip
├── desktop-extension.mcpb
├── .mcp.json
└── .claude-plugin/
    └── plugin.json
```
