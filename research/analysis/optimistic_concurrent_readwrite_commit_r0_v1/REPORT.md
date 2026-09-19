# Optimistic concurrent read/write commit R0 — result

Decision: **PASS_OPTIMISTIC_READWRITE_COMMIT_CRITERION_SCOPED**

Parents: #1713 automatic read-set reconstruction and #23 dependency-aware parallel execution. Retained foundations include #501/#508 mediated-read completeness, #1675 exact dependency-version reuse, #1678 layered lifetime admission and #1688 hidden-global conflict evidence.

## Analytical criterion

Assume complete read/write sets, non-reused semantic version identities, individually linearized final validation+effect, and no separate commutativity certificate. Two prepared intents A and B are generically safe for parallel admission exactly when:

1. every resource in `R_A ∪ R_B` still has its prepared version;
2. `W_A ∩ W_B = ∅`;
3. `W_A ∩ R_B = ∅`;
4. `W_B ∩ R_A = ∅`.

Read/read overlap is harmless. Same-surface operations may therefore parallelize when their actual dependency/resource sets are disjoint. Different-surface operations must still serialize when a shared/global dependency appears in either set.

Necessity is universal under the stated model: stale reads, A-write/B-read, B-write/A-read and W/W overlap each have explicit deterministic counterexample witnesses. A future independently proven commutativity certificate may relax W/W exclusion; this result does not.

## Formal result

Complete finite enumeration over four resources:

- `R_A,W_A,R_B,W_B`: every one of 16 subsets each;
- external changed-resource mask: all 16 subsets;
- total rows: **1,048,576**;
- formal invocations: **1**;
- reruns/replacements/tuning: **0**.

Results:

- candidate/oracle mismatch: **0**;
- candidate stale-read parallel admissions: **0**;
- candidate cross read/write parallel admissions: **0**;
- candidate write/write parallel admissions: **0**;
- oracle-safe PARALLEL rows: **14,641**;
- oracle SERIALIZE rows: **145,359**;
- oracle REVALIDATE rows: **888,576**;
- GLOBAL_SERIAL false serializations: **14,641**;
- WRITE_ONLY unsafe parallel admissions: **35,984**;
- same-surface/disjoint positive control: PASS;
- different-surface/shared-global negative control: PASS;
- read/read-overlap positive control: PASS;
- stale-read revalidation control: PASS.

Hazard coverage (not mutually exclusive): stale-read **888,576**, A-write/B-read **716,800**, B-write/A-read **716,800**, W/W **716,800** rows.

Independent auditor re-enumerated the set algebra without importing candidate functions and returned PASS/errors[]. Six copied-result corruption controls were rejected 6/6. Postformal source identity matches the source freeze 8/8 after normalizing whitespace in the hash manifest; no science/source byte changed after formal.

Hashes:

- RESULT.json `8850e74ede3c74d770353f1aa832373dfa13c48b0fa6e7b2f0f822549a1bd930`
- AUDIT.json `fad852794a6cda0adad7031de8dd14f9d2c7e9c87c5bdc8d5556b6b6f688dcb7`
- CORRUPTION.json `818de28a778eecc2c6bcd4d40ed8ded60fc3fb29256aa1eb995380cfbffa35df`

## Interpretation

The new part of #1713 is not “record read receipts” by itself; older #501/#508/#523 lineage already establishes that mediated read receipts can be precise and that bypasses break soundness. The new concurrency contract is:

> reconstruct complete dependencies, validate their versions, and admit parallel commit only when the pair has no cross read/write or write/write hazard.

This also sharpens #1717: a `SURFACE_ISOLATED` consistency mode is not safe merely because surface IDs differ; hidden/global resources must appear in the dependency sets. Conversely, a `SAFE_SERIAL` mode is correct but provably over-conservative on every one of the 14,641 oracle-safe finite cases.

## Scope limits

Completeness is assumed. A task-relevant unmediated read violates the premise exactly as #508 demonstrated. Individual check+effect linearization is assumed. Natural conflict rates, scheduler overhead, actual wall-time gains, GUI task correctness, model/token effects, multi-process crashes and production ABI are unmeasured.

The next empirical rung should bind the criterion to one real two-surface pair with complete typed receipts and one shared-global negative control. It should not promote unrestricted `FULL_CONCURRENT` execution.
