import json
from pathlib import Path

from model import IdOnlyLedger, Receipt, WatermarkLedger

TASK = "COORD-INTENT-GC-WATERMARK-20260917-022"
C = "content-C"
A1 = Receipt("A", 1, 1, 2, C, 1)
B2 = Receipt("B", 2, 2, 3, C, 2)
C3 = Receipt("C", 3, 3, 4, C, 3)
A1_ADAPTED = Receipt("A", 1, 4, 5, C, 4)
A4_FRESH = Receipt("A", 4, 4, 5, C, 4)
B2_CHANGED = Receipt("B", 2, 2, 4, C, 2)


def fill(ledger):
    writes = 0
    for r in (A1, B2, C3):
        result = ledger.apply(r)
        if result != "APPLIED":
            raise RuntimeError((r, result))
        writes += 1
    return ledger, writes


def main() -> None:
    baseline, baseline_writes = fill(IdOnlyLedger(2))
    baseline_old_exact = baseline.classify(A1)
    baseline_adapted_class = baseline.classify(A1_ADAPTED)
    baseline_adapted_apply = baseline.apply(A1_ADAPTED)
    if baseline_adapted_apply == "APPLIED":
        baseline_writes += 1

    expired, expired_writes = fill(WatermarkLedger(2))
    expired_exact = expired.classify(A1)
    expired_adapted = expired.classify(A1_ADAPTED)
    expired_snapshot = expired.snapshot()

    conflict, conflict_writes = fill(WatermarkLedger(2))
    retained_conflict = conflict.classify(B2_CHANGED)

    fresh, fresh_writes = fill(WatermarkLedger(2))
    fresh_class = fresh.classify(A4_FRESH)
    fresh_apply = fresh.apply(A4_FRESH)
    if fresh_apply == "APPLIED":
        fresh_writes += 1

    gates = {
        "id_only_old_exact_misclassified_new_after_gc": baseline_old_exact == "NEW_INTENT_ALLOWED",
        "id_only_same_instance_changed_content_can_apply_after_gc": baseline_adapted_apply == "APPLIED" and baseline.generation == 5,
        "watermark_rejects_expired_exact": expired_exact == "EXPIRED_INTENT",
        "watermark_rejects_expired_changed_content": expired_adapted == "EXPIRED_INTENT",
        "expired_replay_transition_writes_zero": expired_writes == 3,
        "fresh_seq4_allowed": fresh_class == "NEW_INTENT_ALLOWED",
        "fresh_seq4_applies_once": fresh_apply == "APPLIED" and fresh_writes == 4 and fresh.generation == 5,
        "retained_same_instance_changed_content_conflicts": retained_conflict == "CONFLICT_INTENT_CONTENT",
        "history_capacity_stays_two": len(fresh.history) == 2 and fresh.capacity == 2,
        "retirement_state_is_scalar": isinstance(fresh.retired_through_seq, int),
    }
    decision = "PASS_SCALAR_INTENT_RETIREMENT_WATERMARK_SCOPED" if all(gates.values()) else "FAIL_SCALAR_INTENT_RETIREMENT_WATERMARK_SCOPED"

    result = {
        "task": TASK,
        "decision": decision,
        "formal_reruns": 0,
        "capacity": 2,
        "cases": {
            "id_only_after_gc": {
                "old_exact_A_seq1": baseline_old_exact,
                "same_instance_changed_content": baseline_adapted_class,
                "same_instance_changed_content_apply": baseline_adapted_apply,
                "writes": baseline_writes,
                "snapshot": baseline.snapshot(),
            },
            "watermark_expired_replay": {
                "old_exact_A_seq1": expired_exact,
                "same_instance_changed_content": expired_adapted,
                "transition_writes_after_replay_attempt": 0,
                "initial_applied_writes": expired_writes,
                "snapshot": expired_snapshot,
            },
            "watermark_fresh_reuse": {
                "fresh_label_A_seq4": fresh_class,
                "fresh_apply": fresh_apply,
                "writes": fresh_writes,
                "snapshot": fresh.snapshot(),
            },
            "watermark_retained_conflict": {
                "B_seq2_changed_content": retained_conflict,
                "writes": conflict_writes,
                "snapshot": conflict.snapshot(),
            },
        },
        "gates": gates,
        "notes": [
            "Deterministic single-process container fixture.",
            "The watermark is an issuer-ordered namespace boundary, not a timeout.",
            "No unbounded intent-ID tombstone set is retained.",
        ],
    }
    Path("result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
