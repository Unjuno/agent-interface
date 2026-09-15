"""Independent audit of matched early-release and terminal-only client waits."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent; REPO = HERE.parents[1]
PREREG = HERE / "release_client_wait_live_v2_prereg.json"
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    plan = read(PREREG); root = REPO / plan["output"]
    report, events = read(root / "report.json"), read(root / "events.json")
    registrations = read(root / "server-requests-before-focus.json")
    released = next(row for row in events if row.get("event") == "input_released")
    terminal = next(row for row in events if row.get("event") == "terminal")
    early = report["clients"]["early"]; baseline = report["clients"]["terminal"]
    checks = {
        "frozen_sources": all(sha(REPO / name) == digest
                              for name, digest in plan["source_sha256"].items()),
        "allocation_all_pass": report["allocation_id"] == plan["allocation_id"] and
                               report["passed"] is True and all(report["checks"].values()),
        "matched_same_events": early["reply"]["records"][-1] == released and
                               baseline["reply"]["records"][-1] == terminal,
        "request_receipts_retained_before_fault":
            registrations["schema"] == "server-request-registration-v1" and
            report["server_request_receipt_sha256"] ==
            sha(root / "server-requests-before-focus.json") and
            registrations["requests"] == report["server_request_receipts"] and
            {row["request_id"] for row in registrations["requests"]} ==
            {"early-release", "terminal-only"} and
            all(row["received_ns"] < registrations["snapshot_ns"]
                for row in registrations["requests"]) and
            registrations["snapshot_ns"] < report["focus_request_ns"],
        "verified_release_state": report["pending_state"]["physical_release_verified"] is True and
            report["pending_state"]["program_terminal_pending"] is True and
            report["pending_state"]["current_input_authority"] is False,
        "terminal_reconciled": report["closed_state"]["terminal"] == terminal and
            report["closed_state"]["program_terminal_pending"] is False,
        "actual_recovery_artifact": len(report["post_release_observations"]) == 1 and
            Path(report["post_release_observations"][0]["image"]).name == "002.png",
        "wait_advantage": report["metrics_ms"]["early_client_wait_advantage_ms"] >= 40,
        "round_trip_tradeoff": report["early_exchanges"] == 2 and
                               report["terminal_only_exchanges"] == 1,
        "zero_model_retry_cancel": report["model_calls"] == report["retry_count"] == 0 and
            not any(row.get("event") == "cancel_requested" for row in events),
    }
    audit = {"passed": all(checks.values()), "checks": checks,
             "metrics_ms": report["metrics_ms"],
             "early_response_bytes": early["response_bytes"],
             "terminal_response_bytes": baseline["response_bytes"],
             "events": len(events), "scope": plan["scope"]}
    (root / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2)); return 0 if audit["passed"] else 1

if __name__ == "__main__": raise SystemExit(main())

