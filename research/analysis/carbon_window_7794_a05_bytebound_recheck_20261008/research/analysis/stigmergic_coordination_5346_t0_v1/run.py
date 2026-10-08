"""Single deterministic T0 invocation; raw output is append-only by study path."""

import json
import sys
from pathlib import Path

from candidate import run_all


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python -B run.py OUTPUT.json", file=sys.stderr)
        return 2
    output = Path(sys.argv[1])
    if output.exists():
        print("refusing to overwrite existing raw output", file=sys.stderr)
        return 3
    raw = run_all()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS_FINITE_T0_EXECUTED", "cells": raw["cell_count"],
                      "scenarios": raw["scenario_count"], "output": str(output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
