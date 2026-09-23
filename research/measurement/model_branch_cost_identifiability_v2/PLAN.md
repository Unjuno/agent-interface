# MODEL-BRANCH-COST-RETAINED-IDENTIFIABILITY-V2-20260918-001

Parent: #1199. Successor issue: #1462. Base main: `c2826ec7cfb2aceaf55c9ef0e6fe1e9ed301692c`.

## Roadmap
1. Freeze exact retained inputs and source identities.
2. Verify source readback before formal execution.
3. Run two independent deterministic analyzers in a disposable container.
4. Cross-audit retained whole-run and provider-usage facts.
5. Reject corrupted result/source controls.
6. Retain the first formal outcome without retry.
7. Open a PR only if source-integrity and independent audit pass.

## H
The #1199 source-integrity HOLD can be resolved without recovering its lost analyzer sources if the retained immutable ledger is independently re-analyzed. Existing retained grouped/ungrouped MAP01 evidence is expected to be insufficient to identify marginal rich-model semantic-branch authoring cost.

## T
Analyzer A uses explicit grouped×ungrouped Cartesian gates. Analyzer B independently indexes a canonical pre-model fingerprint. Both use the exact copied v1 ledger. Required matchedness gates are exact model-visible image SHA, effect-memory state, action state, primary command shape, input/cached counters and session state; branch count must differ. Retained contingency audit and model-boundary probe documents are copied byte-for-byte and independently checked. No model/provider/GUI/X11/task input. One formal wrapper invocation; reruns/replacements/tuning 0.

## D
PASS `PASS_RETAINED_MODEL_BRANCH_COST_NOT_IDENTIFIABLE_V2_SCOPED` iff source blobs/readback match; both analyzers report 24 rows, 144 pairs, identical admissible set with count 0; every pair fails at least one required gate; whole-run retained metrics and usage-endpoint feasibility agree with copied sources; no causal per-branch estimate is emitted; corruption controls reject all mutations.

PASS_IDENTIFIABLE only if A/B independently agree on the same non-empty fully matched different-branch pair set. HOLD on source/provenance mismatch. FAIL on analyzer disagreement.

## C
Stable ledger bytes do not prove the normalization was semantically complete. Equal visible state/counters would still not prove hidden provider state. Sequential arms are post-treatment-divergent. A future fresh same-model K1/K2 matched allocation is the legitimate cost experiment if retained evidence is non-identifiable.

## U
This experiment tests identifiability only. It must not report a marginal branch cost from unmatched whole-run deltas.
