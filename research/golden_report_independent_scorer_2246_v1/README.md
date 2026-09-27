# Golden report independent scorer — #2246

This additive fixture independently scores the retained golden-report.json without changing or rerunning the original live allocation. It is a prerequisite rung for #2246: it verifies that a retained report can be reconstructed into task/effect/release/accounting outcomes and that missing provider authority and ambiguous delivery fail closed.

## H/T/D/C/U

- H: the retained six-task golden report preserves independently scoreable task completion, exact submission counts, stale repair, usage accounting, and release evidence.
- T: parse the current-main report, recompute all task-level invariants, and exercise two negative controls: no provider authority and ambiguous delivery.
- D: source-pinned report blob, machine-readable audit output, SHA-256 canonical digest, and container repetition.
- C: no GUI, model, input, network, or task rerun; the original report is immutable evidence, not a new live result.
- U: a fresh desktop-to-CLI live run, model/provider execution, and cross-fixture generality remain unverified.

Scoped disposition: PASS_GOLDEN_REPORT_INDEPENDENT_SCORER_SCOPED. This is not an end-to-end live adapter PASS.
