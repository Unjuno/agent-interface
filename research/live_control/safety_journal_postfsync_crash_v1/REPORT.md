# Post-fsync safety receipt crash recovery v1

Task `SAFETY-JOURNAL-POSTFSYNC-CRASH-RECOVERY-20260917-001`, Issue #874.

Decision: **`PASS_POSTFSYNC_SAFETY_RECEIPT_CRASH_RECOVERY_SCOPED`**.

## First formal outcome

One formal invocation, 10 first rows, formal reruns 0.

- `no_crash`: 5/5 writer journals+fsyncs and publishes exactly once before exit; both later recovery processes return `ALREADY_PUBLISHED`; final durable publication count 1.
- `post_fsync_sigkill`: 5/5 writer appends+fsyncs, emits the frozen `FSYNC_DONE` barrier, is SIGKILLed (`rc=-9`) before publication, and durable publication count remains 0 before recovery. Fresh recovery1 returns `PUBLISHED`; fresh recovery2 returns `ALREADY_PUBLISHED`; final count 1.
- Same receipt ID with altered content returns `RECEIPT_IDENTITY_CONFLICT` in all 10 rows.
- Every retained receipt remains `authority=none`, `task_input_granted=false`, `action_admission_eligible=false`; release/task-action retry counts are 0.

Frozen independent audit errors: `[]`. Postformal source rehash 9/9 exact; copied-evidence corruptions rejected 4/4.

Formal aggregate SHA-256 `49aa00d6da854c856106a353a716db12ed2debd7684d36002f9977574f673bc7"; audit SHA-256 `07903d3540b8d0b25dfeb9f3e6bf9d20bee0b6ff25e33449d7cd3b80fd8db514`.

## Interpretation

A compact safety receipt that was already produced after verified cleanup and durably journalled with fsync can survive the journal-writer process dying before ordinary publication. A fresh local recovery process can publish it exactly once using content-bound receipt identity; a second fresh recovery does not duplicate it.

This is post-release evidence durability only. It does not retry or prove physical release, and it does not establish host-power-loss, storage-controller, distributed, cross-platform or hostile-writer guarantees.
