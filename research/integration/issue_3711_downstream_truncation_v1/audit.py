"""Independent offline audit for the Issue #3711 downstream-truncation probe."""
import hashlib
import json
from pathlib import Path
import sys


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    root = Path(sys.argv[1]).resolve()
    source = Path(sys.argv[2]).resolve()
    raw_bytes = (root / "raw.json").read_bytes()
    raw = json.loads(raw_bytes)
    errors = []
    freeze = json.loads((Path(__file__).with_name("FREEZE.json")).read_text())
    expected = freeze["sha256"]
    observed = {
        "runtime/cli_v1/attempt.py": sha((source / "runtime/cli_v1/attempt.py").read_bytes()),
        "runtime/cli_v1/__main__.py": sha((source / "runtime/cli_v1/__main__.py").read_bytes()),
        "experiment.py": sha(Path(__file__).with_name("experiment.py").read_bytes()),
        "audit.py": sha(Path(__file__).read_bytes()),
        "PLAN.md": sha(Path(__file__).with_name("PLAN.md").read_bytes()),
    }
    if observed != expected or raw.get("source_sha256") != expected:
        errors.append("FROZEN_SOURCE_HASH_MISMATCH")
    accepted = (root / "accepted.json").read_bytes()
    delivered = (root / "delivered-prefix.bin").read_bytes()
    if raw["producer"]["write_calls"] != 1:
        errors.append("PRODUCER_WRITE_CALL_COUNT")
    if raw["producer"]["reported_character_count"] != len(accepted.decode("utf-8")):
        errors.append("FULL_ACCEPT_COUNT_MISMATCH")
    if raw["producer"].get("write_return_values") != [len(accepted.decode("utf-8"))]:
        errors.append("PRODUCER_DID_NOT_REPORT_FULL_ACCEPTANCE")
    if not raw["producer"]["strict_prefix"] or not accepted.startswith(delivered) or len(delivered) >= len(accepted):
        errors.append("DELIVERED_BYTES_NOT_STRICT_PREFIX")
    if raw["producer"]["delivered_byte_count"] != len(delivered):
        errors.append("DELIVERED_LENGTH_MISMATCH")
    if raw["producer"]["accepted_sha256"] != sha(accepted) or raw["producer"]["delivered_sha256"] != sha(delivered):
        errors.append("TRANSPORT_HASH_MISMATCH")
    try:
        json.loads(delivered)
        errors.append("DOWNSTREAM_ACCEPTED_INCOMPLETE_JSON")
    except (UnicodeDecodeError, json.JSONDecodeError):
        pass
    if raw.get("downstream_consumer", {}).get("accepted") is not False:
        errors.append("DOWNSTREAM_CONSUMER_DID_NOT_REJECT")
    request = json.loads((root / "request.json").read_bytes())
    report = json.loads((root / "report.json").read_bytes())
    recovery = json.loads((root / "recovery.stdout").read_bytes())
    if request.get("schema") != "agent-interface/cli-attempt-v1" or report.get("result", {}).get("scope") != "synthetic-only":
        errors.append("RETAINED_ARTIFACT_CONTENT_MISMATCH")
    if recovery.get("status") != "report_recorded" or recovery.get("replay_allowed") is not False:
        errors.append("RECOVERY_NOT_READ_ONLY_REPORT_RECORDED")
    for name, data in (("request", (root / "request.json").read_bytes()),
                       ("report", (root / "report.json").read_bytes())):
        if raw.get(name + "_sha256_before_recovery") != sha(data) or raw.get(name + "_sha256_after_recovery") != sha(data):
            errors.append("RECOVERY_BYTES_CHANGED:" + name)
    if raw.get("attempt_files_before_recovery") != raw.get("attempt_files_after_recovery"):
        errors.append("ATTEMPT_DIRECTORY_CHANGED_DURING_RECOVERY")
    if raw.get("dispatch_call_count_after_recovery") != 1:
        errors.append("DISPATCH_CALL_COUNT_NOT_ONE")
    if raw.get("recovery_exit_code") != 0:
        errors.append("RECOVERY_CLI_NONZERO")
    disposition = "PASS_SCOPED_DOWNSTREAM_REJECTION_AND_READ_ONLY_RECOVERY" if not errors else "FAIL_AUDIT"
    audit = {"schema": "agent-interface/issue3711-downstream-truncation-audit-v1",
             "allocation": freeze["allocation"], "disposition": disposition,
             "raw_sha256": sha(raw_bytes), "source_sha256": observed,
             "accepted_bytes": len(accepted), "delivered_prefix_bytes": len(delivered),
             "request_sha256": sha((root / "request.json").read_bytes()),
             "report_sha256": sha((root / "report.json").read_bytes()), "errors": errors}
    (root / "audit.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")
    print(json.dumps(audit, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
