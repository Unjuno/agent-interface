# Issue #6645 — T0-C formal result

## Disposition

`PASS_METHOD_SCOPED` for allocation `CGREF-6645-T0C-ORB-20261003-03` only.
The candidate and separate raw-only auditor each ran once in separate pinned
OrbStack Docker containers; both exited 0, both report `OOMKilled=false`, and
the independent audit returned PASS with zero errors. Ten fixture rows were
preserved. Retries: zero.

## Result

The candidate preserved all three equally minimal singleton guard refinements
instead of tie-breaking on hidden truth, then admitted only where every
alternative was satisfied. It refused all seven fixture states marked harmful
(zero false admissions), while retaining the ordinary valid common control.
The valid rare control and an identically observed harmful stale-target state
both returned UNKNOWN/fallback. The three held-out harmful families were all
refused; the hidden-family/out-of-envelope case returned UNKNOWN, and the
out-of-envelope no-fallback case stopped. Both specializations depending on
the changed shared predicate were invalidated; the independent sibling was
retained. No row replayed task input or added authority.

| Policy | False admissions / 7 harmful states | Valid-control behavior |
|---|---:|---|
| Unchanged guard | 7 | Admits all three, including harmful states |
| Exact-state blacklist | 6 | Admits controls, but misses held-out harms |
| Invalidate all | 0 | Conservatively admits none |
| Candidate consensus over all minimal refinements | 0 | Admits common control; UNKNOWN for observationally ambiguous rare control |

Mutation checks (false admission, dropped sibling invalidation, tie-break,
authority/replay escape, and changed fixture truth) all failed closed in the
13/13 construction suite. Construction is separate from the one formal
candidate/auditor pair.

## Scope and caveats

This is only a finite authored state machine with an authored effect oracle and
declared predicate-coverage envelope. It does not establish automatic
production guard synthesis, completeness of real observations, GUI behavior,
user outcomes, safety, or latency/token benefit. The rare safe state is
deliberately UNKNOWN because it is observationally identical to a harmful
held-out state. `memory=512m` and `memorySwap=1GiB` are Docker configuration
observations, not evidence of host/cgroup enforcement; no memory-pressure test
was run. The A01 and A02 preformal STOPs remain unaltered and are listed in
`RUN_RECORD.json`.

Exact freeze, commands, runtime identity, invocation counts, and raw paths are
in [`FREEZE.json`](FREEZE.json) and [`RUN_RECORD.json`](RUN_RECORD.json).
