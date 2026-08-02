# Harness-Native Artifacts Design

## Goal

Prevent raw HTML from appearing in coaching responses while preserving the compact, data-rich output intended for each analysis command.

## Design

The canonical coaching reference will instruct the model to choose a visual artifact format supported by its current harness. When no suitable artifact is available, it will render the same information as a compact Markdown card or table. Raw HTML is not a fallback.

The maintained single-file project source will mirror this contract exactly. The MCP server is not changed: it continues to return text content and structured data for the model to interpret.

## Scope

- Update the seven output templates in `skills/triathlon-training/references/COACH.md`.
- Mirror the same wording and headings in `docs/chatgpt-projects/TRIATHLON_TRAINING_CHATGPT_PROJECT_SKILL.md`.
- Validate that neither file retains an HTML-artifact instruction and that both contain the fallback contract.

## Out of Scope

- MCP response types, server code, connector configuration, and historical design/plan documents.
