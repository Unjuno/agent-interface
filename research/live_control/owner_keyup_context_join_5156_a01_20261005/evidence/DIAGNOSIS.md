# A01 frozen run outcome

Candidate ran once and exited 0 with the reverse-order two-key and same-key repeated-cycle cases. The raw-only auditor ran once and exited 1 with `FAIL`; preserve that decision. All six mutations were rejected.

Saved raw operations show the reverse-order case as down A, down B, up B, up A. The cycles case is interleaved as down C, up C, down C, up C. The frozen auditor constructed both expected streams by grouping all admissions before all releases, so only the cycles case produced a false order mismatch. Its raw records show the expected admission positions and nested owner receipts, and both cases ended neutral. This is a post-run explanation, not a reclassification or rerun of A01.

A02 is a separately frozen successor with per-case explicit operation sequences and an added single-key integration case.
