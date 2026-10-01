# Issue #5494 AoI retention successor

This is a deterministic synthetic queue comparison only.

Frozen base: main `f09a0bd0a5a8d683a950df1b360670aaa1f194ca`.
H/T/D/C/U and the outcome gate: Issue #5494.
The source freeze and exact SHA-256 digests are in `FREEZE.json`.

Run:
- `python study.py EXPECTED_STUDY_SHA256` emits the canonical result JSON.
- Pipe that JSON into `python audit.py EXPECTED_STUDY_SHA256 EXPECTED_AUDIT_SHA256`.

The study checks two direct queue-edge controls before executing the paired synthetic stream. The independent auditor reconstructs the offered stream and both policies using separate code, verifies every aggregate and digest, and rejects four deliberate output mutations.

The fixed workload uses one session, a 4-event queue, 200 ticks, one service slot per tick, 1,000 paired trials, seed 43001, 8% critical event probability, and a burst rule frozen in the source. Both arms receive the identical offered event stream. The candidate coalesces queued state for the same session and may evict the oldest queued state to admit an incoming critical event; if a full queue contains only critical events, it rejects and counts that new critical event as dropped.

`policy_operation_count` counts the frozen discrete comparisons and queue operations. It is not CPU time or a runtime-cost estimate. Age of Information is sampled once after service at each tick, using the most recently delivered state event; critical event loss is counted from event identity, with all offered critical events as the shared denominator.

No external runtime, model, GUI, task effect, GPU, or container is involved. No result promotes system safety or user-task benefit.
