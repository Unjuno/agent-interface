# Preserved initial audit failure — Issue #5800 T0

The frozen candidate's single raw run is retained as `candidate.raw.json`. The first in-directory independent audit is retained byte-for-byte as `audit.raw.txt` and returned `FAIL_AUDIT` with 511 `mutation_identity` mismatches. The candidate represented injected false dimensions with set bits; the auditor reconstructed false dimensions from unset bits. This is an auditor/candidate encoding disagreement. It is not erased by the corrected auditor output in `audit.corrected.raw.txt`.

The initial audit was not a clean success. The corrected auditor was produced transparently after diagnosing the mismatch and therefore has weaker independence than a separately frozen auditor would have. All claims remain synthetic method-only claims.
