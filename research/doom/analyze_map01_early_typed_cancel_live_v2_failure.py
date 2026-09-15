"""Describe the first v2 allocation without changing its frozen outcome."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = REPO / "results-local/doom/map01-early-typed-cancel-live-02"
PREREG = HERE / "map01_early_typed_cancel_live_v2_prereg.json"
IDENTIFIER = "early-typed-running-action-fire-02"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    plan, report, audit = read(PREREG), read(ROOT / "report.json"), read(ROOT / "audit.json")
    owner = read(ROOT / "runtime/owner-events.json")
    events = [json.loads(line) for line in
              (ROOT / "runtime/events.jsonl").read_text(encoding="utf-8").splitlines()]
    invalidating = report["invalidating_typed_observation"]
    cancel_release = next(row for row in owner if row.get("reason") == "cancelled")
    capture_ns = invalidating["capture_ns"]
    physical_ms = (cancel_release["verified_ns"] - capture_ns) / 1e6
    terminal_ms = report["metrics_ms"]["capture_to_release_verified_ms"]
    later_inputs = [row for row in events if row.get("event") == "input_admission" and
                    row.get("admitted_ns", 0) > report["cancel_event"]["requested_ns"]]
    evidence = {
        "frozen_sources_match": all(sha(REPO / name) == digest
                                    for name, digest in plan["source_sha256"].items()),
        "original_report_failed": report["passed"] is False,
        "original_audit_failed_only_release_threshold": audit["passed"] is False and
            [name for name, passed in audit["checks"].items() if not passed] ==
            ["capture_to_release_threshold"],
        "cancelled_owner_release_empty": cancel_release["verified"] is True and
            cancel_release["keys_down"] == [] and cancel_release["buttons_down"] == [],
        "physical_release_met_threshold":
            physical_ms <= plan["thresholds_ms"]["capture_to_release_verified_lte"],
        "frozen_terminal_release_missed_threshold":
            terminal_ms > plan["thresholds_ms"]["capture_to_release_verified_lte"],
        "no_input_after_cancel": not later_inputs,
        "cancelled_terminal_and_process_exit":
            report["terminal"]["status"] == "cancelled" and
            report["runtime_process_exit"] == 0,
        "all_typed_artifacts_reconciled":
            len(report["typed_artifact_reconciliations"]) == 3 and
            all(row["matched"] for row in report["typed_artifact_reconciliations"]),
        "zero_model_calls": report["model_calls"] == 0,
    }
    failure = {
        "allocation_id": plan["allocation_id"],
        "allocation_passed": False,
        "wrapper_exit_code": 1,
        "child_process_exit_code": report["runtime_process_exit"],
        "failure_class": "terminal_release_receipt_serialized_behind_artifact_publication",
        "failure": "the independent X11 owner verified empty cancellation release within the threshold, but the frozen allocation measured the later terminal release receipt, which arrived 6.093646 ms beyond its 125 ms threshold",
        "evidence": evidence,
        "metrics_ms": {
            **report["metrics_ms"],
            "capture_to_owner_cancel_release_ms": physical_ms,
            "owner_release_to_terminal_release_ms": terminal_ms - physical_ms,
            "terminal_release_threshold_overrun_ms":
                terminal_ms - plan["thresholds_ms"]["capture_to_release_verified_lte"],
        },
        "owner_cancel_release": cancel_release,
        "original_report_sha256": sha(ROOT / "report.json"),
        "original_audit_sha256": sha(ROOT / "audit.json"),
        "repair_candidate": "publish an identifier-bound independently verified owner release receipt while artifact publication and program finalization remain separate; retain terminal closure as a later lifecycle event",
        "limits": "posthoc analysis of one frozen controller-authored DOOM episode; the early owner record is descriptive evidence and does not retroactively pass the terminal-based preregistered threshold",
    }
    if not all(evidence.values()):
        raise RuntimeError("incomplete failure evidence")
    (ROOT / "failure.json").write_text(
        json.dumps(failure, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"allocation_passed": False,
                      "failure_class": failure["failure_class"],
                      "metrics_ms": failure["metrics_ms"]}, indent=2))


if __name__ == "__main__":
    main()
