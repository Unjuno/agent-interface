# #1816 Exact invalidation semantics for justification graphs

Decision: **PASS_JUSTIFICATION_GRAPH_INVALIDATION_SCOPED**

Formal analytical invocation: **1**. Reruns/replacements/tuning: **0/0/0**.

## Theorem

For an acyclic monotone justification graph where each derived claim owns an OR-of-AND family of declared supports:

- a claim is valid iff at least one justification has all supports valid;
- after retracting root evidence, topological evaluation gives the unique correct derived state;
- iterative invalidation from the previous state converges to the same fixed point;
- claims outside the dependency closure of retracted roots do not change.

This is the minimal truth-maintenance contract needed before selecting a persistent graph implementation.

## Finite confirmation

Frozen family:

- roots: E0,E1,E2;
- claims: C0,C1,C2;
- each candidate justification is one singleton or pair of earlier nodes;
- each claim has one or two distinct candidate justifications;
- family counts: 21 × 55 × 120;
- acyclic structures: **138,600**;
- conditions per structure: 8 source-root valuations × 7 nonempty retractions = 56;
- total source/retraction conditions: **7,761,600**.

Formal result:

- topological vs iterative fixed-point mismatches: **0**;
- unsupported derived-state errors: **0**;
- changes outside declared dependency closure: **0**;
- naive descendant invalidation over-invalidated **3,376,458 derived claim instances**;
- hidden-edge omission false-retain discriminator: **true**;
- independent audit: **PASS**.

The over-invalidation result shows why "retract support -> invalidate every descendant" is not a correct truth-maintenance rule once a claim can have alternative justifications. The correct rule invalidates a claim only when **all** of its declared justifications are broken.

The hidden-edge discriminator shows the opposite failure: if a true support is omitted from the declared graph, a claim may remain apparently justified after its real causal support disappears. Completeness of the declared support relation is therefore an explicit assumption, not a consequence of the fixed-point algorithm.

## Preformal execution record

The first unoptimized local exhaustive implementation exceeded the 45-second disposable-container envelope before producing any result. It consumed no formal allocation and yielded no scientific rows.

The optimized implementation kept the same frozen semantic universe and only cached eight root-state fixed points per structure. Excluded construction over 5,000 structures / 280,000 conditions completed in 0.93s with:

- topo/fixed-point mismatch0;
- unsupported-state errors0;
- nonclosure changes0;
- naive over-invalidation78,918 claim instances;
- hidden-edge discriminator true.

Source was then published, remotely read back, synchronized, and frozen before the one full formal run.

## Formal execution conditions

Container:
- CPython 3.13.5;
- Linux x86_64;
- formal wall time 3.29s;
- audit wall time 5.01s;
- peak RSS approximately 93 MB;
- no GUI/X11/model/provider/network/task input/shared runtime.

Timing is descriptive only; CPU placement and host contention were not controlled.

## Integrity

- exact source frozen before formal;
- PLAN/prove/audit Git blobs unchanged after formal;
- corruption controls pass;
- independent audit all checks true;
- RESULT SHA-256: `dcea4e3bb60a477f4e796a5ace42122b878df2a19f996e864c5937de7d9fc478`;
- AUDIT SHA-256: `4fcaec2963ff8fd677297b90f21b5c7d7824233d83311908d1439c18e5f59a1f`.

Exact outputs are retained as deterministic gzip+base64 with hashes in `EVIDENCE_MANIFEST.json`; `RECONSTRUCT.py` restores them.

## Scope limits

This PASS assumes:
- acyclic support structure;
- positive/monotone support only;
- complete declared supports;
- claim validity = OR of complete AND-justifications.

It does **not** cover cycles, defaults/negation, probabilistic support, priorities, temporal expiry, incomplete declarations, storage design, incremental-update performance, persistence semantics, model quality, GUI behavior or product performance.

The next legitimate successor should test one omitted semantic dimension, not expand this scoped theorem into a general truth-maintenance claim.
