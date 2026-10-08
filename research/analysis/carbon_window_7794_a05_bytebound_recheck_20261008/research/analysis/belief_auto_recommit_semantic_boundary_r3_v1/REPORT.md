# #1880 Local auto-recommit versus opaque semantic YIELD result

Decision: **PASS_BELIEF_AUTO_RECOMMIT_SEMANTIC_BOUNDARY_SCOPED**

The validation requirement is typed rather than treated as one generic belief-repair operation.

## LOCAL_COMPLETE

The runtime owns the complete deterministic predicate and can evaluate it on current trusted inputs. Across all 16 Boolean predicates over four input fingerprints and every old/current fingerprint pair compatible with an old committed TRUE:

- rows: 128
- candidate/direct mismatch: 0
- safe AUTO_RECOMMIT decisions: 80
- local REJECT decisions: 48

An ALWAYS_YIELD policy would therefore unnecessarily yield on 80 locally decidable TRUE cases.

## OPAQUE_SEMANTIC

The only known semantic fact is an approval receipt for the exact old input fingerprint. For every old fingerprint and every changed current fingerprint, all hidden semantic validators consistent with the old TRUE receipt were considered.

- observable old/current classes: 16
- exact-fingerprint approval reuse classes: 4
- changed-fingerprint classes: 12
- changed classes with both TRUE and FALSE hidden validators possible: 12/12
- candidate changed-fingerprint auto-recommits: 0
- candidate YIELD_FOR_APPROVAL: 12

Thus old approval does not identify the correct answer on a changed semantic-input fingerprint. Local auto-recommit would launder semantic authority.

A coarse projected-value comparator p(x)=x mod2 illustrates why looks-equivalent is insufficient: four changed-fingerprint classes share the same projection, and 16 hidden-validator rows would be unsafely auto-approved by projection reuse.

## Boundary

- LOCAL_COMPLETE + current inputs: local re-evaluation may authorize a fresh commit epoch when TRUE.
- OPAQUE_SEMANTIC + exact unchanged approval fingerprint: a still-valid approval receipt may be reused.
- OPAQUE_SEMANTIC + changed fingerprint: YIELD_FOR_APPROVAL.
- any later successful recommit still receives a fresh non-reused commit identity under #1872.

Source-first canonical readback matched 3/3 before formal. Independent audit reproduced all counters. Formal invocation 1; reruns/replacements/tuning 0.

Scope: finite semantic-identifiability boundary only. No rich-model quality, token, latency, runtime, GUI/task or product claim.
