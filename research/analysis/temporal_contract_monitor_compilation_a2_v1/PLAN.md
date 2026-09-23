# #1743 A2 temporal-contract monitor compilation

Direct predecessor #1719 is immutable and consumed. Candidate monitor is byte-identical to parent Git blob c4c812b3e53917fd4ce102f14b689339d580ed20.

One changed factor: P_CONTINUOUS_FOR reference evaluation preserves every same-timestamp Boolean fragment in arrival order instead of collapsing a timestamp to its final Boolean value.

The inherited corpus, event-family semantics, malformed controls, state shape and six mutation controls are unchanged. Hard corpus gates: 1,062,624 traces and 5,144,928 prefix checks.

H: the 168 parent mismatches disappear when false->true transitions at one timestamp reset continuity correctly.

T: directed retained counterexample preflight, source-first readback/freeze, one inherited exhaustive formal invocation, independent full re-enumeration.

D: PASS_TEMPORAL_CONTRACT_MONITOR_COMPILATION_A2_SCOPED only with mismatch0 in both analyzers, exact parent corpus counts, retained counterexample PENDING in candidate/oracles, outcomes/malformed/state-shape gates unchanged, corruption6/6, formal1/reruns0/replacements0/tuning0.

C/U: one-shot discrete timestamp-fragment theorem only; no dropped-event, multi-clock, repeated-obligation, GUI, model, latency or product claim.
