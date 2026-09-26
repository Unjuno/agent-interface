# Issue #2548 — bounded fresh-observation reanchor

This is an additive successor experiment for the closed visual-context guard result. It tests whether exactly one fresh observation in the same live session can re-establish an admissible pair after the guard rejects an older pair.

## H/T/D/C/U

- H: a bounded fresh pair can recover admissibility only when it is same-session, non-duplicate, unambiguous, and within the one-observation budget; the guard remains fail-closed before that pair exists.
- T: six fixed-seed live ViZDoom sessions, one source observation, fixed coast/recovery program, and a single extra `observe` only in the fresh arms.
- D: viewport normalized MAE threshold 0.015; verdicts are `ADMIT`, `REJECT_CONTEXT_CHANGED`, `REJECT_NO_FRESH_OBSERVATION`, or `REJECT_PROVENANCE`.
- C: coast guard-only, drift guard-only, drift with fresh reanchor, unchanged coast with fresh reanchor, stale/no-fresh control, and ambiguous-fresh control.
- U: no model, token, latency, or hidden-state claims; the result is scoped to source-valid visual-pair admission and input release.

The formal plan and source freeze are in `plan.json` and `FREEZE.json`. The v3 allocation is in `formal_v3/`; `formal_v1/` and `formal_v2/` are retained as failed driver allocations with their stop reasons.

## Result

`PASS_BOUNDED_REANCHOR_PRESERVES_SAFETY_SCOPED`.

All six sessions completed with verified empty release and zero kills/deaths/map exit. The guard-only drift cases were rejected (MAE 0.0430–0.0445). The fresh same-session drift case admitted only the new pair (MAE 0.0000371), while the ambiguous fresh control rejected provenance. The unchanged fresh control admitted (MAE 0.0001021). No stale or missing-fresh input was admitted.

The independent Docker audit is `formal_v3/audit.json` and reports `PASS` with zero failures. This does not claim that a recovery action is safe beyond the tested admission contract.

## Failed allocations retained

- v1 stopped because the driver attempted `observe` after `terminal`; the runtime did not emit a fresh observation.
- v2 stopped because the driver selected the final typed observation as both post and fresh, making the fresh index undefined.

Neither failure is used as a scientific result. They remain in the working evidence directories and are described in `FAILURES.md`.
