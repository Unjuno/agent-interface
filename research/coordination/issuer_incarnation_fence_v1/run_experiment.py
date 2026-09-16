import json
from pathlib import Path

from model import IncarnationFencedLedger, Receipt, ResettableSequenceLedger

TASK = "COORD-ISSUER-INCARNATION-FENCE-20260917-023"


def r(inc, label, seq, f, t, rev):
    return Receipt(inc, label, seq, f, t, "content-C", rev)


def seed_i1(ledger):
    for rec in (r(1, "A", 1, 1, 2, 1), r(1, "B", 2, 2, 3, 2), r(1, "C", 3, 3, 4, 3)):
        assert ledger.apply(rec) == "APPLIED"


def main():
    # Negative control: restart resets only the sequence namespace.
    baseline = ResettableSequenceLedger(2)
    seed_i1(baseline)
    pre_restart = baseline.snapshot()
    baseline.restart_reset_namespace()
    old_rebound = r(1, "A", 1, 4, 5, 4)
    baseline_class = baseline.classify(old_rebound)
    baseline_apply = baseline.apply(old_rebound)

    # Candidate old-incarnation replay.
    old = IncarnationFencedLedger(1, 2)
    seed_i1(old)
    assert old.install_incarnation(2) == "INCARNATION_INSTALLED"
    old_replay = r(1, "A", 1, 4, 5, 4)
    old_class = old.classify(old_replay)
    writes_before = old.writes
    old_apply = old.apply(old_replay)
    writes_after = old.writes

    # Candidate fresh restart work.
    fresh = IncarnationFencedLedger(1, 2)
    seed_i1(fresh)
    assert fresh.install_incarnation(2) == "INCARNATION_INSTALLED"
    fresh_req = r(2, "A", 1, 4, 5, 4)
    fresh_class = fresh.classify(fresh_req)
    fresh_apply = fresh.apply(fresh_req)

    # Same installed incarnation + same seq, altered transition content.
    changed = r(2, "A", 1, 5, 6, 5)
    conflict_class = fresh.classify(changed)

    gates = {
        "baseline_old_seq1_revived": baseline_class == "NEW_INTENT_ALLOWED" and baseline_apply == "APPLIED" and baseline.generation == 5,
        "candidate_old_incarnation_rejected": old_class == "STALE_ISSUER_INCARNATION" and old_apply == "REJECTED",
        "candidate_old_incarnation_writes_zero": writes_before == writes_after == 3,
        "fresh_i2_seq1_allowed": fresh_class == "NEW_INTENT_ALLOWED",
        "fresh_i2_seq1_applies_once": fresh_apply == "APPLIED" and fresh.generation == 5 and fresh.writes == 4,
        "retained_same_instance_changed_content_conflicts": conflict_class == "CONFLICT_INTENT_CONTENT",
        "history_capacity_stays_two": len(fresh.history) <= 2 and len(old.history) <= 2,
        "bounded_scalar_state": fresh.snapshot()["retirement_state_shape"] == "scalar_per_current_incarnation",
    }
    decision = "PASS_ISSUER_INCARNATION_FENCE_SCOPED" if all(gates.values()) else "FAIL_ISSUER_INCARNATION_FENCE_SCOPED"
    result = {
        "task": TASK,
        "decision": decision,
        "capacity": 2,
        "formal_reruns": 0,
        "cases": {
            "seq_reset_baseline_old_replay": {
                "pre_restart": pre_restart,
                "classification": baseline_class,
                "apply": baseline_apply,
                "snapshot": baseline.snapshot(),
            },
            "incarnation_old_replay": {
                "classification": old_class,
                "apply": old_apply,
                "transition_writes_after_replay_attempt": writes_after - writes_before,
                "snapshot": old.snapshot(),
            },
            "incarnation_fresh_restart": {
                "classification": fresh_class,
                "apply": fresh_apply,
                "snapshot": fresh.snapshot(),
            },
            "incarnation_retained_conflict": {
                "classification": conflict_class,
                "snapshot": fresh.snapshot(),
            },
        },
        "gates": gates,
        "notes": [
            "Deterministic single-process container fixture.",
            "Incarnation installation is explicit and trusted by fixture construction.",
            "No unbounded tombstone set is retained.",
        ],
    }
    Path("result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
