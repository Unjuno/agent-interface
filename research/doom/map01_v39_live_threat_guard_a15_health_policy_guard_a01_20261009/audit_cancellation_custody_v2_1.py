"""Additive v2.1 reconciliation; tolerate the normal absence of a failure receipt."""
import json
from pathlib import Path

from audit_cancellation_custody_v2 import reconcile_cancellations

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ALLOC = "map01-v39-live-threat-guard-a15-health-policy-guard-20261009"
ROOT = REPO / "results-local/doom" / ALLOC


def build_result(events, audit, score, failure=None):
    custody = reconcile_cancellations(events)
    if not custody["all_cancellations_custodied"]:
        status = "FAIL"
    elif (failure is not None or score.get("player_dead") or score.get("map_exit") or
          score.get("episode_finished")):
        status = "STOP"
    elif audit.get("formal_pass"):
        status = "PASS"
    else:
        status = "HOLD"
    return {
        "schema": "map01-v39-live-threat-guard-a15-health-policy-guard-cancellation-audit-v2.1",
        "allocation": ALLOC,
        "status": status,
        "original_audit_status_preserved": audit.get("status"),
        "custody": custody,
        "controller_failure_receipt_present": failure is not None,
        "controller_cleanup_receipt_reported_empty": (
            failure.get("input_releases_verified_empty") if failure is not None else None
        ),
        "hard_health_guard_exposures": audit.get("counts", {}).get(
            "hard_health_guard_exposures"),
        "useful_events_during_pending_model": audit.get("counts", {}).get(
            "useful_events_during_model_wait"),
        "score": score,
        "primary_runtime_error": ({
            "type": failure.get("primary_error_type"),
            "stage": failure.get("failed_stage"),
        } if failure is not None else None),
        "interpretation": (
            "The original audit is preserved. A verified-empty terminal accounts for "
            "a cancellation with no admitted input or interruption lease; active input "
            "requires matching token-bound owner release. A missing controller-failure "
            "receipt is normal when the controller completes without runtime failure. "
            "This custody result is scoped to this allocation."
        ),
    }


def main():
    events = [json.loads(line) for line in
              (ROOT / "episode/runtime/events.jsonl").read_text().splitlines()
              if line.strip()]
    audit = json.loads((ROOT / "AUDIT.json").read_text())
    score = json.loads((ROOT / "episode/runtime/score.json").read_text())
    failure_path = ROOT / "episode/controller-failure.json"
    failure = json.loads(failure_path.read_text()) if failure_path.is_file() else None
    result = build_result(events, audit, score, failure)
    path = ROOT / "A15_AUDIT_RECONCILIATION_V2_1.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 1 if result["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
