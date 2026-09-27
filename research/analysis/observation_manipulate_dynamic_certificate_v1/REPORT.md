# #1904 state-conditioned MANIPULATE_TO decision certificates

Decision: **PASS_O3_MANIPULATE_DYNAMIC_CERTIFICATE_SCOPED**.

## Why this is a fresh question

Parent #1897 is retained as `STOP_PREFORMAL_FULL_CORPUS_CONSUMED_NO_FORMAL`. Its phase-level support-union exploratory result is non-poolable and was not rerun to manufacture a PASS.

This successor asks a different question: for a **specific current state**, can the branch decision be certified by a smaller support mask than the whole phase-level union?

## Construction

Before source freeze, construction was restricted to six selected current states and the 16 possible masks for each state. The full48-state/768-transition formal corpus was not enumerated.

Examples:
- PREPARE state (T=1,D=1,E=0,S=1), already ABORT -> minimum certificate `S`, versus phase union `TDS`;
- PREPARE READY (1,1,0,0) -> `TDS`;
- EFFECT_PENDING COMPLETE (1,1,1,0) -> `ES`, versus phase union `TDES`;
- EFFECT_PENDING CONTINUE (1,1,0,0) -> `TDES`;
- TERMINAL ABORT -> `S`;
- TERMINAL COMPLETE -> `ES`.

Remote readback matched model/formal/PLAN exactly. The audit source differed only by a trailing semicolon; remote bytes were adopted before freeze and the manifest repaired. Scientific logic was unchanged.

## Formal

Exactly one source-frozen exhaustive invocation:
- current states: **48**;
- transitions: **768**;
- reruns/replacements/tuning: `0/0/0`.

A certificate M for current state s is valid iff every next state agreeing with s on M preserves the same branch decision. The candidate chooses minimum cardinality; ties use deterministic domain order T<D<E<S.

### Result

| Metric | Dynamic certificate | Phase union | Global all |
|---|---:|---:|---:|
| false suppressions | **0** | 0 | 0 |
| safe suppressions | **275** | 112 | exact-no-change only |
| false forwards | **15** | 178 | 242 |

Additional:
- certificate validity errors: **0**;
- minimality errors: **0**;
- strict-narrowing current states: **37 / 48**.

Certificate-size distributions:
- PREPARE: size1=8, size2=6, size3=2;
- EFFECT_PENDING: size1=8, size2=4, size3=3, size4=1;
- TERMINAL: size1=8, size2=8.

The strongest pattern is logical short-circuiting. Whenever S=1, ABORT is already determined, so `S` alone is sufficient regardless of T/D/E. In EFFECT_PENDING, E=1,S=0 makes `ES` sufficient for COMPLETE.

## Integrity

Independent audit re-derived all48 selected certificates without importing candidate selection code, then re-evaluated all768 transitions.

- audit decision: PASS;
- corruption controls:5/5 reject;
- result SHA-256: `5820028dd62f2ae3e18e02c8ae04a9ac1b5fdeebd54aeaaa0649bd4ec69a5b26`;
- audit SHA-256: `67fa8f43bd780edad71fa4a48ca411837bfa813f0cb7683a6515e1f00a1b03ed`;
- ledger SHA-256: `d3e8278a0837adcd869c4ebc68dcd799c3b7926dfbfd96b2e8c02ff107184f63`.

## Interpretation

Phase-level support closure is safe but can be much broader than necessary. For deterministic branch logic, a state-conditioned decision certificate can preserve exact safety while substantially reducing needless dependency sensitivity.

This is closely related to short-circuit evaluation, Boolean certificate complexity, and truth-maintenance systems: dependencies that *could* matter somewhere in a phase need not all remain live for the current branch outcome.

## Boundary

This optimizes support **cardinality**, not actual capture cost. Equal-cardinality certificates may have different observation expense, and real GUI predicates may be noisy or costly. No model, GUI, token, latency, task-success or production compiler claim is made.
