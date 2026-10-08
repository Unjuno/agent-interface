"""Independent oracle for the six frozen finite cases; no candidate imports."""
import json
import argparse
from pathlib import Path
import sys


EXPECTED = [
    ("retained_boundary", "REJECT", "ADMIT_BOUNDED_CONTINUATION", 89, 85, False),
    ("one_below_floor", "REJECT", "REJECT", 89, 85, False),
    ("one_above_floor", "REJECT", "ADMIT_BOUNDED_CONTINUATION", 89, 85, False),
    ("missing_health", "REJECT", "REJECT", 89, 85, False),
    ("stale_evidence", "REJECT", "REJECT", 89, 85, False),
    ("mismatched_source", "REJECT", "REJECT", 89, 85, False),
]


def audit(rows):
    if type(rows) is not list or len(rows) != len(EXPECTED):
        return {"status": "FAIL_CASE_INVENTORY", "expected": len(EXPECTED),
                "actual": len(rows) if type(rows) is list else None}
    failures = []
    for row, expected in zip(rows, EXPECTED):
        name, action, cover, action_floor, cover_floor, authority = expected
        observed = (row.get("case"), row.get("action"), row.get("cover"),
                    row.get("action_floor"), row.get("cover_floor"),
                    row.get("input_authority"))
        if observed != expected:
            failures.append({"case": name, "expected": expected, "observed": observed})
    return {"status": "PASS_METHOD_SCOPED" if not failures else "FAIL_ORACLE_MISMATCH",
            "case_count": len(rows), "failures": failures,
            "scope": "finite contract arithmetic only; no input or live threat efficacy"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path,
                        default=Path(__file__).with_name("candidate_output.json"))
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).with_name("audit.json"))
    args = parser.parse_args()
    payload = json.loads(args.input.read_text())
    result = audit(payload.get("rows"))
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
    sys.exit(0 if result["status"] == "PASS_METHOD_SCOPED" else 1)
