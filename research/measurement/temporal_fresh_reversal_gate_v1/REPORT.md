# Temporal speculation fresh-reversal gate result

Decision: **PASS_FRESH_REVERSAL_GATE_SCOPED**.

Task: `TEMPORAL-SPECULATION-FRESH-REVERSAL-GATE-20260918-001` / Issue #1208.

This is a deterministic contract-composition study over the exact logical #1134 direction shape plus a fresh seeded nuisance corpus; it is **not** a replay of the raw X11 images and does not add new X11 evidence.

## First outcome
- primary invocation: 1; reruns: 0
- #1134-shaped fixed rows: 64
- continuation preserved: 32/32
- reversals yielded: 32/32
- immediate-current baseline reversal misses: 32/32
- fixed candidate/oracle mismatch: 0
- randomized cases: 250000
- randomized candidate/oracle mismatch: 0
- randomized reversal->continue escapes: 0
- malformed evidence fail-closed: 25120
- authority grants / task-input grants: 0 / 0
- independent audit: PASS, errors []
- copied-result corruption controls: 4/4 rejected
- frozen source rehash: all exact
- primary wall/RSS diagnostic: WALL=2.40 RSS_KB=92592; no performance claim

## Interpretation
#1194 established that current+history is observationally aliased for the frozen continue/reverse fixture. This result closes only the next deterministic composition: once one genuinely fresh post-current directional observation exists, a simple sign-consistency gate can preserve all authored continuation rows and YIELD all authored reversal rows without granting authority.

The result does **not** establish that waiting for the fresh sample is fast or useful end-to-end. The retained #1134 fixture makes the first post-current sample fully discriminative by construction. Real domains can reverse between samples, oscillate or have tracking noise. A next rung, if justified, must measure acquisition delay/noise and independently useful task effect; it should not add a learned supervisor to recover information absent at the current point.
