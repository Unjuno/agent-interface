"""Independent integrity audit of the retained first v2 failure."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = HERE / "results/map01-early-typed-cancel-live-02"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    retention, failure = read(ROOT / "retention.json"), read(ROOT / "failure.json")
    prereg, report, original = (read(ROOT / "preregistration.json"),
                                read(ROOT / "report.json"), read(ROOT / "audit.json"))
    manifest = retention["manifest"]
    checks = {
        "retained_manifest": all(sha(ROOT / name) == digest
                                 for name, digest in manifest.items()),
        "frozen_sources": all(sha(REPO / name) == digest
                              for name, digest in prereg["source_sha256"].items()),
        "first_failure_retained": retention["decision"] == "RETAIN_FIRST_FAILURE_NO_RETRY" and
            failure["allocation_passed"] is False and report["passed"] is False,
        "single_frozen_failure": [name for name, passed in original["checks"].items()
                                  if not passed] == ["capture_to_release_threshold"],
        "independent_release_preceded_terminal":
            failure["metrics_ms"]["capture_to_owner_cancel_release_ms"] == 63.48392 and
            failure["metrics_ms"]["capture_to_release_verified_ms"] == 131.093646,
        "threshold_not_reinterpreted":
            abs(failure["metrics_ms"]["terminal_release_threshold_overrun_ms"] -
                6.093646) < 1e-9,
        "cancelled_cleanly": failure["evidence"]["cancelled_owner_release_empty"] and
            failure["evidence"]["cancelled_terminal_and_process_exit"],
        "typed_artifacts_reconciled": failure["evidence"]["all_typed_artifacts_reconciled"],
        "zero_model_calls": failure["evidence"]["zero_model_calls"],
    }
    audit = {"passed": all(checks.values()), "checks": checks,
             "allocation_passed": False, "failure_class": failure["failure_class"],
             "metrics_ms": failure["metrics_ms"],
             "files_in_retention_manifest": len(manifest),
             "retained_bytes_before_retention_receipt": retention["bytes"],
             "limits": failure["limits"]}
    (ROOT / "retained-audit.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))
    return 0 if audit["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
