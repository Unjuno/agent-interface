"""Independent integrity audit of the retained first early-typed failure."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = HERE / "results/map01-early-typed-cancel-live-01"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    retention = read(ROOT / "retention.json")
    failure = read(ROOT / "failure.json")
    prereg = read(ROOT / "preregistration.json")
    events = [json.loads(line) for line in
              (ROOT / "runtime/events.jsonl").read_text(encoding="utf-8").splitlines()]
    manifest = retention["manifest"]
    checks = {
        "retained_manifest": all(sha(ROOT / name) == digest
                                 for name, digest in manifest.items()),
        "frozen_sources": all(sha(REPO / name) == digest
                              for name, digest in prereg["source_sha256"].items()),
        "first_failure_retained": retention["decision"] == "RETAIN_FIRST_FAILURE_NO_RETRY" and
                                  failure["allocation_passed"] is False and
                                  failure["wrapper_exit_code"] == 1,
        "root_cause_exposed":
            failure["failure_class"] == "executor_exception_identity_mismatch" and
            failure["terminal"]["status"] == "failed" and
            failure["terminal"]["error"] == "Cancelled()",
        "typed_path_preceded_artifact":
            failure["metrics_ms"]["capture_to_cancel_requested_ms"] == 47.529214 and
            failure["metrics_ms"]["capture_to_artifact_ready_ms"] == 119.166684 and
            failure["metrics_ms"]["cancel_requested_before_artifact_ms"] == 71.63747,
        "typed_artifacts_reconciled":
            len(failure["typed_artifact_reconciliations"]) == 3 and
            all(row["matched"] for row in failure["typed_artifact_reconciliations"]),
        "input_released": failure["evidence"]["owner_cancel_release_empty"] is True and
                          failure["evidence"]["terminal_release_empty"] is True,
        "no_input_after_cancel": not [row for row in events
            if row.get("event") == "input_admission" and
            row.get("admitted_ns", 0) > failure["cancel_requested"]["requested_ns"]],
        "score_and_close": failure["evidence"]["score_and_owner_close_retained"] is True,
        "zero_model_calls": not list(ROOT.rglob("planner-protocol.jsonl")),
    }
    audit = {"passed": all(checks.values()), "checks": checks,
             "allocation_passed": False,
             "failure_class": failure["failure_class"],
             "metrics_ms": failure["metrics_ms"],
             "files_in_retention_manifest": len(manifest),
             "retained_bytes_before_retention_receipt": retention["bytes"],
             "limits": failure["limits"]}
    (ROOT / "audit.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))
    return 0 if audit["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
