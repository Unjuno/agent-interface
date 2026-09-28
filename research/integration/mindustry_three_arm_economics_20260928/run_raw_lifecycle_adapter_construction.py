"""Capture a fake-mod channel handshake and audit the assembled v2 raw record."""

from __future__ import annotations

import json
import argparse
from pathlib import Path
import sys
import tempfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from raw_allocation_audit_v2 import audit  # noqa: E402
from test_private_benchmark_channel import assemble_raw_from_private_channels  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("capture_name",
        help="new immutable capture directory name under construction/")
    capture_name = parser.parse_args().capture_name
    if not capture_name or Path(capture_name).name != capture_name:
        parser.error("capture_name must be a directory basename")
    output = HERE / "construction" / capture_name
    output.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory() as temp:
        raw = assemble_raw_from_private_channels(Path(temp))
    raw_bytes = (json.dumps(raw, sort_keys=True, indent=2) + "\n").encode()
    result = audit(raw_bytes)
    (output / "raw-events.json").write_bytes(raw_bytes)
    (output / "audit.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "raw_sha256": result["raw_sha256"],
        "audit": result["audit"], "source_identity_verified": result["source_identity_verified"],
        "disposition": result["evaluation"]["disposition"],
        "break_even_task": result["evaluation"]["observed_break_even_task"],
        "lifecycle": result["lifecycle"],
        "scope": "synthetic task events plus exercised fake-mod private protocol; no live game"},
        sort_keys=True))
    return 0 if result["audit"] == "PASS_CONSTRUCTION_ONLY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
