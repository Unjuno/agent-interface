# Semantic predicate fabric v1 — Result

Issue #4215. Allocation `semantic-predicate-fabric-4215-20260923-01`.

## Result

**PASS_SEMANTIC_PREDICATE_FABRIC_SCOPED**.

One prospectively frozen formal invocation over 20 authored cases and six typed predicates (120 predicate labels). Formal reruns/replacements/exclusions/tuning: 0/0/0/0.

- predicate accuracy: **120/120 = 1.0**
- UNKNOWN precision / recall: **1.0 / 1.0**
- joint all-six-predicates correct: **20/20**
- deterministic graph disposition correct: **20/20**
- direct-disposition interface correct: **20/20**
- graph semantic errors masked/amplified: **0**
- backend calls: direct **20**, batched-predicate **20** (one per case per arm)
- reused graph predicate reads without another backend call: **4**
- authority grants: **0**
- independent raw-only audit: **223 checks, errors=[]**
- copied-evidence corruption controls: **12/12 rejected**

Seven cases contained at least one UNKNOWN and all seven ended `YIELD_UNKNOWN`; no missing/conflicting evidence was coerced into executable TRUE/FALSE. Frozen final dispositions: 3 SUBMIT_READY, 2 CONTINUE_FILL, 1 RECOVER, 2 YIELD_TARGET, 2 YIELD_MODAL, 2 YIELD_OUT_OF_ENVELOPE, 1 YIELD_INTENT, 7 YIELD_UNKNOWN.

The graph explicitly consumes the already-returned `TARGET_CORRECT` fact at more than one graph node in cases that reach the submit path. This is structural reuse of one semantic fact within a local program, not a measured task/model-speed benefit.

## H / T / D / C / U

- **H:** a bounded batch of TRUE/FALSE/UNKNOWN semantic predicates can drive a deterministic graph with final semantic correctness no worse than a direct disposition interface, while exposing facts for graph reuse.
- **T:** authority-neutral deterministic standard-library fixture in the provided Linux execution container / CPython 3.13.5. One fixed state encoding, six fixed linear predicate heads, one direct-disposition interface over the same frozen semantic family, one guarded graph, 20 cases including same state/different intent, branch flips, irrelevant input, missing/conflicting evidence and out-of-envelope controls. No GUI/task input or external model/provider.
- **D:** every frozen fidelity/UNKNOWN/disposition/reuse/authority/integrity gate passes; independent audit and all 12 evidence mutations pass.
- **C:** the “backend” is an authored deterministic linear candidate, not Laya/Kev and not a learned-model quality test. The direct arm and predicate arm share the same semantic family by design; this isolates the model-output/graph-input representation boundary rather than backend superiority.
- **U:** real local-model fidelity, cross-question interference, tokenization/model cost, natural semantic error rates, live graph benefit, planner round trips, latency savings and production authority remain unknown.

## Timing (descriptive only)

Nanosecond microtimings on the provided container are not a promotion gate: direct p50/p95/p99 = 1848 / 4223.35 / 7527.07 ns; predicate batch = 956.5 / 3424.35 / 27156.87 ns; serialization = 4562 / 11936.5 / 22416.9 ns. These are Python fixture timings, not model inference measurements.

## Integrity / chronology

Construction used the exact frozen scientific source and passed 7/7 tests before formal. GitHub preformal freeze commit `164dfcfff7a880fd541b60f818a3681f74de6d51` was read back as 13/13 matching Git blobs before formal authorization. No construction or publication STOP occurred after ownership.

Formal raw SHA-256: `094a7c0b3a53b8243ebe077de9e8d0294e66f4fa584875a5366d641661f29ff5`. Raw bytes are retained losslessly as zlib/Base64 with `unpack_formal.py`; the first audit/controls/execution receipts are retained directly.

## Integration meaning

This result supports only the interface contract that a local semantic backend may return a typed predicate batch and leave deterministic action selection to a guarded graph. Predicate confidence/output is not authority. A live or learned-model successor must keep UNKNOWN fail-closed and measure actual model cost, fidelity and task value before promotion.
