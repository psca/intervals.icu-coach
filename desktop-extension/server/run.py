"""
Launcher for intervals-mcp-server via uvx.
The actual server is installed from PyPI/git by uvx at runtime.
"""
import subprocess
import sys

subprocess.run(
    [
        "uvx",
        "--from",
        "git+https://github.com/mvilanova/intervals-mcp-server.git",
        "python",
        "-m",
        "intervals_mcp_server.server",
    ],
    check=True,
)
