# #1720 Resource-footprint contract for phase overlap

Decision: **PASS_PHASE_OVERLAP_RESOURCE_FOOTPRINT_SERIALIZABILITY_SCOPED**

## Question

#1670 established that a single serialized input actuator does not require whole-intent serialization when a first intent's effect/verification tail can remain pending while later work starts. #1688 and the retained #1707 evidence show why surface identity is not enough: independent-looking surfaces can still touch hidden shared state.

This rung asks for the smallest conservative contract between those extremes.

## Result

The formal exhaustively enumerated 104,976 four-phase program vectors over three resources, two initial states and both A→B / B→A intent orders, for **419,904 rows**.

The candidate allows the first intent's pending tail to overlap the second intent only when the first tail's complete declared read/write footprint has no conflict with the union of the second input and tail footprints. Input bursts remain serialized. UNKNOWN declarations serialize.

Results:

- complete-footprint overlap admissions: **116,856**;
- legal overlap completion-order checks: **233,712**;
- candidate/oracle mismatches among admitted overlaps: **0**;
- declared-conflict serializations: **303,048**;
- UNKNOWN parallel admissions: **0**.

Two discriminators show why the contract matters:

- a SURFACE_ONLY policy would produce **248,496** state/observation mismatches;
- deleting the actual conflicting dependency from the first-tail declaration also produces **248,496** mismatches among the admitted defective cases.

A minimal retained counterexample starts from state [2,0,1]: A's tail reads r0 while B's tail writes r0=0. Distinct surface identity cannot preserve A's observation if B's effect is allowed to reorder before A's pending read.

## Analytical argument

For an admitted overlap, the only operations moved across the whole-intent serial boundary are second-intent phases moved before the first intent's pending tail. The frozen predicate excludes every read/write and write/write conflict between that first tail and both second phases. Therefore each moved phase commutes with the first tail with respect to both declared state and the phase return value. Repeated adjacent swaps transform either legal overlap completion order back into whole-intent serial order without changing the observable result.

This proves sufficiency under the stated deterministic complete-footprint model. It does **not** prove necessity: semantically commuting or idempotent conflicting operations can be safe even when the syntactic footprint rule serializes them.

## Integrity

- formal invocations: **1**;
- reruns / replacements / tuning after freeze: **0 / 0 / 0**;
- independent audit errors: **[]**;
- formal digest: 4391782cbe317d7a8948c92804ff7a112eeba38dfbf9c0b8a4780430f252c229;
- audit digest: c77ce4442fc216e0bd769ce0073ee5833b499c1e8177c5d88a5565acbe04ff56;
- postformal SHA-256 for PLAN/prove/audit exactly matches the corrected preformal remote freeze.

A preformal remote-readback mismatch was detected before any formal invocation and is retained separately in PREFORMAL_READBACK.md; the GitHub bytes were made canonical before the one formal run.

## Interpretation

For the scoped phase model, the scheduler should not ask merely "different surface?" It needs a resource/dependency footprint that covers hidden shared resources such as clipboard, filesystem paths, focus/window-manager state, process environment, backend seat state, or other application-global objects. Missing dependencies invalidate the theorem. Unknown dependencies must fail closed to serialization.

The next empirical discriminator is evidence-only: annotate one retained independent XTerm pair and one retained hidden-shared-file pair with explicit footprints and verify that this contract classifies them correctly without rerunning #1707 or interfering with #1710.

No live-XTerm repair, wall-time speedup, token saving, human-tempo, or runtime-promotion claim follows from this result.
