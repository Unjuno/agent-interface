# Terminal reason fallback candidate

`executor_v6.py` preserves v5 execution and release behavior while snapshotting the current lease interruption once at terminal construction. Only a `needs_decision` terminal with an empty exception reason can inherit `focus_changed` or `surface_changed` from that snapshot. Explicit reasons remain authoritative; absent or other causes do not fabricate a decision reason. Cleanup failure remains failed. Global owner release history is not consulted.

## Evidence

- `results/terminal-reason-01/report.json`: eight synthetic cases cover focus/surface fallback, explicit reason precedence, no cause, expired/cancelled/stop cause exclusion, release failure, and fresh execution with the original deadline in every case. These are exception/reporting tests, not full expiry/cancellation behavior tests.
- `results/bundle-focus-03`: actual private X11/Inkscape, seed 224, same registered nine-step bundle and corrected Control_L admission trigger as cohort 02. Executor v6 is the runtime change. The injector blocks output after physical key-down, transfers focus, verifies physical release before resuming output, then checks the terminal and a fresh observe program.
- Result: needs_decision, completed prefix 3, decision_reason focus_changed, retained per-intent owner cause, no later step or admission, verified physical release. Fresh observation with the same deadline completes without interruption or decision reason. All four resource close calls returned.
- Release-record to terminal interval: 1.471877 ms in this one run. This is runtime bookkeeping, not model feedback latency or a speed improvement claim.
- `results/bundle-focus-audit-02.json`: source and step-file hashes, causal owner record, admission order, same-deadline fresh terminal, and nine exact PNG/AIT frames verified. The separate audit passes.

Original cohort 01 failed to inject the keyboard fault; cohort 02 injected correctly and exposed the missing reason. Both remain unchanged. The new result does not establish rollback, task success, general fault coverage, socket/model delivery, or human-like tempo. No default runtime was promoted.

Next: exercise the reporting candidate through the live transport and a non-Inkscape domain before promotion. Keep task-effect validation separate from program status; improve cross-domain recovery and useful feedback rather than extending the same familiar fixture indefinitely.
