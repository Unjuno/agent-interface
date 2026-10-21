# Telemetry-aware resource allocation

## Issue #8897: the encoder/allocation boundary

**Status:** Open, unverified transfer and method proposal.

**Idea.** Test whether a resource allocator makes better work-selection decisions when given bounded, freshness-tagged telemetry, after charging telemetry collection, communication, and retained history against the same finite budget as useful work. Keep allocator rules fixed while varying direct oracle state, noisy/delayed PSI-like signals, sampled guest/cgroup counters, bounded summaries, and explicit UNKNOWN for stale or missing telemetry.

The proposed finite model includes mandatory verification/freshness obligations, recoverable execution, optional analysis, deadlines, regime changes, dropout, correlated metric errors, guest/host disagreement, and telemetry cost. It compares queue/deadline-only scheduling with an oracle upper bound and audits every allocation row and obligation. This is an information-channel/scheduling experiment; it is not a WSL memory fix, OOM-prevention result, host-pressure authorization, or evidence that telemetry should control production work.

**Current evidence:** No implementation or allocation result is reported for #8897. The question is whether telemetry has decision value at matched work and telemetry budgets, not whether a new PSI threshold should be deployed. See [Issue #8897](https://github.com/Unjuno/agent-interface/issues/8897).

## Related evidence: #8488

#8488 tests pressure-triggered shedding before freshness collapse. Its correction in merged [PR #8491](https://github.com/Unjuno/agent-interface/pull/8491) withdraws the earlier `NO_RESIDUAL`: the frozen protocol treats the deadline as exclusive, but the candidate and auditor both treated completion at the deadline tick as on time. A read-only reconstruction found 8/32 rows differed; corrected miss counts were fixed=4, queue/deadline=3, free-memory=4, PSI=1. PSI was lower than both comparators in that trace but failed the preregistered zero-PSI-miss gate. Disposition: `HOLD_DEADLINE_SEMANTICS_MISMATCH`. Candidate and auditor were not rerun; container preflight remained STOP, so no container experiment is claimed.

This corrected finite trace does not validate #8897's telemetry-channel hypothesis or establish a pressure-triggered policy. It also does not imply any worker-wide stop: the STOP concerns that container preflight/allocation only. See [Issue #8488](https://github.com/Unjuno/agent-interface/issues/8488) and the merged qualification record.
