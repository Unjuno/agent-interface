"""Independent offline audit for downstream truncation allocation 02."""
import hashlib
import json
from pathlib import Path
import sys


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    output, source = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    here = Path(__file__).resolve().parent
    freeze = json.loads((here / "FREEZE.json").read_text())
    raw_bytes = (output / "raw.json").read_bytes()
    raw = json.loads(raw_bytes)
    errors = []
    if raw.get("allocation") != freeze["allocation"] or raw.get("base_commit") != freeze["base_commit"]:
        errors.append("ALLOCATION_OR_BASE_MISMATCH")
    if raw.get("image_digest") != freeze["image_digest"]:
        errors.append("IMAGE_DIGEST_MISMATCH")
    observed = {}
    for name in freeze["sha256"]:
        path = (source / name) if name.startswith("runtime/") else (here / name)
        observed[name] = digest(path.read_bytes())
    if observed != freeze["sha256"] or raw.get("source_sha256") != freeze["sha256"]:
        errors.append("FROZEN_SOURCE_HASH_MISMATCH")
    accepted = (output / "accepted.json").read_bytes()
    delivered = (output / "delivered-prefix.bin").read_bytes()
    text = accepted.decode("utf-8")
    if raw["producer"].get("write_return_values") != [len(text)]:
        errors.append("PRODUCER_DID_NOT_REPORT_FULL_ACCEPTANCE")
    if raw["producer"].get("reported_character_count") != len(text):
        errors.append("REPORTED_COUNT_MISMATCH")
    if not accepted.startswith(delivered) or len(delivered) >= len(accepted):
        errors.append("DELIVERY_NOT_STRICT_PREFIX")
    if raw["downstream"].get("delivered_bytes") != len(delivered):
        errors.append("DELIVERED_LENGTH_MISMATCH")
    if raw["downstream"].get("delivered_sha256") != digest(delivered):
        errors.append("DELIVERED_HASH_MISMATCH")
    try:
        json.loads(delivered)
        errors.append("DOWNSTREAM_CONSUMER_ACCEPTED_PREFIX")
    except (UnicodeDecodeError, json.JSONDecodeError):
        pass
    if raw["downstream"].get("consumer", {}).get("accepted") is not False:
        errors.append("CONSUMER_REJECTION_NOT_RECORDED")
    request = (output / "request.json").read_bytes()
    report = (output / "report.json").read_bytes()
    recovery = json.loads((output / "recovery.stdout").read_bytes())
    if json.loads(request).get("schema") != "agent-interface/cli-attempt-v1":
        errors.append("REQUEST_NOT_RETAINED")
    if json.loads(report).get("result", {}).get("scope") != "synthetic-only":
        errors.append("REPORT_NOT_RETAINED")
    if recovery.get("status") != "report_recorded" or recovery.get("replay_allowed") is not False:
        errors.append("RECOVERY_STATUS_OR_REPLAY_GATE")
    for name, data in (("request", request), ("report", report)):
        if raw.get(name + "_sha256_before_recovery") != digest(data):
            errors.append("PRE_RECOVERY_HASH_MISMATCH:" + name)
        if raw.get(name + "_sha256_after_recovery") != digest(data):
            errors.append("POST_RECOVERY_HASH_MISMATCH:" + name)
    if raw.get("attempt_files_before_recovery") != raw.get("attempt_files_after_recovery"):
        errors.append("RECOVERY_CHANGED_ATTEMPT_FILES")
    if raw.get("dispatch_call_count_after_recovery") != 1:
        errors.append("DISPATCH_NOT_EXACTLY_ONCE")
    if raw.get("recovery_exit_code") != 0:
        errors.append("RECOVERY_CLI_FAILED")
    disposition = "PASS_SCOPED_DOWNSTREAM_REJECTION_AND_READ_ONLY_RECOVERY" if not errors else "FAIL_AUDIT"
    result = {"schema": "agent-interface/issue3711-downstream-truncation-audit-v1",
              "allocation": freeze["allocation"], "disposition": disposition,
              "raw_sha256": digest(raw_bytes), "source_sha256": observed,
              "accepted_bytes": len(accepted), "delivered_prefix_bytes": len(delivered),
              "request_sha256": digest(request), "report_sha256": digest(report), "errors": errors}
    (output / "audit.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
