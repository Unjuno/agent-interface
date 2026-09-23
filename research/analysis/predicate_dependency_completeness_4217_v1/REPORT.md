# Predicate dependency completeness gate v1 — Result

Issue #4233. Allocation `predicate-cache-completeness-4233-20260923-01`.

## Overall disposition

**HOLD_AUDIT_CONTROL_HARNESS**.

The scientific formal trace ran exactly once and the frozen raw-only auditor returned the scoped scientific decision `PASS_DEPENDENCY_COMPLETENESS_GATE_SCOPED` with 767 checks and `errors=[]`. However, the frozen copied-evidence controls wrapper crashed on its first `missing_row` mutation because the auditor indexed directed rows after already detecting the shortened denominator. The preregistered >=10 corruption-control gate was therefore not completed by the frozen first audit tooling, so the overall PASS is not awarded.

A separately labelled postformal read-only `audit_v2.py` changes only malformed-evidence bounds handling. It reproduces the same mechanism metrics and raw SHA and rejects 12/12 copied-evidence mutations. It does not rerun, replace, extend or relabel the formal scientific allocation and does not erase the first-outcome HOLD.

## Formal mechanism observations

- states: 12/12
- policies: DECLARED_ONLY / COMPLETE_DECLARATION / COMPLETENESS_GATED
- predicates: READY_TO_SUBMIT / TARGET_MATCH
- policy-predicate observations: 72
- formal invocations/reruns/replacements/tuning: 1/0/0/0
- authority grants: 0
- formal raw SHA-256: `cb315973274975c7324bece5664189218af983f5d978ab17df3b905cff99b966`

Frozen auditor-derived metrics:

| policy | evaluator calls | cache hits | predicate mismatches | graph mismatches | hidden false reuse |
|---|---:|---:|---:|---:|---:|
| DECLARED_ONLY | 11 | 13 | 2 | 2 | 4 |
| COMPLETE_DECLARATION | 14 | 10 | 0 | 0 | 0 |
| COMPLETENESS_GATED | 17 | 7 | 0 | 0 | 0 |

The deliberately incomplete READY_TO_SUBMIT declaration omits `risk`; it therefore false-reuses across hidden risk changes. The complete declaration binds the hidden dependency generation and does not false-reuse. The completeness-gated policy never reuses the incomplete READY_TO_SUBMIT predicate but still reuses the independently complete TARGET_MATCH predicate. Hidden-risk ABA restoration under a new generation is not credited as a safe hit by either safe policy. Source-generation, intent-version and producer-version changes invalidate as frozen.

## H/T/D/C/U

- **H:** dependency-scoped semantic reuse is safe only under a complete applicability declaration; unknown completeness should fail closed to recomputation for that predicate.
- **T:** deterministic CPython 3.13.5 standard-library replay in the provided Linux x86_64 execution container; 12 authored states, 3 policies, 2 predicates; no GUI/model/provider/network/task input.
- **D:** mechanism observations satisfy the scientific semantic gates, but the frozen corruption-control harness did not complete, so overall disposition is HOLD rather than PASS. Postformal v2 rejects 12/12 mutations on the unchanged raw.
- **C:** true dependencies are authored by the fixture. The study tests consequences of incomplete declarations, not automatic dependency discovery. DECLARED_ONLY is a negative control, not a production allegation.
- **U:** dynamic/learned hidden dependencies, real GUI coupling, natural invalidation rates, cross-session reuse, token/model savings, live authority, task benefit and production integration remain unknown.

## Integrity and incidents

Construction passed 7/7 and py_compile before formal. Exact preformal source/environment/trace/auditor bytes were published and all 10 Git blob IDs matched local objects before the formal invocation.

The formal runner exited 0 and produced all 72 observations. The frozen auditor exited 0. The frozen controls wrapper exited 1 on `missing_row` with `IndexError`; the generated mutation and traceback are retained. Formal execution was not repeated. Postformal v2 uses the same raw bytes, exits 0, and rejects all 12 copied-evidence mutations.

The lossless formal-evidence capsule contains the formal raw, first audit, first controls crash evidence, postformal v2 audit/controls, copied mutation files, command streams and execution receipts. `unpack_evidence.py` verifies capsule and member hashes before extraction to a new directory.

## Integration meaning

Do not promote #4217-style dependency-scoped caching merely because declared keys are stable. A cache needs either evidence that the declaration is complete, or a conservative path that recomputes predicates whose completeness is unknown. This HOLD is not a runtime promotion and not a model/task performance claim.
