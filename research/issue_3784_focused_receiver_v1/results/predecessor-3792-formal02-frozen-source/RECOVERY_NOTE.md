# Recovered frozen source — Issue #3792 formal-02

This directory preserves the exact preregistration/source bundle from branch
`research/issue-3792-german-xkb-formal02-20260921`, tip
`12c1730aa87ae7fda962ae58f0184d586ca88dc3`. The later main version of
`issue_3784_explicit_x11_receiver_v2/` belongs to a different subsequent
allocation and must not replace or be confused with this frozen source.

The original one-shot run stopped at `receiver_focused` because the runner's
XLookupString helper raised `KeyError: 'DISPLAY'`; the host wrapper then raised
`AttributeError` before writing the result envelope. No German map change,
preflight, or candidate formula test occurred. The available partial row and
host logs, with their hashes and disposition, are retained separately at
[`../predecessor-3792-formal02-runner-stop/STOP.md`](../predecessor-3792-formal02-runner-stop/STOP.md).
This source recovery does not recreate missing formal output or alter that
STOP. The later #3794 result was a distinct allocation.

Frozen runner SHA-256:
`40ce0dca6bb04ab54305bbe9001c52b34600a5479dc50b8acde871009fa0751f`.
Frozen source-manifest SHA-256:
`b5aafca39bd927098c7074f8dbdd12e46b34c3b6f908505cbdbef54f0ebbf7e5`.
Both were recomputed after copying and match the values in the original
preregistration. No runner, construction test, or formal experiment was run
during recovery.
