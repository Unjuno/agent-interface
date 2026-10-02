# #6285 T5 — independent reconciliation of T2's false-stop assertions

**Disposition: `PASS_T2_FALSE_STOP_RECONCILED_SCOPED`.** One raw-only audit ran, exit 0; retries 0; errors 0. Candidate/runtime/model/GUI/network/action/OS-input invocations: 0. T2's original `FAIL_OR_HOLD` is preserved and not rerun.

## Evidence

- SHA-256 matched for the frozen T2 comparator/tests/output transcription and the pinned T0 model/candidate/audit inputs.
- Independent universal total-correctness recomputation over 10 states and 13 outcomes matched the T0 candidate preimage: `ready_complex`, `ready_simple`, and `unobservable_safe_alias`.
- Candidate rows cover every state/outcome pair. A forward universal check over those complete rows admits exactly the same preimage; therefore T2's `proposal_local_failed_to_illustrate_incompleteness` was an invalid expected outcome, not a disagreement in this fixture.
- `ready_simple` and `already_committed` both have `pixels=save_visible`, but their oracle labels differ (inside versus outside the preimage). The T2 check searched for a partition containing exactly those two states; the actual pixel partition also contains additional states. The pair is still a valid mixed-label alias, so `pixel_alias_not_unknown` was also an invalid assertion.
- T2 produced only one feasible cue-set/cost row. The coordinates were illustrative ordinal toy costs, not measured latency, tokens, or risk. No measured cost ranking, weighted sensitivity, or empirical cost result is established.

## Interpretation and boundary

This audit reconciles two false-stop assertions; it does not prove the backward-derived method superior to every forward checker. A forward checker that covers the entire finite model is extensionally equivalent on that model. #6256's baseline/comparator needs a more precise operational definition before comparative method claims can pass. The observation-cost requirement remains open beyond logical cue sufficiency.

T0 #6276 remains `HOLD_INCOMPLETE_MUTATION_COVERAGE`; T1 #6277 remains `PASS_REQUIRED_MUTATION_COVERAGE_SCOPED`; T2 remains `FAIL_OR_HOLD`; T3 and T4 startup stops remain retained. No historical result was changed. No container was run: Docker Desktop service is stopped and CLI calls timed out; this CPU-only audit requires none. No live GUI, task effect, authority, latency, efficiency, safety, or product claim.
