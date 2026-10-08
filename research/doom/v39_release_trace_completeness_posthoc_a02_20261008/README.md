# V39 retained release trace completeness posthoc A02

## H / T / D / C / U

**H.** The A01 independent auditor recomputed selected release-coverage and timing fields but accepted altered provenance and other result claims because it did not compare the full result against a complete raw-derived oracle.

**T.** Keep A01 and its v2 result/audit unchanged. Reuse A01's frozen raw inputs, verify the exact A01 result and audit blobs from merge `a0d0602b89b1f5a05f851728fe90684ec4bfeff5`, independently reconstruct every v3 result field, and mutate each previously unchecked field one at a time. Run the focused suite normally and with Python optimization enabled. Do not rerun the game, model, or original allocation.

**D.** PASS only when the independent reconstruction exactly equals the complete result object, including provenance and every nested cancellation row; unknown fields and every result mutation must fail closed. Candidate output and the independent audit must reproduce byte-for-byte from frozen inputs.

**C.** Exact-object validation is scoped to the declared result-v3 schema and pinned source set. A future schema or input set requires a new versioned oracle; matching this result does not prove physical-key state or application consumption.

**U.** This is an analytical correction to one retained historical run. It does not add a live threat exposure, per-key timing, useful feedback, recovery, or MAP01 completion.

## Result

The A02 raw-derived result is unchanged in its historical counts and outcome: seven cancelled terminals have verified empty aggregate releases; one of three interrupted, input-bearing programs has a separate verified early-release event. The result now binds its pinned input SHA-256 values and A01 predecessor provenance. The independent auditor reconstructs every field and rejects missing or additional claims.

Seven mutations covering the formerly unchecked `main_commit`, `allocation_id`, `prior_audit_formal_pass`, `all_cancellation_rows`, `per_key_release_measurement_events`, `independent_useful_feedback_timestamp`, and `decision` fields are rejected individually. An unknown extra result field is rejected as well. A01's files remain preserved unchanged under `predecessor/` and their Git blob, byte count, and SHA-256 are checked against the frozen A01 merge.

## Reproduce

From repository root:

```powershell
python -B research/doom/v39_release_trace_completeness_posthoc_a02_20261008/run_audit.py --output RESULT_REPRO.json
python -B research/doom/v39_release_trace_completeness_posthoc_a02_20261008/audit_result.py --result RESULT_REPRO.json --output AUDIT_REPRO.json
python -B -m unittest -v research.doom.v39_release_trace_completeness_posthoc_a02_20261008.test_audit
python -O -B -m unittest -v research.doom.v39_release_trace_completeness_posthoc_a02_20261008.test_audit
```

The scripts refuse to overwrite existing output files. Frozen raw identities and predecessor identities are in `FREEZE.json`. No game, model, GUI, X11, OS input, container, or GPU was used.
