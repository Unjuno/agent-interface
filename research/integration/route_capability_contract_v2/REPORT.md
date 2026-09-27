# Route capability contract v2 — audited retained-evidence negotiation

Task `ROUTE-CAPABILITY-CONTRACT-20260917-002`, Issue #839. BASE `f9989b833611fb9cb8708007445b94a95d70c516`.

## Result

Decision: **`PASS_EFFECT_DIMENSION_CAPABILITY_NEGOTIATION_AUDITED_SCOPED`**.

This is the instrumentation-only successor to #828. Selector semantics, retained #792/#803 evidence, all ten request rows, baseline policy and candidate policy are unchanged from v1. Construction verified baseline+candidate decisions are identical to the retained v1 formal result 10/10 before freeze.

The formal runner was invoked exactly once. The complete generic audit finds three flat-baseline semantic weakenings: `center-fallback-wheel`, `center-native-only`, and `center-insufficient-only`. The dimension-aware candidate has zero semantic weakenings. An independently implemented verifier recovers the same 3/0 sets.

Candidate behavior remains the same as v1: scale-only requests may use either retained scale-capable route; a scale+center request falls back from insufficient `native_fixed80` to `ctrl_wheel` when available; a centered request with only insufficient routes returns `UNSUPPORTED`; the #792 one-contact negative is never selected; unknown dimensions and missing route provenance fail closed.

Five structured corruption controls — retained evidence identity, wrong candidate route, negative-route selection, formal invocation count, and omission of one baseline weakening row — are all rejected.

## Integrity

- formal invocations: 1; reruns: 0;
- unchanged selector Git blob: `4822b72c70d729705b869d08a2b0a96e1dceccab`;
- unchanged runner Git blob: `1c27b71ae7a08c0dd030a8a27c4d62194fe47d57`;
- unchanged request matrix Git blob: `f9275df0e78bc257c9e022bcbbe7669fd8ec3a44`;
- retained #792 evidence Git blob: `389fe8cd93603c0415480fc398664a903dede0f4`;
- retained #803 evidence Git blob: `28bc4a8c07958db58efe98eb73881cbced46c481`;
- formal result SHA-256: `3fc69fe7b0c73dad773719005dbf860c6a78696296bb91aacc76ed94e3a4e525`;
- frozen audit SHA-256: `b1391bf576aa779b90b440b2fd78c94a16d7e4dfe3f89b8ac095fde6daf85bca`;
- independent verifier SHA-256: `fcb972fac562a76cba559507abee084154f1b1701768f7720673e501ac658dd9`;
- corruption controls SHA-256: `339056192983e0b07c058893ba750934604225035eb3c98dc7c27d7903433763`;
- frozen source rehash after formal: exact, zero mismatches.

## Interpretation

This PASS repairs v1's measurement defect and supports one narrow integration claim: a route-selection layer can preserve already-measured semantic effect dimensions instead of treating any successful zoom route as interchangeable. It does **not** discover route capabilities automatically and does not establish that a capability remains valid after session, geometry, surface or environment changes.

No GUI/model/device input or shared runtime mutation occurred. The next discriminating question is whether capability evidence must be bound to current session/geometry and fail closed when those dependencies change.
