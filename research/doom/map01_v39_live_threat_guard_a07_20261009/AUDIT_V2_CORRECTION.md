# A07 audit-v2 correction

This correction addresses two false-PASS paths in `audit_live_v2.py`: last-row-wins maps hid duplicate terminal or input-release events, and hard-health/scorer evidence counted without proving it fell inside the decision's recorded model interval. Per-key release transitions now also have to match the admitted keys exactly.

The reconciliation requires exactly one terminal for each cancellation, rejects duplicate cancellation/release identities, accepts no-input cancellations only with no release transitions or release event and one verified empty terminal, and requires admitted keys to have matching verified transitions plus one verified empty release event. A hard-health invalidation counts only when both its monitor receipt and outcome evaluation timestamps lie in that decision's `[controller_model_started_ns, controller_model_ended_ns]` interval. Useful scorer evidence must have `observed_ns` in a recorded model interval.

`PASS` now means only that these scoped reconciliation checks passed. `formal_pass` remains false because this additive auditor does not rerun the original audit's source, stale-admission, bounded-recovery, and full preregistration gates. The original `AUDIT.json`, v1 auditor, and saved episode were not modified or rerun.

Construction regressions: `python3 -B -m unittest research.doom.map01_v39_live_threat_guard_a07_20261009.test_audit_live_v2 -v` (10 passed). These use synthetic files in temporary directories and do not inspect the saved raw episode or start the game, model, VM, or GUI.
