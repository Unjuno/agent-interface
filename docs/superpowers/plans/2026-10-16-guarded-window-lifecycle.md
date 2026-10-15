# Guarded X11 window lifecycle integration

Goal: refuse stale same-process XID reuse through the standard guarded MCP caller.
Scope: explicit Fake X construction and opt-in implementation, no live allocation.
This follows the current consolidation work map and unresolved #5/#59 boundaries.

- [ ] Subscribe on each target itself using StructureNotify on the existing dedicated
  query connection. Validate its own event mask after a round trip. Drain a bounded
  event queue; Destroy, synthetic/malformed/unexpected events, transport failure or
  lost coverage make the reader permanently unavailable. Preserve repaint/remap/
  reparent continuity; a new reader has a new opaque token. No root inventory,
  event sequence number, process ID or pixels alone becomes window incarnation.
- [ ] Add an explicit window_lifecycle policy requiring process_identity and
  query_worker. Keep active visual isolation usable. Bracket every observation,
  retain/deliver window_generation, compare it in handles, and verify the original
  source again before each new key/button/activation request. Releases bypass reads.
- [ ] Forward startup policy through bridge, owner, create_server and CLI. Tool
  calls cannot toggle it. Keep existing unselected modes unchanged.
- [ ] TDD: direct subscription coverage/reparent, Destroy/reuse, new reader,
  malformed/synthetic/mask loss/overflow and transport failures. Compose actual MCP,
  bridge, handles, dispatch/session/backend with Fake X; unchanged positives,
  old-alias rejection, modifier-prefix release, activation, capture-time change,
  blocked lifecycle cancellation/expiry and late-answer retirement. Check both
  ordinary and isolated observation paths.
- [ ] Run affected guarded/CLI/distribution tests normal and optimized where
  applicable. Preserve RED/first failures/final logs/source hashes and exact scope.
  Review/integrate using actual protection and local checks, without reviewer quota.

Limits: trusted local X server, reliable ordered connection and honest event
semantics are assumptions. This remains sampled check/use, not atomic XTEST target
execution, unknown-loss detection, durable identity or a physical release bound.
Native subscription/reparent/toolkit behavior, live task effect/recovery and
matched economics remain unqualified until a separately authorized fresh run.
