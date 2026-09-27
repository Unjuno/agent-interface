# CURRENTNESS_INVALIDATED critical kind v1 — retained first outcome

Decision: **`PASS_CURRENTNESS_INVALIDATED_KIND_SCOPED`**.

One source-first formal invocation, reruns0. Candidate differs from exact #1021 parent queue contract only by adding `CURRENTNESS_INVALIDATED` to `CRITICAL`.

Formal seed `106020260918001`:
- mixed streams: **100,000**, candidate/reference mismatches **0**;
- generated `CURRENTNESS_INVALIDATED` events: **45,566**, loss/duplication cases **0**;
- parent-domain streams without the new kind: **50,000**, candidate/parent regressions **0**;
- authority promotions: **0**.

Thus one explicit currentness-invalidated evidence role can be added without changing old-domain reducer outputs; it is retained exactly like other critical evidence regardless age and never grants input authority.

Independent audit PASS with errors `[]`; five corruption controls rejected5/5. Model/GUI/task-input actions0. Formal diagnostic wall ~5.50s / max RSS92,708KB in this container; not a performance claim.

Scope: queue vocabulary/mechanics only. This does not yet prove the observable-signal guard adapter. The next bounded rung is to normalize exact `HARD_INVALIDATED/UNKNOWN` guard outcomes into this new role while preserving reason/provenance and no-authority semantics.
