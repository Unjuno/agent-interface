# Issue #5593 multistate roster-bound successor T1

**Result: `PASS_METHOD_MULTISTATE_ROSTER_SCOPED`** for one authored six-episode synthetic fixture only. The frozen launch-ID roster is independent of the candidate output. The raw-only auditor verified all six IDs, all six integer ticks, denominator mass 6 at each tick, event-transition counts, and six rejected corruption controls.

The predecessor [T0 failure](../multistate_stop_recovery_5593_t0_20261002_01/FORMAL_FAILURE.md) remains unchanged: its auditor trusted a shortened ledger's self-reported denominator. T1 binds a separate frozen N=6 roster and exact ID set. It does not retroactively fix or replace T0.

## Reproduce

Using the pinned image ID in `FREEZE.json`, with `--network none`, `--cpus 1`, `--memory 256m`, `--pids-limit 64`, read-only `/src`, and separate disposable containers:

```sh
python -B /src/candidate.py /src/fixture.json /out/candidate_result.json
python -B /src/audit.py /src/fixture.json /src/frozen_roster.json /src/candidate_result.json /out/audit_result.json
```

The candidate and auditor each ran exactly once; retries=0. Construction tests are separate and ran 11/11 before freeze.

## Scope

Finite synthetic bookkeeping only. No real task cohort, estimator, policy effect, causal recovery benefit, independent-censoring assumption, model, GUI, or product claim is established. SAFE_STOP is nonterminal only where the explicit same-episode recovery event follows; terminal stop and administrative censor remain distinct states.
