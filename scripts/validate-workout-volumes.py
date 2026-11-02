#!/usr/bin/env python3
"""Check explicit default totals against expanded workout steps (no MCP calls)."""

import argparse
import re
from pathlib import Path


def check(path):
    checked = 0
    failures = []
    for block in re.split(r"(?m)^### ", path.read_text())[1:]:
        name = block.splitlines()[0]
        declared = re.search(r"\*\*Default (distance|duration):\*\* (\d+)(m|min)\b", block)
        if not declared:
            continue
        kind, amount, _ = declared.groups()
        multiplier = 1
        metres = seconds = 0
        for line in block.splitlines()[1:]:
            line = line.strip()
            if not line or line == "---" or line.startswith(("#", "- **")):
                continue
            if not line.startswith("-"):
                repeat = re.search(r"\b(\d+)x$", line)
                multiplier = int(repeat.group(1)) if repeat else 1
                continue
            step = re.match(r"- (\d+)(mtr|m|s)\b", line)
            if not step:
                failures.append(f"{name}: cannot expand step {line!r}")
                continue
            value, unit = step.groups()
            value = int(value) * multiplier
            if unit == "mtr":
                metres += value
            else:
                seconds += value * (60 if unit == "m" else 1)
        actual = metres if kind == "distance" else seconds
        expected = int(amount) * (60 if kind == "duration" else 1)
        if actual != expected:
            failures.append(f"{name}: declared {expected}, expanded {actual} ({kind} base units)")
        checked += 1
    if checked == 0:
        failures.append("No explicit defaults found; volume accounting is not covered.")
    for failure in failures:
        print(f"FAIL: {failure}")
    if failures:
        return 1
    print(f"Validated {checked} explicit workout defaults against expanded steps.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("library", nargs="?", type=Path, default=Path(__file__).resolve().parent.parent / "skills/triathlon-training/references/WORKOUT_LIBRARY.md")
    raise SystemExit(check(parser.parse_args().library))
