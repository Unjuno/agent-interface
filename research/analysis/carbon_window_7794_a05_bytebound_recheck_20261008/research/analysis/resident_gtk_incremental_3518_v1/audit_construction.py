"""Independent expected traces; deliberately does not import policies.py."""
import json
import subprocess
import sys


CASES = [
    ("revoke_after_emit", [
        {"kind": "obs", "id": "rise", "seq": 1, "gen": 1, "target": 1, "value": True},
        {"kind": "revoke", "seq": 2, "gen": 1}],
     [["emit", "rise"], ["release", 1]]),
    ("revoke_before_obs", [
        {"kind": "revoke", "seq": 1, "gen": 1},
        {"kind": "obs", "id": "late", "seq": 2, "gen": 1, "target": 1, "value": True}],
     [["release", 1], ["refuse", "late"]]),
    ("replacement_then_old", [
        {"kind": "replace", "seq": 3, "gen": 2, "target": 2},
        {"kind": "obs", "id": "old", "seq": 2, "gen": 1, "target": 1, "value": True}],
     [["invalidate", 2, 2], ["refuse", "old"]]),
    ("old_false_does_not_reset", [
        {"kind": "obs", "id": "rise", "seq": 3, "gen": 1, "target": 1, "value": True},
        {"kind": "obs", "id": "delayed-false", "seq": 2, "gen": 1, "target": 1, "value": False},
        {"kind": "obs", "id": "still-high", "seq": 4, "gen": 1, "target": 1, "value": True}],
     [["emit", "rise"], ["refuse", "delayed-false"]]),
    ("duplicate_true_is_one_rising_edge", [
        {"kind": "obs", "id": "first", "seq": 1, "gen": 1, "target": 1, "value": True},
        {"kind": "obs", "id": "duplicate", "seq": 2, "gen": 1, "target": 1, "value": True}],
     [["emit", "first"]]),
]


def invoke_case(name, events):
    program = r'''
import json, sys
from policies import Resident
name, encoded = sys.argv[1:]
p = Resident()
for event in json.loads(encoded): p.step(event)
print(json.dumps({"name": name, "actions": p.actions}))
'''
    result = subprocess.run([sys.executable, "-c", program, name,
                             json.dumps(events)], check=True, capture_output=True,
                            text=True)
    return json.loads(result.stdout)


def main():
    rows = []
    for name, events, expected in CASES:
        observed = invoke_case(name, events)["actions"]
        passed = observed == expected
        rows.append({"case": name, "expected": expected,
                     "observed": observed, "passed": passed})
    report = {"schema": "resident3518_independent_construction_audit_v1",
              "rows": rows, "passed": all(row["passed"] for row in rows)}
    print(json.dumps(report, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
