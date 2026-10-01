import hashlib
import json
from pathlib import Path
from model import Receipt, SingleSlotLedger, BoundedHistoryLedger

C = "content-C"
A = Receipt("intent-A", 1, 2, C, 1)
B = Receipt("intent-B", 2, 3, C, 2)
C3 = Receipt("intent-C", 3, 4, C, 3)
A_CONFLICT = Receipt("intent-A", 1, 3, C, 1)


def run():
    single = SingleSlotLedger()
    single.apply(A); single.apply(B)

    bounded_two = BoundedHistoryLedger(capacity=2)
    bounded_two.apply(A); bounded_two.apply(B)

    bounded_evict = BoundedHistoryLedger(capacity=2)
    bounded_evict.apply(A); bounded_evict.apply(B); bounded_evict.apply(C3)

    cases = {
        "single_slot_overwrite": {
            "recovery_A": single.recover(A),
            "generation": single.generation,
            "last": single.last_applied_transition.content(),
        },
        "bounded_history_two": {
            "recovery_A": bounded_two.recover(A),
            "snapshot": bounded_two.snapshot(),
        },
        "bounded_history_conflict": {
            "recovery_A_changed_content": bounded_two.recover(A_CONFLICT),
            "snapshot": bounded_two.snapshot(),
        },
        "bounded_history_eviction": {
            "recovery_A": bounded_evict.recover(A),
            "recovery_B": bounded_evict.recover(B),
            "snapshot": bounded_evict.snapshot(),
        },
    }

    gates = {
        "single_slot_loses_A_after_B": cases["single_slot_overwrite"]["recovery_A"] == "UNKNOWN_INTENT_NOT_RETAINED",
        "bounded_capacity2_retains_A_after_B": cases["bounded_history_two"]["recovery_A"] == "ALREADY_COMMITTED_SELF",
        "same_id_changed_content_conflicts": cases["bounded_history_conflict"]["recovery_A_changed_content"] == "CONFLICT_INTENT_CONTENT",
        "capacity2_evicts_A_after_C": cases["bounded_history_eviction"]["recovery_A"] == "UNKNOWN_INTENT_EVICTED",
        "capacity2_still_recognizes_B_after_C": cases["bounded_history_eviction"]["recovery_B"] == "ALREADY_COMMITTED_SELF",
        "history_is_bounded_to_2": len(cases["bounded_history_eviction"]["snapshot"]["history"]) == 2,
    }
    decision = "PASS_BOUNDED_APPLIED_INTENT_HISTORY_SCOPED" if all(gates.values()) else "FAIL_BOUNDED_APPLIED_INTENT_HISTORY_SCOPED"
    result = {
        "task": "COORD-BOUNDED-INTENT-HISTORY-20260917-021",
        "decision": decision,
        "capacity": 2,
        "cases": cases,
        "gates": gates,
        "formal_reruns": 0,
        "notes": [
            "Deterministic single-process container fixture.",
            "UNKNOWN_INTENT_EVICTED is derived from generation horizon; no unbounded intent tombstone set is retained.",
        ],
    }
    Path("result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    run()
