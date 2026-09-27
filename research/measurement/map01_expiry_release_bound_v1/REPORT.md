# MAP01 expiry-release bound reconstruction

Issue #4189. Retained-artifact successor to #3243 run 35471098475 / artifact 10592963131.

## Decision

**PASS_EXPIRY_RELEASE_BOUND_RECONSTRUCTION_SCOPED**

The historical #3243 -06 runner summary remains unchanged and remains FAIL because pair2/3 BOUNDED_RECOVERY recorded `d:unverified_release`. This successor asks only whether the retained owner-level expiry evidence can support a stricter, correctly scoped occupancy interval.

## First outcome

| pair | historical input bounds | expiry substitutions | reconstructed lower occupancy | reconstructed upper occupancy | reconstructed valid |
|---|---|---:|---:|---:|---|
| 1 | valid | 0 | 136,957,024 ns | 137,945,142 ns | yes |
| 2 | invalid: unverified release | 1 | 137,666,359 ns | 140,109,955 ns | yes |
| 3 | invalid: unverified release | 1 | 136,225,925 ns | 137,954,010 ns | yes |

Pair1 reproduces the original bounds exactly and needs no substitution.

In pair2/3 the third `d` admission occurs just before the lease deadline. InputOwner v10 reaches `time.perf_counter_ns() >= active.deadline`, releases all held input, XSyncs, verifies an empty key/button state, and records `owner_release(reason="expired")`. Only later does the ordinary hold path attempt another key-up; because ownership was already cleared, that later transition is marked `owner_transition_verified=false`.

For those two rows only, the candidate treats key-up as interval-censored between the exact lease deadline and owner-release `verified_ns`:
- pair2: [140899286892, 140900507559] ns;
- pair3: [160941656037, 160942234565] ns.

The later ordinary releases begin 60.3 ms / 55.0 ms after those verified expiry releases and are classified only as redundant post-expiry attempts.

## Integrity

- artifact ZIP SHA-256: `571be29b4501b7e697f5edcfdc373519f6e404190ae93fdee0f87ba3cfb39f49`;
- InputOwner v10 Git blob: `341b3c01649943ddaad5f28431a792c4889cc36e`;
- preformal candidate corruption controls: 8/8 rejected;
- independent audit self-test: 5/5;
- formal invocation/reruns/replacements/tuning: 1/0/0/0;
- formal result SHA-256: `ce30e77a43a921306f132625a020765700ad2fb4ed1866e18a9eb434a1c52a0d`;
- formal audit SHA-256: `4d822e29eeb4d1f5451d30253c171976102ed644e7d2ab69c06ed3a94fc48a90`;
- independent audit mismatch count: 0.

## Interpretation boundary

This does not turn #3243 into a recovery efficacy PASS. It establishes only that its pair2/3 input-bound failures are explainable by a measurement contract that ignored an earlier verified owner-expiry release and then treated the later redundant up as fatal.

The reconstruction is intentionally narrow: one key, one owner, exact matching lease deadline, exactly one neutral verified expiry record, strict timestamp order, independently neutral terminal. Multi-key attribution or missing/mismatched expiry evidence remains fail-closed.

There are still zero independently useful TASK_EFFECT events in the retained -06 recovery arms, so no recovery-benefit conclusion follows.
