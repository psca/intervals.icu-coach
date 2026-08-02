# Harness-Native Artifacts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace raw-HTML output instructions with harness-native artifacts and a Markdown fallback.

**Architecture:** The canonical coach reference owns the output contract. The derived single-file project source mirrors it exactly. No MCP tool or server response changes are needed.

**Tech Stack:** Markdown documentation; `rg` structural validation.

## Global Constraints

- Do not name a specific AI product or harness.
- Prefer a harness-supported visual artifact when available.
- Fall back to a compact Markdown card or table when no artifact is supported.
- Never instruct the model to emit raw HTML.
- Keep `COACH.md` and the derived project source behaviorally equivalent.

---

### Task 1: Replace the output contract and validate parity

**Files:**
- Modify: `skills/triathlon-training/references/COACH.md`
- Modify: `docs/chatgpt-projects/TRIATHLON_TRAINING_CHATGPT_PROJECT_SKILL.md`

**Interfaces:**
- Consumes: Existing seven output-template headings and metric specifications.
- Produces: A client-neutral artifact contract with an explicit Markdown fallback.

- [x] **Step 1: Add the Markdown fallback contract to both sources**

Replace each HTML-artifact instruction with:

```markdown
Use a visual artifact supported by the current harness when available. Otherwise, present this as a compact Markdown card or table. Do not emit raw HTML.
```

Rename each `HTML artifact` heading to `Artifact or Markdown fallback`; retain the existing contents of each card specification.

- [x] **Step 2: Verify raw HTML instructions are absent**

Run:

```bash
rg -n -i 'render an html artifact|html artifact' skills/triathlon-training/references/COACH.md docs/chatgpt-projects/TRIATHLON_TRAINING_CHATGPT_PROJECT_SKILL.md
```

Expected: no matches.

- [x] **Step 3: Verify both maintained sources contain the fallback contract**

Run:

```bash
rg -n -F 'Use a visual artifact supported by the current harness when available. Otherwise, present this as a compact Markdown card or table. Do not emit raw HTML.' skills/triathlon-training/references/COACH.md docs/chatgpt-projects/TRIATHLON_TRAINING_CHATGPT_PROJECT_SKILL.md
```

Expected: seven matches in each file.

- [x] **Step 4: Review the final diff**

Run:

```bash
git -C intervals.icu-coach diff --check
git -C intervals.icu-coach diff -- skills/triathlon-training/references/COACH.md docs/chatgpt-projects/TRIATHLON_TRAINING_CHATGPT_PROJECT_SKILL.md
```

Expected: no whitespace errors; only output-contract wording and headings differ.
