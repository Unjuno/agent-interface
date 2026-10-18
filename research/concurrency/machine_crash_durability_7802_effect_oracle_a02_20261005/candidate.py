"""Test explicit independent effect truth in finite recovery classifications."""
from itertools import product
import json
import sys
from pathlib import Path


TRUTHS = ("OCCURRED", "NOT_OCCURRED", "UNAVAILABLE")


def a01_bits_only(effect_record, completion_receipt, untrusted=False):
    if untrusted:
        return "CORRUPT_OR_UNTRUSTED"
    if effect_record and completion_receipt:
        return "EFFECT_AND_RECEIPT_CONFIRMED"
    if not effect_record and not completion_receipt:
        return "NO_EFFECT_CONFIRMED"
    return "UNKNOWN_RECONCILE"


def classify(effect_truth, effect_record, completion_receipt, untrusted=False):
    if untrusted:
        return "CORRUPT_OR_UNTRUSTED"
    if effect_truth == "UNAVAILABLE":
        return "UNKNOWN_RECONCILE"
    if effect_truth == "OCCURRED":
        return "EFFECT_AND_RECEIPT_CONFIRMED" if completion_receipt else "UNKNOWN_RECONCILE"
    if effect_truth == "NOT_OCCURRED":
        if effect_record or completion_receipt:
            return "CORRUPT_OR_UNTRUSTED"
        return "NO_EFFECT_CONFIRMED"
    raise ValueError("invalid independent effect truth")


def rows():
    result = []
    for truth, effect_record, receipt in product(TRUTHS, (False, True), (False, True)):
        result.append({
            "effect_truth": truth,
            "effect_record_present": effect_record,
            "completion_receipt_present": receipt,
            "a01_bits_only": a01_bits_only(effect_record, receipt),
            "strict_classification": classify(truth, effect_record, receipt),
            "retry_authorized": False,
        })
    result.append({
        "effect_truth": "UNAVAILABLE", "effect_record_present": False,
        "completion_receipt_present": False, "untrusted": True,
        "a01_bits_only": a01_bits_only(False, False, True),
        "strict_classification": classify("UNAVAILABLE", False, False, True),
        "retry_authorized": False,
    })
    return result


def main(out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    data = {"schema": "machine-crash-durability-7802-a02-candidate-v1", "rows": rows()}
    (out / "candidate.json").write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"rows": len(data["rows"]), "a01_false_no_effect": sum(
        r["a01_bits_only"] == "NO_EFFECT_CONFIRMED" and r["effect_truth"] != "NOT_OCCURRED"
        for r in data["rows"]), "output": str(out / "candidate.json")}))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: candidate.py OUTPUT_DIR")
    main(sys.argv[1])
