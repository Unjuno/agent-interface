"""Independent audit of release-aware visual-planner overlap allocation."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent; REPO = HERE.parents[1]
PREREG = HERE / "release_planner_overlap_live_v1_prereg.json"
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    plan = read(PREREG); root = REPO / plan["output"]
    report, events = read(root / "report.json"), read(root / "events.json")
    registrations = read(root / "server-requests-before-focus.json")
    early, baseline = report["clients"]["early"], report["clients"]["terminal"]
    terminal = report["terminal"]; metrics = report["metrics_ms"]
    checks = {
        "frozen_sources": all(sha(REPO / name) == digest
                              for name, digest in plan["source_sha256"].items()),
        "allocation_all_pass": report["passed"] is True and all(report["checks"].values()),
        "request_receipts_before_fault": len(registrations["requests"]) == 2 and
            {row["request_id"] for row in registrations["requests"]} ==
            {"early-release", "terminal-only"} and
            all(row["received_ns"] < registrations["snapshot_ns"]
                for row in registrations["requests"]) and
            registrations["snapshot_ns"] < report["focus_request_ns"] and
            report["server_request_receipt_sha256"] ==
            sha(root / "server-requests-before-focus.json"),
        "early_preparation_overlaps_terminal":
            early["reply"]["records"][-1]["event"] == "input_released" and
            early["preparation_started_ns"] >= early["client_returned_ns"] and
            early["preparation_completed_ns"] < terminal["terminal_ns"] and
            early["prepared_state"]["state"] == "PREPARED_AWAITING_TERMINAL",
        "terminal_first_preparation_is_sequential":
            baseline["reply"]["records"][-1] == terminal and
            baseline["preparation_started_ns"] >= baseline["client_returned_ns"] >=
            terminal["terminal_ns"],
        "same_actual_visual_work": early["candidate"] == baseline["candidate"] and
            early["candidate"]["target"] == {"bbox": [596, 373, 643, 408],
                "red_pixels": 1645, "center": [619, 390]},
        "terminal_then_fresh_validation":
            early["reconciled_state"]["state"] ==
            "PREPARED_REQUIRES_FRESH_ACTION_VALIDITY" and
            early["validation_started_ns"] >=
            early["terminal_exchange"]["client_returned_ns"] and
            early["validation"] == baseline["validation"] and
            early["validation"]["status"] == "VALID_CURRENT",
        "no_candidate_authority_or_input":
            early["candidate"]["grants_input_authority"] is False and
            early["validation"]["grants_input_authority"] is False and
            early["reconciled_state"]["may_submit_to_executor"] is False and
            len([row for row in events if row.get("event") == "accepted"]) == 1,
        "timing_limits":
            metrics["focus_to_early_useful_ready_ms"] <=
            plan["thresholds_ms"]["focus_to_early_useful_ready_lte"] and
            metrics["useful_ready_advantage_ms"] >=
            plan["thresholds_ms"]["useful_ready_advantage_gte"] and
            metrics["focus_to_terminal_useful_ready_ms"] <=
            plan["thresholds_ms"]["focus_to_terminal_useful_ready_lte"],
        "round_trip_tradeoff": report["early_exchanges"] == 2 and
                                report["terminal_only_exchanges"] == 1,
        "zero_model_retry_cancel": report["model_calls"] == report["retry_count"] == 0 and
            not any(row.get("event") == "cancel_requested" for row in events),
    }
    audit = {"passed": all(checks.values()), "checks": checks,
        "metrics_ms": metrics, "candidate": early["candidate"],
        "validation": early["validation"], "events": len(events),
        "scope": plan["scope"]}
    (root / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2)); return 0 if audit["passed"] else 1

if __name__ == "__main__": raise SystemExit(main())
