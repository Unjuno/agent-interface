# DECISION-POLICY-CACHE-RUNG0-20260918-001
H: one already-authored bounded policy can be reused across local cycles with a deterministic monitor, matching a per-cycle semantic oracle while avoiding repeated semantic decisions and yielding before stale continuation.
T: compare REDECIDE_EVERY_CYCLE versus CACHED_POLICY_DETERMINISTIC_MONITOR on identical generated traces; exact strategy/macro/evidence/effect oracle fixed; required regimes VALID_CONTINUATION, HARD_INVALIDATION, AMBIGUOUS_BOUNDARY plus generation/provenance/expiry/intent/strategy/max-update controls.
D: PASS cache semantics iff disposition/effect mismatch0, stale continuation0, missed invalidation0, unnecessary yield0, authority actions0, semantic calls strictly reduced, source/audit integrity pass. Independently record HOLD_DETERMINISTIC_MONITOR_SUFFICIENT_FOR_SUPERVISOR if every ambiguous case safely YIELDs with no residual requiring a learned supervisor.
C: saved semantic calls can be explained by deterministic envelope checks; this is intentional and does not prove a learned supervisor or live planner-gap benefit.
U: synthetic deterministic Rung0 only; no model/GUI/task input, no live timing or general task claim.
