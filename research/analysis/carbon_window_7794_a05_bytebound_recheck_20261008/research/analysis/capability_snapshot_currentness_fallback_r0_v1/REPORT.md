# Capability snapshot currentness/fallback R0 — retained result

Issue #1919. Parents #40/#1597/#1607/#1623; live prerequisite #1910.

## Disposition

**PASS_CAPABILITY_SNAPSHOT_CURRENTNESS_FALLBACK_SCOPED**

Formal1 / reruns0 / replacements0 / tuning0.

## Contract

A capability snapshot may guide candidate path selection only when it is runtime-owned, exact-current in session/surface scope and capability generation, self-content-bound, equal to the runtime current snapshot identity, and explicitly non-authoritative.

The resolver returns:
- DIRECT only for a current supported capability;
- FALLBACK only for the declared obligation-preserving SEMANTIC_ACTIVATE -> PIXEL_ACTIVATE edge when PIXEL_ACTIVATE is current+supported;
- UNSUPPORTED when no admissible capability path exists;
- an invalid/stale disposition for wrong provenance, scope, generation, digest, authority framing, or fallback revision.

Every result has `grants_action_authority=false`. Capability discovery selects a candidate execution path; actual execution still requires the ordinary authority/focus/currentness admission path.

## Formal exhaustive result

248,832 Cartesian rows.

Candidate/oracle mismatch: **0**.

Invalid snapshot selections:
- wrong scope: 0
- stale generation: 0
- future generation: 0
- non-runtime-owned: 0
- tampered digest: 0
- authority=true snapshot: 0
- invented/cross-obligation fallback: 0
- total invalid-selected: 0

Valid current outcomes:
- DIRECT: **144**
- typed FALLBACK: **24**
- UNSUPPORTED: **120**
- capability result authority grants: **0**

Negative discriminators:
- PRESENCE_ONLY stale/revoked selections: **144,984**
- FALLBACK_INVENTING noncanonical selections: **100,224**
- explicit cross-obligation invented selections: **6,912**
- CAPABILITY_EQUALS_AUTHORITY laundering opportunities: **168**

The explicit cross-obligation negative maps SEMANTIC_ACTIVATE to OBSERVE_CONTEXT; the candidate rejects that fallback mode.

Primary audit passes six corruption controls. Independent audit regenerates the phase-specific Cartesian corpus without importing candidate/oracle modules; checked_rows248832/errors[].

## Retained preformal defect

The first construction used the first5,000 lexicographic formal rows. Those rows were concentrated in runtime_owned=false states and therefore exercised no valid DIRECT/FALLBACK paths. Candidate/oracle mismatch and all invalid-selection safety counters were already zero, but positive discriminator gates were absent. The construction auditor also compared that 5,000-row result against the full formal corpus.

Formal remained0. Before source freeze, construction was replaced by a frozen balanced18-case directed set and the independent auditor was made phase-specific. The full248,832-row formal corpus and scientific H/T/D/C/U were unchanged.

Before freeze, the already-declared invented-cross negative was also made explicit as SEMANTIC_ACTIVATE -> OBSERVE_CONTEXT so obligation crossing is directly exercised.

## Integrity

- exact source bundle Git blob: `f773464ec8fff2540725eb9cf39e80d55e3e1bde`
- formal RESULT SHA-256: `e5b75a6e5bbc35164630c46863e816a5f27319ea8a7bc27ba27718eddaf68400`
- primary AUDIT SHA-256: `45d569a76e7b5b68b1e12966dc15b293d8d87a75add7f5d2ded1ef438ddf7cb1`
- independent audit SHA-256: `2124d46575979bf398c09ed8d595f40c0f43c9b5ac0f84eb4599fdb879b000ee`
- postformal source identities: 6/6 unchanged.

## Interpretation

This closes the missing contract between a stable service manifest and mutable session capabilities: a stable manifest may reference a separately current snapshot, but that snapshot must itself be scope/generation/content bound and non-authoritative.

A capability being present is not permission. A fallback being technically available is not admissible unless it is explicitly declared and preserves the operation obligation.

## Scope / next rung

Synthetic capability vocabulary only. No signing, transport, planner usability, model/token/latency/task/general-GUI or runtime-ABI claim.

The next valid live rung is to bind #1910's real XTEST discovery into this generation-bound snapshot and exercise capability revocation/scope changes while preserving authority=false.
