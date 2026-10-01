# Recovery review: Issue #3778 formal allocation

## Disposition

Preserve the predecessor allocation as `STOP_RESULT_CAPTURE_TRUNCATED`. Do not
interpret this record as a formal PASS or FAIL, and do not rerun the one-shot
allocation. Its distinct compact-evidence successor is #3780, whose scoped
result is recorded under `research/needle_role_graph_3780_compact_v1/` and was
merged by PR #3786. The successor does not change this predecessor's outcome.

## Frozen source identity

- Allocation: `needle-role-graph-3775-v1` (Issue #3778)
- Original branch: `research/needle-role-graph-3775-20260921`
- Original tip reviewed: `e57dcd1151c5983793e0c9a887ed8fb7e7895985`
- Runner SHA-256: `17aec07ff6b0dc0de2bb68eb040843fecf9307b1aca446561f94e522fee12d58`
- Auditor SHA-256: `39c3e65cbc009067b492b5dab43cacb8659ea547023a2e246bc90ffb20058d66`

Both source hashes were recomputed from the original branch blobs during this
review and match the frozen values in the original STOP record and Issue #3778.
No runner, auditor, or formal allocation was executed during recovery.

## Evidence boundary

The original record says the frozen runner was invoked once on host CPU and
exited successfully, but its compressed stdout result was truncated before a
complete raw envelope or result hash could be retained. Consequently there is
no auditable formal metric, transition, snapshot, or independent-audit result
for this allocation. Construction-only screening is not formal evidence.
Docker was unavailable and this was not a container run. The missing output
cannot be reconstructed from the source hashes or the later successor's data.

The original STOP and preregistration remain immutable on the original GitHub
branch history; this file is an additive recovery index, not a replacement or
amendment to those artifacts. See Issue #3778 and PR #3786 for the original
disposition and separate successor scope.
