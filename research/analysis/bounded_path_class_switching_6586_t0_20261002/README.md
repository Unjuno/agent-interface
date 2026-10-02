# Bounded path-class switching — Issue #6586 T0

This is a finite synthetic method experiment, not a gameplay or product result.

## Reproduction

Run from this directory with Python 3.10+:

```sh
python3 -B -m unittest -v test_method.py
python3 -B -m py_compile candidate.py run_candidate.py audit.py test_method.py
python3 -B run_candidate.py --out results/a01/raw.json
python3 -B audit.py --raw results/a01/raw.json --out results/a01/audit.json
```

The candidate invocation is one-shot and refuses an existing output. The independent auditor is a separate process and refuses an existing audit output. `oracle.json` is evaluator-only and is never read by the candidate runner. Verify `FREEZE.json` before execution and preserve both outputs unchanged.

## Protocol and scope

See [preregistration](preregistration.md) for H/T/D/C/U, gates, host limitation, and interpretation. The experiment compares novelty-first and visited-edge/backtrack controls against a policy that accepts only a current binding/epoch/sequence-matched complete-cutset receipt, then switches only to a root-observed alternate route token. Six fixtures include viable same-class, recoverable detour, false cue, epoch invalidation, and no-alternate controls.

The retained formal disposition is **`FAIL_OR_HOLD`**: the frozen independent auditor reports 15 `missing_action_after_observation` errors because the one-shot runner ends goal rows at the goal observation without an explicit `STOP_GOAL` action event. The audit output is `results/a01/audit.json`; do not repair or relabel it. The raw event ledger is `results/a01/raw.json`; it retains all 18 rows. A separate trace review confirms the observed primary costs (23 for each baseline, 11 for class-aware) and goal attainment, but this is not the preregistered independent-audit gate and cannot be promoted to PASS. The next useful work is a separately frozen audit/protocol repair and successor allocation if still warranted, preserving this attempt byte-for-byte.

This is not a formal container pass and establishes no visual path-class inference, GUI/DOOM behavior, real task effect, safety, or runtime benefit.

## Provenance

- Source main SHA: `f1d8f6319ad6a1d6fd7f0219c17bb13f48fae7aa`
- Allocation: `PATH-CLASS-6586-T0-20261002-01`
- Additive evidence path; no predecessor evidence modified.
- Exact source hashes: `FREEZE.json`; result byte hashes are recorded by Git and should be computed when publishing this evidence.
