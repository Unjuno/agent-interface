"""Independent audit of the deterministic compiled GUI interface probe."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/compiled-gui-interface-01"
REPORT = ROOT / "report.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def runtime(row):
    return row["runtime"] if "runtime" in row else row


def main():
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    scenarios = report["scenarios"]
    assert report["passed"] is True and len(scenarios) == 15
    assert report["decision"] == "ADVANCE_TO_PREREGISTERED_LIVE_DESKTOP_BLOCK"
    for filename, digest in report["sources"].items():
        assert sha(HERE / filename) == digest
    assert all(report["invalid_controls"].values())

    positive = scenarios["positive-two-dependent-actions"]
    assert positive["outcome"] == "TASK_SUCCEEDED"
    assert positive["reason"] == "method_complete"
    assert positive["completed_transitions"] == 2
    assert len(positive["observations"]) == 3
    first, second = positive["transitions"]
    assert first["action"] == "request_save" and first["from_state"] == "editing"
    assert second["action"] == "confirm_save" and second["from_state"] == "confirming"
    assert second["matched_conditions"] == {
        "document_dirty": True, "confirm_dialog": "present",
        "confirm_target_present": True}
    assert second["observation_sequence"] > first["observation_sequence"]
    assert all(row["release_verified"] is True for row in positive["transitions"])
    event_types = [row["event"] for row in positive["critical_events"]]
    assert event_types.count("branch_selected") == 3
    assert event_types.count("action_terminal") == 2
    assert event_types.count("effect_checked") == 2
    assert event_types[-1] == "runtime_finished"

    expected_reasons = {
        "unknown-intermediate-state": "unknown_state",
        "stale-second-symbol": "stale_symbol",
        "ambiguous-branch": "ambiguous_state",
        "no-progress": "no_progress",
        "effect-failed": "effect_failed",
        "effect-unavailable": "effect_unavailable",
        "cancel-before-second-admission": "cancelled",
        "transition-budget": "budget_exhausted",
        "delivery-uncertain": "delivery_uncertain",
        "release-failure": "execution_failed",
        "stale-observation": "stale_observation",
        "surface-association-change": "association_changed",
    }
    for name, reason in expected_reasons.items():
        row = scenarios[name]
        assert row["reason"] == reason
        assert row["outcome"] in {"SAFE_YIELD", "RUNTIME_FAILED"}
        assert row["completed_transitions"] <= 1

    counts = report["adapter_call_counts"]
    assert counts["positive"] == {
        "observe": 3, "admit": 2, "execute": 2,
        "verify_effect": 2, "cancelled": 7}
    for name in ("unknown", "stale_symbol", "no_progress", "effect-failed",
                 "effect-unavailable", "cancel", "budget", "stale_observation",
                 "association"):
        assert counts[name]["execute"] <= 1
    assert counts["ambiguous"]["execute"] == 0
    assert counts["stale_symbol"]["admit"] == 2
    assert counts["stale_symbol"]["execute"] == 1
    assert counts["cancel"]["admit"] == 1 and counts["cancel"]["execute"] == 1

    cold_wrapper = scenarios["adaptive-cold"]
    warm_wrapper = scenarios["adaptive-warm"]
    cold = cold_wrapper["adaptive"]
    warm = warm_wrapper["adaptive"]
    assert cold["outcome"] == warm["outcome"] == "TASK_SUCCEEDED"
    assert cold["accounting"]["attempted_calls"] == 2
    assert cold["accounting"]["completed_calls"] == 2
    assert all(value is None for value in cold["accounting"]["usage_totals"].values())
    assert all(value == 0 for value in cold["accounting"]["usage_coverage"].values())
    assert cold["comparison"]["class"] == "full_cold"
    assert warm["accounting"]["attempted_calls"] == 0
    assert warm["accounting"]["completed_calls"] == 0
    assert warm["comparison"]["class"] == "warm_reuse"
    assert cold_wrapper["runtime"]["completed_transitions"] == 2
    assert warm_wrapper["runtime"]["completed_transitions"] == 2
    compiled = cold["selected_target"]["interface"]
    assert compiled["actions"]["request_save"]["expected_effect"] == {
        "confirm_dialog": "present"}
    assert compiled["actions"]["confirm_save"]["expected_effect"] == {
        "document_dirty": False, "confirm_dialog": "absent"}
    for symbol in compiled["symbols"].values():
        assert not ({"authority", "authorization", "point", "coordinate", "steps"}
                    & set(symbol))

    receipts = [runtime(row) for row in scenarios.values()]
    assert all(row["frontier_model_resumptions"] == 0 for row in receipts)
    serialized_receipts = json.dumps(receipts, sort_keys=True)
    assert "private:" not in serialized_receipts
    assert '"authorization"' not in serialized_receipts
    assert all(row["input_authority"] == "admission_per_action_only" for row in receipts)
    assert all(row["raw_evidence_retention"] == "adapter_responsibility_unverified"
               for row in receipts)

    audit = {
        "passed": True,
        "scenarios": len(scenarios),
        "positive_observe_action_transitions": 2,
        "positive_frontier_model_resumptions": 0,
        "typed_safe_or_failed_controls": len(expected_reasons),
        "adaptive_cold_attempts": 2,
        "adaptive_warm_attempts": 0,
        "source_hashes_verified": len(report["sources"]),
        "decision": report["decision"],
        "scope": report["scope"],
    }
    (ROOT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n",
                                      encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
