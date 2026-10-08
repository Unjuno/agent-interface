"""Verify V3 binds raw trace bytes before parsing or accepting their fields."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from audit_a01_v2 import audit as audit_v2
from audit_a01_v3 import audit_trace


def main() -> None:
    trace_bytes = (ROOT / "raw/trace.json").read_bytes()
    freeze_v2 = json.loads(
        (ROOT / "AUDIT_REPAIR_V2_FREEZE.json").read_text(encoding="utf-8")
    )
    manifest = json.loads(
        (ROOT / "SOURCE_MANIFEST.json").read_text(encoding="utf-8")
    )
    freeze_v3 = json.loads(
        (ROOT / "AUDIT_REPAIR_V3_FREEZE.json").read_text(encoding="utf-8")
    )
    assert hashlib.sha256(
        (ROOT / "AUDIT_REPAIR_V2_FREEZE.json").read_bytes()
    ).hexdigest() == freeze_v3["v2_freeze_sha256"]
    assert hashlib.sha256((ROOT / "audit_a01_v3.py").read_bytes()).hexdigest() == freeze_v3[
        "auditor_sha256"
    ]
    assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == freeze_v3[
        "mutation_test_sha256"
    ]
    assert hashlib.sha256(trace_bytes).hexdigest() == freeze_v2["raw_trace_sha256"]
    assert hashlib.sha256(trace_bytes).hexdigest() == freeze_v3["raw_trace_sha256"]
    assert audit_trace(trace_bytes, freeze_v2, manifest) == []

    changed = json.loads(trace_bytes)
    changed["started_at"] = "edited-without-changing-scored-fields"
    batch = next(
        case for case in changed["cases"]
        if case["case"] == "batch_cancel_during_sync"
    )
    batch["receipt"]["owner_id"] = "edited-owner"
    changed_bytes = json.dumps(changed, sort_keys=True).encode("utf-8")
    # V2's semantic fields still accept these edits; V3 must reject bytes first.
    assert audit_v2(changed, manifest) == []
    assert audit_trace(changed_bytes, freeze_v2, manifest) == [
        "raw_trace_hash_mismatch"
    ]
    assert freeze_v3["raw_trace_sha256"] == freeze_v2["raw_trace_sha256"]
    print("V2 semantic-gap reproduction passed; V3 rejected changed raw bytes")


if __name__ == "__main__":
    main()
