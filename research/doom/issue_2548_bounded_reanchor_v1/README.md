# Issue #2548 — bounded fresh-observation reanchor

This is an additive successor experiment for the closed visual-context guard result. It tests whether exactly one fresh observation in the same live session can re-establish an admissible pair after the guard rejects an older pair.

## H/T/D/C/U

- H: a bounded fresh pair can recover admissibility only when it is same-session, non-duplicate, unambiguous, and within the one-observation budget; the guard remains fail-closed before that pair exists.
- T: six fixed-seed live ViZDoom sessions, one source observation, fixed coast/recovery program, and a single extra `observe` only in the fresh arms.
- D: viewport normalized MAE threshold 0.015; verdicts are `ADMIT`, `REJECT_CONTEXT_CHANGED`, `REJECT_NO_FRESH_OBSERVATION`, or `REJECT_PROVENANCE`.
- C: coast guard-only, drift guard-only, drift with fresh reanchor, unchanged coast with fresh reanchor, stale/no-fresh control, and ambiguous-fresh control.
- U: no model, token, latency, or hidden-state claims; the result is scoped to source-valid visual-pair admission and input release.

The formal plan and source freeze are in `plan.json` and `FREEZE.json`. The v3 allocation is in `formal_v3/`; `formal_v1/` and `formal_v2/` are retained as failed driver allocations with their stop reasons.

## Result and qualification history

Formal v3 initially reported `PASS_BOUNDED_REANCHOR_PRESERVES_SAFETY_SCOPED`, but PR review found that its auditor did not enforce completeness/safety invariants and its provenance decision trusted plan booleans. That v3 PASS is **not qualified**; see `REVIEW_RESPONSE.md` and the retained raw `formal_v3/` files.

Formal v4 is the authoritative result: `PASS_BOUNDED_REANCHOR_PRESERVES_SAFETY_SCOPED`.

All seven fresh sessions completed with verified empty release and zero kills/deaths/map exit. Guard-only drift was rejected (MAE 0.04418). The same-session fresh drift pair admitted at MAE 0.00362, below the fixed 0.015 threshold. The unchanged fresh pair admitted at MAE 0.0000991. Stale/duplicate, cross-session, and incomplete receipts rejected from their captured receipt identity. No stale or malformed receipt was admitted.

The independent v4 Docker audit is `formal_v4/audit.json` and reports `PASS` with zero errors. The mutation audit is `formal_v4/mutation-check.json`; it rejected empty/truncated data, terminal failure, unverified release, nonzero death, and a foreign-session mutation. This does not claim that a recovery action is safe beyond the tested admission contract.

## Failed allocations retained

- v1 stopped because the driver attempted `observe` after `terminal`; the runtime did not emit a fresh observation.
- v2 stopped because the driver selected the final typed observation as both post and fresh, making the fresh index undefined.

Neither failure is used as a scientific result. The v3 execution completed, but its PASS was invalidated during review because its gate and audit were insufficient; see `FAILURES.md`. Raw allocations remain retained.
