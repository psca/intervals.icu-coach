"""
Proxy launcher for intervals-mcp via mcp-remote.
Connects Claude Desktop to the deployed Cloudflare Worker MCP server.
Requires Node.js (npx) to be installed.
"""
import os
import subprocess
import sys

url = os.environ.get("INTERVALS_MCP_URL")
secret = os.environ.get("INTERVALS_MCP_SECRET")

if not url or not secret:
    print("Missing INTERVALS_MCP_URL or INTERVALS_MCP_SECRET", file=sys.stderr)
    sys.exit(1)

subprocess.run(
    ["npx", "mcp-remote", url, "--header", f"Authorization: Bearer {secret}"],
    check=True,
)
