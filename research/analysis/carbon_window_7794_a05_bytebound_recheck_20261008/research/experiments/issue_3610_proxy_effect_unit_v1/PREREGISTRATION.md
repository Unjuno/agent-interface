# Issue #3610 — first proxy effect-binding unit

Parent idea: #3584. Allocation ID: `issue3610-proxy-effect-unit-formal-01`.

## H/T/D/C/U

- **H:** Four representation arms can perform the same non-destructive GTK counter operation while refusing stale, replaced, unavailable, ambiguous, and macro-failure states. An acknowledged click with no application effect must yield and never be success.
- **T:** One fresh GTK3/Xvfb fixture per row, 4 arms × 7 cases = 28 rows. Cases: positive; input acknowledged/no effect; stale version; replaced process/window; unavailable target; ambiguous duplicate targets; injected macro failure. Same task information and common guarded executor across arms. Source binds process PID/start ticks, XID, version, and counter. One formal container invocation, no retry; raw UI frames, proxy image, requests/replies, effect events and cleanup retained.
- **D:** PASS only for 28 unique rows; positive effects exactly 0→1; each negative case yields/refuses with zero task effects (no-effect may emit one click but must report YIELD); current identity/version checked before emission; release, audit, hashes, and process/socket cleanup complete. Any unsafe task effect is FAIL; incomplete setup/evidence STOP/HOLD. No arm winner.
- **C:** Fixture, task, geometry, state schema, executor, pinned image; only representation and declared control vary.
- **U:** No model/human comparison, usability, tokens/cost, performance advantage, production authority, general GUI reliability, or integrated desktop claim.

## Frozen controls and representation arms

The arms are `ordinary_screenshot`, `proxy_image`, `structured_proxy`, and `hybrid`. The fixture asks only to increment its visible counter exactly once. The proxy image is a PPM rendering of the same observed counter and one increment operation. Structured/hybrid arms use the same source-bound state token; all arms go through the same final identity/version/effect guard. `no_effect` accepts the native click but deliberately suppresses the GTK state change. Stale version is created by a fixture-owned signal handler. Replacement launches a new fixture incarnation on the same display. Unavailable unmaps the target; ambiguous launches a second matching target. Macro failure stops before input.

The runner does not invoke a language model. Time/cost/token comparisons are out of scope.

## Container

OrbStack local image `sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27`, Linux/arm64, network none, read-only root; source mounted read-only and a fresh evidence directory read-write. The exact invocation and image identity are retained in `FREEZE.json`.

## One-shot rule

Construction tests and a non-GUI dependency preflight may run before formal. The 28-row formal runner is invoked once. Preserve any startup failure or partial matrix as STOP/HOLD/FAIL; do not repair and rerun this allocation.
