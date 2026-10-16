# Constrained fault diagnosis: adaptive versus fixed plans

- **Status:** Unverified evaluation-method transfer.
- **Source:** [Issue #8895](https://github.com/Unjuno/agent-interface/issues/8895), successor to #8894; duplicate [#8896](https://github.com/Unjuno/agent-interface/issues/8896) was closed and its useful emphasis is retained here.
- **Idea:** Compare outcome-adaptive configuration selection with a fixed suite for locating failures in one finite constrained fault catalog.
- **Discriminator:** Report executed configurations, adaptive sequential rounds, and fixed-suite makespan under a preregistered worker cap with per-test, reset, and communication costs. If those assumptions cannot be justified, report a tests-versus-rounds/parallelism frontier; fewer tests alone do not imply a faster diagnosis.
- **Boundary:** Adaptive fault localization and multiple interaction testing are established prior art. This is an unverified repository-specific comparison proposal; no result or runtime change is reported.
