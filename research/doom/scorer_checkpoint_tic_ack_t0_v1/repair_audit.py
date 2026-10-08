"""Independent audit of the patched helper's retained fake run."""
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED = {
    "one_tic_acknowledged": True,
    "refresh_no_op": False,
    "refresh_two_tics": False,
    "tic_changes_during_score_read": False,
    "refresh_raises": False,
}


def audit():
    raw = json.loads((ROOT / "repair-raw.json").read_text(encoding="utf-8"))
    errors = []
    if raw.get("schema") != "scorer-checkpoint-tic-ack-repair-raw-v1":
        errors.append("schema")
    rows = raw.get("rows")
    if not isinstance(rows, list) or len(rows) != len(EXPECTED):
        errors.append("row_count")
        rows = rows if isinstance(rows, list) else []
    candidate_hash = hashlib.sha256((ROOT / "candidate_helper.py").read_bytes()).hexdigest()
    if raw.get("candidate_helper_sha256") != candidate_hash:
        errors.append("candidate_helper_hash")
    pins = json.loads((ROOT / "source-pins.json").read_text(encoding="utf-8"))
    if raw.get("source_helper_sha256") != pins["files"]["helper"]["sha256"]:
        errors.append("source_helper_hash")
    seen = set()
    for row in rows:
        case = row.get("case")
        if case not in EXPECTED or case in seen:
            errors.append(f"unexpected_or_duplicate:{case}")
            continue
        seen.add(case)
        if row.get("controller_gate_accepts") is not EXPECTED[case]:
            errors.append(f"controller_gate:{case}")
        if row.get("public_has_values") is not False:
            errors.append(f"public_score_leak:{case}")
        if case == "one_tic_acknowledged":
            if not (row.get("tic_after") == row.get("tic_before") + 1 == row.get("tic_after_read")):
                errors.append("valid_ack_tics")
        elif case in {"refresh_no_op", "refresh_two_tics", "tic_changes_during_score_read"}:
            if row.get("status") != "UNKNOWN":
                errors.append(f"counterexample_not_unknown:{case}")
    if seen != set(EXPECTED):
        errors.append("case_completeness")
    return {
        "schema": "scorer-checkpoint-tic-ack-repair-audit-v1",
        "pass": not errors,
        "errors": errors,
        "accepted_cases": [r["case"] for r in rows if r.get("controller_gate_accepts") is True],
        "scope": "minimal source repair with synthetic fakes only",
    }


if __name__ == "__main__":
    result = audit()
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    (ROOT / "repair-audit.json").write_text(text, encoding="utf-8")
    print(text, end="")
    raise SystemExit(0 if result["pass"] else 1)
