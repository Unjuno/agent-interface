# Issue #8636 T0 A04 — fresh-seed rotation-feature allocation

**Before-run state: frozen package; candidate invocations = 0, auditor invocations = 0.**

A04 is a new deterministic CPU-only allocation using disjoint seeds 30090–30119 in each of four strata. A01, A02, and A03 are preserved at their original dispositions and will not be rerun. Candidate code and method are unchanged. The independent auditor incorporates the A03 finding: it still independently reconstructs the pairwise-shape gate, then predicts the candidate's exact recorded reason `feature shape changed` rather than its internal phrase `shape changed`. A construction regression covers the A03 counterexample. A04 retains the previously corrected ViewState-oracle replay as well.

Read `PROTOCOL.md` and `FREEZE.json` before running. The exact CPython executable, source hashes, commands, fresh seed set, and one-invocation limits are frozen. Candidate and auditor each have one invocation; retries are prohibited.

No WSLc, container, GUI, game, model, OS input, external service, or live effect is used. Any result is limited to this synthetic analytic fixture.
