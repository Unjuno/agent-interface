# Issue #3626 — preregistration, formal-03

This is a fresh, immutable allocation after #3619 formal-02 HOLD. It does not modify or rerun either predecessor. Allocation ID: `issue3626-proxy-effect-unit-formal-03`.

## Hypothesis and scope

In a disposable GTK counter fixture, requiring two independently ready, distinct, viewable targets before the ambiguous negative-control decision prevents action while ambiguity is established. An Xlib query on the root-window resource independently observes Button1 released. This is a deterministic adapter/safety unit, not a model or usability comparison.

## Frozen design

- Four presentation arms: ordinary screenshot, proxy image, structured proxy, hybrid.
- Seven fresh cases per arm: positive, acknowledged no-effect, stale version, replaced process, unavailable, two-target ambiguity, macro failure (28 rows).
- Ambiguous setup requires two ready fixture events for the exact child PIDs and exactly two viewable windows with distinct XIDs, all before pre-dispatch state and any emission. Missing setup is HOLD; no action may be emitted.
- Every row records `root.query_pointer()` result/mask after input completion/decision. Button1 must be up and the query must succeed. Missing observation is HOLD.
- Positive case must independently observe exact visible counter 0→1. All other cases must have zero effects; no-effect may acknowledge one click but must yield.
- One formal invocation; no retries. Independent auditor runs separately in a pinned network-disabled container against read-only source/raw evidence.
- Container: OrbStack Docker, image `sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27`, Linux/arm64, network none, read-only root and source, fresh writable output only.

## Decision

PASS only if all 28 identities, decisions, effects, process/socket cleanup, row/artifact hashes, distinct ready ambiguity targets, successful Button1-up observations, and corruption challenges reconcile with zero auditor errors. Any setup/instrumentation/evidence gap is HOLD; any action/effect in established ambiguity or held input is FAIL. No arm winner is tested.

## Limits

No human/model task, usability, latency, token/cost, broad GUI reliability, general proxy-safety, or production-authority claims.
