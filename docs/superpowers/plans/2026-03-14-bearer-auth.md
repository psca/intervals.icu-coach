# Bearer Token Auth Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add bearer token authentication to the CF Worker and remove hardcoded URL from the coach repo config.

**Architecture:** The Worker checks `Authorization: Bearer <WORKER_SECRET>` on every inbound request, returning 401 immediately for missing or wrong tokens. Claude Code reads the Worker URL and secret from shell env vars via `.mcp.json`. Claude Desktop uses `mcp-remote --header` to inject the token at the proxy layer.

**Tech Stack:** TypeScript, Cloudflare Workers, Wrangler, Vitest (Node pool)

---

## File Structure

**`../intervals.icu-server/` (CF Worker repo):**
- Create: `test/index.test.ts` — new file, 3 auth tests for the Worker `fetch` handler
- Modify: `src/index.ts` — add `WORKER_SECRET` to `Env` interface + auth guard in `fetch`

**`./` (intervals.icu-coach repo):**
- Modify: `.mcp.json` — replace hardcoded URL with `${INTERVALS_MCP_URL}`, add `headers`
- Modify: `CLAUDE.md` — document `INTERVALS_MCP_URL` and `INTERVALS_MCP_SECRET`
- Modify: `skills/triathlon-training/SKILL.md` — update Claude Code + add Desktop setup

---

## Chunk 1: Auth + Config

### Task 1: Worker Bearer Token Guard

**Working directory:** `../intervals.icu-server/`

- [ ] **Step 1: Orient — read `src/index.ts` to confirm export style**

Read `src/index.ts`. Confirm the worker is exported as `export default { async fetch(...) }`. The test in Step 2 imports this default export.

Also run `npx vitest run` to confirm the baseline — all existing tests should pass before any changes.

- [ ] **Step 2: Create `test/index.test.ts` with failing auth tests**

Create a new file `test/index.test.ts`:

```typescript
import { describe, it, expect } from "vitest";
import worker from "../src/index";

describe("auth", () => {
  it("returns 401 with no Authorization header", async () => {
    const env = { API_KEY: "key", ATHLETE_ID: "i123", WORKER_SECRET: "secret" };
    const req = new Request("https://example.com/mcp", { method: "POST" });
    const res = await worker.fetch(req, env);
    expect(res.status).toBe(401);
  });

  it("returns 401 with wrong token", async () => {
    const env = { API_KEY: "key", ATHLETE_ID: "i123", WORKER_SECRET: "secret" };
    const req = new Request("https://example.com/mcp", {
      method: "POST",
      headers: { Authorization: "Bearer wrongtoken" },
    });
    const res = await worker.fetch(req, env);
    expect(res.status).toBe(401);
  });

  it("does not return 401 with correct token", async () => {
    const env = { API_KEY: "key", ATHLETE_ID: "i123", WORKER_SECRET: "secret" };
    const req = new Request("https://example.com/mcp", {
      method: "POST",
      headers: { Authorization: "Bearer secret" },
    });
    const res = await worker.fetch(req, env);
    expect(res.status).not.toBe(401);
  });
});
```

- [ ] **Step 3: Run tests to verify the 3 new tests fail**

```bash
npx vitest run
```

Expected: the 3 new auth tests in `test/index.test.ts` FAIL; all pre-existing tests still PASS.

If pre-existing tests also fail at this point — stop. There is a pre-existing issue unrelated to this change.

- [ ] **Step 4: Add `WORKER_SECRET` to the `Env` interface in `src/index.ts`**

Find the `Env` interface (currently has `API_KEY` and `ATHLETE_ID`). Add the new field:

```typescript
export interface Env {
  API_KEY: string;
  ATHLETE_ID: string;
  WORKER_SECRET: string;
}
```

Note: CF Worker secrets set via `wrangler secret put` are available as `env.WORKER_SECRET` at runtime automatically — no `wrangler.toml` change required.

- [ ] **Step 5: Add the auth guard at the top of the `fetch` handler**

In `src/index.ts`, at the very start of `async fetch(request, env)` — before any MCP logic:

```typescript
const auth = request.headers.get("Authorization");
if (auth !== `Bearer ${env.WORKER_SECRET}`) {
  return new Response("Unauthorized", { status: 401 });
}
```

- [ ] **Step 6: Run all tests and verify they pass**

```bash
npx vitest run
```

Expected: all tests pass, including the 3 new auth tests.

- [ ] **Step 7: Generate a token, set the CF secret, and deploy**

```bash
# Generate a strong random token
TOKEN=$(openssl rand -hex 32)
echo "WORKER_SECRET: $TOKEN"
# ⚠️ Note this value — you will need it for Task 2 docs and your shell profile

# Set the secret non-interactively
echo "$TOKEN" | wrangler secret put WORKER_SECRET

# Deploy
wrangler deploy
```

