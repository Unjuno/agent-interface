"""Independent structural/oracle audit. Does not import candidate code."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def audit(raw_path, mutate=None):
    fixture = json.loads((HERE / "fixture.json").read_text())
    oracle = json.loads((HERE / "oracle.json").read_text())
    rows = [json.loads(line) for line in Path(raw_path).read_text().splitlines() if line]
    if mutate:
        row = next(r for r in rows if r["case_id"] == "same_new_request_id" and r["arm"] == "ledger")
        if mutate == "erased_denial": row["outcome"] = "ALLOW_REASK_UNSAFE"
        elif mutate == "forged_reopen": row["outcome"] = "ALLOW_REOPENED_FRESH_REQUEST"
        elif mutate == "principal_mapping": row["required_principals"] = ["owner-b"]
        elif mutate == "hidden_effect": row["effect_digest"] = "0" * 64
    expected = {(c["case_id"], a) for c in fixture["cases"] for a in ("id_only", "prompt_cap", "ledger")}
    found = [(r["case_id"], r["arm"]) for r in rows]
    errors = []
    if len(found) != len(set(found)) or set(found) != expected: errors.append("coverage")
    case_map = {c["case_id"]: c for c in fixture["cases"]}
    for row in rows:
        case = case_map.get(row["case_id"])
        if case is None: continue
        if row["approval_authority_granted"] is not False: errors.append("authority")
        if row["required_principals"] != fixture["required_principals"]: errors.append("principal_mapping")
        if row["arm"] == "ledger":
            exp = oracle["case_labels"][case["case_id"]]
            if row["equivalence"] != exp["equivalence"]: errors.append("equivalence")
            if row["outcome"] != exp["ledger_outcome"]: errors.append("outcome")
            proposed = dict(fixture["base_denial_effect"])
            proposed.update(case.get("effect", {}))
            fields = ("task_id", "task_version", "target", "recipient", "resource", "consequence_ids")
            if any(proposed.get(k) is None for k in fields):
                expected_digest = None
            else:
                canonical = {k: sorted(proposed[k]) if k == "consequence_ids" else proposed[k] for k in fields}
                expected_digest = hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            if row["effect_digest"] != expected_digest: errors.append("effect_digest")
    return {"status": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT", "rows": len(rows), "errors": sorted(set(errors)), "mutation": mutate}


if __name__ == "__main__":
    result = audit(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    print(json.dumps(result, sort_keys=True))
    if result["errors"]: raise SystemExit(1)
