"""One-shot output wrapper: candidate source stays read-only; artifact is exclusive."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from candidate import run


def main(arguments: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if arguments is None else arguments
    if len(arguments) != 1:
        print("usage: run_candidate.py OUTPUT_JSON", file=sys.stderr)
        return 2
    result = run(Path(__file__).with_name("fixtures.json"))
    payload = json.dumps(result, sort_keys=True, indent=2).encode("utf-8") + bytes((10,))
    with Path(arguments[0]).open("xb") as artifact:
        artifact.write(payload)
    print(f"candidate cases={len(result['cases'])} bytes={len(payload)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
