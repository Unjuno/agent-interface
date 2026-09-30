# Issue #5370 waiter-deadline ordering — audit-v2 result

**Disposition: `PASS_AUDIT_V2_SCOPED`.** The separately frozen raw-only auditor-v2 was invoked exactly once on the exact retained raw and exited 0: seven rows audited, zero errors. Audit-v1's earlier FAIL and all its bytes remain unchanged.

The v2 audit explicitly reconstructs the logical tick consumed by each stale abstention from its `observed_at` field. It combines those ticks with scheduled service events before checking contiguous time. This explains the v1 `schedule_gap_or_duplicate` error for the inherited FIFO row: a stale-abstain decision consumes tick 3 but is intentionally absent from the v1 `schedule` array. The empty completion expectation was also represented with a set rather than a dict. These are audit-v1 contract/implementation defects exposed by comparing against the already frozen raw, not changes to the candidate or expected scientific outcome.

## Reconciled findings

- No inheritance/FIFO: both waiters stale-abstain; holder releases at tick 7; medium service is 5.
- Bounded inheritance/FIFO: H1 finishes at 3 by deadline 5; H2 stale-abstains at tick 3/deadline 3.
- Same inherited trace/EDF: H2 finishes at 3 by deadline 3, then H1 at 4 by deadline 5; no stale abstention.
- Equal-deadline control: FIFO and EDF produce the same H1 then H2 completion at ticks 3 and 4.
- Forged unauthenticated H2 is rejected; effective inherited priority remains 3; H1 completes.
- Each inherited row uses exactly two owner ticks. The primary inherited FIFO/EDF rows reconcile on holder release and medium service.

The seven-row raw, audit-v1 output, and audit-v2 output are included under `source/` and `results/`; raw and v1 are copied byte-identically from the immutable evidence branch. Construction mutation controls passed 8/8 before freeze.

## Limits

This audit checks one deterministic synthetic output against a separately written set of frozen expectations and structural invariants. It does not rerun or independently reproduce the candidate algorithm; does not test a live scheduler, stochastic latency, production fairness/starvation, or task quality; and makes no GPU or container claim. It does not replace the other T5 urgency-claim-binding result in PR #5568.
