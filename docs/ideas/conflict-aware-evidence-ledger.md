# Conflict-aware evidence ledger

- **Status:** inconclusive; transfer refinements unverified
- **Source:** [#5305](https://github.com/Unjuno/agent-interface/issues/5305), adjacent #5314 and #5339; implementation/evidence PR [#5321](https://github.com/Unjuno/agent-interface/pull/5321) is merged.
- **Idea:** Preserve conflict separately from ignorance and stale evidence, while preventing duplicate or correlated receipts from being counted as independent support. This is a conservative evidence-routing proposal; it grants no action authority.

## Evidence and limits

- **T0 (`PASS_T0_FINITE_MODEL`):** Main retains the frozen five-atom / 31-subset report at [`research/analysis/conflict_aware_evidence_ledger_5305_t0/REPORT.md`](../../research/analysis/conflict_aware_evidence_ledger_5305_t0/REPORT.md). A corrected independent raw-only audit matched 31/31 rows and rejected 4/4 corruption controls. The first audit `STOP_AUDIT_EXPECTATION_MISMATCH` remains preserved. Candidate counts were 14 `CONFLICT`, 14 `PASS`, 2 `FAIL`, and 1 `UNCERTAIN`; the lossy ternary projection collapsed all 14 conflict cases into `UNCERTAIN`. The fixed fixture trusts its freshness and independence metadata; this is not calibrated risk, verifier quality, action safety, or runtime benefit.
- **Held-out T1 (`STOP / incomplete evidence`):** [Issue comment 5907937584](https://github.com/Unjuno/agent-interface/issues/5305#issuecomment-5907937584) reports 8 synthetic cases with semantic labels matching 4/8. False independence and missing provenance conservatively abstained, but the policy also rejected single-group positives/negatives and mixed stale/current support. Its raw SHA-256 is `e7ca2b633cfc48cd521678027b6fb7d6696226c7483f840131f91abf08384e5c`; the issue thread records the local raw path, but this file is not part of the main-tree T0 package, so canonical raw custody for this later run remains unverified.
- **Separate fusion-policy check:** [Issue comment 5913504474](https://github.com/Unjuno/agent-interface/issues/5305#issuecomment-5913504474) reports 4/4 assertions for a finite threshold example: normalization returned `PASS` on weak conflict while a conflict-preserving policy returned `CONFLICT_REVIEW`. The threshold and mass assignment remain policy choices; this does not repair T1's coverage limitation or validate an operational route.
- **Unverified refinements:** [Derived-evidence feedback](https://github.com/Unjuno/agent-interface/issues/5305#issuecomment-5923478347) and [provenance-expression audit](https://github.com/Unjuno/agent-interface/issues/5305#issuecomment-5923842471) propose tracing shared raw roots through derived receipts. Neither has an executed result. Do not create a duplicate Issue or count these proposals as evidence.

No result establishes live GUI behavior, calibrated belief masses, real verifier reliability, correct action admission, reduced retries, latency benefit, or task success. The research Issue remains open because the held-out and routing question is unresolved.

## Next discriminating work

Do not rerun the consumed five-atom T0. First verify custody of any claimed held-out raw; if it cannot be read back, preserve the STOP and construct a new, explicitly distinct fixture only under a valid allocation. Compare ternary and conflict-preserving decisions on held-out traces that include a single trusted group, mixed stale/current evidence, duplicate roots through a derivation diamond, genuinely independent roots, false/missing lineage, and a decision-level routing consequence. Freeze thresholds and expected outcomes before execution. Keep `UNKNOWN`/abstention on uncertain lineage and measure whether conflict changes routing without increasing unsafe admissions.

The source Issue and its comments remain authoritative; this summary is an index entry, not a replacement for raw or a closure rationale.
