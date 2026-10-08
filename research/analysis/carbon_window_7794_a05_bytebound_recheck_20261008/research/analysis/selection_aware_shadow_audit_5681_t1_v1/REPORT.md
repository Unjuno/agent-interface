# Selection-aware shadow audit T1 — STOP receipt

**Disposition: `STOP_CANDIDATE_COMMAND_DIVERGENCE`. No scientific result.**

Issue #5681's finite construction was assigned allocation #03 for an isolated local OrbStack/Docker run. The candidate container was invoked once, but the command called `candidate.build()` through `runpy` and printed a Python dictionary instead of running the candidate CLI and saving its JSON output. The rendered output was truncated and no byte-exact raw artifact or explicit exit code was retained. The independent raw-only auditor therefore had no valid input and was not run. Candidate count=1; auditor count=0. The allocation must not be retried.

The frozen design remains a proposed method test only: event-dependent suppression, a label-independent null, zero-inclusion refusal, and an out-of-frame transient. Because the required independent audit did not run, none of the design's decision gates are evaluated and `METHOD_PASS_SCOPED` is not supported. T0 remains `HOLD_NO_ELIGIBLE_SOURCE`; no empirical GUI claim or change to prior A1/A2 evidence follows.

Execution identities, the exact divergent command, environment/image versions, source hashes, and evidence limitations are recorded in [STOP.md](STOP.md). Local tests, if run, are source validation only and cannot change this disposition.
