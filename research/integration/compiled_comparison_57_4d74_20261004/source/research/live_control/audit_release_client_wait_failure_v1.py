"""Independent cross-platform audit of retained client-wait failure."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent; REPO = HERE.parents[1]
ROOT = HERE / "results/release-client-wait-live-01"
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    retention, failure = read(ROOT / "retention.json"), read(ROOT / "failure.json")
    plan, report = read(ROOT / "preregistration.json"), read(ROOT / "report.json")
    checks = {
        "manifest": all(sha(ROOT / name) == digest
                        for name, digest in retention["manifest"].items()),
        "frozen_sources": all(sha(REPO / name) == digest
                              for name, digest in plan["source_sha256"].items()),
        "first_failure": retention["decision"] == "RETAIN_FIRST_FAILURE_NO_RETRY" and
                         failure["allocation_passed"] is False,
        "audit_failure_retained": (ROOT / "audit-exit-code.txt").read_text().strip() == "1" and
            "KeyError: 'received_ns'" in (ROOT / "audit-stderr.txt").read_text(),
        "missing_evidence_explicit": failure["failure_class"] ==
            "server_request_registration_receipt_not_serialized" and
            all("received_ns" not in client for client in report["clients"].values()),
        "descriptive_wait_retained": report["metrics_ms"]["early_client_wait_advantage_ms"] ==
                                     110.444045,
        "zero_model": failure["evidence"]["zero_model_retry_cancel"] is True,
    }
    audit = {"passed": all(checks.values()), "checks": checks,
        "allocation_passed": False, "failure_class": failure["failure_class"],
        "metrics_ms": failure["metrics_ms"],
        "files_in_manifest": len(retention["manifest"]),
        "bytes_before_receipt": retention["bytes"], "limits": failure["limits"]}
    (ROOT / "retained-audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2)); return 0 if audit["passed"] else 1

if __name__ == "__main__": raise SystemExit(main())
