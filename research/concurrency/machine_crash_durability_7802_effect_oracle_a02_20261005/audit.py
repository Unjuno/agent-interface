"""Independent decision-table oracle for explicit effect-truth classifications."""
import json
import sys
from itertools import product
from pathlib import Path


def oracle(truth, effect_record, receipt, untrusted):
    if untrusted:
        return "CORRUPT_OR_UNTRUSTED"
    if truth == "UNAVAILABLE":
        return "UNKNOWN_RECONCILE"
    if truth == "OCCURRED":
        return "EFFECT_AND_RECEIPT_CONFIRMED" if receipt else "UNKNOWN_RECONCILE"
    if truth == "NOT_OCCURRED":
        return "CORRUPT_OR_UNTRUSTED" if effect_record or receipt else "NO_EFFECT_CONFIRMED"
    return "INVALID"


def main(path):
    data = json.loads(Path(path).read_text())
    actual = data.get("rows", [])
    expected = list(product(("OCCURRED", "NOT_OCCURRED", "UNAVAILABLE"), (False, True), (False, True)))
    errors = []
    if data.get("schema") != "machine-crash-durability-7802-a02-candidate-v1":
        errors.append("schema")
    if len(actual) != 13:
        errors.append("row-count")
    for index, (truth, effect_record, receipt) in enumerate(expected):
        row = actual[index] if index < len(actual) else {}
        wanted = oracle(truth, effect_record, receipt, False)
        baseline = ("EFFECT_AND_RECEIPT_CONFIRMED" if effect_record and receipt else
                    "NO_EFFECT_CONFIRMED" if not effect_record and not receipt else
                    "UNKNOWN_RECONCILE")
        if (row.get("effect_truth"), row.get("effect_record_present"),
                row.get("completion_receipt_present"), row.get("strict_classification"),
                row.get("retry_authorized"), row.get("a01_bits_only")) != (
                    truth, effect_record, receipt, wanted, False, baseline):
            errors.append(f"row-{index}")
    control = actual[12] if len(actual) > 12 else {}
    if (control.get("untrusted"), control.get("strict_classification"),
            control.get("retry_authorized")) != (True, "CORRUPT_OR_UNTRUSTED", False):
        errors.append("untrusted-control")
    false_absence = [r for r in actual if r.get("strict_classification") == "NO_EFFECT_CONFIRMED"
                     and r.get("effect_truth") != "NOT_OCCURRED"]
    if false_absence:
        errors.append("false-no-effect")
    a01_false_absence = [r for r in actual if r.get("a01_bits_only") == "NO_EFFECT_CONFIRMED"
                         and r.get("effect_truth") != "NOT_OCCURRED"]
    if len(a01_false_absence) != 2:
        errors.append("a01-counterexamples")
    print(json.dumps({"status": "PASS" if not errors else "FAIL", "checked": min(len(actual), 13), "errors": errors}))
    return 0 if not errors else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: audit.py CANDIDATE_JSON")
    raise SystemExit(main(sys.argv[1]))
