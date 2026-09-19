# Source-first freeze — safety journal post-fsync crash recovery v1

Task `SAFETY-JOURNAL-POSTFSYNC-CRASH-RECOVERY-20260917-001`, Issue #874.
Publication BASE `275480a47f8f06e119b3eb66709b96dbf735bd4b`.

Formal rows before this freeze: **0/10**. Formal invocation budget: 1. Same-ID rerun/replacement budget: 0.

Single factor: writer process fate after exact append+fsync and before ordinary publish. Physical release is not executed in this rung; the input receipt is already verified cleanup evidence and every row records release/task-action retry count zero.

Decision is frozen to the Issue #874 D rule. No threshold exists to tune.
