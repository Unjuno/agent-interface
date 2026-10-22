"""Independent raw-only outcome check; invariants stay active under python -O."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise SystemExit(message)


raw = json.loads(Path(sys.argv[1]).read_text())
lock = json.loads(Path(sys.argv[2]).read_text())
require(raw.get("schema") == "map01-v39-legacy-owner-identity-a01-raw-v1",
        "wrong raw schema")
require(raw.get("source_sha256") == lock.get("sha256"), "source hash mismatch")
rows = {case["case"]: case for case in raw.get("cases", [])}
expected_cases = {
    "positive_exact_ids", "top_level_owner_mismatch", "nested_owner_mismatch",
    "cross_layer_mismatch", "partial_explicit_identity", "legacy_all_ids_absent",
}
require(set(rows) == expected_cases, "case inventory mismatch")
require(rows["positive_exact_ids"]["baseline"]["status"] ==
        rows["positive_exact_ids"]["candidate"]["status"] == "paired",
        "positive control failed")
for name in ("top_level_owner_mismatch", "nested_owner_mismatch",
             "cross_layer_mismatch", "partial_explicit_identity"):
    require(rows[name]["baseline"]["status"] == "paired",
            f"baseline mutation changed: {name}")
    require(rows[name]["candidate"]["status"] == "release_receipt_incomplete",
            f"candidate accepted conflicting identity: {name}")
    require(rows[name]["candidate"]["input_ack_to_owner_keyup_start_ms"] is None,
            f"candidate exposed derived timing: {name}")
require(rows["legacy_all_ids_absent"]["baseline"]["status"] ==
        rows["legacy_all_ids_absent"]["candidate"]["status"] == "paired",
        "legacy compatibility control changed")
print(json.dumps({
    "disposition": "PASS_IDENTITY_CONFLICT_REJECTED_WITH_LEGACY_ABSENCE_COMPATIBILITY",
    "cases": 6,
    "mismatches": 0,
}, sort_keys=True))
