# Durable effect receiver generation fence after reclaim

Task `COORD-DURABLE-EFFECT-GENERATION-FENCE-20260916-010`, Issue #422.

**Decision: `PASS_DURABLE_EFFECT_GENERATION_FENCE_SCOPED`.**

This is a narrow GitHub-backed durable receiver fixture. It tests receiver-side generation admission after generation 2 is already durably installed at the receiver. It is not a live process/service, network protocol, crash-recovery study, or production exactly-once claim.

## Frozen single-factor comparison

Both receivers began with `accepted_generation=2`, empty effects and empty receipts. They use identical request-ID/content replay rules. The only policy difference is whether a new unseen request must also match `accepted_generation`.

Requests:

- delayed old: `cmd-old-010`, generation 1, payload `{"delta":3}`;
- current: `cmd-new-010`, generation 2, payload `{"delta":5}`;
- exact replay: byte/field-identical to current;
- conflict control: same `cmd-new-010` ID, generation 2, payload `{"delta":7}`.

## First outcomes

### Idempotency-only negative control

The delayed generation-1 request had a new request ID, so the idempotency-only policy admitted it and one stale effect was durably written in commit `23b3dc57f6e4e3dc0a6f4a04e944d00c10a04700`.

The generation-2 request then committed a second effect in `f3f1721c15a34e8f3027e19c56db6fdc0016deca`. Exact replay sent no write. Final effect count: **2**, including **1 stale-generation effect**.

This negative control demonstrates that request-ID idempotency alone does not encode current authority generation.

### Generation-fenced candidate

The delayed generation-1 request was classified `FENCED_STALE`; no write was sent and the empty receiver remained unchanged.

The generation-2 request committed exactly one effect in `79d3a9eba6b2e9233d9cbef4aec2248f827081b0`. Exact replay classified `REPLAY_APPLIED` with no write. Same-ID/different-payload classified `CONFLICT` with no write.

Final effect count: **1**. Stale-generation effects: **0**. Current-generation effects: **1**.

## What this establishes

Once receiver-side accepted generation has already advanced to 2, an explicit equality gate is sufficient in this fixture to prevent a delayed generation-1 request from creating an effect, while preserving the existing durable idempotency/content-binding behavior for the current generation.

## Boundary

The experiment deliberately starts after durable receiver-generation propagation. It does **not** show that coordination-register reclaim and receiver-generation advance are atomic. A delayed generation-1 request arriving in the propagation gap remains the next unresolved boundary.

GitHub Contents files are the durable receiver records here. There is no separate process, SQLite database, network service, real external effect, crash/power-loss injection, concurrency, latency/rate or production authorization claim.

## Next single question

Keep receiver generation checking and idempotency fixed. Introduce only the propagation gap between coordination generation advance and receiver accepted-generation advance. Determine whether a two-step handoff permits an old-generation effect in that gap, and if so whether an activation barrier can close it without allowing two active generations.
