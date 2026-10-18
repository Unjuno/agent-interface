# Within-task recoverable-pause trajectory measurement

Issue #8902 proposes representing safe pauses, recovery attempts, and resumed work as transient within-task states when evaluating route performance. It remains an unverified method-transfer proposal; it does not claim current recovery routes are mismeasured, safe, or more effective.

## Recoverable pauses as within-task transitions — #8902

- **Status:** open and unverified; no experiment, implementation, or evidence PR is recorded.
- **Source:** [Issue #8902](https://github.com/Unjuno/agent-interface/issues/8902); [#5593 first-terminal outcome curves](https://github.com/Unjuno/agent-interface/issues/5593).
- **Idea:** Keep one assigned task episode open across a transient safe pause, recovery attempt, and resumed execution. Distinguish these transitions from absorbing verified success/failure, terminal safe stop, abandonment, and administrative loss of follow-up. Report success by deadline from the original launch (including recovery time), terminal cumulative incidence, transition counts, recurrent pauses, time in state, and unresolved episodes with censoring cause.
- **Proposed method test:** Use complete finite event histories for two synthetic routes, including zero pause, pause-then-success, repeated recovery, failed recovery, terminal safe stop, wrong-effect failure, abandonment, and administrative censoring. Compare exact enumeration with lossy comparators that make the first pause absorbing or omit recovery duration. Independently audit assignment denominator, launch boundary, event identity/time/clock, transitions, deadline success, and restricted time-in-state; mutate pause type, recovery interval, timestamp, and assigned-episode presence.
- **Decision boundary:** A method PASS would validate only the finite transition-accounting fixture. It would not establish empirical route benefit, real recovery-state incidence, censoring assumptions, or Markov behavior. If same-episode identity, transition evidence, clocks, or final effect cannot be independently established, the result remains HOLD; use direct proportions rather than a multi-state estimator when a complete finite cohort suffices.

## Neighboring questions

#5593 concerns first-terminal competing outcomes and notes the recoverable-pause gap; #5962 concerns mission survival across a sequence of tasks. #7042 tests whether recovery actually removes failure-enabling state, and #30 proposes an observation-only recovery channel. #8902 is an evaluation estimand for transient and recurrent states inside one assigned task, not a recovery mechanism or safety certificate.
