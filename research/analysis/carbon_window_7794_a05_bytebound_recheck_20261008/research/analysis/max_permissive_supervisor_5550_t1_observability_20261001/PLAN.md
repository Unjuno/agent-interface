# Issue #5550 successor T1 — indistinguishable fresh/stale state

**State: preregistration; no candidate or audit run has occurred.** This is a
new synthetic successor and does not alter T0 or its window STOP correction.

## H / T / D / C / U

- **H:** If `ACTED` and `STALE` are observationally indistinguishable, a
  belief-safe supervisor must disable `COMMIT` but can preserve a common safe
  `REVALIDATE` action that returns either plant state to `READY`.
- **T:** Extend the frozen T0 finite plant with `REVALIDATE` from `ACTED` and
  `STALE` to `READY`; merge those two states into one observation class. Run
  one candidate that enumerates actions safe across the entire belief set,
  followed by a separate auditor that uses a literal transition table and
  independently enumerates all controllable-edge subsets. Test exact action
  inclusion/exclusion and reject corrupted candidate decisions.
- **D:** Scoped PASS only if the belief-safe policy enables `REVALIDATE`,
  disables `COMMIT`, all enabled actions are defined and safe in every
  consistent plant state, the independent exhaustive oracle agrees, and all
  preregistered corruption controls are rejected. Otherwise FAIL/STOP without
  altering inputs or retrying the candidate/audit.
- **C:** This tiny model deliberately adds a perfectly effective
  `REVALIDATE`; progress may be entirely due to that hand-authored edge. A
  real observation may itself be stale or fail to distinguish states.
- **U:** Host-only deterministic finite model. No GUI, real event classifier,
  observation freshness, timing, fairness, user effects, utility, runtime
  integration, or transfer claim. This is not a reproduction of the expired
  OrbStack allocation.

## Frozen protocol

1. Record the current GitHub `main` SHA and SHA-256 of candidate, auditor, and
   tests in the freeze receipt after this preregistration is committed.
2. Run construction tests once; if green, run the candidate once and preserve
   its output byte-for-byte.
3. Run the independent auditor once against only the retained raw output.
4. No retries or expected-value edits. Container execution is not part of this
   host-only successor and no shared runtime lane is touched.
