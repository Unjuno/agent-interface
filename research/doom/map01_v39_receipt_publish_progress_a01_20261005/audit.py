#!/usr/bin/env python3
"""Independent raw-only audit of the frozen A01 row-publication outcomes."""
import json, sys
from pathlib import Path

RAW = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
expected = sorted([
    "owner-a:r1:cleanup-up:65",
    "owner-a:r1:cleanup-up:74",
    "owner-a:r1:cleanup-up:38",
])
assert RAW["expected_ids"] == expected
assert len(RAW["cases"]) == 4
by_name = {x["name"]: x for x in RAW["cases"]}
for name in ("normal", "before_append_row_2", "append_then_raise_row_2"):
    case = by_name[name]
    assert sorted(case["persisted"]) == expected, (name, case)
    assert case["completed_ids"] == expected, (name, case)
    assert all(case["persisted"][rid]["physical_key_measurement"]["bracket"]["release_id"] == rid
               for rid in expected), name
    assert case["duplicates"] == {}, name
    if name == "normal":
        assert len(case["append_attempts"]) == 3
    else:
        assert len(case["append_attempts"]) == 4
assert by_name["normal"]["first_error"] is None
assert by_name["before_append_row_2"]["first_error"] == "injected before-append failure"
assert by_name["append_then_raise_row_2"]["first_error"] == "injected append-then-raise acknowledgement loss"
non_idem = by_name["non_idempotent_append_then_raise_row_2"]
assert non_idem["idempotent_sink"] is False
assert non_idem["duplicates"] == {"owner-a:r1:cleanup-up:74": 1}
assert sorted(non_idem["persisted"]) == expected
assert RAW["controls"]["duplicate_id_different_payload_rejected"] is True
print(json.dumps({
    "audit": "PASS_IDEMPOTENT_ROW_PROGRESS_SCOPED",
    "idempotent_cases": 3,
    "expected_receipts": len(expected),
    "non_idempotent_control": "UNKNOWN_DUPLICATE_AFTER_ACK_LOSS",
    "collision_control": "REJECTED",
}, sort_keys=True))
