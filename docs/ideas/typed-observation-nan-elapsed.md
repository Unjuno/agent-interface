# NaN elapsed metadata at the typed-observation boundary

- **Status:** A focused negative test exposed the bug; proposed fix remains unmerged.
- **Source:** Issue [#8249](https://github.com/Unjuno/agent-interface/issues/8249), related to #59.
- **Idea:** Reject nonfinite redundant elapsed metadata instead of relying on a negative tolerance comparison that evaluates false for NaN.
- **Outcome:** The complete current-module RED test showed that `abs(elapsed_ms - derived_ms) > 1e-9` admits JSON `NaN`. An exact one-line candidate patch and regression test are in open Draft [PR #8268](https://github.com/Unjuno/agent-interface/pull/8268); the current main blob still contains the vulnerable predicate. The focused tests used no-op PIL import stubs for admission-only suites, so they do not verify image handling. No game or GUI run occurred.
