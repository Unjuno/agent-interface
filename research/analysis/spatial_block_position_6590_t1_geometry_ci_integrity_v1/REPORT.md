# #6590 sparse-checkout freeze-integrity CI regression

## Finding

The #6590 T1 geometry freezes include `.github/workflows/analysis-index.yml` in their `source_sha256` inventory. Analysis Index Actions checks out only `research/analysis`, so the workflow file is absent from that job. The original geometry suite consequently failed in CI when it attempted to read the workflow path. Local execution did not reveal this because the full checkout includes `.github/`.

## Regression coverage

The additive test package runs entirely inside the existing sparse checkout. It validates the allocation-02 FREEZE sidecar, checks that both freeze fixtures carry the expected recorded workflow blob SHA-256, and checks the preserved run record's disposition, invocation cardinality, retries and candidate/audit digests. The fixtures were copied byte-for-byte from PR #6623 head `8ff174bd4ccfff580c9bc45aaef5a2ce3018aa2a`; no allocation was rerun or modified.

This test does **not** re-hash the actual `.github/workflows/analysis-index.yml` blob in Actions; that file is absent by design in the sparse checkout. It verifies recorded freeze values against a literal expected digest and immutable freeze fixtures. Full source-to-workflow-hash verification remains available in a non-sparse checkout and should not be claimed from this CI test alone.

## Scope

This is CI compatibility/integrity regression coverage only. It does not change either scientific allocation, the geometry HOLD, or any #4752/#4814/T0 result. It is not evidence for model efficacy, spatial dependence, GUI behavior or issue-level T1.
