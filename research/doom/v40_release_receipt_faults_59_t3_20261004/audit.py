"""Independent deterministic audit of the retained T3 case matrix."""
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
data = json.loads((ROOT / "experiment-result.json").read_text(encoding="utf-8"))
assert data["schema"] == "v40-release-receipt-fault-injection-v1"
rows = data["cases"]
assert len(rows) == 12
for helper in ("initial", "renewal"):
    group = [row for row in rows if row["helper"] == helper]
    assert len(group) == 6
    valid = next(row for row in group if row["case"] == "valid_empty_release")
    assert valid["disposition"] == "accepted"
    for row in group:
        assert row["cancel_command"] == {"op": "cancel", "id": "cover-t3"}
        if helper == "initial":
            assert row["planner_interrupts"] == []
        else:
            assert row["planner_interrupts"] == ["turn-t3"]
        if row["case"] == "valid_empty_release":
            assert row["disposition"] == "accepted"
        else:
            assert row["disposition"] == "rejected"
            expected = ("invalidated cover before planning did not verify empty release"
                        if helper == "initial" else
                        "invalidated cover did not verify empty release")
            assert row["error"] == expected
manifest = (ROOT / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
for line in manifest:
    digest, relative = line.split("  ", 1)
    assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest
metadata = json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8"))
assert metadata["disposition"] == "PASS_CONSTRUCTION_FAULT_INJECTION"
assert metadata["case_counts"] == {
    "total": 12, "valid_controls_accepted": 2, "adverse_receipts_rejected": 10}
assert all(command["exit_code"] == 0 for command in metadata["commands"])
print("PASS: case matrix, fail-closed dispositions, bindings, command exits, and checksums verified")
