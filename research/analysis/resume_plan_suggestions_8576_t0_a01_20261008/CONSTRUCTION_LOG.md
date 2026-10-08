# Construction log — Issue #8576 T0 A01

- Tests were written before implementation; initial WSLc run failed on the explicit missing-candidate assertion (2 expected RED failures).
- Implemented candidate's public evidence gates and a separate auditor that enumerates topological orders rather than importing/reusing candidate logic.
- Added a malformed-graph behavior test. Its first RED run found duplicate checkpoint IDs were reported as generic ambiguity instead of invalid-plan abstention. Candidate validation was corrected; the focused test and whole package suite then passed.
- WSLc normal construction suite: 3 tests passed.
- WSLc optimized (`python -O`) construction suite: 3 tests passed.
- Both construction runs used a read-only bind and `--network none`; formal outputs were not created during construction.
- Baseline repository analysis-index tests: 22 passed.
- Baseline `research/check_workspace_index.py` reports the pre-existing root `outputs/` namespace missing from `research/README.md` / `research/ROOT_NAMESPACE_MAP.md` on current main `28b6f0fc0dd3cf6d798d97ee608a409ce773e409`; this is unrelated to the experiment and will be reconciled with the in-flight index repair before delivery.
