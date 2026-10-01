"""Independent raw receipt binding checks and two in-memory corruption probes."""
import hashlib
import json
from pathlib import Path
import sys


def sha(data):
    return hashlib.sha256(data).hexdigest()


def inspect(raw, accepted, delivered):
    errors = []
    producer, downstream = raw["producer"], raw["downstream"]
    if sha(accepted) != producer["accepted_sha256"]:
        errors.append("PRODUCER_ACCEPTED_SHA256_MISMATCH")
    if len(accepted) != producer["reported_character_count"]:
        errors.append("PRODUCER_ACCEPTED_BYTE_COUNT_MISMATCH")
    if sha(delivered) != downstream["delivered_sha256"]:
        errors.append("DOWNSTREAM_PREFIX_SHA256_MISMATCH")
    if len(delivered) != downstream["delivered_bytes"]:
        errors.append("DOWNSTREAM_PREFIX_BYTE_COUNT_MISMATCH")
    if not accepted.startswith(delivered) or len(delivered) >= len(accepted):
        errors.append("STRICT_PREFIX_RELATION_MISMATCH")
    try:
        full = json.loads(accepted)
        if full.get("status") != "returned" or full.get("result", {}).get("scope") != "synthetic-only":
            errors.append("FULL_JSON_CONTENT_MISMATCH")
    except (UnicodeDecodeError, json.JSONDecodeError):
        errors.append("FULL_JSON_INVALID")
    try:
        json.loads(delivered)
    except (UnicodeDecodeError, json.JSONDecodeError):
        pass
    else:
        errors.append("PREFIX_JSON_ACCEPTED")
    return errors


def main():
    root, out = Path(sys.argv[1]), Path(sys.argv[2])
    raw_bytes = (root / "formal-02/raw.json").read_bytes()
    raw = json.loads(raw_bytes)
    accepted = (root / "formal-02/accepted.json").read_bytes()
    delivered = (root / "formal-02/delivered-prefix.bin").read_bytes()
    errors = []
    if sha(raw_bytes) != "3f51dc5a4c9c8acb48fc2929a8219260575271e5794cd5bd4afedf6f712afc73":
        errors.append("FROZEN_RAW_SHA256_MISMATCH")
    baseline_errors = inspect(raw, accepted, delivered)
    if baseline_errors:
        errors.append("BASELINE:" + ",".join(baseline_errors))

    mutated_accepted = accepted.replace(b"/out/attempt", b"/bad/attempt", 1)
    if len(mutated_accepted) != len(accepted) or mutated_accepted == accepted:
        errors.append("MUTATION_1_NOT_SAME_LENGTH_CHANGE")
    mutation1_errors = inspect(raw, mutated_accepted, delivered)
    if "PRODUCER_ACCEPTED_SHA256_MISMATCH" not in mutation1_errors:
        errors.append("MUTATION_1_NOT_REJECTED_BY_RECEIPT_BINDING")

    mutated_delivered = delivered[:-1]
    mutation2_errors = inspect(raw, accepted, mutated_delivered)
    required2 = {"DOWNSTREAM_PREFIX_SHA256_MISMATCH", "DOWNSTREAM_PREFIX_BYTE_COUNT_MISMATCH"}
    if not required2.issubset(mutation2_errors):
        errors.append("MUTATION_2_NOT_REJECTED_BY_RECEIPT_BINDING")

    result = {
        "allocation": "issue3793-raw-receipt-byte-binding-orbstack-01",
        "disposition": "PASS_AUDIT_BINDING_SCOPED" if not errors else "FAIL_AUDIT_BINDING_SCOPED",
        "errors": errors,
        "input_raw_sha256": sha(raw_bytes),
        "baseline": {"accepted_bytes": len(accepted), "accepted_sha256": sha(accepted),
                     "delivered_bytes": len(delivered), "delivered_sha256": sha(delivered),
                     "errors": baseline_errors},
        "mutation_same_length_accepted": {"original_bytes": len(accepted),
                     "mutated_bytes": len(mutated_accepted), "errors": mutation1_errors},
        "mutation_shorter_prefix": {"original_bytes": len(delivered),
                     "mutated_bytes": len(mutated_delivered), "errors": mutation2_errors},
        "scope": "two in-memory corruption probes against retained synthetic receipts; no CLI/backend execution",
    }
    (out / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
