# Generation fence after explicit claim reclaim

Task `COORD-GITHUB-CLAIM-FENCE-20260916-007`, Issue #396.

**Decision: `PASS_GENERATION_FENCE_SCOPED`.**

This is a narrow coordination fixture. It tests what happens **after** an explicitly authorized reclaim has advanced a canonical claim generation. It does not define when expiry/reclaim is legitimate and does not make elapsed time or an UNKNOWN outcome sufficient to reclaim.

## Frozen mechanism

A writer is current only when both `owner_id` and `generation` match the current register. Reclaim authorization is fixture-provided; an accepted reclaim must advance generation by exactly one. An old-generation writer that re-reads a newer generation receives `FENCED_STALE` and no fresh-SHA retry.

Freeze commit: `a1e16229dc17cb203e3b18c9e17f31114f0ff865`.

## Measured first outcomes

| Case | Outcome |
|---|---|
| current_generation_control | A/g1 classified CURRENT_OWNER; GitHub update succeeded at commit `8bef5b6f...`; final generation remains 1 |
| different_owner_reclaim | B/g2 reclaim succeeded `f2145e54...`; late A/g1 write with old blob SHA returned GitHub 409; readback is B/g2; policy => FENCED_STALE; no retry |
| same_owner_new_generation | A/g2 reclaim succeeded `bcb6c1a1...`; late A/g1 write with old blob SHA returned GitHub 409; readback is A/g2; policy => FENCED_STALE; no retry |

Totals: 3 successful measured commits, 2 old-generation stale-write attempts, 2 explicit GitHub file-SHA mismatch 409s, 2 post-409 readbacks, 2 `FENCED_STALE` decisions, and 0 fresh-SHA retries by a fenced writer.

The same-owner control is the discriminating result: logical owner equality alone does not revive an old generation.

## Interpretation

GitHub file-SHA CAS blocks the first stale write. The added generation test addresses the next step: even after the old writer learns the fresh register state, it remains unable to turn that fresh SHA into authority because its generation is obsolete.

This is a fencing building block for coordination state only. To fence an external side effect, that external receiver would also have to check the generation. A GitHub-register fence by itself cannot revoke authority already granted elsewhere.

## Evidence boundary

The two reclaim events are explicit fixture interventions. No timeout, TTL, wall-clock age, missing acknowledgement, or UNKNOWN state is treated as reclaim authority. Therefore this experiment does not solve the terminal-UNKNOWN liveness problem; it only establishes the post-reclaim stale-writer rule at this scope.

The 409s are GitHub Contents API stale-file-SHA responses. The schedules are sequential, not simultaneous HTTP requests. `verify.py` is retained as deterministic offline checking code; no independent-agent execution is claimed by this report.

## Limits

One repository, branch, connector and three authored schedules. No clock skew, network partition, permission change, authentication, simultaneous-request linearizability, lease expiry, fairness, external task effect, rate/latency, production authorization, or exactly-once execution claim.

## Next single question

A useful next discriminator is the missing authorization side: given a terminal UNKNOWN claim, what evidence is sufficient to permit a generation-advancing reclaim without allowing two living owners? Keep fencing fixed and vary only the reclaim predicate; do not use elapsed time alone as proof that the old owner is dead or uncommitted.
