"""Independent raw-only replay audit. Does not import candidate.py."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parent
model = json.loads((ROOT / "model.json").read_text(encoding="utf-8"))
raw_path = ROOT / "results" / "candidate.raw.json"
raw_bytes = raw_path.read_bytes()
raw = json.loads(raw_bytes)
assert raw["run_id"] == model["run_id"]
assert len(raw["cases"]) == len(model["cases"]) == 10

expected = {}
for case in model["cases"]:
    cid = case["id"]
    events = case["events"]
    snapshot = case["snapshot"]
    if not case["coverage_complete"]:
        expected[cid] = ("UNKNOWN", "UNKNOWN_COVERAGE")
    elif [e["seq"] for e in events] != list(range(1, len(events) + 1)):
        expected[cid] = ("UNKNOWN", "UNKNOWN_EVENT_ORDER_OR_GAP")
    elif any(e["global_revision"] != 1 + i for i, e in enumerate(events, start=1)):
        expected[cid] = ("UNKNOWN", "UNKNOWN_REVISION_GAP")
    elif cid == "snapshot_mismatch":
        expected[cid] = ("UNKNOWN", "UNKNOWN_SNAPSHOT_DISAGREEMENT")
    elif cid == "unjournaled_revision":
        expected[cid] = ("UNKNOWN", "UNKNOWN_UNJOURNALED_REVISION")
    elif cid == "object_replaced":
        expected[cid] = ("RECONCILED", "CONFLICT_TARGET_REPLACED")
    elif cid == "same_field_write":
        expected[cid] = ("RECONCILED", "CONFLICT_OWNED_FIELD_CHANGED")
    elif cid == "aba_same_final_value":
        expected[cid] = ("RECONCILED", "CONFLICT_OWNED_FIELD_CHANGED")
    else:
        expected[cid] = ("RECONCILED", "ELIGIBLE")

seen = {row["case_id"]: row for row in raw["cases"]}
assert len(seen) == 10
assert list(seen) == [case["id"] for case in model["cases"]]
errors = []
for cid, row in seen.items():
    disposition, field_result = expected[cid]
    if (row["disposition"], row["field_scoped"]) != (disposition, field_result):
        errors.append(f"{cid}: classification mismatch")
    if disposition == "UNKNOWN" and (row["compensation"] is not None or row["field_scoped"] != "UNKNOWN"):
        errors.append(f"{cid}: unknown case was eligible")
    if cid == "disjoint_y_write":
        comp = row["compensation"]
        if not comp or comp["fields_after"] != {"x": 0, "y": 9} or comp["claims_exact_rollback"]:
            errors.append("disjoint compensation did not preserve y or overstated rollback")
        if not row["blind_inverse"]["lost_disjoint_y"] or row["whole_object"] != "CONFLICT":
            errors.append("control contrast missing")
    if cid == "no_interference" and (not row["compensation"] or row["compensation"]["fields_after"] != {"x": 0, "y": 0}):
        errors.append("no-interference positive did not compensate")
    if cid in {"same_field_write", "aba_same_final_value", "object_replaced"} and row["compensation"] is not None:
        errors.append(f"{cid}: unsafe compensation emitted")

assert not errors, errors
mutations = []
for mutation_id, predicate in (
    ("delete_case", lambda rows: rows.pop()),
    ("forge_gap_as_eligible", lambda rows: rows[5].update(disposition="RECONCILED", field_scoped="ELIGIBLE")),
    ("erase_external_y", lambda rows: rows[1]["compensation"]["fields_after"].update(y=0)),
    ("claim_rollback", lambda rows: rows[1]["compensation"].update(claims_exact_rollback=True)),
):
    changed = json.loads(raw_bytes)
    predicate(changed["cases"])
    rejected = False
    try:
        # Independent core assertions for copied evidence corruption.
        if len(changed["cases"]) != 10:
            raise ValueError("case count")
        candidate_rows = {r["case_id"]: r for r in changed["cases"]}
        if candidate_rows["sequence_gap"]["field_scoped"] != "UNKNOWN":
            raise ValueError("gap accepted")
        if candidate_rows["disjoint_y_write"]["compensation"]["fields_after"]["y"] != 9:
            raise ValueError("external field lost")
        if candidate_rows["disjoint_y_write"]["compensation"]["claims_exact_rollback"]:
            raise ValueError("false rollback claim")
    except (ValueError, KeyError, TypeError):
        rejected = True
    assert rejected, mutation_id
    mutations.append(mutation_id)

audit = {"run_id": raw["run_id"], "disposition": "PASS_EXTERNAL_WRITE_BOUNDARY_SCOPED",
         "case_count": len(seen), "errors": errors, "mutation_rejected_count": len(mutations),
         "mutations_rejected": mutations, "candidate_sha256": hashlib.sha256(raw_bytes).hexdigest()}
(ROOT / "results" / "audit.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps(audit, sort_keys=True, indent=2))
