# #1258 first outcome — stopped by outer execution ceiling

Task `TEMPORAL-BUFFER-X11-PROCESS-TREE-CPU-20260918-001`.

The source-first formal supervisor was invoked exactly once. The container tool execution ceiling interrupted the outer process before the preregistered 8 matched pairs completed. No same-allocation rerun/replacement was performed.

Recoverable partial evidence contains 5 complete matched pairs / 10 complete private-X11 sessions. These rows are descriptive only and are not pooled into a PASS/HOLD decision. Candidate total process-tree CPU fraction in the completed rows ranged 0.0558253..0.0629766; descriptive paired median candidate-minus-baseline fraction 0.0368566; no capture/liveness mechanics errors in those recovered pairs. This does not satisfy the frozen 8-pair gate.

Disposition: **STOPPED_OUTER_EXECUTION_TIMEOUT**. Scientific decision eligible: false.

Formal invocation marker SHA-256 `2efff977057b900ec8ec9c2dc3624551befa748328821725738ddfd3913b13e0`.
Raw PARTIAL SHA-256 `76989c49080215d9b7d032c97c325a05e1912ae03466ea7e8d1d99558ac645fc`.

No owned Xvfb/Tk/runner process or private X11 socket remained after timeout. A fresh successor may change orchestration containment only (e.g. bounded case batches) while keeping scientific sources/gates fixed.
