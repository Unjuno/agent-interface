"""Enumerate bounded durable images for Issue #7802's T0 storage model."""
from itertools import product
import json
from pathlib import Path


def classify(image):
    if image["corrupt"]:
        return "CORRUPT_OR_UNTRUSTED", False
    effect = image["effect_durable"]
    receipt = image["receipt_durable"]
    if effect and receipt:
        return "EFFECT_AND_RECEIPT_CONFIRMED", False
    if not effect and not receipt:
        return "NO_EFFECT_CONFIRMED", False
    return "UNKNOWN_RECONCILE", False


def enumerate_protocol(name):
    cuts = {
        "effect_then_receipt_separate_domains": [(False, False), (True, False), (True, True)],
        "receipt_then_effect_separate_domains": [(False, False), (False, True), (True, True)],
        "effect_and_receipt_single_atomic_transaction": [(False, False), (True, True)],
        "effect_commit_then_ack_before_receipt": [(False, False), (True, False), (True, True)],
        "corrupt_or_untrusted_record": [(False, False), (True, False), (False, True), (True, True)],
    }[name]
    rows = []
    for index, (effect, receipt) in enumerate(cuts):
        corrupt = name == "corrupt_or_untrusted_record" and index == 2
        image = {"effect_durable": effect, "receipt_durable": receipt, "corrupt": corrupt}
        state, retry = classify(image)
        rows.append({"cut": index, **image, "classification": state, "retry_authorized": retry})
    return rows


def main(out_dir):
    protocols = [
        "effect_then_receipt_separate_domains",
        "receipt_then_effect_separate_domains",
        "effect_and_receipt_single_atomic_transaction",
        "effect_commit_then_ack_before_receipt",
        "corrupt_or_untrusted_record",
    ]
    result = {"schema": "machine-crash-durability-7802-candidate-v1",
              "rows": {name: enumerate_protocol(name) for name in protocols}}
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "candidate.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"protocols": len(protocols), "images": sum(map(len, result["rows"].values())),
                      "output": str(out / "candidate.json")}))


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        raise SystemExit("usage: candidate.py OUTPUT_DIR")
    main(sys.argv[1])
