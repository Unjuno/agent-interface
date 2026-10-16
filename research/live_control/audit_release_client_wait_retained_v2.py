"""Independent cross-platform audit of retained client-wait v2 evidence."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent; REPO = HERE.parents[1]
ROOT = HERE / "results/release-client-wait-live-02"
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    retention = read(ROOT / "retention.json")
    plan, report = read(ROOT / "preregistration.json"), read(ROOT / "report.json")
    original_audit = read(ROOT / "audit.json")
    registrations = read(ROOT / "server-requests-before-focus.json")
    requests = registrations["requests"]
    checks = {
        "manifest": all(sha(ROOT / name) == digest
                        for name, digest in retention["manifest"].items()),
        "frozen_sources": all(sha(REPO / name) == digest
                              for name, digest in plan["source_sha256"].items()),
        "first_outcome": retention["decision"] == "RETAIN_FIRST_OUTCOME_NO_RETRY" and
                         retention["allocation_passed"] is True,
        "original_audits_pass": report["passed"] is True and original_audit["passed"] is True,
        "registration_artifact_bound":
            sha(ROOT / "server-requests-before-focus.json") ==
            report["server_request_receipt_sha256"] and
            requests == report["server_request_receipts"],
        "registered_before_fault": len(requests) == 2 and
            {row["request_id"] for row in requests} ==
            {"early-release", "terminal-only"} and
            all(row["received_ns"] < registrations["snapshot_ns"] for row in requests) and
            registrations["snapshot_ns"] < report["focus_request_ns"],
        "frozen_timing_limits":
            report["metrics_ms"]["focus_to_early_client_ms"] <=
            plan["thresholds_ms"]["focus_to_early_client_lte"] and
            report["metrics_ms"]["early_client_wait_advantage_ms"] >=
            plan["thresholds_ms"]["early_client_advantage_gte"] and
            report["metrics_ms"]["focus_to_terminal_client_ms"] <=
            plan["thresholds_ms"]["focus_to_terminal_client_lte"],
        "round_trip_tradeoff": report["early_exchanges"] == 2 and
                                report["terminal_only_exchanges"] == 1,
        "zero_model_retry_cancel": report["checks"]["zero_model_retry_cancel"] is True,
    }
    audit = {"passed": all(checks.values()), "checks": checks,
        "allocation_passed": True, "metrics_ms": report["metrics_ms"],
        "files_in_manifest": len(retention["manifest"]),
        "bytes_before_receipt": retention["bytes"], "scope": report["scope"]}
    (ROOT / "retained-audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2)); return 0 if audit["passed"] else 1

if __name__ == "__main__": raise SystemExit(main())
