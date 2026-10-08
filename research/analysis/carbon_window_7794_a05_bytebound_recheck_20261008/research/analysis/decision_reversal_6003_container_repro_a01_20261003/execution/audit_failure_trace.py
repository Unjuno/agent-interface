"""Post-hoc audit of the retained failed invocation; never imports/runs selector."""
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
TRACE = HERE / "candidate.stdout.log"
EXPECTED_SHA256 = "ef8181e6dc1f006e27ea5bb59f10ba451832d16386363c5176c57398161e8679"
REQUIRED = (
    'File "/tmp/run/select.py"',
    "platform.platform()",
    "import subprocess",
    "/usr/local/lib/python3.12/selectors.py",
    "_select = select.select",
    "AttributeError: module 'select' has no attribute 'select'",
)


def main():
    raw = TRACE.read_bytes()
    text = raw.decode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    missing = [item for item in REQUIRED if item not in text]
    errors = []
    if digest != EXPECTED_SHA256:
        errors.append("retained candidate trace digest mismatch")
    if missing:
        errors.append("missing failure-chain evidence: " + repr(missing))
    if not (HERE.parent / "select.py").is_file():
        errors.append("the colliding select.py source is absent")
    report = {
        "status": "PASS_FAILURE_TRACE_CLASSIFICATION" if not errors else "FAIL_FAILURE_TRACE_AUDIT",
        "allocation_id": "6003-container-repro-a01-20261003",
        "candidate_exit_code": 1,
        "method_result": "NOT_EVALUATED",
        "classification": "FAIL_RUNNER_IMPORT_COLLISION_NO_RESULT",
        "candidate_trace_sha256": digest,
        "required_failure_chain_markers": list(REQUIRED),
        "missing_markers": missing,
        "errors": errors,
        "candidate_rerun": False,
        "scope": "post-hoc independent trace classification only; no selector result or scientific support",
        "audit_started_utc": datetime.now(timezone.utc).isoformat(),
    }
    out = HERE / "failure_trace_audit.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
