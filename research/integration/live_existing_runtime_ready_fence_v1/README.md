# live_existing_runtime_ready_fence_v1

Issue #818 retained the existing-runtime readiness experiment.

- A1: `STOPPED_OUTER_ORCHESTRATION_TIMEOUT`, unpooled.
- A2: `FAIL_EXISTING_READY_LIVENESS`.
- Exact v11 baseline clock timeout: 3/3.
- Existing `interactive_v27` ready-gated candidate: boundary 1/3, timeout 2/3 at unchanged 300 ms.
- Failure mechanism: the existing `ready` event precedes the initial snapshot and stdin command loop; post-ready initial-snapshot work ranged 263.676–343.077 ms.
- Safety/integrity: no task program input, 6/6 exit0, 6/6 verified-neutral final owner release, exact pinned runtime blobs.

Do not promote the current `ready` event as a bounded command-ready socket fence. If integration still needs a bounded command-ready milestone, test an already-existing post-initial-observation boundary rather than adding a new synthetic readiness vocabulary.
