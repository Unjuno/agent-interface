# Bandwidth inheritance for blocked verifier budgets

- **Status:** Finite model result passed; implementation and host scheduling remain untested.
- **Source:** Issues [#7944](https://github.com/Unjuno/agent-interface/issues/7944) and successor [#7979](https://github.com/Unjuno/agent-interface/issues/7979).
- **Idea:** Test whether a bounded Bandwidth Inheritance policy can charge a depleted resource holder to a blocked verifier's reservation and meet freshness deadlines where home-charged priority inheritance cannot.
- **Outcome:** Successor A01 `PASS_METHOD_SCOPED` / `H_PASS_SCOPED`: a deterministic integer-tick single-CPU model independently reconstructed 27 traces and 63 events. In the budget-inversion case, BWI completed at tick 2 while NONE and home-charged PI completed at tick 8 after a tick-4 deadline; no-contention traces were identical. Two-waiter and insufficient-budget controls exposed limits. This is not an OS-scheduler implementation or host real-time guarantee. Merged [PR #7994](https://github.com/Unjuno/agent-interface/pull/7994) preserves the successor allocation.
