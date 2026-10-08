# Issue #5370 T5 — bound authenticated urgency claims

## H/T/D/C/U

- **H:** A signed/authenticated urgency value alone is insufficient to justify priority inheritance. Inheritance must also match the exact verifier request and target, remain within its expiry, and correspond to a live wait-for/blocking edge.
- **T:** One finite Docker candidate run enumerates all 256 combinations of five Boolean binding predicates, claimed priority 1–4, and priority cap 2 or 3. A separately authored oracle independently enumerates and recomputes all output rows in a second container.
- **D:** PASS only if all 256 unique rows match; effective priority rises above the base only when all five Boolean predicates are true; unauthorized/unbound inheritance is zero; and the cap is never exceeded. Any mismatch is retained as FAIL/STOP/UNCERTAIN without rerun.
- **C:** If authentication, request/target binding, freshness, and a real blocking edge are externally trusted, those are adequate gates; additional claim attenuation is unnecessary. This is a predicate-logic toy, not cryptographic validation.
- **U:** No cryptography, key lifecycle, real scheduler, distributed wait graph, time source, starvation, GUI, verifier, or production authorization is tested. `unexpired` and `blocking_edge_exists` are trusted input bits in this model.

## Why this rung

Issue #5370 T4 found that unauthenticated self-asserted urgency must not trigger inheritance and explicitly identified trusted verifier request, target, and expiry binding as the next boundary. T5 adds exact request and target match, expiry, and a live blocker edge as independent predicates while retaining the T4 authentication gate. The priority-ceiling value is also checked separately from claim validity.

## Frozen inputs

See `FREEZE.json` for source hashes, image digest, base-main SHA, finite dimensions, invocation counts, and decision gate. Candidate and auditor are separate programs; the auditor imports no candidate code.

Pre-freeze construction correction: the first draft's expected count assumed eight inherited rows; inspection of the finite domain showed six (`claimed_priority` 2–4 for each of two caps). This was corrected before the source freeze and before any candidate or auditor invocation. It is a pre-run harness correction, not an experimental outcome.
