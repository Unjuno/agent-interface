"""Independent durable-image enumeration and decision audit."""
import json
from pathlib import Path
import sys


EXPECTED = {
    "effect_then_receipt_separate_domains": [(0, 0), (1, 0), (1, 1)],
    "receipt_then_effect_separate_domains": [(0, 0), (0, 1), (1, 1)],
    "effect_and_receipt_single_atomic_transaction": [(0, 0), (1, 1)],
    "effect_commit_then_ack_before_receipt": [(0, 0), (1, 0), (1, 1)],
    "corrupt_or_untrusted_record": [(0, 0), (1, 0), (0, 1), (1, 1)],
}


def oracle(effect, receipt, corrupt):
    if corrupt:
        return "CORRUPT_OR_UNTRUSTED"
    if effect and receipt:
        return "EFFECT_AND_RECEIPT_CONFIRMED"
    if not effect and not receipt:
        return "NO_EFFECT_CONFIRMED"
    return "UNKNOWN_RECONCILE"


def main(path):
    data = json.loads(Path(path).read_text())
    errors = []
    if data.get("schema") != "machine-crash-durability-7802-candidate-v1":
        errors.append("schema")
    rows = data.get("rows", {})
    if set(rows) != set(EXPECTED):
        errors.append("protocol-set")
    checked = 0
    for name, pairs in EXPECTED.items():
        observed = rows.get(name, [])
        if len(observed) != len(pairs):
            errors.append(f"{name}:cut-count")
            continue
        for i, (row, pair) in enumerate(zip(observed, pairs)):
            e, r = pair
            corrupt = name == "corrupt_or_untrusted_record" and i == 2
            expected = oracle(bool(e), bool(r), corrupt)
            if (row.get("cut"), row.get("effect_durable"), row.get("receipt_durable"),
                row.get("corrupt"), row.get("classification"), row.get("retry_authorized")) != (
                    i, bool(e), bool(r), corrupt, expected, False):
                errors.append(f"{name}:row-{i}")
            checked += 1
    print(json.dumps({"status": "PASS" if not errors else "FAIL", "checked": checked,
                      "errors": errors}))
    return 0 if not errors else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: audit.py CANDIDATE_JSON")
    raise SystemExit(main(sys.argv[1]))
