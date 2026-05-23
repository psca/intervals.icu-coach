# Repository Guidelines

## Project Structure & Module Organization

This repository packages the `triathlon-training` Claude skill for intervals.icu coaching. The skill pulls live data through MCP and must analyze swim, bike, and run separately. The main source lives in `skills/triathlon-training/`: `SKILL.md` is the router and MCP tool map, while `references/COACH.md`, `METRICS_REFERENCE.md`, `WORKOUT_PLANNING.md`, `WORKOUT_LIBRARY.md`, and `BLOCK_TEMPLATES.md` hold coaching rules and reusable guidance. Plugin metadata is stored in `.claude-plugin/`; edit `.claude-plugin/marketplace.json` first, then generate `.claude-plugin/plugin.json`. `docs/superpowers/` contains design notes and implementation plans. `desktop-extension.mcpb` is the packaged desktop extension artifact.

## Build, Test, and Development Commands

- `npm install` installs the local dependency set, currently `@openai/codex`.
- `./scripts/sync-plugin.sh` regenerates `.claude-plugin/plugin.json` from `.claude-plugin/marketplace.json`; requires `jq`.
- `/plugin install triathlon-training@intervals-icu-coach` loads the skill in Claude Code after the plugin is available.
- `npx @anthropic-ai/mcpb pack ./desktop-extension` is documented for packaging a desktop extension, but confirm the `desktop-extension/` source directory exists before running it.

There are no npm scripts at present, so do not document or rely on `npm test`, `npm run build`, or `npm run lint` until they are added.

## MCP Setup & Runtime Assumptions

This skill requires the external `psca/intervals.icu-server` MCP server. For local stdio use, clone that server, run `npm install`, and configure `.mcp.json` with `API_KEY` and `ATHLETE_ID`; Claude Code spawns the server with `npm run stdio`. Remote Claude Web usage can connect to the deployed Cloudflare Worker integration documented in `README.md`.

Key MCP rules: use `get_activity_weather` for outdoor ride/run weather context; do not manually call `get_activity_route` just to calculate weather. Treat `get_activity_streams` as high token cost and use it only for decoupling or variability-index analysis that needs second-by-second data. For fitness status, follow `get_activities` -> `get_wellness_data` -> `get_activity_details`. For single-activity analysis, follow `get_activity_details` -> `get_activity_intervals` -> `get_activity_streams` only if needed.

## Coding Style & Naming Conventions

Most changes are Markdown and JSON. Use concise headings, short imperative guidance, and fenced examples for commands or MCP payloads. Keep skill filenames uppercase where established (`SKILL.md`, `COACH.md`) and reference files in `skills/triathlon-training/references/` as uppercase snake case. Preserve JSON with two-space indentation. Shell scripts should remain POSIX `sh` unless a feature requires Bash.

## Coaching Invariants

Never aggregate swim, bike, and run into a single training-load figure. Surface missing data instead of inferring across disciplines. Before analysis, check for enough activity history, discipline coverage, CTL/ATL/TSB availability, and HRV presence when recovery is discussed.

## Testing Guidelines

Validation is manual. Load the skill in Claude Code or Claude Desktop with the intervals.icu MCP server configured, then exercise the major request types: wellness, fitness status, last activity, weekly summary, race readiness, scheduling, and training-block creation. For write operations, verify planned workouts use the `description` workout syntax and do not dump raw JSON into event descriptions.

## Commit & Pull Request Guidelines

Recent history uses Conventional Commit-style subjects such as `docs: ...`, `fix: ...`, `feat: ...`, and `refactor: ...`. Keep commits scoped to one behavior or document area. Pull requests should summarize the changed coaching behavior or packaging metadata, list manual validation performed, and mention any MCP setup assumptions. Include screenshots only when changing install or desktop-extension workflows.

## Security & Configuration Tips

Never commit intervals.icu API keys, athlete IDs, or local `.mcp.json` credentials. Keep examples generic, such as `API_KEY=your_intervals_icu_api_key` and `ATHLETE_ID=i12345`.
