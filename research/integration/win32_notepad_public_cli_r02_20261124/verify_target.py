"""Read-only check that the exact launched Notepad window is still selected."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from launch_target import windows_with_title


def main() -> int:
    if len(sys.argv) != 4:
        raise SystemExit("usage: verify_target.py LAUNCH_RECEIPT OUTPUT_JSON PHASE")
    launch = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    output = Path(sys.argv[2])
    phase = sys.argv[3]
    if output.exists():
        raise RuntimeError("IDENTITY_RECEIPT_ALREADY_EXISTS")
    expected = launch["target_window"]
    matches = windows_with_title(Path(launch["target_file"]).name)
    actual = matches[0] if len(matches) == 1 else None
    identity_matches = bool(actual) and all(
        actual.get(key) == expected.get(key)
        for key in ("hwnd", "pid", "process_path")
    )
    row = {
        "schema": "agent-interface/win32-notepad-identity-check-r02-v1",
        "phase": phase,
        "captured_monotonic_ns": time.monotonic_ns(),
        "match_count": len(matches),
        "identity_matches": identity_matches,
        "expected": {key: expected.get(key) for key in ("hwnd", "pid", "process_path")},
        "actual": actual,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(row, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(row, sort_keys=True))
    return 0 if identity_matches else 1


if __name__ == "__main__":
    raise SystemExit(main())
