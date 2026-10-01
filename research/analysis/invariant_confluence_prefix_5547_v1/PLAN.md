# Issue #5547 finite-state construction experiment

Frozen source main: `59ffec5d551b0adcf11057eee6da814237a748c8`.

## H / T / D / C / U

- **H:** For the frozen finite interface-operation model, join-closure classifies evidence addition and tombstone-dominant revocation as `monotone_safe`, while epoch refresh versus action admission, distinct quota reservations, multiple grants beyond capacity, and duplicate semantic-effect commits have invariant-breaking concurrent joins. A serializable baseline rejects or orders those conflicting updates and remains invariant-safe.
- **T:** From one fixed empty state, enumerate every ordered pair of the frozen 13 commands. Apply each command independently, join the resulting states, and check both merge argument orders. Also try both serial execution orders with the same preconditions. Use a separate invariant oracle, a fixed expected conflict matrix, unit tests, and a separate-process raw-only audit with five frozen mutations.
- **D:** PASS only if exactly the four preregistered conflict families are found, every accepted classification is invariant-closed in the enumerated matrix, both serial orders remain invariant-safe, unknown operations are coordination-required, and all five raw mutations are rejected. Any missed counterexample is FAIL; any unexpected conflict is UNCERTAIN pending model review.
- **C:** Coordination may be avoidable for more or fewer cases under richer operation semantics; in particular, revocation is only safe here because immutable revocation tombstones dominate grants, and evidence has no authority side effect.
- **U:** Finite synthetic model only. The result says nothing about arbitrary operation schemas, external systems, liveness, fairness, production coordination costs, or real interface behavior.

## Fixed finite model

State fields are evidence IDs, granted capability IDs, revoked capability tombstones, an authority epoch, admissions tagged by epoch, invalidated admission IDs, quota reservations (limit 1), and semantic effect commit records. Set-valued facts merge by union; epoch merges by max. The independent oracle checks the explicit safety invariants. No randomization or outcome-dependent tuning is used.

## Invocation boundary

Host CPU only because no exact Docker/OrbStack slot is assigned by #5085. The test suite runs once, the frozen runner once, and the raw-only auditor once in a distinct process if the runner exits successfully. No GUI, input, model, GPU, CUDA, or Docker command is part of this allocation.
