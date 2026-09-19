# Serialized journal stalls and actual assistant integration

`probe_journal_stall_v3.py` serializes event and receipt emission with one lock.
Cancellation runs on an independent caller thread: executor_v3 sets the authority
cancel flag before its notification blocks on that lock. The test observes physical
and owned button release before resuming journal I/O, while cancel() itself has not
returned, and before original lease expiry in cancellation cases.

All four `journal-stall-03` cases pass: write/flush stalls under expiry yield expired;
write/flush stalls under explicit cancel yield cancelled. Receipt order is preserved,
release is verified and no late continuation occurs. Eight exact frames and all
source hashes pass audit. Earlier setup failure and concurrent receipt-order failure
remain unchanged. Cancellation effect, notification delivery and caller return are
distinct endpoints; this result does not make cancel() nonblocking.

`interactive_v17.py` now uses the persistent receipt file within an outer file
context, retaining emitter serialization, per-record flush, session_v16 and
delivery_ledger_v2. The ready response advertises the required decision_evidence
fields. Bounded ledger v3 is not silently included. File context closure also runs
when inner teardown raises; disk errors still propagate and are not rollback.

Actual assistant cohort `journal-self-use-01` viewed PNG 001, referenced delivery:2
and observation 1, typed t991021 plus Return/settle, viewed PNG 003, and requested
independent evaluation. Saved content matches. Seven reconstructed frames, fifteen
output/flush pairs, source manifests, source ID preservation and release pass audit.
Local accepted program took 460.769 ms. This is one familiar-task run, not a causal
comparison with previous timing; stdout flush timing excludes journal append time.

Stall tests use session_v17 and probe receipts; the interactive typing test uses
session_v16 and actual output receipts. Neither establishes every interactive fault
path. Permanent disk-error recovery, public concurrency, bounded retention and
cross-domain task qualification remain open. Next prioritize a matched actual-task
comparison or another domain using this experimental entrypoint; keep implementation
overhead distinct from the much larger external planner gaps.
