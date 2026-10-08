# Durable A2 for repeated mixed-app guarded recovery

Task: MULTI-APP-GUARDED-RECOVERY-R3-DURABLE-A2-20260918-004, Issue #1798.

One factor only: preserve #1769 scientific common.py byte-identically and replace monolithic formal retention with four immutable per-session batch files. Each completed batch is fsync'd and atomically renamed before the next starts. Aggregate only after BATCH_1..4 exist.

Scientific gates remain #1769: 4 sessions × 3 cycles, refusal zero-task-input48/48, intended active target48/48, exact effect48/48, adjacent replacement12/12, terminal-neutral4/4. Batch failure/timeout stops without rerun and preserves earlier durable batches.

Scope: Linux private-X11 only; no model/provider/network/token/latency/human-tempo/cross-backend claim.
