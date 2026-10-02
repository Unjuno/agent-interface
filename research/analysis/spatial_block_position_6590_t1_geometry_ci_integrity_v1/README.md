# #6590 freeze-integrity CI regression

This additive test package preserves the two published #6590 T1 geometry freeze blobs and their recovery sidecar so Analysis Index CI can validate them from its `research/analysis` sparse checkout. The freeze hashed `.github/workflows/analysis-index.yml`, but the workflow checks out only `research/analysis`; the original geometry tests therefore attempted to read a file absent in CI.

The regression verifies the allocation-02 freeze/sidecar and asserts both frozen workflow hashes, candidate/auditor cardinality, retry count, disposition and raw/audit digests from immutable fixtures. It does not modify or rerun either consumed allocation. It does not establish model efficacy, visual T1, or spatial generalization.

The assertion checks the recorded workflow hash without reading `.github/workflows/analysis-index.yml` from the sparse checkout. This matches the current workflow contract and avoids claiming to recompute that external blob in CI.
