"""Independent audit of pre-artifact typed running-action cancellation."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PREREG = HERE / "map01_early_typed_cancel_live_v2_prereg.json"
def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    plan = read(PREREG); output = REPO / plan["output"]
    report = read(output / "report.json")
    events = [json.loads(line) for line in
              (output / "runtime/events.jsonl").read_text(encoding="utf-8").splitlines()]
    identifier = "early-typed-running-action-fire-02"
    accepted = [row for row in events if row.get("event") == "accepted" and row.get("id") == identifier]
    cancels = [row for row in events if row.get("event") == "cancel_requested" and row.get("id") == identifier]
    terminals = [row for row in events if row.get("event") == "terminal" and row.get("id") == identifier]
    invalidity = report["running_guard"]["invalidation"]["result"]
    invalidated_ns = invalidity["controller_decided_ns"]
    persisted = read(output / f"running-invalidation-{identifier}.json")
    later_down = [row for row in events if row.get("event") == "input_admission" and
                  row.get("admitted_ns", 0) > invalidated_ns]
    checks = {
        "frozen_sources": all(sha(REPO / name) == digest
                              for name, digest in plan["source_sha256"].items()),
        "allocation": report["allocation_id"] == plan["allocation_id"],
        "one_accept_cancel_terminal": len(accepted) == len(cancels) == len(terminals) == 1,
        "exact_attested_acceptance": accepted and
            accepted[0]["accepted_ns"] ==
            report["running_guard"]["program_bindings"][0]["accepted"]["accepted_ns"] and
            accepted[0]["program_sha256"] ==
            report["running_guard"]["program_bindings"][0]["accepted"]["program_sha256"],
        "decision_persisted_before_terminal_validation":
            persisted["running_action_guard"]["invalidation"]["result"] == invalidity and
            persisted["source_event"]["capture_ns"] ==
            invalidity["snapshot"]["capture_ns"] and
            report["persisted_invalidation_sha256"] == sha(
                output / f"running-invalidation-{identifier}.json"),
        "screen_ammo_decreased": invalidity["snapshot"]["signals"]["ammo"]["value"] <
                                 report["source_signals"]["ammo"]["value"],
        "typed_ammo_invalidation": invalidity["reason"] == "ammo_minimum_failed",
        "matched_cancel": cancels and cancels[0]["matched"] is True,
        "cancel_after_invalidation": cancels and cancels[0]["requested_ns"] >= invalidated_ns,
        "no_input_admission_after_invalidation": not later_down,
        "typed_before_artifact": report["checks"]["typed_before_artifact"] is True,
        "guard_decided_before_artifact":
            report["checks"]["guard_decided_before_artifact"] is True,
        "all_typed_artifacts_reconciled":
            report["checks"]["all_typed_artifacts_reconciled"] is True and
            all(row["matched"] for row in report["typed_artifact_reconciliations"]),
        "cancelled_empty_release": terminals and terminals[0]["status"] == "cancelled" and
            terminals[0]["release"]["verified"] is True and
            terminals[0]["release"]["keys_down"] == [] and
            terminals[0]["release"]["buttons_down"] == [],
        "capture_to_guard_decision_threshold":
            report["metrics_ms"]["capture_to_guard_decision_ms"] <=
            plan["thresholds_ms"]["capture_to_guard_decision_lte"],
        "capture_to_cancel_threshold": report["metrics_ms"]["capture_to_cancel_requested_ms"] <=
                                       plan["thresholds_ms"]["capture_to_cancel_requested_lte"],
        "capture_to_release_threshold": report["metrics_ms"]["capture_to_release_verified_ms"] <=
                                        plan["thresholds_ms"]["capture_to_release_verified_lte"],
        "zero_model_calls": report["model_calls"] == 0 and
                            not list(output.rglob("planner-protocol.jsonl")),
        "process_exit_zero": report["runtime_process_exit"] == 0,
        "strictly_faster_than_v2_capture_to_decision":
            report["metrics_ms"]["capture_to_guard_decision_ms"] <
            plan["comparison_baseline_ms"]["v2_capture_to_guard_decision"],
    }
    audit = {"passed": all(checks.values()), "checks": checks,
             "metrics_ms": report["metrics_ms"],
             "source_ammo": report["source_signals"]["ammo"]["value"],
             "invalidating_ammo": invalidity["snapshot"]["signals"]["ammo"]["value"],
             "events": len(events), "observations": sum(row.get("event") == "observation" for row in events),
             "typed_observations": sum(row.get("event") == "typed_observation" for row in events),
             "scope": plan["scope"]}
    (output / "audit.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))
    return 0 if audit["passed"] else 1


if __name__ == "__main__": raise SystemExit(main())
