# Runtime reliability under uncertainty

This page groups four related but non-identical research questions. Each result belongs to its named fixture/allocation; a `STOP`, `HOLD`, or failed gate records that evidence and does not suspend unrelated work. GitHub Issues remain open where the broader question is unresolved.

## Liveness suspicion and verifier failure — #5531

**Idea.** Represent delayed or missing responses as suspicion, distinct from terminal failure, invalid evidence, and revoked authority. A late response must not silently restore authority.

**Evidence.** Early T0–T3 toy checks separate temporary suspicion, independent crash witnesses, restart fences, and failure domains. The T6 report preserves the original candidate trace: its corrected independent audit verifies 18 trials / 114 rows and finds the typed policy avoids permanent revocation of healthy-slow subjects in the three tested deadlines; it remains host-only logical-time evidence. A separate T4 hierarchical witness test is a finite synthetic classification result. These are not asynchronous-system guarantees or production availability evidence. The T6 report also preserves the preflight STOP and the rejected v1 audit; the corrected v2 audit did not rerun the candidate. [T6 report](../../research/analysis/failure_detector_5531_async_bound_t6_v1/REPORT.md), [T4 report](../../research/analysis/research_failure_detector_5531_t4/REPORT.md), [Issue #5531](https://github.com/Unjuno/agent-interface/issues/5531).

**Unresolved.** The prospective host-regime comparison was held after its derived labels were found unauditable; real observer timing, correlated failures, and runtime integration remain unestablished. Preserve each allocation's disposition independently.

## Timed resource deadlocks — #5410

**Idea.** Prevent structural wait cycles while respecting timed leases, hidden dependencies, and bounded recovery.

**Evidence.** The original 28-trace formal T0 failed its preregistered timed-liveness gate: short lease expiry repeatedly caused reacquire/replan livelock, including under SCC and reachability guards. Separate toy follow-ups show SCC rejection of a visible cycle, atomic bundle acquisition as an escape, and `UNKNOWN_MODEL` when dependency coverage is incomplete. These narrow mechanisms do not erase the timed-liveness counterexample or prove a live scheduler safe. [Preserved formal failure](../../research/analysis/siphon_5410_t0/FORMAL_FAILURE.md), [execution record](../../research/analysis/siphon_5410_t0/EXECUTION.md), [Issue #5410](https://github.com/Unjuno/agent-interface/issues/5410), [lease-feasible successor #5570](https://github.com/Unjuno/agent-interface/issues/5570).

**Unresolved.** Establish feasibility against the full lease critical path and a justified dependency model before claiming deadlock prevention or liveness.

## Verifier cascades and overload cost — #5375

**Idea.** Bound retry/cascade resource use while preserving capacity for mandatory safety verification; include the costs of rejection and quarantine.

**Evidence.** T0-a2 is `PASS_METHOD_AND_HYPOTHESIS_SCOPED` for its 270-row synthetic feedback model and joint capacity invariant; it does not establish runtime or production behavior. Rejection-cost A01's candidate violated the frozen per-tick capacity invariant, leaving its hypothesis unevaluated and preserving the auditor STOP. The distinct A02 allocation passed a 10-row raw-only audit with 4/4 corruption controls rejected; this supports only the finite method under its authored capacity model. [T0-a2 report](../../research/analysis/verifier_cascade_capacity_5375_t0a2_20261002/REPORT.md), [A01 report](../../research/analysis/circuit_rejection_cost_5375_a01_20261004/REPORT.md), [A02 report](../../research/analysis/circuit_rejection_cost_5375_a02_20261004/REPORT.md), [Issue #5375](https://github.com/Unjuno/agent-interface/issues/5375), [executor successor #5539](https://github.com/Unjuno/agent-interface/issues/5539).

**Unresolved.** Real verifier costs, concurrent-runtime interactions, and whether any admission policy improves service under operational workloads remain open.

## Belief contracts for hidden state — #5368

**Idea.** Admit an action only when its effects are acceptable across the hidden states consistent with current evidence; model external transitions and observation ambiguity explicitly.

**Evidence.** Risk-budget T0-v3 passed its read-only independent audit for 28/28 exact-rational rows, but the deliberate misspecification case reported 4% risk against a declared 20% actual hazard. External-transition T0 separately passed its finite nine-case audit: reachability prediction had zero unsafe admissions and retained two safe controls, while the sticky baseline made seven false admissions in that fixture. Observation-fiber successor #6774 is another separate synthetic result, merged by PR #6775; its nine-case reported result remains distinct from a separately disclosed 12-row duplicate, and current raw-byte custody does not match `RUN.json`. See the [#6774 custody record](observation-fiber-updateability-custody.md). None establishes calibration, GUI safety, or live action effects. [Risk-budget result](../../research/analysis/belief_risk_budget_5368_v3/RESULT.md), [external-drift result](../../research/analysis/belief_external_drift_5368_t0_20261003/RESULT.md), [Issue #5368](https://github.com/Unjuno/agent-interface/issues/5368), [successor #6774](https://github.com/Unjuno/agent-interface/issues/6774), [merged PR #6775](https://github.com/Unjuno/agent-interface/pull/6775).

**Unresolved.** Hypothesis completeness, event-alphabet coverage, source trust, calibration, and action/effect validation need independent evidence. View-updateability is a conceptual refinement, not an additional empirical result.

## Relationship and next work

These themes share conservative decisions under incomplete or delayed evidence, but they have different state models and failure criteria. Keep each Issue and allocation traceable; do not combine scoped passes into an integrated reliability claim. Useful follow-up work should target the remaining specific boundary in each Issue and should not require all workers to wait for this documentation or for one allocation's STOP/HOLD.
