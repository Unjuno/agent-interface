"""Read-only independent audit of retained candidate output and model mutations."""
import copy
import hashlib
import json
from pathlib import Path

import candidate
import oracle

ROOT = Path(__file__).parent
model = json.loads((ROOT / "model.json").read_text(encoding="utf-8"))
raw_path = ROOT / "raw" / "candidate.stdout.json"
raw_bytes = raw_path.read_bytes()
observed = json.loads(raw_bytes)
oracle_rows = oracle.run(model)
candidate_rows = observed["cases"]
assert observed["run_id"] == "gui-reversibility-7949-t0-a01-20261005"
assert [r["id"] for r in candidate_rows] == [c["id"] for c in model["cases"]]
assert [r["label"] for r in candidate_rows] == [r["label"] for r in oracle_rows]
assert all(r["label"] == r["expected"] for r in candidate_rows)
assert candidate_rows[0]["label"] == "UNIVERSALLY_UNIFORM"
assert candidate_rows[1]["label"] == "UNIVERSALLY_BRANCHING"
assert candidate_rows[2]["label"] == "PARTIALLY_RECOVERABLE"
assert candidate_rows[2]["static_label"] == "UNIVERSALLY_UNIFORM"
assert candidate_rows[3]["label"] == "UNKNOWN"
assert candidate_rows[4]["label"] == "UNKNOWN"
assert candidate_rows[5]["label"] == "UNKNOWN"

# Construction-time adversarial controls: the candidate must fail closed before
# exploring recoveries when coverage or the evidence receipt is invalid.
mutations = []
for case_id, field, replacement in (
    ("uniform", "coverage_complete", False),
    ("uniform", "receipt_valid", False),
):
    changed = copy.deepcopy(model)
    case = next(c for c in changed["cases"] if c["id"] == case_id)
    case[field] = replacement
    result = candidate.evaluate(case, changed)
    assert result["label"] == "UNKNOWN"
    mutations.append({"id": case_id + "_" + field, "label": result["label"], "reason": result["reason"]})

audit = {
    "run_id": observed["run_id"],
    "disposition": "PASS_METHOD_SCOPED",
    "candidate_oracle_agree": True,
    "expected_classifications_match": True,
    "static_baseline_false_positive": "partial",
    "mutation_controls": mutations,
    "oracle_case_count": len(oracle_rows),
    "oracle_enumerated_transition_traces": sum(len(r.get("enumeration", [])) for r in oracle_rows),
    "candidate_raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
    "oracle": oracle_rows,
}
serialized = json.dumps(audit, sort_keys=True, indent=2) + "\n"
(ROOT / "raw" / "audit.json").write_text(serialized, encoding="utf-8")
print(serialized, end="")
