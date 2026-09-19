# Plan v2 — batched native X11 sub-ms robustness

V1's scientific schedule was not completed because one 20-session wrapper exceeded the container 180 s execution limit. V1 is retained as `INCOMPLETE_OUTER_TIMEOUT` and is never resumed or pooled.

V2 keeps all scientific conditions unchanged: requested post-character delays 0.8, 0.9, 1.0, 1.1 ms; same 16-string corpus; same precise busy-wait builder; same PR #145 runner/scorer; stale zero-input and terminal-release gates; five fresh sessions per condition.

Only orchestration changes. The original counterbalanced rounds become five independently invoked/checkpointed four-session batches:
- batch 1: 0.8, 0.9, 1.0, 1.1
- batch 2: 1.1, 1.0, 0.9, 0.8
- batch 3: 0.9, 1.1, 0.8, 1.0
- batch 4: 1.0, 0.8, 1.1, 0.9
- batch 5: 1.1, 0.9, 1.0, 0.8

Every V2 session is new and executes once. A batch is complete when all four report receipts exist, regardless of semantic pass/fail. The final aggregate runs only after all five batches complete.

`ROBUST_CANDIDATE` remains the lowest requested delay with 5/5 eligible exact sessions and all control gates. This is a conservative engineering gate, not a statistical reliability guarantee. V1 completed sessions are excluded from all V2 counts.
