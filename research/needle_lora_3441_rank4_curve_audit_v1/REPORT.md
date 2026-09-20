# Successor #3865 — independent CPU audit of #3851 curves

Status: construction only; exact predecessor audit not yet invoked.

Construction suite is frozen at 6/6 checks: static contract, case normalization, CPU/offline scope, helper boundaries, and exact hashes for all copied predecessor files. The tests do not invoke the full raw-curve audit.

This additive block performs offline, CPU-only audit of the immutable #3851 raw stdout. It does not train or call CUDA. The #3851 formal invocation is consumed and remains an audit STOP: the frozen runner scored final predictions after its rollback helper reset the live adapter. #3865's single CPU audit also stopped before payload processing because the SHA comparison was case-sensitive; its empty stdout capture and predecessor freeze are preserved under renamed files. This block audits only the 16 retained pre-rollback learning curves and never uses those invalid post-rollback final scores.

The exact input is copied as `predecessor_raw_stdout.txt`; runner, original auditor and its output are retained beside it for provenance. The planned one-shot auditor regenerates inputs/labels from frozen seeds, verifies each row and reported curve, checks exact predecessor/source hashes with case-normalized comparisons, and reports arrival-16 per-arm and paired-seed accuracies. Construction tests must pass and source hashes must be posted to Issue #3875 before running the exact artifact audit once.

Scope: five synthetic seeds and this paired sampling-stream comparison only. No runtime/product or broad generalization claim.
