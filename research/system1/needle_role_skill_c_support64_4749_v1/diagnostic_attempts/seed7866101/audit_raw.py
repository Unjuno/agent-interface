"""Independent raw-only audit for one role-C support diagnostic record."""
import hashlib
import json
import sys
from pathlib import Path

raw_path = Path(sys.argv[1])
raw_bytes = raw_path.read_bytes()
raw = json.loads(raw_bytes)
errors = []
expected_allocation = "needle-role-c-support64-diagnostic-4749-v1-seed7866101"
if raw.get("allocation") != expected_allocation: errors.append("allocation")
if raw.get("seed") != 7866101: errors.append("seed")
if raw.get("pairing", {}).get("support16_is_prefix_of_64") is not True: errors.append("support_prefix")
if raw.get("pairing", {}).get("A_base_immutable") is not True: errors.append("base_immutable")
if raw.get("pairing", {}).get("A_B_hash_equal_across_arms") is not True: errors.append("paired_AB")
arms = raw.get("arms", {})
if set(arms) != {"control16", "treatment64"}: errors.append("arms")
for name, n in (("control16", 16), ("treatment64", 64)):
    arm = arms.get(name, {})
    pred, expected = arm.get("predictions"), arm.get("expected")
    if arm.get("support_count") != n: errors.append(name + ":support_count")
    if not isinstance(pred, list) or not isinstance(expected, list) or len(pred) != 4096 or len(expected) != 4096:
        errors.append(name + ":vector_length")
    elif arm.get("correct") != sum(p == y for p, y in zip(pred, expected)):
        errors.append(name + ":correct")
    elif arm.get("total") != 4096 or arm.get("accuracy") != arm.get("correct") / 4096:
        errors.append(name + ":accuracy")
if arms and raw.get("delta_treatment_minus_control") != arms["treatment64"].get("accuracy", 0) - arms["control16"].get("accuracy", 0):
    errors.append("delta")
if raw.get("raw_payload_sha256") != "e24eb708ab5de7d1c3beaafa8ac2fba795c46ccf35e447dd82184438134ae9dc":
    errors.append("raw_payload_sha256_expected")
# Reconstruct the self-hash over the record excluding its self-hash field.
payload = dict(raw)
payload.pop("raw_payload_sha256", None)
canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
if hashlib.sha256(canonical).hexdigest() != raw.get("raw_payload_sha256"):
    errors.append("raw_self_hash")
report = {"allocation": expected_allocation, "raw_file_sha256": hashlib.sha256(raw_bytes).hexdigest(), "raw_payload_sha256": raw.get("raw_payload_sha256"), "errors": errors, "audit_status": "PASS_RAW_RECORD_ONLY" if not errors else "HOLD_RAW_RECORD", "verified_fields": ["seed/allocation", "prefix assertion as recorded", "paired A/B/base assertions as recorded", "prediction lengths", "accuracy and delta arithmetic", "raw self-hash"], "not_verified": ["prefix assertion truth from omitted raw input", "source replay", "Docker invocation receipt/source hash", "independent retraining", "model-state identity"]}
print(json.dumps(report, sort_keys=True))
if errors: raise SystemExit(2)