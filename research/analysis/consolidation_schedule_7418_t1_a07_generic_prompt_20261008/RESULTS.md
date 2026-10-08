# T1 A07 result — output schema STOP

The candidate was stopped after 48 calls when the prefix-2 consolidation emitted a claim kind `common_success`, outside the frozen output schema. The generic prompt had not stated the mapping from episode kinds to memory claim kinds. No auditor or schedule analysis was run. This is a prompt-contract failure, not evidence about cadence. The 48 raw rows are retained with SHA-256 `83aa2bdcc9e815993b7f5296e6cd795f32392532069c3c92b32d618fa7ef77ea`. See `STOP.md` and `RUN_RECORD.json`.
