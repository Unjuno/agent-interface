# Cross-domain handback evidence envelope v1

Issue #1530. Retained-evidence analysis only; zero new model, GUI, X11, task-input or formal allocations.

## Decision

`PASS_REPRESENTATION_TRANSFER_CANDIDATE`

A single scalar `CURRENT_EFFECT` does **not** transfer safely. The smallest representation that preserves the retained evidence is a common no-authority envelope with a tagged evidence variant and an explicit historical `source_role`.

Retained variants represented here:

- `OBSERVED_CURRENT_EFFECT` — the exact #1518 X11 `CURRENT_EFFECT` role; it resolves that fixture's pixel-effect handback only.
- `OBSERVED_STATE_CHANGE` — MAP01 HUD health/ammo transition; explicitly non-causal and not established as useful task effect.
- `VERIFIED_PHYSICAL_RELEASE` — MAP01 owner verified empty input; does not imply task effect.
- `UNRESOLVED_EFFECT` — absence/insufficiency stays unresolved rather than being coerced to success.

All variants carry `input_authority=false` and `semantic_authority=false` in this transfer representation. A future runtime schema may carry authority elsewhere; this evidence envelope must not mint it.

## Retained evidence

- #1518 `FORMAL_SUMMARY.json` blob `458ba631c0d5ba58332bc5c432db42a497061169`: 16/16 candidate current-effect receipts, effect-after-handback 0/16, four NO_EFFECT unresolved controls.
- #1518 `experiment.py` blob `429e790f08ea4f083dec9ab61a5a282e0f2b45ed`: receipt role `CURRENT_EFFECT`, session/request lineage, input/semantic authority false.
- MAP01 first-useful-feedback summary blob `bfdcd8c299a7dbe759977b346737bf592e3f4772`: one admitted plan has no state feedback; three have health/ammo state feedback; all stronger task-effect feedback is null; decision `SCHEMA_INSUFFICIENT_FIRST_USEFUL_FEEDBACK`.
- MAP01 held-input source closure blob `f077c1bd576af8f3e83c6d394669361f597b6e5c`: one natural revocation reaches verified empty owner input 26.090 ms after typed event emission, but usefulness remains unproven.

## Container test

Seven representation records cover the X11 positive/current-effect case, X11 NO_EFFECT unresolved case, four MAP01 admitted plans, and the MAP01 verified-release boundary. The corrected validator returns no semantic/authority errors. Five corruption controls are rejected: MAP01 unknown→useful, authority escalation, X11 source-role collapse, state-change→resolved-effect coercion, and physical-release→useful coercion.

Independent audit rechecks the source blob identities, X11 role, MAP01 insufficiency, no-authority invariant, the 26.090 ms retained release sample, and separately implemented corruption detectors.

## Retained precheck failure

The first corruption-control precheck failed because a fixed row index selected a MAP01 `UNRESOLVED_EFFECT` row instead of an `OBSERVED_STATE_CHANGE` row. Scientific disposition was NONE. The repair changed only test targeting to select by domain+variant; retained evidence, thresholds and the decision rule were unchanged.

## Boundary

This PASS is a **representation-transfer candidate**, not a runtime or behavioral PASS. It rejects the stronger proposal that all domains share one generic current-effect receipt. Domain-specific evidence semantics remain distinct under a shared envelope. MAP01 first useful task effect remains unresolved and must be measured by a new allocation before it can close handback on that basis.

## Next discriminator

Use the envelope on a fresh real-application task-semantic transition only after the effect source independently establishes the requested task predicate. #1537 remains a retained delivery stop. #1539 repaired XTEST→raw-PTY delivery. #1541 then passed semantic-handback construction with that readiness rule but consumed one monolithic formal invocation that hit the 45 s outer limit before `FORMAL.json` serialization; scientific disposition is `NONE`. The next XTerm discriminator should therefore change only execution packaging to immutable batches, preserve #1541 science/gates, and exclude its partial formal sessions from pooling.
