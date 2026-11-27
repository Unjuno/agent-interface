"""Additive post-run custody reconciliation for a normal or failed A14 episode."""
import hashlib
import json
from pathlib import Path

from audit_cancellation_custody_v2 import reconcile_cancellations

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ALLOC = "map01-v39-live-threat-guard-a14-recovery-20261009"
ROOT = REPO / "results-local/doom" / ALLOC


def classify_status(custody_ok, audit_checks, score, failure):
    if not custody_ok:
        return "FAIL"
    if (failure is not None or score.get("player_dead") or score.get("map_exit") or
            score.get("episode_finished")):
        return "STOP"
    if audit_checks.get("hard_health_guard_exposed") and \
            audit_checks.get("useful_feedback_during_pending_model") and \
            audit_checks.get("bounded_fresh_recovery_after_guard"):
        return "PASS"
    return "HOLD"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_result(events, audit, score, failure=None, audit_path=None):
    custody = reconcile_cancellations(events)
    checks = audit.get("checks", {})
    status = classify_status(custody["all_cancellations_custodied"], checks,
                             score, failure)
    return {
        "schema": "map01-v39-live-threat-guard-a14-recovery-custody-reconciliation-v3",
        "allocation": ALLOC,
        "status": status,
        "original_audit_status_preserved": audit.get("status"),
        "original_audit_sha256": sha256(audit_path) if audit_path else None,
        "custody": custody,
        "controller_failure_receipt_present": failure is not None,
        "hard_health_guard_exposed": checks.get("hard_health_guard_exposed"),
        "useful_feedback_during_pending_model": checks.get(
            "useful_feedback_during_pending_model"),
        "bounded_fresh_recovery_after_guard": checks.get(
            "bounded_fresh_recovery_after_guard"),
        "score": score,
        "interpretation": (
            "The original audit is preserved unchanged. A verified-empty terminal "
            "accounts for a cancellation with no admitted input or interruption lease; "
            "active input requires matching token-bound owner release. Missing failure "
            "receipts are normal when the controller completed without a runtime error. "
            "The allocation status remains scoped to this episode."
        ),
    }


def main():
    events = [json.loads(line) for line in
              (ROOT / "episode/runtime/events.jsonl").read_text().splitlines()
              if line.strip()]
    audit_path = ROOT / "AUDIT.json"
    audit = json.loads(audit_path.read_text())
    score = json.loads((ROOT / "episode/runtime/score.json").read_text())
    failure_path = ROOT / "episode/controller-failure.json"
    failure = json.loads(failure_path.read_text()) if failure_path.is_file() else None
    result = build_result(events, audit, score, failure, audit_path)
    path = ROOT / "A14_AUDIT_RECONCILIATION_V3.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 1 if result["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
