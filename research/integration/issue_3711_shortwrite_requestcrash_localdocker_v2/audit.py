"""Independent raw-artifact auditor; imports no harness code."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, label, errors):
    if not condition:
        errors.append(label)


def main(root: Path):
    errors = []
    result_bytes = (root / "result.json").read_bytes()
    result = json.loads(result_bytes)
    producer = ((root / "complete-control/report.json").read_bytes())
    retained = (root / "short-write/report.json").read_bytes()
    prefix = (root / "short-write/delivered-prefix.bin").read_bytes()
    recovered = (root / "short-write/recovered-report.json").read_bytes()
    request_only = root / "request-only"
    req = (request_only / "request.json").read_bytes()

    require(result["allocation"] == "issue3711-shortwrite-requestcrash-localdocker-formal02", "allocation", errors)
    require(result["short_write"]["status"] == f"INCOMPLETE_STDOUT_WRITE:{len(prefix)}/{len(producer)}", "short-write-rejected", errors)
    require(prefix == producer[:-1] and prefix != producer, "strict-prefix-minus-lf", errors)
    require(json.loads(prefix) == json.loads(producer), "prefix-remains-valid-json", errors)
    require(retained == producer == recovered, "exact-retained-recovery", errors)
    require(digest(retained) == result["short_write"]["retained_report_sha256"], "retained-digest", errors)
    require(result["short_write"]["backend_invocations"] == 1, "short-dispatch-once", errors)
    state = result["request_only_crash"]["recovery"]
    require(result["request_only_crash"]["child_exit"] == 23, "expected-child-exit", errors)
    require(not (request_only / "report.json").exists(), "no-report-after-crash", errors)
    require(state["status"] == "unknown_or_incomplete", "unknown-state", errors)
    require(state["process_state"] == "unknown", "unknown-process-state", errors)
    require(state["replay_allowed"] is False and state["report_state"] == "missing", "no-replay", errors)
    require(state["request_sha256"] == digest(req), "request-digest", errors)
    require(result["request_only_crash"]["backend_invocations"] == 0, "crash-no-dispatch", errors)
    require(result["complete_control"]["exact"] is True, "complete-control", errors)
    require(result["complete_control"]["backend_invocations"] == 1, "complete-dispatch-once", errors)

    report = {"schema": "issue3711-localdocker-audit-v1", "decision": "PASS_SYNTHETIC_MECHANICS_SCOPED" if not errors else "FAIL_AUDIT", "errors": errors,
              "inputs": {"result_sha256": digest(result_bytes), "producer_sha256": digest(producer),
                         "request_only_sha256": digest(req)},
              "checks": 16}
    print(json.dumps(report, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve())