Expected: `wrangler secret put` confirms the secret was set; `wrangler deploy` succeeds with Worker URL unchanged.

- [ ] **Step 8: Smoke test the deployed auth**

```bash
# No auth — must return 401
curl -s -o /dev/null -w "%{http_code}" \
  -X POST https://<your-worker-name>.<your-account>.workers.dev/mcp
# Expected: 401

# Wrong token — must return 401
curl -s -o /dev/null -w "%{http_code}" \
  -X POST -H "Authorization: Bearer wrongtoken" \
  https://<your-worker-name>.<your-account>.workers.dev/mcp
# Expected: 401

# Correct token — use $TOKEN from Step 7 (must be in the same shell session)
curl -s -o /dev/null -w "%{http_code}" \
  -X POST -H "Authorization: Bearer $TOKEN" \
  https://<your-worker-name>.<your-account>.workers.dev/mcp
# Expected: anything except 401
```

If this shell session is fresh and `$TOKEN` is empty, re-run: `TOKEN=$(wrangler secret list | ...)` — or simply re-run Step 7's `openssl` + `echo` line to regenerate and re-check. The key signal is that the correct token passes and the wrong one 401s.

- [ ] **Step 9: Commit**

```bash
git add src/index.ts test/index.test.ts
git commit -m "feat: add bearer token auth guard to Worker fetch handler"
```

---

### Task 2: Coach Repo Config + Documentation

**Working directory:** `./` (intervals.icu-coach — the repo this plan lives in)

**Files:**
- Modify: `.mcp.json`
- Modify: `CLAUDE.md`
- Modify: `skills/triathlon-training/SKILL.md`

- [ ] **Step 1: Update `.mcp.json`**

**Note for Claude Desktop users:** The `.mcpb` extension (if installed) and `.mcp.json` would both register an `intervals-mcp` server, creating a conflict. Uninstall the `.mcpb` extension from Claude Desktop settings before following this plan. Desktop setup is covered via `claude_desktop_config.json` in Step 4.

Replace the current content of `.mcp.json` with:

```json
{
  "mcpServers": {
    "intervals-mcp": {
      "type": "http",
      "url": "${INTERVALS_MCP_URL}",
      "headers": {
        "Authorization": "Bearer ${INTERVALS_MCP_SECRET}"
      }
    }
  }
}
```

- [ ] **Step 2: Smoke test the Worker accepts the token**

Set the env vars and verify the deployed Worker responds (not 401):

```bash
export INTERVALS_MCP_URL=https://<your-worker-name>.<your-account>.workers.dev/mcp
export INTERVALS_MCP_SECRET=<paste-TOKEN-from-Task-1-Step-7>

curl -s -o /dev/null -w "%{http_code}" \
  -X POST -H "Authorization: Bearer $INTERVALS_MCP_SECRET" \
  $INTERVALS_MCP_URL
# Expected: anything except 401
```

If this returns 401, the deploy in Task 1 Step 7 may have failed. Re-check `wrangler deploy` output before proceeding.

- [ ] **Step 3: Update `CLAUDE.md` MCP Setup section**

Read `CLAUDE.md` first to locate the Claude Code setup block. Replace that block with:

~~~markdown
**Claude Code — env vars required:**

```bash
export INTERVALS_MCP_URL=https://<your-worker-name>.<your-account>.workers.dev/mcp
export INTERVALS_MCP_SECRET=<your-worker-secret>
```

Add both to your shell profile (`~/.zshrc` or `~/.bashrc`). The `.mcp.json` in this repo reads them automatically. No API key, no local process.
~~~

- [ ] **Step 4: Update `skills/triathlon-training/SKILL.md` setup sections**

Read `SKILL.md` first to locate the Claude Code setup block (under `### Claude Code`). Replace that block with:

~~~markdown
### Claude Code

Export these in your shell profile (`~/.zshrc` or `~/.bashrc`):

```bash
export INTERVALS_MCP_URL=https://<your-worker-name>.<your-account>.workers.dev/mcp
export INTERVALS_MCP_SECRET=<your-worker-secret>
```

The `.mcp.json` in this repo reads them automatically. No local process needed.
~~~

Then add a `### Claude Desktop` section directly after the Claude Code section:

~~~markdown
### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "intervals-mcp": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://<your-worker-name>.<your-account>.workers.dev/mcp",
        "--header",
        "Authorization: Bearer YOUR_WORKER_SECRET"
      ]
    }
  }
}
```

Replace `YOUR_WORKER_SECRET` with the token set as the CF `WORKER_SECRET` secret.
Note the space after `Authorization:` — required by the `mcp-remote` header format.
~~~

- [ ] **Step 5: Commit**

```bash
git add .mcp.json CLAUDE.md skills/triathlon-training/SKILL.md
git commit -m "feat: env-based MCP URL/secret, add Desktop setup docs"
```
