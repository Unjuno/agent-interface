# Issue #3619 — formal-02 result

## Decision

`HOLD_EVIDENCE_INCOMPLETE`. The 28-row runner completed without row exceptions and the independent audit verified the raw/source/frame/event hashes, row accounting, process/socket cleanup, and four mutation challenges. Two preregistered safety gates did not pass: the ambiguous-target control was not established before dispatch, and release state was not independently observable. This is not a proxy-safety PASS and does not choose a representation arm.

## Observed rows

| Case | Rows | Runner decision / observation |
|---|---:|---|
| Positive | 4/4 | One click acknowledgement and exact GTK counter 0→1 effect |
| No effect | 4/4 | Click acknowledged, counter unchanged, `YIELD_NO_APPLICATION_EFFECT` |
| Stale version | 4/4 | `REFUSE_STALE_BINDING`, zero emission/effect |
| Target/process replaced | 4/4 | `REFUSE_STALE_BINDING`, zero emission/effect |
| Unavailable | 4/4 | `YIELD_TARGET_UNAVAILABLE`, zero emission/effect |
| Macro failure | 4/4 | `YIELD_MACRO_FAILURE`, zero emission/effect |
| Ambiguous duplicate target | 4/4 | Control was not present at dispatch: current state saw one target; the second fixture's `ready` event followed the click/effect. Each row emitted one click and changed the counter, then observed two targets. This does not establish that action occurred while ambiguity was present; the intended negative control is invalid/incomplete. |

The release observer set `release_verified=false` in all 28 rows. The source called `conn.query_pointer(...)`, but python-xlib exposes `query_pointer()` on the root window resource; the runner swallowed the resulting `AttributeError`. XTest press/release calls appear in the emission path, but the independent release gate is unverified, so no release-safety claim is made.

## Audit and immutable evidence

- Formal invocation: 1; retries: 0; rows: 28; runner row errors: 0.
- Independent audit: `HOLD_OR_FAIL_PROXY_BINDING_EFFECT_UNIT`, 44 gate errors (28 release-verification gaps and four each for the unestablished ambiguous scenario, unexpected decision, effect count, and negative-control emission).
- Corruption challenges: 4/4 detected.
- Raw JSON SHA-256: `8ec91661284ec0bef7efd2d6a06955085acec224980704eb49e27494fe0db8d9`.
- Audit JSON SHA-256: `a25508ef7661ef679b5bde84a6a8a5191c1db44d9a733955cd1b3e79a4d899b5`.
- Formal preflight receipt SHA-256: `22c4aaf56faf7593fbc8842a1d2d343abe1b6169f6a39181a9ae44bc17823ab3`.
- Source commit: `20c3afbc4e03b5dea94e2e04bce430e39c0e92ff`; source-manifest SHA-256: `bf5368f40296d40d1a5da0cdc4018645e66067c22ce2c31b61a26599fb731ebc`; freeze SHA-256: `c9fcb551f3cdf5b2e605a65d428d476d1942b870dd9f1f0a49b0297789c5909a`.
- Image: `sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27`, Linux/arm64; network none, read-only root/source.

All row JSON, fixture event logs, raw X11 frame bytes, and proxy images are retained alongside `raw.json` and `audit.json`. No formal retry was made. A new successor is required for a fresh allocation that synchronizes target replacement before dispatch and uses the correct root-window pointer query; formal-02 remains immutable.

## Scope limit

This was a deterministic non-model fixture unit. It provides no human/model usability comparison, token/cost result, latency advantage, general GUI reliability, production authority, or integrated desktop claim.
