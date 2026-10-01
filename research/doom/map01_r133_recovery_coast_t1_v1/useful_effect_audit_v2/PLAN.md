# Recovery-arm useful-effect gate audit T3 v2

Successor to v1's immutable `STOP_INTEGRITY / counterbalance_order`; v1 raw and audit are unchanged. This version repairs only the finite fixture schedule to match the adjudicator's frozen `(1 recovery, 1 coast, 2 coast, 2 recovery, 3 recovery, 3 coast)` order.

## H / T / D / C / U

**H.** The frozen v2 paired adjudicator can emit `PASS_DIRECTIONAL_FIXTURE_SCOPED` when recovery has no positive kill/exit pair, because a coast-arm kill satisfies its global `useful_present` gate while survival dominates the paired progress tuple.

**T.** Freeze the exact existing adjudicator and five synthetic six-session records: coast-only positive effect with recovery survival; both arms positive; no positive effect; no threat contact; overlapping exposure. Respect exact counterbalance order. Candidate once; then independent raw-only audit once. No live experiment or rule mutation.

**D.** `COUNTEREXAMPLE_SCOPED` iff the coast-only case passes with zero recovery kill/exit and 3 coast-positive pairs, and the positive, no-effect, no-threat and overlapping-exposure controls respectively pass, HOLD, HOLD and non-PASS. Else preserve exact FAIL/STOP.

**C.** Deterministic stdlib-only host construction frozen to main `5759a6e65b8b5e7487fb2ad61f53bb531aeaf512`. Container not used: exact pure-Python semantics only; no container lease or platform-specific behavior is needed. No model, game, GUI, input, GPU, or shared allocation.

**U.** Synthetic specification counterexample only. It cannot establish task-effect validity, policy suitability, live efficacy/safety, or authorize a live allocation. Survival may intentionally count as a useful recovery outcome; the result therefore identifies a choice the live-study estimand must state, not an automatic defect in the rule.
