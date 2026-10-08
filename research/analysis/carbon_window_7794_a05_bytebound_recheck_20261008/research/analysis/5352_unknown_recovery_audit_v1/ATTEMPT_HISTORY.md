# Attempt history — Issue #5352 audit path

This file preserves the sequence without relabeling outcomes:

1. **Construction-01:** stopped at prefix 57 after detecting `(STALE, 0.64) -> [UNKNOWN, UNKNOWN]`. No formal-count claim.
2. **Docker launch-01:** `docker run ... python /work/enumerate.py` stopped before Python because this image had no `/work` source.
3. **Docker bind-01:** stopped before container execution because Docker Desktop rejected the supplied Windows bind-mount path.
4. **Construction-02:** candidate completed all 299,592 traces. Its first summary counted 101,952 stale-followed-by-valid-and-still-UNKNOWN cases. The first auditor summary counted 169,434 stale-to-valid pairs; definitions were not aligned, so no comparison was valid.
5. **Formal-03:** frozen candidate and an independent auditor each enumerated all 299,592 traces in separate isolated Docker invocations. Candidate/auditor disagree on post-UNKNOWN threshold priority and corresponding counters. Terminal disposition: `STOP_AUDIT_SEMANTIC_MISMATCH`.

No retry of formal-03, source edit after freeze, or substitution of its outcome occurred. Later work, if any, needs a new allocation ID and an explicit UNKNOWN recovery contract.
