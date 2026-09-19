# Evidence-bound reclaim predicate for UNKNOWN claim

Task `COORD-GITHUB-RECLAIM-EVIDENCE-20260916-008`, Issue #402.

**Decision: `PASS_EVIDENCE_BOUND_RECLAIM_SCOPED`.**

This is a narrow coordination-fixture result. It keeps the generation fence from #396 fixed and changes only which evidence may authorize a generation advance from a generation-1 UNKNOWN claim.

## Frozen rule

Reclaim evidence must bind the exact current `owner_id`, `generation`, and `claim_id`. Accepted terminal forms in this fixture are:

- owner-issued `RELINQUISHED`;
- trusted-supervisor `TERMINATED`.

Elapsed time alone is never sufficient. Missing generation binding or a stale generation is insufficient.

## First measured outcomes

| Case | Frozen decision | GitHub mutation | Final state |
|---|---|---|---|
| elapsed_only | `HOLD_UNKNOWN` | none | A / generation 1 / UNKNOWN |
| owner_relinquish_exact | `ALLOW_RECLAIM` | one gen2 reclaim; old gen1 attempt -> HTTP 409 | B / generation 2 / ACTIVE |
| supervisor_terminal_exact | `ALLOW_RECLAIM` | one gen2 reclaim; old gen1 attempt -> HTTP 409 | C / generation 2 / ACTIVE |
| stale_relinquish_generation | `HOLD_UNKNOWN` | none | A / generation 1 / UNKNOWN |
| unbound_terminal | `HOLD_UNKNOWN` | none | A / generation 1 / UNKNOWN |

Positive cases each performed one post-409 GET. The current register was generation 2, so the fixed generation fence classifies old A/g1 as `FENCED_STALE`; no fresh-SHA retry was sent.

Totals: two successful reclaim commits, zero writes in the three negative cases, two old-generation late attempts, two explicit GitHub file-SHA mismatch 409s, and zero fresh-SHA retries.

## Interpretation

Within this fixture, elapsed time and weak terminal evidence are correctly weaker than an exact terminal record. Exact binding is material: a terminal record for generation 0 does not reclaim generation 1, and a terminal record with no generation field does not reclaim at all.

The result does **not** establish that the positive terminal records are authentic or truthful. Their trust is fixture-provided. In a real system, owner relinquish must be defined as authority surrender, and supervisor evidence needs an authentication/trust model.

The generation fence is also only useful where checked. If task effects are accepted by another service, that service must check the same generation to reject delayed old-generation effects.

## Evidence boundary

Publication BASE: `b3bc631d2c6dfae8586bb28abdc9eb2002bb624b`.
Pre-measurement freeze: `37c12944adc71058fcc24da52ad00aebab0d30da`.

Measured successful reclaims:

- owner relinquish -> commit `1314724299367f6b552bdbf49a59fc16064c1f55`, blob `e7c8524f6fc316eb2af793c5756e724a2c94269a`;
- supervisor terminal -> commit `100af190f253ead1d3b68091cc7e21ad50101c38`, blob `f3d40dfc072f6f8717d1683d10a77248bb409f17`.

Both late gen1 attempts returned GitHub Contents API 409 file-SHA mismatch responses. `verify.py` is retained for deterministic offline checking but no independent-agent execution is claimed.

## Limits / next single question

No real TTL, liveness detector, process authentication, signed relinquish, clock skew, network partition, external effect receiver, or production reclaim semantics were tested.

Next single question: keep this exact evidence predicate and generation fence fixed, and test **evidence authenticity/binding at the writer boundary**. Can an owner relinquish record or supervisor terminal record be tied to an authenticated principal/context strongly enough that a forged record cannot advance generation? Do not add timeout-based reclaim in the same rung.
