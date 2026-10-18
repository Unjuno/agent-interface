"""Independent A03 raw-data audit; never imports candidate.py."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parent
model = json.loads((ROOT / "model.json").read_text(encoding="utf-8"))
raw_bytes = (ROOT / "results/candidate.raw.json").read_bytes()
raw = json.loads(raw_bytes)
assert raw["run_id"] == model["run_id"]
assert len(raw["cases"]) == len(model["cases"]) == 11
rows = {r["case_id"]: r for r in raw["cases"]}
assert list(rows) == [c["id"] for c in model["cases"]]

expected_unknown = {"sequence_gap", "out_of_order", "incomplete_coverage", "snapshot_mismatch", "unjournaled_revision"}
errors = []
for c in model["cases"]:
    row = rows[c["id"]]
    if c["id"] in expected_unknown:
        if row["disposition"] != "UNKNOWN" or row["field_scoped"] != "UNKNOWN" or row["compensation"] is not None:
            errors.append(c["id"] + " was not safely UNKNOWN")
    elif c["id"] in {"same_field_write", "aba_same_final_value"}:
        if row["field_scoped"] != "CONFLICT_OWNED_FIELD_CHANGED" or row["compensation"] is not None:
            errors.append(c["id"] + " incorrectly compensated owned-field change")
    elif c["id"] == "object_replaced":
        if row["field_scoped"] != "CONFLICT_TARGET_REPLACED" or row["compensation"] is not None:
            errors.append("replacement incorrectly compensated")
    else:
        if row["disposition"] != "RECONCILED" or row["field_scoped"] != "ELIGIBLE" or not row["compensation"]:
            errors.append(c["id"] + " eligible case failed")
        elif row["compensation"]["claims_exact_rollback"]:
            errors.append(c["id"] + " overclaimed rollback")

for cid, expected_y in (("no_interference", 0), ("disjoint_y_write", 9), ("two_disjoint_writes", 11)):
    comp = rows[cid]["compensation"]
    if not comp or comp["fields_after"] != {"x": 0, "y": expected_y}:
        errors.append(cid + " compensation did not preserve expected external state")
    if comp and comp.get("kind") != "semantic_compensation" or comp and not comp.get("event_id"):
        errors.append(cid + " missing distinct compensation identity")
for cid in ("disjoint_y_write", "two_disjoint_writes"):
    if not rows[cid]["blind_inverse"]["lost_disjoint_y"] or rows[cid]["whole_object"] != "CONFLICT":
        errors.append(cid + " missing blind inverse/version control contrast")

mutations = []
for mid, mut in (
    ("delete_row", lambda rs: rs.pop()),
    ("forge_gap", lambda rs: rs[5].update(disposition="RECONCILED", field_scoped="ELIGIBLE")),
    ("erase_latest_y", lambda rs: rs[-1]["compensation"]["fields_after"].update(y=0)),
    ("claim_rollback", lambda rs: rs[-1]["compensation"].update(claims_exact_rollback=True)),
):
    changed = json.loads(raw_bytes)
    mut(changed["cases"])
    rejected = len(changed["cases"]) != 11
    table = {r["case_id"]: r for r in changed["cases"]}
    rejected = rejected or table.get("sequence_gap", {}).get("field_scoped") != "UNKNOWN"
    latest = table.get("two_disjoint_writes", {}).get("compensation") or {}
    rejected = rejected or latest.get("fields_after") != {"x": 0, "y": 11} or latest.get("claims_exact_rollback") is not False
    assert rejected, mid
    mutations.append(mid)

assert not errors, errors
audit = {"run_id": raw["run_id"], "disposition": "PASS_EXTERNAL_WRITE_BOUNDARY_SCOPED", "case_count": 11,
         "errors": errors, "mutation_rejected_count": len(mutations), "mutations_rejected": mutations,
         "candidate_sha256": hashlib.sha256(raw_bytes).hexdigest()}
(ROOT / "results/audit.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps(audit, sort_keys=True, indent=2))
