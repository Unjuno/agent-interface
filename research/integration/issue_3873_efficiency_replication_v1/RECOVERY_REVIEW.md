# Recovery review: Issue #3898 consumed replication STOP

This package is the exact 98-file, 192,933-byte owned subtree from remote
branch `research/issue-3873-efficiency-replication-20260921` at commit
`ac63590d81372419a99a19003b6da91ebaa691a`. The directory is added to main
without edits to its frozen source or captured outputs.

## First outcome and scope

Issue [#3898](https://github.com/Unjuno/agent-interface/issues/3898) records
one consumed seed-284937 OrbStack allocation. It stopped as
`STOP_INFRA_BROKER_ZERO_EXIT_MISREPORTED` after the first schema-only host
model call: one response and broker receipt, zero task calls, zero retries.
A second schema-only request was staged but has no response or receipt. The
STOP and partial raw audit are retained as-is. This is not a task failure,
replication result, or evidence for/against the efficiency hypothesis.

The issue records that correcting broker exit propagation and any later
fresh-seed replication require a distinct successor allocation. No model,
broker, task, or audit process was rerun for this recovery. The live #4520
broker fix is not modified by this evidence-only change.

## Validation boundary

All copied files are checked byte-for-byte against the old branch before
publication. The bundle's own frozen manifests and first-outcome records are
preserved; this note does not upgrade the allocation's scoped STOP or make
broader task/product claims.
