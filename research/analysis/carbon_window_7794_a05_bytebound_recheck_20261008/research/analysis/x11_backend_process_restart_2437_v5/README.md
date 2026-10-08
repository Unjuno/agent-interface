# Issue #2437 — backend-process restart, multi-control extension

This directory retains the preparation and STOP evidence for a proposed fifth allocation. It contains **no formal candidate raw**: allocation 05 was stopped before freeze/launch because the required exclusive shared Docker/OrbStack slot was not assigned.

- `PREPARATION_V5.md` — H/T/D/C/U, proposed decision rules, exact candidate source hashes, and construction gates.
- `STOP_ALLOCATION_04.md` — prior version's inconclusive audit; preserved independently and not pooled.
- `STOP_ALLOCATION_05.md` — current pre-launch coordination STOP.
- `SHA256SUMS` — hashes for every retained artifact.
- `ENVIRONMENT.md` — host preparation and scope.

The private Xvfb test is only a host-side construction preflight. It is not a substitute for the requested Docker lane and does not establish the scientific hypothesis. On a future explicit grant, recheck current main, owners, queue and image identity, then create a new freeze; do not resume this proposal blindly.

Related retained evidence: [PR #5618](https://github.com/Unjuno/agent-interface/pull/5618) records earlier backend-restart FAIL/STOP outcomes. Those outcomes remain separate; none is rewritten or pooled here.
