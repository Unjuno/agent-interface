# #1764 A3 temporal-contract monitor compilation

Direct predecessor #1743 is immutable and consumed. A3 changes only the prefix accounting gate.

Canonical constants:
- generated traces: 1,062,624
- complete prefix checks: 5,144,980

The complete prefix count is derived from the frozen generator rather than inherited from #1719's failure-truncated runtime counter.

Candidate monitor is byte-identical to A2 and #1719. Primary and independent reference semantics, event generators, malformed controls, outcome gates and corruption controls are A2-identical except task/decision labels and the accounting constant/gate.

D: PASS_TEMPORAL_CONTRACT_MONITOR_COMPILATION_A3_SCOPED only with full counts exact, mismatch0 in both analyzers, retained counterexample PENDING, corruption6/6, malformed UNKNOWN, fixed state shape, formal1/reruns0/replacements0/tuning0.
