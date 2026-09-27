# GTK formal receipt integrity successor (#2753)

This is a preregistration and implementation boundary, not an execution result.

## Scope

This successor repairs the evidence defects identified in merged preflight PRs #2690 and #2709:

- dispositions must be derived from observed receipts, not preregistered tuples;
- stale repair must record the original stale revision and a real bounded reacquisition before any second dispatch;
- cleanup is safe only when every release is verified and `keys_down`/`buttons_down` are empty;
- the input ledger must include backend dispatch and terminal release evidence, not only fixture callbacks;
- an independent scorer must consume retained receipts without importing the adapter.

## Fixed order

`useful, unavailable, guarded, no_effect, partial, stale_repair, ambiguous, cleanup_failure`

Replay is disabled for all cases. Model/provider/network calls are disabled.

## Required frozen inputs

Before any GUI input, record:

- immutable container image ID/digest;
- Python, GTK, and Xvfb versions;
- build/dependency manifest hash;
- SHA-256 for runner, fixture, case manifest, scorer, and auditor.

## Decision

- `PASS_FORMAL_RECEIPT_INTEGRITY_SCOPED`: all eight rows have immutable provenance, observed input/effect/cleanup receipts, genuine stale-repair lineage, and independent scorer agreement.
- `STOP_RECEIPT_INTEGRITY`: missing or mutable provenance, hard-coded outcome evidence, absent repair, incomplete input ledger, ambiguous release, or hash drift.

This path does not by itself claim provider/model utility, general application coverage, or full #2606 acceptance.
