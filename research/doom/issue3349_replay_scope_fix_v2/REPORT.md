# Issue #3349 replay/identity correction v2

Decision: **PASS_REPLAY_IDENTITY_CORRECTION_SCOPED**

The existing v3 full-runner candidate already made retained-event replay opt-in and fail-closed on duplicate terminal evidence, but its production-style `_submit()` still waited on a broad `accepted|rejected` predicate and checked the identifier only afterward. This leaves a stale-response interruption: an old accepted/rejected event can be returned first while the valid fallback response remains queued.

This continuation copied exact main candidate blob `ec16c9bbb72e02662f31d195cb3bfc9339af5c19` and changed exactly one predicate in the additive full-runner copy:

`accepted|rejected` -> `accepted|rejected AND id == requested identifier`.

GitHub readback of the corrected full runner is blob `471db061f24d9f96a706e1ec39ffec93aa5a001d`, 24,010 bytes.

## First outcome

Nine deterministic protocol cases, one invocation, no retry/tuning:

- old semantics: stale accepted and stale rejected each abort before the matching fallback response; old stale failures 2/2;
- corrected semantics: matching fallback returned in both; corrected stale failures 0/2;
- matching rejection remains an explicit error;
- unrelated/malformed rows do not satisfy submit and a later matching response is accepted;
- exact single retained terminal replay succeeds;
- duplicate retained terminal is ambiguous and fails closed;
- wrong-ID retained terminal does not satisfy replay.

Independent raw-only audit: errors=[].

Raw SHA-256: `8bcaf2c1d52b217ad96199144b0a63816205b2ab58ced22f943f045ea18badff`.
Audit SHA-256: `1dd581688aec504969db0a4e34e1780f28bfe1b5a1bde33e2af4b26681c4e408`.
Experiment source SHA-256: `da3deeca2fd847e0fa6a297dca838ce20f9ee3bcea163783cf9ce03e2ccbd82d`.
Audit source SHA-256: `cbc3c2ebe0226b759549652b5e1f6c42a36af6c851bdf62b07d7fd7c1de972ef`.

## Scope

Protocol/harness semantics only. No ViZDoom, X11, model, task input or recovery efficacy was exercised. #3243's later BOUNDED_RECOVERY input-bound failures remain unresolved and must not be relabelled by this PASS. A future live matched allocation needs a fresh identity, source freeze and #60 coordination.
