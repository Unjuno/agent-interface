# Issue #5817 finite conservation T0

This synthetic deterministic study compares task-status-only admission, strict global wait, and a cross-task unresolved-obligation ledger with resource-dependency checks. Eleven frozen histories exercise delayed effects, timeouts, transfer/acknowledgement, owner crash, child release, compensation, resolution, and resource-footprint ambiguity. The independent auditor reconstructs every prefix and all next-task decisions from `fixture.json`.

The H/T/D/C/U preregistration is `PLAN.md`; `FREEZE.json` binds the allocation, image, branch, counts and source digests. The formal candidate and separate auditor each run once in isolated Docker containers. A consumed or failed allocation is retained without retry. Raw outcome, audit, container inspection, invocation counts, and checksum are kept under `results/<allocation>/`.

Scope is strictly fixture-level: obligation accounting is not evidence that a GUI effect happened, that an app exposes a complete footprint, or that a ledger survives a real crash. Unknown stays unresolved; transfer, timeout, escalation, inverse emission, and task completion do not discharge an obligation.

Construction tests:

```sh
python -B -m unittest research.analysis.obligation_conservation_5817_t0_v1.test_t0 -v
```
