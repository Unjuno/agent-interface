# Issue #7865 A01 — finite history-conditioned compensation test

Allocation: `UNJUNO-7865-HCC-A01-20261005`. See `FREEZE.json` for input hashes, exact runtime identity, invocation commands, and no-retry rule.

## Result

Candidate and independent raw-only auditor each ran once in the pinned offline WSLc Python image; both exited 0 with zero retries. The auditor reports `PASS_METHOD_SCOPED`, `errors=[]`, and exact case agreement.

On the finite fixture, blind whole-snapshot inverse erased a disjoint external field update. The validated whole-object generation guard refused compensation after any generation change. Field-scoped compare-and-compensate restored the agent-owned field after a known disjoint update while preserving the other field. It refused same-field changes and ABA, and returned conflict/unknown for object replacement, incomplete or uncertain history, version-integrity failure, and unverified footprint. Every accepted recovery was recorded as a new compensating effect; none claimed literal rollback.

## Limits

This is a deterministic synthetic method fixture. It does not verify any live application's object identity, generation semantics, event-history completeness, write footprints, field independence, undo behavior, task success, or deployment. The requested 512 MiB container setting is not a verified hard limit: WSLc warns that swap-limit/cgroup support is unavailable. No GUI, model, network, or external effect was used.

## Evidence

`formal/` preserves raw candidate/auditor output, stderr, and exit/argv metadata. `SHA256SUMS.txt` covers the full package except itself; `FROZEN_INPUTS_SHA256SUMS.txt` covers the frozen execution inputs.
