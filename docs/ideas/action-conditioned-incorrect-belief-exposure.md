# Action-conditioned incorrect-belief exposure

- **Status:** Finite method result passed; no live authority or belief exposure was measured.
- **Source:** Issue [#7986](https://github.com/Unjuno/agent-interface/issues/7986).
- **Idea:** Measure the duration that an action is admissible under a live authority/belief combination while an independent truth sidecar says the belief is wrong, separately from whether an unsafe effect occurs.
- **Outcome:** A01 `PASS_METHOD_SCOPED` on eight finite synthetic rows, with candidate and raw-only truth auditor each run once and 8/8 rows reconstructed. Old-but-correct belief, stale-after-transition, fresh-but-misbound belief, no action opportunity, and forbidden action were assigned distinct exposure/effect outcomes. Missing truth and ambiguous clocks returned UNKNOWN. The candidate never saw truth-sidecar data. No live authority, GUI, or task-safety result. Merged [PR #7994](https://github.com/Unjuno/agent-interface/pull/7994) preserves the package.
