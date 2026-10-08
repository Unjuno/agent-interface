"""Write a new immutable v2 synthetic lifecycle-audit artifact."""

from __future__ import annotations

import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from raw_allocation_audit_v2 import audit  # noqa: E402
from test_raw_allocation_audit_v2 import raw_v2  # noqa: E402


def main() -> int:
    output = HERE / "construction" / "raw_audit_v2_20260929_01"
    output.mkdir(parents=True, exist_ok=False)
    raw_bytes = (json.dumps(raw_v2(), sort_keys=True, indent=2) + "\n").encode()
    result = audit(raw_bytes)
    (output / "raw-events.json").write_bytes(raw_bytes)
    (output / "audit.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "raw_sha256": result["raw_sha256"],
        "audit": result["audit"], "source_identity_verified": result["source_identity_verified"],
        "disposition": result["evaluation"]["disposition"],
        "break_even_task": result["evaluation"]["observed_break_even_task"],
        "lifecycle": result["lifecycle"],
        "scope": "synthetic construction only; source identity sentinels are not real pins"},
        sort_keys=True))
    return 0 if result["audit"] == "PASS_CONSTRUCTION_ONLY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
