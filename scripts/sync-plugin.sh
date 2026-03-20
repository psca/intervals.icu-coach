#!/bin/sh
# Derives .claude-plugin/plugin.json from .claude-plugin/marketplace.json
# Run this after editing marketplace.json

set -e

MARKETPLACE=".claude-plugin/marketplace.json"
PLUGIN=".claude-plugin/plugin.json"

if ! command -v jq >/dev/null 2>&1; then
  echo "Error: jq is required. Install with: brew install jq"
  exit 1
fi

jq '{
  name: .name,
  version: .metadata.version,
  description: .metadata.description,
  author: { name: .owner.name }
}' "$MARKETPLACE" > "$PLUGIN"

echo "✓ $PLUGIN updated from $MARKETPLACE"
