"""Independent-oracle wrapper for the changed-goal successor allocation."""
import json
import sys

from audit import expected_case

fixture = json.load(open(sys.argv[1], encoding="utf-8"))
case = fixture["case"]
actual = json.load(sys.stdin)
expected = {case["id"]: expected_case(case)}
if actual != expected:
    raise SystemExit("changed-goal independent reconstruction mismatch")
d = actual[case["id"]]["retry_plus_obligation_ledger"]
if d["admitted"] != ["op-A", "op-B"]:
    raise SystemExit("D did not allow the disjoint new-goal operation while retaining old unresolved work")
if d["unresolved_at_end"] != ["op-A"]:
    raise SystemExit("new goal falsely discharged prior operation")
print(json.dumps({"audit": "PASS_METHOD_SCOPED", "case": case["id"],
                  "D_admitted": d["admitted"], "old_goal_unresolved": d["unresolved_at_end"]},
                 sort_keys=True, separators=(",", ":")))
