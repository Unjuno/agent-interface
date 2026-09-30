import copy
import json
import sys
from pathlib import Path

CASES = [
    ("int_int_same", 2097155, 2097155, True, "admitted", "source_window_bound"),
    ("str_str_same", "2097155", "2097155", True, "admitted", "source_window_bound"),
    ("int_str_cross", 2097155, "2097155", True, "admitted", "source_window_bound"),
    ("str_int_cross", "2097155", 2097155, True, "admitted", "source_window_bound"),
    ("int_str_leading_zero", 2097155, "02097155", False, "source_window_mismatch", "source_window_mismatch"),
    ("str_int_different", "2097155", 2097156, False, "source_window_mismatch", "source_window_mismatch"),
]

def valid(payload):
    rows = payload.get("rows")
    if not isinstance(rows, list) or len(rows) != len(CASES): return False
    for row, (name, observed, trusted, admitted, gate_reason, verifier_reason) in zip(rows, CASES):
        if (row.get("case"), row.get("observed"), row.get("trusted")) != (name, observed, trusted): return False
        if type(row.get("observed")) is not type(observed) or type(row.get("trusted")) is not type(trusted): return False
        if row.get("gate_admitted") is not admitted or row.get("gate_reason") != gate_reason: return False
        if row.get("verifier_bound") is not (verifier_reason == "source_window_bound"): return False
        if row.get("verifier_reason") != verifier_reason: return False
        strict = type(observed) is type(trusted) and observed == trusted
        if row.get("strict_identity_matches") is not strict: return False
    return True

def main(path):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    errors = [] if valid(payload) else ["raw_rows_do_not_match_independent_oracle"]
    mutations = (
        lambda p: p["rows"].pop(),
        lambda p: p["rows"].append(copy.deepcopy(p["rows"][0])),
        lambda p: p["rows"][0].__setitem__("gate_admitted", not p["rows"][0]["gate_admitted"]),
        lambda p: p["rows"][2].__setitem__("observed", "2097156"),
        lambda p: p["rows"][4].__setitem__("verifier_reason", "source_window_bound"),
    )
    rejected = 0
    for mutate in mutations:
        altered = copy.deepcopy(payload); mutate(altered)
        if not valid(altered): rejected += 1
    cross = payload.get("rows", [])[2:4]
    if errors: disposition = "FAIL_TYPE_BOUNDARY_UNEXPECTED"
    elif len(cross) == 2 and all(r["gate_admitted"] and r["verifier_bound"] for r in cross): disposition = "HOLD_CALLER_NORMALIZATION_CONTRACT"
    else: disposition = "PASS_TYPE_BOUNDARY_SCOPED"
    print(json.dumps({"decision":disposition,"rows":len(payload.get("rows",[])),"errors":errors,"mutation_controls_rejected":rejected},sort_keys=True))
    if errors or rejected != 5: raise SystemExit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2: raise SystemExit("usage: python -B audit.py RAW.json")
    main(sys.argv[1])
